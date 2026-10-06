"""Case workflow API (sign-in required). What each role receives is decided here, on the server.
GET  /api/cases                      -> staff: all cases, letters, audit log, server capabilities.  provider: own requests (status only).  agent: nothing until a lookup.
GET  /api/cases?id=PA-...            -> one case (staff only)
GET  /api/cases?letter=L-...&t=      -> decision letter as PDF (staff, or the provider who raised the case)
GET  /api/cases?doc=MP-101&version=v2&t=  -> the source policy PDF;   ?sections=MP-101&version=v2 -> its text
POST /api/cases {action: create | review | decide | send_letter | reset | coverage | lookup | prove, ...}"""
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
            q = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}; staff = s["r"] in auth.STAFF
            server = {"storage": store.backend(), "email": letters.mail_ready(), "live": llm.has_key(), "model": llm.MODEL}
            if q.get("letter"):
                L = store.get("letter", q["letter"])
                if not L: return auth.send(self, 404, {"error": "not found"})
                if not staff:
                    c = cases.get(L["case_id"])
                    if s["r"] != "provider" or not c or (c.get("created") or {}).get("user") != s["u"]: return auth.send(self, 403, {"error": "This notice belongs to another office."})
                return auth.send(self, 200, letters.to_pdf(L), "application/pdf")
            if q.get("doc"):
                d = next((x for x in core.REGISTRY if x["doc_id"] == q["doc"] and (x["version"] or "") == q.get("version", "")), None)
                return auth.send(self, 200, open(os.path.join(ROOT, d["file"]), "rb").read(), "application/pdf") if d else auth.send(self, 404, {"error": "not found"})
            if q.get("sections"):
                return auth.send(self, 200, [x for x in core.SECTIONS if x["doc_id"] == q["sections"] and (x["version"] or "") == q.get("version", "") and x["section"] != "0"])
            if s["r"] == "provider":
                mine = cases.own(s); ids = {c["id"] for c in mine}
                return auth.send(self, 200, {"cases": mine, "letters": sorted([L for L in store.all("letter").values() if L["case_id"] in ids], key=lambda x: x["ts"], reverse=True), "audit": [], "server": server})
            if s["r"] == "agent": return auth.send(self, 200, {"cases": [], "letters": [], "audit": [], "server": server})
            if q.get("id"): return auth.send(self, 200, cases.get(q["id"]) or {"error": "not found"})
            auth.send(self, 200, {"cases": cases.all_cases(), "letters": sorted(store.all("letter").values(), key=lambda x: x["ts"], reverse=True),
                                  "audit": sorted(store.all("audit").values(), key=lambda x: x["ts"], reverse=True)[:200], "server": server})
        except Exception as e: auth.send(self, 500, {"error": str(e)[:300]})
    def do_POST(self):
        from copilot import auth
        try:
            from copilot import cases, store, llm, core, controls
            s = auth.session(self)
            if not s: return auth.send(self, 401, {"error": "not signed in"})
            b = auth.read_json(self); a = b.get("action")
            if a == "coverage": return auth.send(self, 200, core.coverage_check(str(b.get("member_id") or ""), str(b.get("client_id") or ""), str(b.get("service_code") or ""), str(b.get("date_of_service") or ""), str(b.get("urgency") or "STANDARD")))
            if a == "lookup": return auth.send(self, 200, cases.lookup(s, str(b.get("case_id") or ""), str(b.get("dob") or "")))
            if a == "prove": return auth.send(self, 200, controls.prove(str(b.get("kind")), s, b))
            if s["r"] in ("auditor", "agent"): return auth.send(self, 403, {"error": "Your role is read-only."})
            if a in ("create", "review") and not llm.has_key(): return auth.send(self, 503, {"error": "No model key is set on the server."})
            if a == "create": out = cases.create(s, b)
            elif a == "review": out = cases.review(s, str(b.get("id")), b.get("client_id"))
            elif a == "decide": out = cases.decide(s, str(b.get("id")), str(b.get("decision")), str(b.get("note") or "")[:600])
            elif a == "send_letter": out = cases.send_letter(s, str(b.get("letter_id")))
            elif a == "reset":
                if s["r"] not in auth.STAFF: raise PermissionError("Staff only.")
                store.clear(); out = {"ok": True}
            else: return auth.send(self, 400, {"error": "unknown action"})
            if s["r"] == "provider" and isinstance(out, dict) and out.get("raw"): out = cases.public_view(out)
            auth.send(self, 200, out)
        except PermissionError as e: auth.send(self, 403, {"error": str(e)})
        except ValueError as e: auth.send(self, 400, {"error": str(e)})
        except Exception as e: auth.send(self, 500, {"error": str(e)[:300]})
