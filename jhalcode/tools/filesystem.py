import os

FS_DEFS = [
    {"type": "function", "function": {"name": "list_dir", "description": "List directory contents.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read text file (truncated).",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Write/overwrite text file.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
]

def list_dir(path: str) -> dict:
    try:
        rp = os.path.realpath(path)
        base = os.path.realpath(os.getcwd())
        if os.path.commonpath([rp, base]) != base:
            return {"error": "list confined to workdir"}
        return {"entries": sorted(os.listdir(rp))[:500]}
    except Exception as e:
        return {"error": str(e)[:200]}

def read_file(path: str) -> dict:
    try:
        import os as _os
        with open(path, "rb") as f:
            raw = f.read(12000 + 1)
        if b"\x00" in raw:
            return {"binary": True, "size": _os.path.getsize(path), "note": "binary file, no text. Images: attach with @path so you can SEE them. Media: use open_file to show the user."}
        text = raw.decode("utf-8", errors="strict")
        trunc = len(raw) > 12000
        return {"content": text[:12000] + ("...[truncated]" if trunc else "")}
    except UnicodeDecodeError:
        return {"binary": True, "note": "not UTF-8 text. Images: attach with @path so you can SEE them."}
    except Exception as e:
        return {"error": str(e)}

def write_file(path: str, content: str) -> dict:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)}
