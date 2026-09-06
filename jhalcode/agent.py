import json
from jhalcode.config import JhalConfig
from jhalcode.models import ModelClient
from jhalcode import permissions as perm
from jhalcode import tui as T
from jhalcode.audit import log
from jhalcode.tools import ALL_DEFS, DISPATCH

SYSTEM = """You are Jhal Code, a PC agent that does anything a human can do on Windows.
You have shell, files, mouse/keyboard, screenshots (vision), browser.
You CAN see images: @attached images and your screenshots are shown to you as pictures.
Always: 1) screenshot to see screen before GUI actions (the picture is attached automatically), 2) prefer safe APIs over GUI clicks, 3) explain briefly.
Tool args MUST be valid JSON with double quotes. Never use single quotes.
If output is missing dependency, tell user the pip install command."""

def _safe_args(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    s = str(raw).strip()
    try:
        v = json.loads(s)
        return v if isinstance(v, dict) else {"_parse_error": s[:500]}
    except Exception:
        pass
    try:
        import re
        fixed = re.sub(r",\s*([}\]])", r"\1", s)
        v = json.loads(fixed)
        return v if isinstance(v, dict) else {"_parse_error": s[:500]}
    except Exception:
        return {"_parse_error": s[:500]}


def _shorten(obj, limit: int = 4000):
    import json as _j
    try:
        s = _j.dumps(obj)
    except Exception:
        return str(obj)[:limit]
    if len(s) <= limit:
        return obj
    def cut(v, n: int):
        if isinstance(v, str):
            return v[:n] + "...[truncated]"
        if isinstance(v, dict):
            return {k: cut(x, max(n // max(len(v), 1), 50)) for k, x in v.items()}
        if isinstance(v, list):
            return [cut(x, max(n // max(len(v), 1), 50)) for x in v[:20]]
        return v
    return cut(obj, limit)

class JhalAgent:
    def __init__(self, cfg: JhalConfig, role: str | None = None, roles: dict | None = None):
        import threading
        self.cfg = cfg
        self.role = role
        self.roles = roles or {}
        self.cancel = threading.Event()
        self._vision_off = False
        if role and role in self.roles:
            self.system = self.roles[role].get("system", SYSTEM)
            from jhalcode import team as _team
            want = set(self.roles[role].get("tools", []))
            if role == "manager" or "all" in want:
                self.defs = ALL_DEFS + [_team.DELEGATE_DEF, _team.ADD_ROLE_DEF]
            else:
                self.defs = [d for d in ALL_DEFS if d["function"]["name"] in want]
            self.model = self.roles[role].get("model", cfg.model)
            self.max_steps = int(self.roles[role].get("steps", cfg.max_steps))
        else:
            self.system = SYSTEM
            self.defs = ALL_DEFS
            self.model = cfg.model
            self.max_steps = cfg.max_steps
        self.messages = [{"role": "system", "content": self.system + f"\nYour model id is {self.model} — say it exactly when asked."}]

    def set_model(self, mid: str):
        self.model = mid
        self.messages[0]["content"] = self.system + f"\nYour model id is {self.model} — say it exactly when asked."

    def save(self, path: str = "jhal-session.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.messages, f)
        return path

    def load(self, path: str = "jhal-session.json"):
        with open(path, encoding="utf-8") as f:
            self.messages = json.load(f)
        return len(self.messages)

    def compact(self) -> str:
        if len(self.messages) < 10:
            return "too short to compact"
        mid = len(self.messages) // 2
        head = self.messages[1:mid]
        summary = "Summary of earlier turns:\n" + "\n".join(str(m.get("content", ""))[:120] for m in head if m.get("role") in ("user", "assistant"))
        try:
            from jhalcode.models import ModelClient
            c = ModelClient(self.cfg.base_url, self.cfg.api_key, self.model)
            r = c.chat([{"role": "system", "content": "Summarize this conversation in under 200 words, keeping goals and decisions."},
                        {"role": "user", "content": summary}])
            summary = r["choices"][0]["message"].get("content", summary)
        except Exception:
            pass
        self.messages = [self.messages[0], {"role": "user", "content": f"[compacted context]\n{summary}"}] + self.messages[mid:]
        return f"compacted {len(head)} turns → {len(summary)} chars"

    def cost(self) -> str:
        u = getattr(self, "_usage", {"prompt_tokens": 0, "completion_tokens": 0})
        total = u.get("prompt_tokens", 0) + u.get("completion_tokens", 0)
        return f"prompt {u.get('prompt_tokens', 0)} + completion {u.get('completion_tokens', 0)} = {total} tokens"

    def _chat(self):
        models = [self.model] + [m for m in self.cfg.model_list() if m != self.model]
        errs = []
        for m in models:
            try:
                c = ModelClient(self.cfg.base_url, self.cfg.api_key, m)
                return c.chat(self.messages, self.defs)
            except Exception as e:
                errs.append(f"{m}: {str(e)[:200]}")
        if any(k in e.lower() for e in errs for k in ("image input", "image_url", "does not support image", "no endpoints found that support image")):
            self._strip_images()
            errs2 = []
            for m in models:
                try:
                    c = ModelClient(self.cfg.base_url, self.cfg.api_key, m)
                    return c.chat(self.messages, self.defs)
                except Exception as e:
                    errs2.append(f"{m}: {str(e)[:200]}")
            raise RuntimeError("All models failed: " + " | ".join(errs2))
        raise RuntimeError("All models failed: " + " | ".join(errs))

    def _strip_images(self):
        self._vision_off = True
        T.tool_err("vision rejected by model — continuing text-only (file names kept)")
        for msg in self.messages:
            c = msg.get("content")
            if isinstance(c, list):
                text = " ".join(p.get("text", "") for p in c if p.get("type") == "text")
                n_img = sum(1 for p in c if p.get("type") == "image_url")
                if n_img:
                    text += f" [{n_img} image(s) could not be shown — work from file names]"
                msg["content"] = text

    def _exec_pc_tool(self, name: str, args: dict, call_id: str, pending: list | None = None):
        reason = perm.blocked_reason(name, args)
        if reason:
            T.blocked(reason)
            self.messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps({"error": reason})})
            return
        if perm.needs_approval(name, args, self.cfg.auto_mode):
            ok = perm.ask_user(name, args)
            if not ok:
                self.messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps({"denied": True})})
                return
            if ok == "always":
                self.cfg.auto_mode = True
                print("  auto mode on")
        else:
            T.tool_line(name, perm._short(name, args))
        fn = DISPATCH.get(name)
        try:
            res = fn(**args) if fn else {"error": f"unknown tool {name}"}
        except TypeError as e:
            res = {"error": f"bad args for {name}: {e}"}
        except Exception as e:
            res = {"error": str(e)}
        if "error" in res:
            T.tool_err(res["error"])
        else:
            T.tool_ok(name, res if isinstance(res, dict) else {})
        if pending is not None and not self._vision_off and name == "screenshot" and "error" not in res and isinstance(res.get("path"), str):
            import os as _os
            if _os.path.isfile(res["path"]):
                pending.append(res["path"])
                pending[:] = pending[-3:]
        log(self.cfg.audit_log, {"event": "tool", "tool": name, "args": args, "result": str(res)[:2000]})
        self.messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps(res)})

    def run(self, task: str, images: list | None = None) -> str:
        import time as _t
        from jhalcode import team as _team
        from jhalcode.models import image_part
        t0 = _t.time()
        self._usage = {"prompt_tokens": 0, "completion_tokens": 0}
        if images:
            parts: list = [{"type": "text", "text": task}]
            for p in images:
                part = image_part(p)
                if part:
                    parts.append(part)
            self.messages.append({"role": "user", "content": parts})
        else:
            self.messages.append({"role": "user", "content": task})
        log(self.cfg.audit_log, {"event": "task_start", "task": task[:500], "role": self.role or "solo", "images": len(images or [])})
        self.cancel.clear()
        self._vision_off = False
        from jhalcode import team as _team2
        _team2.set_cancel(self.cancel)
        pending: list = []
        for _ in range(self.max_steps):
            if self.cancel.is_set():
                T.tool_err("cancelled")
                return "cancelled by user"
            if pending:
                vision: list = [{"type": "text", "text": "[vision: screenshot(s) you just took — look at them]"}]
                for p in pending:
                    part = image_part(p)
                    if part:
                        vision.append(part)
                pending = []
                if len(vision) > 1:
                    self.messages.append({"role": "user", "content": vision})
            with T.thinking():
                resp = self._chat()
            u = resp.get("usage") or {}
            self._usage["prompt_tokens"] += u.get("prompt_tokens", 0)
            self._usage["completion_tokens"] += u.get("completion_tokens", 0)
            choices = resp.get("choices") or []
            if not choices:
                return "empty response from model"
            msg = choices[0]["message"]
            self.messages.append(msg)
            calls = msg.get("tool_calls") or []
            if not calls:
                out = msg.get("content", "")
                log(self.cfg.audit_log, {"event": "done", "output": out})
                import time as _t2
                dt = _t2.time() - t0
                total = self._usage['prompt_tokens'] + self._usage['completion_tokens']
                stats = f"{dt:.1f}s · {total} tokens"
                T.assistant(out, stats)
                T._status_bar(self.model, total, dt)
                return out
            parsed = []
            for c in calls:
                try:
                    name = c["function"]["name"]
                except Exception:
                    continue
                args = _safe_args(c["function"].get("arguments"))
                if "_parse_error" in args:
                    self.messages.append({"role": "tool", "tool_call_id": c.get("id", "0"), "content": json.dumps({"error": "bad JSON args, retry with valid JSON"})})
                    continue
                parsed.append((c.get("id", "0"), name, args))
            deleg = [(i, n, a) for i, n, a in parsed if n == "delegate" and self.role == "manager"]
            rest = [(i, n, a) for i, n, a in parsed if not (n == "delegate" and self.role == "manager")]
            if deleg:
                T.tool_line("delegate", f"{len(deleg)} job(s) {'in parallel' if len(deleg) > 1 else 'one at a time'}")
                results = _team.fan_out(self.roles, self.cfg, [{"role": a.get("role", ""), "task": a.get("task", ""), "images": a.get("images", "")} for _, _, a in deleg])
                for (cid, _, a), res in zip(deleg, results):
                    log(self.cfg.audit_log, {"event": "delegate", "role": a.get("role"), "result": str(res)[:2000]})
                    self.messages.append({"role": "tool", "tool_call_id": cid, "content": json.dumps(_shorten(res, 6000))})
            for cid, name, args in rest:
                if name == "add_role" and self.role == "manager":
                    ok = perm.ask_user(name, args)
                    if not ok:
                        self.messages.append({"role": "tool", "tool_call_id": cid, "content": json.dumps({"denied": True, "hint": "user declined; use default roles instead"})})
                        continue
                    from jhalcode import roles as _roles
                    tools = [t.strip() for t in str(args.get("tools", "")).split(",") if t.strip()]
                    msg_out = _roles.add_role(args.get("name", ""), args.get("model", self.cfg.model), tools, args.get("system", ""), fallback=self.roles.get("manager", {}).get("fallback", []))
                    self.roles = _roles.load()
                    T.tool_line("add_role", msg_out)
                    self.messages.append({"role": "tool", "tool_call_id": cid, "content": json.dumps({"ok": msg_out})})
                    continue
                self._exec_pc_tool(name, args, cid, pending)
        return "Max steps reached."
