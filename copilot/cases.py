"""Case lifecycle: create (form, file, fax or PDF upload) -> review -> human decision -> decision letter. Every step is recorded."""
import os, json, time, base64, tempfile, glob
from . import core, store, pipeline, agent, letters, auth

NOW = lambda: time.strftime("%Y-%m-%d %H:%M:%S")
RECEIVED = core.DEMO_NOW.strftime("%Y-%m-%d %H:%M")          # demo clock is pinned, so new cases are stamped at the demo "now"
DECISIONS = {  # decision -> (roles allowed, resulting status, creates a letter)
    "APPROVED": ({"nurse", "physician"}, "DECIDED", True), "PENDED_INFO": ({"intake", "nurse", "physician"}, "PENDED", True),
    "ROUTED_PHYSICIAN": ({"nurse", "intake"}, "ROUTED", False), "DENIED_MEDICAL_NECESSITY": ({"physician"}, "DECIDED", True), "DENIED_NOT_COVERED": ({"physician"}, "DECIDED", True)}
_seed = None
def seeds():
    """The 30 open cases from the data pack, shown as if imported from PACE and the fax share, with their saved reviews."""
    global _seed
    if _seed is None:
        raws = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(core.D, "open_cases", "*.json"))}
        _seed = {}
        for rv in json.load(open(os.path.join(core.D, "results", "open_cases.json"))):
            cid = rv["case"]["case_id"]; rv["case"]["patient_name"] = raws[cid].get("patient_name") or (rv["case"].get("fax") or {}).get("patient_name")
            _seed[cid] = dict(id=cid, status="REVIEWED", raw=raws[cid], review=rv, decision=None, letter_id=None, seeded=True,
                              created=dict(by="System import", ts=raws[cid]["received_ts"], source={"FAX": "Fax share", "PORTAL": "Portal webhook", "PHONE": "PACE (phone)", "ELECTRONIC": "PACE (X12 278)"}[raws[cid]["channel"]]))
    return _seed
def priority(c):
    rv = c.get("review"); clk = rv["clock"] if rv else core.clock(c["raw"]["client_id"], c["raw"]["received_ts"], c["raw"].get("urgency"), c["raw"].get("urgency_form"))
    h = clk["hours_remaining"]; p = "OVERDUE" if h < 0 else "URGENT" if (clk["effective_urgency"] == "URGENT" or h < 24) else "DUE_SOON" if h < 96 else "STANDARD"
    return dict(level=p, hours_remaining=h, due=clk["due"], rank={"OVERDUE": 0, "URGENT": 1, "DUE_SOON": 2, "STANDARD": 3}[p])
def all_cases():
    d = dict(seeds()); d.update(store.all("case"))
    out = []
    for c in d.values(): c = dict(c); c["priority"] = priority(c); out.append(c)
    return sorted(out, key=lambda c: (c["status"] in ("DECIDED",), c["priority"]["rank"], c["priority"]["hours_remaining"]))
def get(cid):
    c = store.get("case", cid) or seeds().get(cid)
    if c: c = dict(c); c["priority"] = priority(c)
    return c
def audit(sess, action, case_id, detail=""):
    store.put("audit", f"{time.time():.4f}", dict(ts=NOW(), user=sess["u"], name=sess["n"], role=sess["r"], action=action, case_id=case_id, detail=detail))

