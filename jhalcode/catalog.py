import json
import os
import time
import urllib.request

URL = "https://models.opencode.ai/api.json"
TTL = 3600

def _cache() -> str:
    d = os.path.join(os.path.expanduser("~"), ".cache", "jhalcode")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "models.json")

def fetch() -> dict:
    c = _cache()
    try:
        if os.path.isfile(c) and time.time() - os.path.getmtime(c) < TTL:
            with open(c, encoding="utf-8") as f:
                return json.load(f)["opencode"]["models"]
    except Exception:
        pass
    req = urllib.request.Request(URL, headers={"User-Agent": "Jhal-Code/0.2.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode())
    try:
        tmp = c + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, c)
    except Exception:
        pass
    return data["opencode"]["models"]

def endpoint(npm: str, mid: str) -> str:
    if npm == "@ai-sdk/openai":
        return "responses"
    if npm == "@ai-sdk/anthropic":
        return "messages"
    if npm == "@ai-sdk/google":
        return "models/*"
    return "chat"

def table(free_only: bool = False) -> list:
    rows = []
    for mid, m in fetch().items():
        cost = m.get("cost", {})
        free = (cost.get("input", 1) == 0 and cost.get("output", 1) == 0)
        if free_only and not free:
            continue
        mod = m.get("modalities", {})
        rows.append({
            "id": mid,
            "in": ",".join(mod.get("input", ["?"])),
            "out": ",".join(mod.get("output", ["?"])),
            "tools": "y" if m.get("tool_call") else "-",
            "ctx": (m.get("limit") or {}).get("context", "?"),
            "price": "FREE" if free else f"${cost.get('input', '?')}/M",
            "via": endpoint(m.get("npm", ""), mid),
            "free": free,
        })
    return sorted(rows, key=lambda r: (not r["free"], r["id"]))
