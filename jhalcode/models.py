import json
import urllib.request

DEFAULT_BASE = "https://opencode.ai/zen/v1"

class ModelClient:
    """OpenAI-compatible chat client. Works with OpenAI, OpenRouter, Gemini, Ollama, LM Studio."""
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = (base_url or "").strip().rstrip("/") or DEFAULT_BASE
        self.api_key = api_key
        self.model = model

    def chat(self, messages: list, tools: list | None = None) -> dict:
        payload: dict = {"model": self.model, "messages": messages}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        headers = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Jhal-Code/0.1.0", "HTTP-Referer": "https://github.com/jhal-code", "X-Title": "Jhal Code"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )
        import time as _t
        import urllib.error as ue
        last = None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    return json.loads(r.read().decode())
            except ue.HTTPError as e:
                try:
                    body = e.read().decode()[:1000]
                except Exception:
                    body = ""
                if e.code == 429 and attempt < 3:
                    wait = 2 * (2 ** attempt)
                    try:
                        wait = min(float(e.headers.get("retry-after", wait)), 30)
                    except Exception:
                        pass
                    _t.sleep(wait)
                    last = RuntimeError(f"HTTP {e.code}: {body}")
                    continue
                raise RuntimeError(f"HTTP {e.code}: {body}")
            except (ue.URLError, TimeoutError, ConnectionError, OSError) as e:
                last = RuntimeError(f"net error: {str(e)[:200]}")
                _t.sleep(2 * (2 ** attempt))
        raise last or RuntimeError("request failed")


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}

def image_part(path: str, max_side: int = 1568) -> dict | None:
    import base64
    import os as _os
    if _os.path.splitext(path)[1].lower() not in IMAGE_EXTS:
        return None
    try:
        from PIL import Image
        import io
        Image.MAX_IMAGE_PIXELS = 50_000_000
        im = Image.open(path)
        im.load()
        im = im.convert("RGB")
        im.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=80)
        data = base64.b64encode(buf.getvalue()).decode()
        return {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data}"}}
    except Exception:
        return None
