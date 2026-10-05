"""Login and role-based access. Standard library only.
Passwords are never stored: copilot/users.json holds salted PBKDF2 hashes. Sessions are signed tokens (HMAC-SHA256, 8 hours).
The signing secret comes from the AUTH_SECRET environment variable and is never in the repository."""
import os, json, hmac, hashlib, base64, time
from . import llm  # loads .env for local runs

USERS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")))
ROLES = {"nurse": "Nurse reviewer", "physician": "Physician reviewer", "intake": "Intake coordinator", "auditor": "Auditor (read only)"}
CAN_RUN_LIVE = {"nurse", "physician", "intake"}          # the auditor role is read-only, enforced on the server
TTL = 8 * 3600

def _secret():
    s = os.environ.get("AUTH_SECRET")
    if not s: raise RuntimeError("AUTH_SECRET is not set on the server")
    return s.encode()
def hash_password(password, salt): return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000).hex()
def _sign(body): return base64.urlsafe_b64encode(hmac.new(_secret(), body.encode(), hashlib.sha256).digest()).decode().rstrip("=")

def login(username, password):
    u = USERS.get((username or "").strip().lower())
    ok = bool(u) and hmac.compare_digest(hash_password(password or "", u["salt"]), u["hash"])
    if not u: hash_password(password or "", "00" * 16)   # same work for unknown users, so timing reveals nothing
    if not ok: return None
    body = base64.urlsafe_b64encode(json.dumps({"u": username.strip().lower(), "r": u["role"], "n": u["name"], "exp": int(time.time()) + TTL}).encode()).decode().rstrip("=")
    return dict(token=body + "." + _sign(body), role=u["role"], role_label=ROLES[u["role"]], name=u["name"], can_run_live=u["role"] in CAN_RUN_LIVE)

def check(token):
    """Returns the session dict or None."""
    try:
        body, sig = (token or "").split(".")
        if not hmac.compare_digest(sig, _sign(body)): return None
        s = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        return s if s["exp"] > time.time() else None
    except Exception: return None

def session(handler):
    """Session from the Authorization header, or from ?t= for image tags."""
    h = handler.headers.get("Authorization", "")
    tok = h[7:] if h.startswith("Bearer ") else ""
    if not tok and "t=" in handler.path: tok = handler.path.split("t=")[-1].split("&")[0]
    return check(tok)

def send(handler, code, body, ctype="application/json"):
    data = body if isinstance(body, bytes) else json.dumps(body).encode()
    handler.send_response(code); handler.send_header("Content-Type", ctype); handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Cache-Control", "no-store"); handler.end_headers(); handler.wfile.write(data)
def read_json(handler):
    try: return json.loads(handler.rfile.read(int(handler.headers.get("Content-Length", 0)) or 0) or b"{}")
    except Exception: return {}
