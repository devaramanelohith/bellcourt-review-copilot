"""POST /api/ask  {"question": "...", "client_id": "JUNIPER", "service_code": "BHA-SURG-6350", "date_of_service": "2026-10-01"}
Ask the policy library. Retrieval is filtered to the documents in force for that client and date, so a retired version or a memo is never the answer."""
from http.server import BaseHTTPRequestHandler
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SYSTEM = ("You answer questions from Bellcourt nurse reviewers about which rules apply. Use only the GOVERNING passages. Passages marked NOT_GOVERNING "
          "are retired versions or memos: never use them as the rule, but you may say they exist and why they do not apply. Cite document ID, version and "
          "section for every statement. If the passages do not answer the question, say so. Return JSON {\"answer\": \"...\", \"citations\": [\"MP-101 v2 Section 3\"]}.")
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            from copilot import core, llm
            b = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0) or b"{}"); q = str(b.get("question", ""))[:500]
            gov = exc = None
            if b.get("client_id") and b.get("service_code") and b.get("date_of_service"):
                gov, exc = core.governing_set(b["client_id"], b["service_code"], b["date_of_service"])
            qv = llm.embed([q])[0] if llm.has_key() else None
            hits = core.search(q, gov, k=6, qvec=qv)
            out = {"hits": [{k: h[k] for k in ("doc_id", "version", "section", "title", "status")} | {"text": h["text"][:400]} for h in hits], "excluded": exc or []}
            if llm.has_key():
                ctx = "\n\n".join(f"[{h['doc_id']} {h['version'] or ''} Section {h['section']} | {h['status']}]\n{h['text']}" for h in hits)
                ans, _ = llm.chat_json(SYSTEM, f"QUESTION: {q}\n\nPASSAGES\n{ctx}\n\nEXCLUDED DOCUMENTS: {json.dumps(exc or [])}", max_tokens=900); out.update(ans)
            else: out["answer"] = "Live mode is off, so only the retrieved passages are shown."
            code = 200
        except Exception as e: out, code = {"error": str(e)[:300]}, 500
        data = json.dumps(out).encode(); self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
