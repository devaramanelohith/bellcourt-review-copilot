"""POST /api/review  {"case_id": "PA-2609-8100"}  or  {"custom": {client_id, service_code, date_of_service, clinical_notes, member_id?}}
Runs the full pipeline live. Needs OPENROUTER_API_KEY in the environment."""
from http.server import BaseHTTPRequestHandler
import json, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        data = json.dumps(body).encode(); self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        from copilot import llm
        self._send(200, {"live": llm.has_key(), "model": llm.MODEL})
    def do_POST(self):
        try:
            from copilot import pipeline, llm, core
            if not llm.has_key(): return self._send(503, {"error": "Live mode is off: OPENROUTER_API_KEY is not set on the server. Saved results are still available."})
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0) or b"{}")
            if body.get("case_id"):
                p = os.path.join(core.ROOT, "data", "open_cases", os.path.basename(body["case_id"]) + ".json")
                if not os.path.exists(p): return self._send(404, {"error": "unknown case"})
                return self._send(200, pipeline.run_case(json.load(open(p))))
            c = body.get("custom") or {}
            raw = dict(case_id="CUSTOM-1", received_ts="2026-09-25 09:00", channel="PORTAL", urgency=c.get("urgency", "STANDARD"), client_id=c.get("client_id", ""),
                       service_code=c.get("service_code"), date_of_service=c.get("date_of_service"), clinical_notes=str(c.get("clinical_notes", ""))[:4000],
                       member_id=c.get("member_id") or None, patient_dob=c.get("patient_dob") or None, requesting_provider="Custom request")
            return self._send(200, pipeline.run_case(raw, assume_eligible=not raw["member_id"]))
        except Exception as e:
            self._send(500, {"error": str(e)[:300]})
