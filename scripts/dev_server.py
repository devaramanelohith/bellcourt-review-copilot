"""Local server that mimics Vercel: static files from public/ plus the two API functions.  python scripts/dev_server.py  ->  http://localhost:8765"""
import os, sys, importlib.util
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "api", name + ".py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m.handler
API = {"/api/review": load("review"), "/api/ask": load("ask")}
class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=os.path.join(ROOT, "public"), **k)
    def do_GET(self):
        h = API.get(self.path.split("?")[0])
        return h.do_GET(self) if h and hasattr(h, "do_GET") else super().do_GET()
    def do_POST(self):
        h = API.get(self.path.split("?")[0]); return h.do_POST(self) if h else self.send_error(404)
H._send = API["/api/review"]._send
port = int(os.environ.get("PORT", 8765)); print(f"http://localhost:{port}"); ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
