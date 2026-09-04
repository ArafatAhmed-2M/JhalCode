import subprocess, os

class WindowsBackend:
    name = "windows"
    def shell(self, command: str, cwd: str | None = None, timeout: int = 60) -> dict:
        try:
            timeout = min(300, max(1, int(timeout or 60)))
        except Exception:
            timeout = 60
        try:
            p = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd or os.getcwd(), timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"code": 124, "output": "timed out after %ss" % timeout}
        except Exception as e:
            return {"error": str(e)[:300]}
        out = (p.stdout or "") + (p.stderr or "")
        if len(out) > 8000:
            return {"code": p.returncode, "output": "...[truncated, showing last 8000 chars]\n" + out[-8000:]}
        return {"code": p.returncode, "output": out}
