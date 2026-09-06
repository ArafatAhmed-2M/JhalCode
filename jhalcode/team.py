import json, itertools, threading
from concurrent.futures import ThreadPoolExecutor
from jhalcode.models import ModelClient
from jhalcode import permissions as perm
from jhalcode.audit import log
from jhalcode.tools import ALL_DEFS, DISPATCH
from jhalcode.agent import _shorten

ACTIVE: dict = {}
_active_lock = threading.Lock()
_seq = itertools.count(1)
_seq_lock = threading.Lock()
CANCEL = None
_cancel_lock = threading.Lock()

def set_cancel(ev):
    global CANCEL
    with _cancel_lock:
        CANCEL = ev

def _cancelled() -> bool:
    try:
        with _cancel_lock:
            ev = CANCEL
        return bool(ev and ev.is_set())
    except Exception:
        return False

DELEGATE_DEF = {"type": "function", "function": {"name": "delegate", "description": "Assign work to a specialist role. Manager decides: one call = one at a time, several calls at once = parallel fan-out. Pass images (comma-separated file paths) when the specialist must SEE pictures.",
    "parameters": {"type": "object", "properties": {"role": {"type": "string"}, "task": {"type": "string"}, "images": {"type": "string", "description": "optional comma-separated image paths"}}, "required": ["role", "task"]}}}
ADD_ROLE_DEF = {"type": "function", "function": {"name": "add_role", "description": "Create a new team role (saved to roles.yaml). Use when the team lacks a skill or the user asks.",
    "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "model": {"type": "string"}, "tools": {"type": "string", "description": "comma-separated tool names"}, "system": {"type": "string"}}, "required": ["name", "model", "tools", "system"]}}}

def role_defs(roles: dict, name: str) -> list:
    want = set((roles.get(name) or {}).get("tools", []))
    return [d for d in ALL_DEFS if d["function"]["name"] in want and d["function"]["name"] in ("read_file", "list_dir", "run_shell", "run_bg", "bg_kill", "write_file", "edit_file", "grep", "glob", "web_search", "webfetch", "open_file", "screenshot", "browser_open", "todo", "plan", "symbols", "diagnose", "refs", "question")]

def run_specialist(roles: dict, cfg, role: str, task: str, depth: int = 0, images: list | None = None) -> dict:
    from jhalcode.models import image_part
    r = roles.get(role)
    if not r:
        return {"error": f"unknown role '{role}'. Known: {sorted(roles)}"}
    with _seq_lock:
        aid = f"{role}-{next(_seq)}"
    with _active_lock:
        ACTIVE[aid] = {"role": role, "task": task[:80], "status": "running"}
        while len(ACTIVE) > 100:
            ACTIVE.pop(next(iter(ACTIVE)))
    try:
        client = ModelClient(cfg.base_url, cfg.api_key, r["model"])
        tool_defs = role_defs(roles, role)
        if depth < 1 and role in ("coder", "planner"):
            tool_defs = tool_defs + [DELEGATE_DEF]
        first: dict = {"role": "user", "content": task}
        if images:
            parts: list = [{"type": "text", "text": task}]
            for p in images:
                part = image_part(p)
                if part:
                    parts.append(part)
            if len(parts) > 1:
                first = {"role": "user", "content": parts}
        msgs = [{"role": "system", "content": r.get("system", "")}, first]
        for _ in range(int(r.get("steps", 12))):
            if _cancelled():
                ACTIVE[aid]["status"] = "cancelled"
                return {"role": role, "result": "cancelled by user"}
            resp = client.chat(msgs, tool_defs)
            choices = resp.get("choices") or []
            if not choices:
                return {"role": role, "result": "empty response from model"}
            msg = choices[0]["message"]
            msgs.append(msg)
            calls = msg.get("tool_calls") or []
            if not calls:
                out = msg.get("content", "")
                log(cfg.audit_log, {"event": "specialist_done", "role": role, "output": out[:2000]})
                ACTIVE[aid]["status"] = "done"
                return {"role": role, "result": out}
            for c in calls:
                fn_name = c["function"]["name"]
                try:
                    fargs = json.loads(c["function"].get("arguments") or "{}")
                except Exception:
                    fargs = {}
                if fn_name == "delegate" and depth < 1:
                    sub = run_specialist(roles, cfg, fargs.get("role", "sub-coder"), fargs.get("task", ""), depth + 1)
                    msgs.append({"role": "tool", "tool_call_id": c.get("id", "0"), "content": json.dumps(_shorten(sub, 4000))})
                    continue
                allowed = {d["function"]["name"] for d in tool_defs}
                if fn_name not in allowed:
                    res = {"error": f"tool '{fn_name}' not allowed for role '{role}'"}
                    msgs.append({"role": "tool", "tool_call_id": c.get("id", "0"), "content": json.dumps(res)})
                    continue
                fn = DISPATCH.get(fn_name)
                try:
                    res = fn(**fargs) if fn else {"error": f"unknown tool {fn_name}"}
                except Exception as e:
                    res = {"error": str(e)[:300]}
                log(cfg.audit_log, {"event": "specialist_tool", "role": role, "tool": fn_name})
                msgs.append({"role": "tool", "tool_call_id": c.get("id", "0"), "content": json.dumps(_shorten(res, 4000))})
        ACTIVE[aid]["status"] = "capped"
        return {"role": role, "result": "step cap reached, partial work done"}
    except Exception as e:
        with _active_lock:
            ACTIVE[aid]["status"] = f"error: {e}"[:100]
        return {"role": role, "error": str(e)[:500]}
    finally:
        with _active_lock:
            ACTIVE.pop(aid, None)

def fan_out(roles: dict, cfg, jobs: list) -> list:
    def one(j):
        imgs = [s.strip() for s in str(j.get("images") or "").split(",") if s.strip()]
        return run_specialist(roles, cfg, j["role"], j["task"], images=imgs or None)
    if len(jobs) < 2 or _cancelled():
        return [one(j) for j in jobs]
    with ThreadPoolExecutor(max_workers=min(max(len(jobs), 1), 8)) as ex:
        return list(ex.map(one, jobs))
