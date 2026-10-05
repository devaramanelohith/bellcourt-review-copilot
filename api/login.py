"""POST /api/login {"username": "...", "password": "..."} -> signed session token and role.   GET /api/login -> current session."""
from http.server import BaseHTTPRequestHandler
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from copilot import auth, llm
        s = auth.session(self)
        if not s: return auth.send(self, 401, {"error": "not signed in"})
        auth.send(self, 200, {"role": s["r"], "role_label": auth.ROLES[s["r"]], "name": s["n"], "can_run_live": s["r"] in auth.CAN_RUN_LIVE, "live": llm.has_key(), "model": llm.MODEL})
    def do_POST(self):
        from copilot import auth, llm
        try:
            b = auth.read_json(self); out = auth.login(str(b.get("username", ""))[:40], str(b.get("password", ""))[:200])
            if not out: time.sleep(0.6); return auth.send(self, 401, {"error": "Wrong username or password"})
            out.update(live=llm.has_key(), model=llm.MODEL); auth.send(self, 200, out)
        except Exception as e: auth.send(self, 500, {"error": str(e)[:200]})
