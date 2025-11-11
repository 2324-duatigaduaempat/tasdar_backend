# backend/modules/multimodel_hub.py
import os, json, hashlib, time
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path("cache"); CACHE_DIR.mkdir(exist_ok=True)

def now_iso(): 
    return datetime.now(timezone.utc).isoformat()

def sha(s: str) -> str: 
    return hashlib.sha256(s.encode()).hexdigest()[:16]

def cache_get(key: str, ttl_min: int):
    p = CACHE_DIR / f"{key}.json"
    if not p.exists(): 
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    if time.time() - data.get("_ts", 0) > ttl_min * 60:
        return None
    return data

def cache_set(key: str, value: dict):
    value["_ts"] = int(time.time())
    (CACHE_DIR / f"{key}.json").write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )

# ------- Provider stubs (selamat; sambung SDK sebenar bila siap kunci) -------
def call_gpt(prompt, cfg):
    if not os.getenv("OPENAI_API_KEY"):
        return {"text": "(GPT tidak dikonfigurasi)", "ok": False}
    return {"text": f"[GPT] {prompt[:200]}", "ok": True}

def call_claude(prompt, cfg):
    if not os.getenv("ANTHROPIC_API_KEY"):
        return {"text": "(Claude tidak dikonfigurasi)", "ok": False}
    return {"text": f"[Claude] {prompt[:200]}", "ok": True}

def call_perplex(prompt, cfg):
    if not os.getenv("PERPLEXITY_API_KEY"):
        return {"text": "(Perplexity tidak dikonfigurasi)", "ok": False}
    return {"text": f"[Perplexity] (ringkasan carian) {prompt[:180]}", "ok": True}

def call_synthetic(prompt, cfg):
    text = (
        f"[Reflective] Aku faham begini: {prompt[:160]}. "
        "Jawapan selamat: nyatakan tujuan, kekangan, dan langkah pertama yang kecil."
    )
    return {"text": text, "ok": True}

PROVIDERS = {
    "gpt": call_gpt,
    "claude": call_claude,
    "perplex": call_perplex,
    "synthetic": call_synthetic,
}

# ---------------- Core helpers ----------------
def load_map():
    p = Path("config/multimodel_map.json")
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    # default minimal
    return {
        "providers": {
            "gpt": {"enabled": True},
            "claude": {"enabled": True},
            "synthetic": {"enabled": True},
        }
    }

def pick_providers(cfg, topk: int):
    active = [k for k, v in cfg["providers"].items() if v.get("enabled")]
    if "synthetic" in active:
        active.remove("synthetic")
        active.append("synthetic")  # fallback di hujung
    return active[:topk] if topk > 0 else active

def score(text: str, ok: bool):
    return (1 if len(text) > 40 else 0) + (1 if text.count("\n") < 12 else 0) + (1 if ok else 0)

def fuse(results: dict):
    ranked = sorted(
        ((score(r["text"], r["ok"]), name) for name, r in results.items()),
        reverse=True,
    )
    best = ranked[0][1]
    notes = " | ".join([f"{name}:{s}" for s, name in ranked])
    fused = f"{results[best]['text']}\n\n— Fused by TAS.DAR (scores: {notes})"
    return fused

# ---------------- Public API ----------------
def ask(prompt: str, mode: str = "fusion", topk: int = 2):
    """API utama untuk Multi-Model Hub"""
    if os.getenv("MMHUB_ON", "true").lower() != "true":
        return {"answer": "(Multi-Model Hub dimatikan)", "used": []}

    cfg = load_map()
    key = sha(f"{mode}:{topk}:{prompt.strip()}")
    ttl = int(os.getenv("MMHUB_CACHE_TTL_MIN", "60"))

    c = cache_get(key, ttl)
    if c:
        return c  # <-- SEKARANG berada dalam fungsi, sah

    used = pick_providers(cfg, topk)
    results = {}
    for name in used:
        fn = PROVIDERS.get(name)
        results[name] = fn(prompt, cfg["providers"].get(name, {})) if fn else {"text": f"({name} tiada)", "ok": False}

    if mode == "single":
        answer = results[used[0]]["text"]
    elif mode == "compare":
        answer = "\n\n---\n\n".join([f"[{n.upper()}]\n{results[n]['text']}" for n in used])
    else:
        answer = fuse(results)

    out = {"ts": now_iso(), "prompt": prompt, "mode": mode, "used": used, "results": results, "answer": answer}
    cache_set(key, out)
    return out
