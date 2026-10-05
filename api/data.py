"""GET /api/data?name=open_cases|eval|open_score   and   GET /api/data?fax=FAX-PA-2609-8100.png&t=<token>
Case data and fax images are served only to signed-in users."""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os, sys, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from copilot import auth
        if not auth.session(self): return auth.send(self, 401, {"error": "not signed in"})
        q = parse_qs(urlparse(self.path).query); name = (q.get("name") or [""])[0]; fax = (q.get("fax") or [""])[0]
        if name in ("open_cases", "eval", "open_score"): return auth.send(self, 200, open(os.path.join(ROOT, "data", "results", name + ".json"), "rb").read())
        if re.fullmatch(r"FAX-PA-\d{4}-\d{4}\.png", fax): return auth.send(self, 200, open(os.path.join(ROOT, "data", "fax", fax), "rb").read(), "image/png")
        auth.send(self, 404, {"error": "not found"})
