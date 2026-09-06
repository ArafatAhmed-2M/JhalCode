import os
from jhalcode import tui as T

RISK = {
    "screenshot": "low", "read_file": "low", "list_dir": "low", "web_search": "low",
    "delegate": "low", "grep": "low", "glob": "low", "webfetch": "low",
    "question": "low", "todo": "low", "plan": "low",
    "symbols": "low", "diagnose": "low", "refs": "low",
    "write_file": "medium", "edit_file": "medium", "run_shell": "medium", "browser_open": "medium",
    "browser_act": "medium", "open_file": "medium",
    "mouse_move": "high", "mouse_click": "high",
    "key_press": "high", "key_type": "high", "add_role": "high",
}
BLOCK_SHELL = ("format ", "format.com", "mkfs", "dd if=", "shutdown ", "shutdown.exe", ":\\windows\\system32",
               "reg delete hklm", "vssadmin delete", "bcdedit /delete", "rd /s", "rmdir /s", "takeown",
               "cipher /w", "del /s", "remove-item", "wmic shadowcopy delete",
               "rm -rf /", ":(){", "shutdown -h", "shutdown now", "poweroff", "reboot")
PROTECTED = ("c:\\windows", "c:\\program files", "c:\\program files (x86)",
             "/etc", "/usr", "/bin", "/sbin", "/boot", "/sys", "/proc")


def _norm(p: str) -> str:
    return os.path.realpath(os.path.expandvars(p)).lower().replace("/", "\\")


def _under(path: str, root: str) -> bool:
    path = _norm(path)
    root = _norm(root).rstrip("\\")
    return path == root or path.startswith(root + "\\")


def _hits_protected(text: str) -> str | None:
    low = text.lower().replace("/", "\\")
    for d in PROTECTED:
        if d in low and (d + "\\" in low or low.rstrip().endswith(d)):
            return d
    return None


def _segments(cmd: str) -> list:
    import re
    parts, cur, q = [], "", None
    for ch in cmd:
        if q:
            cur += ch
            if ch == q:
                q = None
        elif ch in "\"'":
            q, cur = ch, cur + ch
        elif ch in "&|;":
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p for p in parts if p.strip()]

def risk_of(tool: str, args: dict) -> str:
    if tool == "run_shell":
        cmd = str(args.get("command", "")).lower()
        if any(h in cmd for h in ("rm -rf", "del /f", "del /s", "rd /s", "shutdown", "reg delete", "takeown", "cipher /w", "remove-item")):
            return "high"
        return "medium"
    return RISK.get(tool, "medium")

def blocked_reason(tool: str, args: dict) -> str | None:
    if tool == "run_shell":
        import re
        for seg in _segments(str(args.get("command", ""))):
            low = seg.lower()
            for h in BLOCK_SHELL:
                if h in low:
                    return f"blocked shell pattern: {h}"
            for m in re.finditer(r"(?:^|[\s&|;])(?:2?>|&>|out-file)\s*\"?([a-z]:\\[^\s\"|<>]+|\S+)", low):
                if any(_under(m.group(1).strip("\"'"), d) for d in PROTECTED):
                    return "protected redirect target"
        cwd = str(args.get("cwd") or "")
        if cwd and any(_under(cwd, d) for d in PROTECTED):
            return "protected cwd"
        return None
    if tool in ("write_file", "edit_file"):
        p = str(args.get("path", ""))
        for d in PROTECTED:
            if _under(p, d):
                return f"protected path: {d}"
    return None

def needs_approval(tool: str, args: dict, auto_mode: bool) -> bool:
    if auto_mode:
        return False
    return risk_of(tool, args) in ("medium", "high")

def _short(tool: str, args: dict) -> str:
    if tool == "write_file":
        return f"{args.get('path')} ({len(str(args.get('content', '')))} chars)"
    if tool == "run_shell":
        c = str(args.get("command", ""))
        return c[:160] + ("..." if len(c) > 160 else "")
    if tool == "key_type":
        t = str(args.get("text", ""))
        return t[:60] + ("..." if len(t) > 60 else "")
    s = str(args)
    return s[:160] + ("..." if len(s) > 160 else "")

def _preview(tool: str, args: dict) -> str:
    if tool == "write_file":
        return str(args.get("content", ""))[:400]
    return ""

def _diff_for(tool: str, args: dict) -> str:
    if tool not in ("write_file", "edit_file"):
        return ""
    path = str(args.get("path", ""))
    try:
        old = open(path, encoding="utf-8").read() if os.path.isfile(path) else ""
    except Exception:
        old = ""
    new = args.get("content", "") if tool == "write_file" else args.get("newString", "")
    if tool == "edit_file":
        old2 = args.get("oldString", "")
        if old2 and old2 in old:
            new = old.replace(old2, new, 1)
    import jhalcode.tui as _T
    return _T._diff(old, new, path)[:2000]

def ask_user(tool: str, args: dict):
    ans = T.approval(tool, _short(tool, args), risk_of(tool, args), _preview(tool, args), _diff_for(tool, args))
    if ans in ("always", "auto"):
        return "always"
    return ans in ("y", "yes")
