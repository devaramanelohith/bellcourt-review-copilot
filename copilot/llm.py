"""The only module that talks to a model. OpenRouter, standard library only (runs on Vercel with no dependencies)."""
import json, os, time, base64, urllib.request, urllib.error

BASE = "https://openrouter.ai/api/v1"
MODEL = os.environ.get("LLM_MODEL", "google/gemini-2.5-flash")
EMBED_MODEL = "openai/text-embedding-3-small"
EMBED_DIM = 256

def _load_env():
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1); os.environ.setdefault(k, v)
_load_env()
MODEL = os.environ.get("LLM_MODEL", MODEL)

def has_key(): return bool(os.environ.get("OPENROUTER_API_KEY"))

def _post(path, payload, timeout=90, retries=4):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(), method="POST", headers={
        "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json",
        "X-Title": "Bellcourt Review Copilot"})
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.loads(r.read().decode())
                if "error" in out: raise RuntimeError(str(out["error"])[:300])
                return out
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as e:
            last = e
            if isinstance(e, urllib.error.HTTPError) and e.code in (400, 401, 402, 403): break
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"model call failed: {last}")

def chat_json(system, user, image_path=None, max_tokens=4000):
    """One model call that must return a JSON object. Returns (dict, usage)."""
    content = [{"type": "text", "text": user}]
    if image_path:
        b64 = base64.b64encode(open(image_path, "rb").read()).decode()
        content.insert(0, {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}})
    out = _post("/chat/completions", {"model": MODEL, "temperature": 0, "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}]})
    text = out["choices"][0]["message"]["content"] or ""
    text = text.strip()
    if text.startswith("```"): text = text.strip("`"); text = text[text.find("{"):]
    s, e = text.find("{"), text.rfind("}")
    u = out.get("usage", {})
    return json.loads(text[s:e + 1]), {"in": u.get("prompt_tokens", 0), "out": u.get("completion_tokens", 0)}

def embed(texts):
    out = _post("/embeddings", {"model": EMBED_MODEL, "input": texts, "dimensions": EMBED_DIM})
    return [d["embedding"] for d in sorted(out["data"], key=lambda d: d["index"])]