def create(sess, b):
    """source: form | json | text | fax (image as data URL; a PDF is rendered to an image in the browser first)."""
    src = b.get("source", "form"); n = len(store.all("case")) + 1; cid = f"PA-2610-{9000 + n}"; image = None
    base = dict(case_id=cid, received_ts=RECEIVED, urgency="STANDARD", requesting_provider="", client_id="", source=src)
    if src == "json":
        j = b.get("case") or {}; raw = {**base, **{k: j.get(k) for k in ("channel", "urgency", "client_id", "requesting_provider", "member_id", "patient_name", "patient_dob", "date_of_service", "service_code", "service_requested", "clinical_notes", "icd10") if j.get(k)}}
        raw.setdefault("channel", "PORTAL"); raw["imported_from"] = j.get("case_id")
        if j.get("fax_image") and not j.get("clinical_notes"): raw["fax_image"] = j["fax_image"]; raw["channel"] = "FAX"     # an un-keyed fax case from the pack
    elif src in ("fax", "text"):
        if src == "fax":
            image = b.get("image") or ""; data = base64.b64decode(image.split(",", 1)[-1]); tmp = tempfile.NamedTemporaryFile(suffix=".img", delete=False); tmp.write(data); tmp.close()
            fx, _ = agent.read_fax(tmp.name); os.unlink(tmp.name)
        else: fx, _ = agent.read_text(str(b.get("text", "")))
        raw = {**base, "channel": "FAX" if src == "fax" else str(b.get("channel") or "PORTAL"), "client_id": b.get("client_id") or "", "fax": fx, "planted": list(fx.get("embedded_instructions") or []),
               "urgency_form": (fx.get("review_type") or "").upper() or None, "urgency": (fx.get("review_type") or "STANDARD").upper(), "member_id": (fx.get("member_id") or "").strip() or None,
               "patient_name": fx.get("patient_name"), "patient_dob": fx.get("date_of_birth") or None, "requesting_provider": fx.get("requesting_provider") or "",
               "service_requested": fx.get("service_requested"), "service_code": core.service_code_for(fx.get("service_requested")), "icd10": (fx.get("icd10") or "").strip() or None,
               "clinical_notes": fx.get("clinical_text") or "", "date_of_service": str(core.to_date(fx.get("planned_date_of_service")) or "") or None}
    else:
        f = b.get("form") or {}; raw = {**base, **{k: (str(f.get(k)).strip() or None) if f.get(k) is not None else None for k in ("channel", "urgency", "client_id", "requesting_provider", "member_id", "patient_name", "patient_dob", "date_of_service", "service_code", "clinical_notes", "icd10")}}
        raw["channel"] = raw.get("channel") or "PORTAL"; raw["urgency"] = raw.get("urgency") or "STANDARD"
    if not raw.get("client_id") and raw.get("member_id") in core.ELIG: raw["client_id"] = core.ELIG[raw["member_id"]]["client_id"]     # client from the member ID
    if raw.get("service_code") and not raw.get("service_requested"): raw["service_requested"] = core.SERVICES.get(raw["service_code"])
    c = dict(id=cid, status="NEW", raw=raw, review=None, decision=None, letter_id=None, image=image, created=dict(by=sess["n"], ts=NOW(), source={"form": "Form", "json": "Case file upload", "fax": "Fax or PDF upload", "text": "Text document upload"}[src]),
             intake_gaps=core.intake_gaps(raw) + ([] if raw.get("client_id") else ["Health plan or employer (client)"]))
    store.put("case", cid, c); audit(sess, "CASE_CREATED", cid, c["created"]["source"]); return get(cid)

def review(sess, cid, client_id=None):
    c = get(cid)
    if not c: raise ValueError("unknown case")
    if client_id and not c["raw"].get("client_id") and client_id in core.PLAN_CLIENTS: c["raw"]["client_id"] = client_id
    if not c["raw"].get("client_id"): raise ValueError("Set the client (health plan or employer) before running a review.")
    rv = pipeline.run_case(c["raw"]); rv["case"]["patient_name"] = c["raw"].get("patient_name") or (rv["case"].get("fax") or {}).get("patient_name")
    c.update(review=rv, status="REVIEWED", decision=None, letter_id=None, reviewed=dict(by=sess["n"], ts=NOW())); c.pop("priority", None); c.pop("seeded", None)
    store.put("case", cid, c); audit(sess, "REVIEW_RUN", cid, rv["result"]["outcome"]); return get(cid)

def decide(sess, cid, decision, note=""):
    c = get(cid)
    if not c or not c.get("review"): raise ValueError("Run a review before recording a decision.")
    if decision not in DECISIONS: raise ValueError("unknown decision")
    roles, status, makes_letter = DECISIONS[decision]
    if sess["r"] not in roles: raise PermissionError(f"Your role cannot record this decision. Allowed: {', '.join(sorted(roles))}.")
    rec = c["review"]["result"]["outcome"]; expected = {"APPROVED": "APPROVE_READY", "PENDED_INFO": "NEED_INFO", "ROUTED_PHYSICIAN": "ROUTE_PHYSICIAN", "DENIED_MEDICAL_NECESSITY": "ROUTE_PHYSICIAN", "DENIED_NOT_COVERED": "ROUTE_NOT_COVERED"}[decision]
    override = rec != expected and not (decision == "ROUTED_PHYSICIAN" and rec == "ROUTE_NOT_COVERED")
    if override and not (note or "").strip(): raise ValueError("This differs from the recommendation. A reason is required.")
    c["decision"] = dict(type=decision, by=sess["n"], user=sess["u"], role=sess["r"], ts=NOW(), note=note, override=override, recommended=rec); c["status"] = status
    if makes_letter:
        L = letters.build(c, decision, sess["n"], auth.ROLES[sess["r"]]); L.update(id=f"L-{cid[3:]}-{int(time.time()) % 100000}", created_by=sess["n"], ts=NOW(), sent=None)
        store.put("letter", L["id"], L); c["letter_id"] = L["id"]
    c.pop("priority", None); c.pop("seeded", None); store.put("case", cid, c); audit(sess, "DECISION_" + decision, cid, ("OVERRIDE: " if override else "") + (note or "")); return get(cid)

def send_letter(sess, lid):
    L = store.get("letter", lid)
    if not L: raise ValueError("unknown letter")
    if sess["r"] == "auditor": raise PermissionError("Your role is read-only.")
    to = letters.send(L); L["sent"] = dict(ts=NOW(), to=to, by=sess["n"]); store.put("letter", lid, L); audit(sess, "LETTER_SENT", L["case_id"], to); return L
