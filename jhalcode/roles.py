import os
import yaml

def _path():
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [os.path.join(os.getcwd(), "roles.yaml"), os.path.join(here, "roles.yaml")]
    for p in cands:
        if os.path.isfile(p):
            return p
    return cands[0] if os.path.isdir(os.getcwd()) else cands[1]

KNOWN_TOOLS = {"run_shell", "run_bg", "bg_kill", "list_dir", "read_file", "write_file", "edit_file", "grep", "glob",
               "screenshot", "mouse_move", "mouse_click", "key_press", "key_type", "browser_open",
               "browser_act", "web_search", "webfetch", "open_file", "question", "todo", "plan",
               "symbols", "diagnose", "refs", "delegate", "add_role", "all"}

def load() -> dict:
    try:
        with open(_path(), encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        roles = data.get("roles", {})
        return roles if isinstance(roles, dict) else {}
    except Exception:
        return {}

def save(roles: dict):
    p = _path()
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        yaml.safe_dump({"roles": roles}, f, sort_keys=False)
    os.replace(tmp, p)

def add_role(name: str, model: str, tools: list, system: str, steps: int = 12, fallback: list | None = None) -> str:
    import re
    if not re.fullmatch(r"[a-z0-9_-]{1,32}", (name or "").lower()):
        return "bad name: lowercase letters/numbers/_/- only, max 32"
    name = name.lower()
    roles = load()
    if name in roles:
        return f"role '{name}' exists — use another name"
    bad = [t for t in tools if t not in KNOWN_TOOLS]
    if bad:
        return f"unknown tools: {bad}"
    if not model or len(model) > 120 or not system or len(system) > 4000:
        return "bad model/system"
    try:
        steps = min(50, max(1, int(steps)))
    except Exception:
        steps = 12
    roles[name] = {"model": model, "fallback": fallback or [], "tools": tools, "steps": steps, "system": system}
    save(roles)
    return f"role '{name}' added"

def available_models(base_url: str, api_key: str) -> set:
    import urllib.request, json
    req = urllib.request.Request(f"{base_url.rstrip('/')}/models", headers={"Authorization": f"Bearer {api_key}", "User-Agent": "Jhal-Code/0.2.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return {m["id"] for m in json.loads(r.read().decode()).get("data", [])}

def resolve(roles: dict, base_url: str, api_key: str) -> list:
    """Swap any unknown model id for first working fallback. Returns swap notes."""
    try:
        have = available_models(base_url, api_key)
    except Exception as e:
        return [f"model check skipped: {e}"]
    notes = []
    for name, r in roles.items():
        if r.get("model") not in have:
            for fb in (r.get("fallback") or []):
                if fb in have:
                    notes.append(f"{name}: {r['model']} -> {fb}")
                    r["model"] = fb
                    break
            else:
                notes.append(f"{name}: {r.get('model')} unknown, no fallback works")
    return notes

def probe(base_url: str, api_key: str, model: str, timeout: int = 15) -> str:
    """Returns ok | flaky (rate/overload/timeout — keep model) | broken (bad id/denied — swap it)."""
    import urllib.request, json, time
    payload = {"model": model, "messages": [{"role": "user", "content": "ok"}], "max_tokens": 5}
    last = "broken"
    for attempt in range(2):
        try:
            req = urllib.request.Request(f"{base_url.rstrip('/')}/chat/completions", data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Jhal-Code/0.2.0", "Authorization": f"Bearer {api_key}"}, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                json.loads(r.read().decode())
            return "ok"
        except Exception as e:
            s = str(e)
            if any(k in s for k in ("429", "503", "timed out", "Timeout", "FreeUsageLimit", "overloaded")):
                last = "flaky"
                time.sleep(3)
            elif "500" in s and attempt == 0:
                last = "broken"
                time.sleep(2)
            else:
                last = "broken"
    return last

def resolve_live(roles: dict, base_url: str, api_key: str) -> list:
    """ actually call each role model; swap broken ones (500/unavailable) for working fallbacks."""
    from concurrent.futures import ThreadPoolExecutor
    notes = resolve(roles, base_url, api_key)
    cands = {}
    for name, r in roles.items():
        cands[name] = [r.get("model", "")] + [fb for fb in (r.get("fallback") or []) if fb != r.get("model")]
    flat = [(n, m) for n, ms in cands.items() for m in ms]
    print(f"  probing {len(flat)} models...")
    with ThreadPoolExecutor(max_workers=4) as ex:
        ok = dict(zip(flat, ex.map(lambda t: probe(base_url, api_key, t[1]), flat)))
    for name, r in roles.items():
        st = ok.get((name, r.get("model")))
        pin = " (pinned)" if r.get("pinned") else ""
        if st == "ok":
            notes.append(f"{name}: {r['model']} ok{pin}")
            continue
        if st == "flaky" or r.get("pinned"):
            notes.append(f"{name}: {r['model']} {st}{pin} — kept")
            continue
        for fb in (r.get("fallback") or []):
            if ok.get((name, fb)) == "ok":
                notes.append(f"{name}: {r['model']} broken -> {fb}")
                r["model"] = fb
                break
        else:
            notes.append(f"{name}: {r.get('model')} broken, no working fallback")
    return notes
