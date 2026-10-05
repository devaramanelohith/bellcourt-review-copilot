"""The only module that talks to a model. Two providers, standard library only (runs on Vercel with no dependencies).
  LLM_PROVIDER=openrouter (default when OPENROUTER_API_KEY is set)  ->  OpenRouter, model e.g. google/gemini-2.5-flash
  LLM_PROVIDER=gemini     (default when only GEMINI_API_KEY is set) ->  Google Gemini API directly, model e.g. gemini-2.5-flash
Note: a free-tier Gemini key allows about 20 requests a day per model. One case review needs 3 to 5 calls, so use a paid key or OpenRouter."""
import json, os, time, base64, urllib.request, urllib.error

GEMINI = "https://generativelanguage.googleapis.com/v1beta/models/"
OPENROUTER = "https://openrouter.ai/api/v1"
EMBED_DIM = 256   # data/vectors.json was built with openai/text-embedding-3-small through OpenRouter

def _load_env():
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1); os.environ.setdefault(k, v)
_load_env()
PROVIDER = os.environ.get("LLM_PROVIDER") or ("openrouter" if os.environ.get("OPENROUTER_API_KEY") else "gemini")
MODEL = os.environ.get("LLM_MODEL") or ("google/gemini-2.5-flash" if PROVIDER == "openrouter" else "gemini-2.5-flash")
if PROVIDER == "gemini": MODEL = MODEL.split("/")[-1]
elif "/" not in MODEL: MODEL = "google/" + MODEL

def has_key(): return bool(os.environ.get("OPENROUTER_API_KEY" if PROVIDER == "openrouter" else "GEMINI_API_KEY"))

def _post(url, headers, payload, timeout=90, retries=4):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST", headers={"Content-Type": "application/json", **headers})
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.loads(r.read().decode())
                if "error" in out: raise RuntimeError(str(out["error"])[:300])
                return out
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode()[:160]}"
            if e.code in (400, 401, 402, 403, 404, 429): break
            time.sleep(1.5 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as e:
            last = e; time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"model call failed: {last}")

def _parse(text):
    text = (text or "").strip(); s, e = text.find("{"), text.rfind("}")
    if s < 0: raise RuntimeError("model returned no JSON")
    return json.loads(text[s:e + 1])

def chat_json(system, user, image_path=None, max_tokens=4000):
    """One model call that must return a JSON object. Returns (dict, usage)."""
    b64 = base64.b64encode(open(image_path, "rb").read()).decode() if image_path else None
    if PROVIDER == "gemini":
        parts = ([{"inline_data": {"mime_type": "image/png", "data": b64}}] if b64 else []) + [{"text": user}]
        out = _post(f"{GEMINI}{MODEL}:generateContent", {"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, {
            "system_instruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": max_tokens, "responseMimeType": "application/json", "thinkingConfig": {"thinkingBudget": 0}}})
        cand = (out.get("candidates") or [{}])[0]; u = out.get("usageMetadata", {})
        text = "".join(p.get("text", "") for p in (cand.get("content") or {}).get("parts", []))
        return _parse(text), {"in": u.get("promptTokenCount", 0), "out": u.get("candidatesTokenCount", 0)}
    content = ([{"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}}] if b64 else []) + [{"type": "text", "text": user}]
    out = _post(OPENROUTER + "/chat/completions", {"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "X-Title": "Bellcourt Review Copilot"},
                {"model": MODEL, "temperature": 0, "max_tokens": max_tokens, "response_format": {"type": "json_object"},
                 "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}]})
    u = out.get("usage", {})
    return _parse(out["choices"][0]["message"]["content"]), {"in": u.get("prompt_tokens", 0), "out": u.get("completion_tokens", 0)}

def embed(texts):
    """Query and document embeddings must come from the same model, so embeddings always use OpenRouter.
    Without that key this raises, and search falls back to keyword ranking only."""
    if not os.environ.get("OPENROUTER_API_KEY"): raise RuntimeError("no embedding key: keyword search only")
    out = _post(OPENROUTER + "/embeddings", {"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]},
                {"model": "openai/text-embedding-3-small", "input": texts, "dimensions": EMBED_DIM})
    return [d["embedding"] for d in sorted(out["data"], key=lambda d: d["index"])]
