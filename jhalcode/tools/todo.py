import json
import os

TODO_DEFS = [
    {"type": "function", "function": {"name": "todo", "description": "Manage task plan list. action: add|done|in_progress|pending|list|clear. done matches by #id or fuzzy text.",
        "parameters": {"type": "object", "properties": {"action": {"type": "string"}, "item": {"type": "string", "description": "#id from list, or words from the task"}}, "required": ["action"]}}},
    {"type": "function", "function": {"name": "plan", "description": "Write a step-by-step plan to plan.md and show it. Call before big builds.",
        "parameters": {"type": "object", "properties": {"goal": {"type": "string"}, "steps": {"type": "string", "description": "newline-separated steps"}}, "required": ["goal", "steps"]}}},
]

def _path() -> str:
    return os.path.join(os.getcwd(), ".jhal-todos.json")

def _load() -> list:
    try:
        with open(_path(), encoding="utf-8") as f:
            v = json.load(f)
        return v if isinstance(v, list) else []
    except Exception:
        return []

def _save(items: list):
    p = _path()
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f)
    os.replace(tmp, p)

STATES = ("pending", "in_progress", "done")

def _score(a: str, b: str) -> float:
    a, b = a.lower().split(), b.lower().split()
    if not a or not b:
        return 0.0
    hit = sum(1 for w in a if any(w in x or x in w for x in b))
    return hit / max(len(a), len(b))

def _find(items: list, item: str):
    if item.strip().isdigit():
        i = int(item.strip()) - 1
        if 0 <= i < len(items):
            return items[i]
        return None
    best, score = None, 0.0
    for t in items:
        s = _score(item, t["task"])
        if s > score:
            best, score = t, s
    return best if score >= 0.3 else None

def todo(action: str, item: str = "") -> dict:
    items = _load()
    for t in items:
        t.setdefault("state", "done" if t.get("done") else "pending")
    a = (action or "").strip().lower()
    if a == "add" and item:
        items.append({"task": item, "done": False, "state": "pending"})
        _save(items)
        return {"ok": f"added #{len(items)} ({len(items)} total)"}
    if a in ("done", "in_progress", "pending", "start"):
        state = {"done": "done", "in_progress": "in_progress", "pending": "pending", "start": "in_progress"}[a]
        t = _find([x for x in items] if state == "done" else items, item) if item else None
        if a == "done" and not item and items:
            t = next((x for x in items if x.get("state") not in ("done",)), None)
        if not t:
            open_ = [f"#{i + 1} {x['task']}" for i, x in enumerate(items) if x.get("state") != "done"]
            return {"error": f"no match for '{item}'. open: {open_ or 'none'}"}
        t["state"] = state
        t["done"] = state == "done"
        _save(items)
        return {"ok": f"#{items.index(t) + 1} -> {state}: {t['task']}"}
    if a == "list":
        return {"todos": [(t.get("state", "?"), t["task"]) for t in items]}
    if a == "clear":
        _save([])
        return {"ok": "cleared"}
    return {"error": f"action must be add|done|in_progress|pending|list|clear — e.g. todo(done, #2)"}

def plan(goal: str, steps: str) -> dict:
    try:
        body = f"# Plan: {goal}\n\n" + "\n".join(f"{i}. {s.strip()}" for i, s in enumerate(steps.splitlines(), 1) if s.strip())
        with open(os.path.join(os.getcwd(), "plan.md"), "w", encoding="utf-8") as f:
            f.write(body + "\n")
        try:
            from jhalcode import tui as T
            if T.RICH:
                T.console.print(f"\n[bold cyan]plan: {goal}[/]")
                for i, s in enumerate([s.strip() for s in steps.splitlines() if s.strip()], 1):
                    T.console.print(f"  {i}. {s}")
        except Exception:
            pass
        return {"ok": "plan.md written", "plan": body[:2000]}
    except Exception as e:
        return {"error": str(e)[:300]}
