"""run_case: intake -> member and clock -> rule resolver -> review agent -> verifier -> overrides. Returns everything the screen shows."""
import os, json, hashlib, time
from . import core, llm, agent

PROMPT_VERSION = "v1"
CACHE = "/tmp/copilot_cache" if os.environ.get("VERCEL") else os.path.join(core.ROOT, ".cache")

def _cached(key, fn):
    try: os.makedirs(CACHE, exist_ok=True)
    except OSError: pass
    p = os.path.join(CACHE, key + ".json")
    if os.path.exists(p) and not os.environ.get("NO_CACHE"): return json.load(open(p))
    v = fn()
    try: json.dump(v, open(p, "w"))
    except OSError: pass
    return v

def normalize(raw):
    """Turn a case header (plus a fax transcription when there is one) into one flat case dict."""
    c = dict(case_id=raw["case_id"], received_ts=raw["received_ts"], channel=raw["channel"], client_id=raw["client_id"],
             requesting_provider=raw.get("requesting_provider"), urgency_header=raw.get("urgency"), urgency_form=None,
             member_id=raw.get("member_id"), patient_dob=raw.get("patient_dob"), date_of_service=raw.get("date_of_service"),
             service_code=raw.get("service_code"), service_requested=raw.get("service_requested"), icd10=raw.get("icd10"),
             clinical_notes=raw.get("clinical_notes"), fax_image=raw.get("fax_image"), fax=None, planted=[])
    if raw.get("fax_image") and not raw.get("clinical_notes"):
        img = os.path.join(core.ROOT, "data", "fax", os.path.basename(raw["fax_image"]))
        h = hashlib.sha256(open(img, "rb").read() + (llm.MODEL + PROMPT_VERSION).encode()).hexdigest()[:20]
        fx, _ = _cached("fax_" + h, lambda: list(agent.read_fax(img)))
        c.update(fax=fx, urgency_form=(fx.get("review_type") or "").upper() or None, member_id=(fx.get("member_id") or "").strip() or None,
                 patient_dob=fx.get("date_of_birth") or None, service_requested=fx.get("service_requested") or None,
                 icd10=(fx.get("icd10") or "").strip() or None, clinical_notes=fx.get("clinical_text") or "",
                 date_of_service=str(core.to_date(fx.get("planned_date_of_service")) or "") or None)
        c["service_code"] = core.service_code_for(c["service_requested"])
        c["planted"] = list(fx.get("embedded_instructions") or [])
    if not c["service_requested"] and c["service_code"]: c["service_requested"] = core.SERVICES.get(c["service_code"])
    return c

