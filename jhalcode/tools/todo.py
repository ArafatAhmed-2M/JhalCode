import json
import os

TODO_DEFS = [
    {"type": "function", "function": {"name": "todo", "description": "Manage task plan list. action: add|done|list. Use for multi-step work so progress is visible.",
        "parameters": {"type": "object", "properties": {"action": {"type": "string"}, "item": {"type": "string"}}, "required": ["action"]}}},
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

def todo(action: str, item: str = "") -> dict:
    items = _load()
    if action == "add" and item:
        items.append({"task": item, "done": False})
        _save(items)
        return {"ok": f"added ({len(items)} total)"}
    if action == "done" and item:
        for t in items:
            if not t["done"] and item.lower() in t["task"].lower():
                t["done"] = True
                _save(items)
                return {"ok": f"done: {t['task']}"}
        return {"error": "no matching open item"}
    if action == "list":
        return {"todos": [("x" if t["done"] else " ", t["task"]) for t in items]}
    if action == "clear":
        _save([])
        return {"ok": "cleared"}
    return {"error": "action: add|done|list|clear"}

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
