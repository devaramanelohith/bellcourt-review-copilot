"""Persistence. Supabase (Postgres over its REST API, standard library only) when SUPABASE_URL and SUPABASE_SERVICE_KEY are set;
otherwise a JSON file, which is fine locally but does not persist on serverless hosting.
One table holds everything:  copilot_store(kind text, id text, data jsonb, updated_at timestamptz, primary key (kind, id))"""
import os, json, time, threading, urllib.request, urllib.parse
from . import llm  # loads .env

URL = (os.environ.get("SUPABASE_URL") or "").rstrip("/"); KEY = os.environ.get("SUPABASE_SERVICE_KEY") or ""
FILE = "/tmp/copilot_store.json" if os.environ.get("VERCEL") else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache", "store.json")
_lock = threading.Lock()
def backend(): return "supabase" if URL and KEY else "file"

def _rest(method, query="", body=None, prefer=None):
    h = {"apikey": KEY, "Authorization": "Bearer " + KEY, "Content-Type": "application/json"}
    if prefer: h["Prefer"] = prefer
    req = urllib.request.Request(f"{URL}/rest/v1/copilot_store{query}", data=json.dumps(body).encode() if body is not None else None, method=method, headers=h)
    with urllib.request.urlopen(req, timeout=20) as r:
        t = r.read().decode(); return json.loads(t) if t else None
def _load():
    try: return json.load(open(FILE))
    except Exception: return {}
def _save(d):
    os.makedirs(os.path.dirname(FILE), exist_ok=True); json.dump(d, open(FILE, "w"))

def put(kind, id_, data):
    if backend() == "supabase":
        _rest("POST", "?on_conflict=kind,id", [{"kind": kind, "id": id_, "data": data, "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}], "resolution=merge-duplicates,return=minimal")
    else:
        with _lock: d = _load(); d.setdefault(kind, {})[id_] = data; _save(d)
    return data
def get(kind, id_):
    if backend() == "supabase":
        r = _rest("GET", f"?kind=eq.{kind}&id=eq.{urllib.parse.quote(id_)}&select=data"); return r[0]["data"] if r else None
    return _load().get(kind, {}).get(id_)
def all(kind):
    if backend() == "supabase": return {r["id"]: r["data"] for r in _rest("GET", f"?kind=eq.{kind}&select=id,data&order=updated_at.asc")}
    return _load().get(kind, {})
def clear():
    if backend() == "supabase": _rest("DELETE", "?kind=neq.__none__")
    else: _save({})
