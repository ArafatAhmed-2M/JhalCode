EDIT_DEFS = [
    {"type": "function", "function": {"name": "edit_file", "description": "Surgical edit: replace first occurrence of oldString with newString. Prefer over write_file.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "oldString": {"type": "string"}, "newString": {"type": "string"}}, "required": ["path", "oldString", "newString"]}}},
]

def edit_file(path: str, oldString: str, newString: str) -> dict:
    import os as _os
    try:
        if not oldString:
            return {"error": "oldString empty"}
        if oldString == newString:
            return {"error": "no change"}
        with open(path, encoding="utf-8") as f:
            src = f.read()
        if oldString not in src:
            return {"error": "oldString not found"}
        if src.count(oldString) > 1:
            return {"error": f"oldString matches {src.count(oldString)}x — include more context"}
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(src.replace(oldString, newString, 1))
        _os.replace(tmp, path)
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)[:300]}
