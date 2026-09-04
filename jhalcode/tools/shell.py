from jhalcode.platform import get_backend

SHELL_DEF = [{
    "type": "function", "function": {
        "name": "run_shell",
        "description": "Run a Windows shell command (powershell/cmd). Returns exit code + output.",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string"}, "cwd": {"type": "string"}, "timeout": {"type": "integer"}},
            "required": ["command"]}}}]

def run_shell(command: str, cwd: str | None = None, timeout: int = 60) -> dict:
    return get_backend().shell(command, cwd, timeout or 60)

