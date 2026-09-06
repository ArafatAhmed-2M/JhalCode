from jhalcode.platform import get_backend

SHELL_DEF = [{
    "type": "function", "function": {
        "name": "run_shell",
        "description": "Run a Windows shell command (powershell/cmd). Returns exit code + output.",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string"}, "cwd": {"type": "string"}, "timeout": {"type": "integer"}},
            "required": ["command"]}}}]

def run_shell(command: str, cwd: str | None = None, timeout: int = 60, **_) -> dict:
    return get_backend().shell(command, cwd, timeout or 60)


BG_DEFS = [{
    "type": "function", "function": {
        "name": "run_bg",
        "description": "Start a command detached in background. Returns pid + log path. Read output with read_file(log). Stop with bg_kill.",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string"}, "cwd": {"type": "string"}, "log": {"type": "string"}},
            "required": ["command"]}}}]

BG_KILL_DEFS = [{
    "type": "function", "function": {
        "name": "bg_kill",
        "description": "Stop a background process started by run_bg.",
        "parameters": {"type": "object", "properties": {"pid": {"type": "integer"}}, "required": ["pid"]}}}]

def run_bg(command: str, cwd: str | None = None, log: str | None = None, **_) -> dict:
    import os
    import subprocess
    import time
    log = log or os.path.join(cwd or os.getcwd(), f"bg-{int(time.time())}.log")
    try:
        lf = open(log, "ab")
    except Exception as e:
        return {"error": f"bad log path: {e}"[:200]}
    try:
        if os.name == "nt":
            p = subprocess.Popen(command, shell=True, stdout=lf, stderr=subprocess.STDOUT,
                                 cwd=cwd or None, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            p = subprocess.Popen(command, shell=True, stdout=lf, stderr=subprocess.STDOUT,
                                 cwd=cwd or None, start_new_session=True)
        return {"pid": p.pid, "log": log}
    except Exception as e:
        try:
            lf.close()
        except Exception:
            pass
        return {"error": str(e)[:300]}

def bg_kill(pid: int, **_) -> dict:
    try:
        import os
        import signal
        if os.name == "nt":
            import subprocess
            subprocess.run(["taskkill", "/PID", str(int(pid)), "/F"], capture_output=True, timeout=15)
        else:
            os.kill(int(pid), signal.SIGTERM)
        return {"ok": f"killed {int(pid)}"}
    except Exception as e:
        return {"error": str(e)[:200]}

