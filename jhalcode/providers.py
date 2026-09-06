"""Provider presets (multi-provider support): id -> base URL, key hint, key check."""

PRESETS = {
    "zen": {
        "base": "https://opencode.ai/zen/v1",
        "key_hint": "Zen key (sk-...)",
        "check": "models",
        "models": "zen catalog (/models)",
    },
    "openrouter": {
        "base": "https://openrouter.ai/api/v1",
        "key_hint": "OpenRouter key (sk-or-v1-...)",
        "check": "authkey",
        "models": "provider list (/models)",
    },
    "ollama": {
        "base": "http://localhost:11434/v1",
        "key_hint": "any text (ollama)",
        "check": "models",
        "models": "ollama pull <name> first",
    },
    "lmstudio": {
        "base": "http://localhost:1234/v1",
        "key_hint": "any text (lm-studio)",
        "check": "models",
        "models": "loaded model in LM Studio",
    },
    "openai": {
        "base": "https://api.openai.com/v1",
        "key_hint": "OpenAI key (sk-...)",
        "check": "models",
        "models": "gpt-4o, gpt-4o-mini, ...",
    },
    "gemini": {
        "base": "https://generativelanguage.googleapis.com/v1beta/openai",
        "key_hint": "Google AI key",
        "check": "models",
        "models": "gemini-2.0-flash, ...",
    },
}

GUESS = [("sk-or-", "openrouter")]


def detect(key: str) -> str:
    for prefix, pid in GUESS:
        if key.startswith(prefix):
            return pid
    return "zen"


def check(pid: str, base: str, key: str) -> str:
    import urllib.request, json
    kind = PRESETS.get(pid, {}).get("check", "models")
    url = f"{base.rstrip('/')}/auth/key" if kind == "authkey" else f"{base.rstrip('/')}/models"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}",
        "User-Agent": "Jhal-Code/0.3.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    if kind == "authkey":
        return f"key ok ({data.get('data', {}).get('label', 'no label')})"
    return f"{len(data.get('data', []))} models"