def run_case(raw, assume_eligible=False, state=None):
    t0 = time.time(); c = normalize(raw); flags = []
    record = core.deidentify(c["clinical_notes"])
    planted = sorted(set(c["planted"]) | set(core.find_planted_text(record)))
    elig = core.eligibility(c["member_id"], c["client_id"], c["date_of_service"], assume=assume_eligible)
    state = state or elig.get("member_state")
    clk = core.clock(c["client_id"], c["received_ts"], c["urgency_header"], c["urgency_form"])
    gaps = core.intake_gaps(c) if not assume_eligible else []
    if not c["member_id"] and not assume_eligible: flags.append(dict(code="MISSING_MEMBER_ID", detail="No member ID on the request. Eligibility cannot be confirmed."))
    elif elig["status"] == "UNVERIFIED": flags.append(dict(code="MEMBER_NOT_VERIFIED", detail=elig["reason"]))
    for g in gaps:
        if "Member ID" not in g: flags.append(dict(code="MISSING_FIELD", detail=g))
    if clk["conflict"]: flags.append(dict(code="URGENCY_CONFLICT", detail=f"Header says {c['urgency_header']}, form says {c['urgency_form']}. Using the urgent clock."))
    if clk["hours_remaining"] < 0: flags.append(dict(code="OVERDUE", detail=f"Deadline passed {abs(clk['hours_remaining'])} hours ago."))
    if planted: flags.append(dict(code="EMBEDDED_INSTRUCTION", detail="Text in the request tries to direct the reviewer. Ignored: " + " | ".join(planted)[:300]))
    out = dict(case=c, record=record, eligibility=elig, clock=clk, governing=[], excluded=[], result=None, flags=flags, trace=[], verifier_errors=[],
               usage={}, intake_gaps=gaps, info_request=None, model=llm.MODEL, prompt_version=PROMPT_VERSION)
    def manual(reason):
        out["result"] = dict(outcome="MANUAL_REVIEW", rationale=reason, criteria=[], coverage_checks=[], missing_information=gaps, letter_paragraph="", primary_source={})
        if gaps: out["info_request"] = core.info_request_fax(c, gaps)
        out["latency_s"] = round(time.time() - t0, 1); return out
    if not c["service_code"] or not c["date_of_service"] or not record:
        return manual("The request is missing the service, the date of service or the clinical notes, so no rules can be selected. Intake must complete it first.")
    try: gov, exc = core.governing_set(c["client_id"], c["service_code"], c["date_of_service"])
    except ValueError as e: return manual(str(e))
    out["governing"], out["excluded"] = gov, exc
    facts = dict(client_id=c["client_id"], product=core.product(c["client_id"]), member_state=state, service=c["service_requested"], service_code=c["service_code"],
                 date_of_service=c["date_of_service"], urgency=clk["effective_urgency"], requesting_provider=c["requesting_provider"],
                 age_on_date_of_service=core.age_on(c["patient_dob"], c["date_of_service"]), diagnosis_code=c["icd10"])
    try: result, errs, trace, usage = agent.review(facts, elig, gov, exc, record, planted)
    except Exception as e: return manual(f"The model call failed ({str(e)[:120]}). Review this case manually.")
    out.update(trace=trace, usage=usage, verifier_errors=errs)
    if errs:
        result = dict(result, model_outcome=result.get("outcome"), outcome="MANUAL_REVIEW")
        flags.append(dict(code="UNVERIFIED_OUTPUT", detail="The recommendation failed verification: " + "; ".join(errs)[:300]))
    # overrides the model cannot undo
    if elig["status"] == "NOT_ELIGIBLE" and result["outcome"] != "MANUAL_REVIEW":
        result["outcome"] = "ROUTE_NOT_COVERED"; flags.append(dict(code="NOT_ELIGIBLE_ON_DOS", detail=elig["reason"]))
        result["rationale"] = "Member is not eligible on the date of service. " + (result.get("rationale") or "")
    blockers = [g for g in gaps]
    if elig["status"] == "UNVERIFIED" and "Member ID" not in " ".join(blockers): blockers.append("Member verification: " + elig["reason"])
    if result["outcome"] == "APPROVE_READY" and blockers:
        result["outcome"] = "NEED_INFO"; result["missing_information"] = blockers + list(result.get("missing_information") or [])
        result["rationale"] = "Clinically the criteria are met, but the request cannot be approved until intake items are resolved. " + (result.get("rationale") or "")
    for f in result.get("flags") or []:
        if isinstance(f, dict) and f.get("code") and f["code"] not in [x["code"] for x in flags]: flags.append(dict(code=f["code"], detail=str(f.get("detail"))[:300]))
    flags += core.state_flags(c["client_id"], state, result["outcome"])
    if result["outcome"] == "NEED_INFO" or gaps:
        need = list(dict.fromkeys(list(gaps) + list(result.get("missing_information") or [])))
        pol = next((g for g in gov if g["doc_type"] == "policy" and g["doc_id"] != "MP-117"), None)
        doc_req = ""
        if pol:
            s5 = core.read_sections([dict(doc_id=pol["doc_id"], version=pol["version"], section="5")], gov)
            if s5: doc_req = s5[0]["text"].split("\n", 1)[-1].split("If required documentation")[0].replace("\n", " ").strip()
        out["info_request"] = core.info_request_fax(c, need, doc_req)
    out["result"] = result; out["latency_s"] = round(time.time() - t0, 1)
    return out
