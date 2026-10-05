"""Case workflow API (sign-in required).
GET  /api/cases                      -> all cases, letters, audit log, server capabilities
GET  /api/cases?id=PA-...            -> one case
GET  /api/cases?letter=L-...&t=      -> decision letter as PDF
GET  /api/cases?doc=MP-101&version=v2&t=  -> the source policy PDF
POST /api/cases {action: create | review | decide | send_letter | reset, ...}"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from copilot import auth
        try:
            from copilot import cases, store, letters, core, llm
            s = auth.session(self)
            if not s: return auth.send(self, 401, {"error": "not signed in"})
            q = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
            if q.get("letter"):
                L = store.get("letter", q["letter"]); return auth.send(self, 200, letters.to_pdf(L), "application/pdf") if L else auth.send(self, 404, {"error": "not found"})
            if q.get("doc"):
                d = next((x for x in core.REGISTRY if x["doc_id"] == q["doc"] and (x["version"] or "") == q.get("version", "")), None)
                return auth.send(self, 200, open(os.path.join(ROOT, d["file"]), "rb").read(), "application/pdf") if d else auth.send(self, 404, {"error": "not found"})
            if q.get("sections"):
                return auth.send(self, 200, [x for x in core.SECTIONS if x["doc_id"] == q["sections"] and (x["version"] or "") == q.get("version", "") and x["section"] != "0"])
            if q.get("id"): return auth.send(self, 200, cases.get(q["id"]) or {"error": "not found"})
            auth.send(self, 200, {"cases": cases.all_cases(), "letters": sorted(store.all("letter").values(), key=lambda x: x["ts"], reverse=True),
                                  "audit": sorted(store.all("audit").values(), key=lambda x: x["ts"], reverse=True)[:200],
                                  "server": {"storage": store.backend(), "email": letters.mail_ready(), "live": llm.has_key(), "model": llm.MODEL}})
        except Exception as e: auth.send(self, 500, {"error": str(e)[:300]})
    def do_POST(self):
        from copilot import auth
        try:
            from copilot import cases, store, llm
            s = auth.session(self)
            if not s: return auth.send(self, 401, {"error": "not signed in"})
            b = auth.read_json(self); a = b.get("action")
            if s["r"] == "auditor": return auth.send(self, 403, {"error": "Your role is read-only."})
            if a in ("create", "review") and not llm.has_key(): return auth.send(self, 503, {"error": "No model key is set on the server."})
            if a == "create": out = cases.create(s, b)
            elif a == "review": out = cases.review(s, str(b.get("id")), b.get("client_id"))
            elif a == "decide": out = cases.decide(s, str(b.get("id")), str(b.get("decision")), str(b.get("note") or "")[:600])
            elif a == "send_letter": out = cases.send_letter(s, str(b.get("letter_id")))
            elif a == "reset": store.clear(); out = {"ok": True}
            else: return auth.send(self, 400, {"error": "unknown action"})
            auth.send(self, 200, out)
        except PermissionError as e: auth.send(self, 403, {"error": str(e)})
        except ValueError as e: auth.send(self, 400, {"error": str(e)})
        except Exception as e: auth.send(self, 500, {"error": str(e)[:300]})
