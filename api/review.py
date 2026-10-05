"""POST /api/review  {"case_id": "PA-2609-8100"}  or  {"custom": {client_id, service_code, date_of_service, clinical_notes, member_id?}}
Runs the full pipeline live. Signed-in nurse, physician or intake roles only."""
from http.server import BaseHTTPRequestHandler
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        from copilot import auth
        try:
            from copilot import pipeline, llm, core
            s = auth.session(self)
            if not s: return auth.send(self, 401, {"error": "not signed in"})
            if s["r"] not in auth.CAN_RUN_LIVE: return auth.send(self, 403, {"error": "Your role is read-only and cannot run a review."})
            if not llm.has_key(): return auth.send(self, 503, {"error": "Live mode is off: no model key is set on the server. Saved results are still available."})
            body = auth.read_json(self)
            if body.get("case_id"):
                p = os.path.join(core.ROOT, "data", "open_cases", os.path.basename(str(body["case_id"])) + ".json")
                if not os.path.exists(p): return auth.send(self, 404, {"error": "unknown case"})
                out = pipeline.run_case(json.load(open(p)))
            else:
                c = body.get("custom") or {}
                raw = dict(case_id="NEW-" + str(c.get("channel", "PORTAL"))[:10], received_ts="2026-09-25 09:00", channel=str(c.get("channel", "PORTAL"))[:12], urgency=c.get("urgency", "STANDARD"),
                           client_id=c.get("client_id", ""), service_code=c.get("service_code"), date_of_service=c.get("date_of_service"), clinical_notes=str(c.get("clinical_notes", ""))[:4000],
                           member_id=c.get("member_id") or None, patient_dob=c.get("patient_dob") or None, requesting_provider=str(c.get("requesting_provider") or "Requesting provider")[:80])
                out = pipeline.run_case(raw, assume_eligible=not raw["member_id"])
            out["run_by"] = dict(user=s["u"], role=s["r"]); auth.send(self, 200, out)
        except Exception as e: auth.send(self, 500, {"error": str(e)[:300]})
