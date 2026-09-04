import json
import datetime
import os
import threading

_lock = threading.Lock()
MAX_BYTES = 5 * 1024 * 1024

def log(path: str, event: dict):
    event = {"ts": datetime.datetime.now().isoformat(), **event}
    with _lock:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        except Exception:
            pass
        try:
            if os.path.isfile(path) and os.path.getsize(path) > MAX_BYTES:
                try:
                    if os.path.isfile(path + ".1"):
                        os.replace(path + ".1", path + ".2")
                except Exception:
                    pass
                os.replace(path, path + ".1")
        except Exception:
            pass
        try:
            line = json.dumps(event)
            key = os.environ.get("JHAL_API_KEY", "")
            if key and len(key) > 8:
                line = line.replace(key, "***KEY***")
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass
