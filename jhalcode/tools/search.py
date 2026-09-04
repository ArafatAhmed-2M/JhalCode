import os
import re

SEARCH_DEFS = [
    {"type": "function", "function": {"name": "grep", "description": "Search file contents by regex. Returns file:line matches (capped).",
        "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}, "include": {"type": "string"}}, "required": ["pattern"]}}},
    {"type": "function", "function": {"name": "glob", "description": "Find files by glob pattern, e.g. **/*.py.",
        "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern"]}}},
]

SKIP = {".git", "__pycache__", "node_modules", ".venv", "venv", ".cache"}

def grep(pattern: str, path: str | None = None, include: str | None = None) -> dict:
    try:
        rx = re.compile(pattern)
    except Exception as e:
        return {"error": f"bad regex: {e}"}
    import fnmatch
    root = os.path.realpath(path or os.getcwd())
    base = os.path.realpath(os.getcwd())
    try:
        if os.path.commonpath([root, base]) != base:
            return {"error": "search confined to workdir"}
    except Exception:
        return {"error": "bad path"}
    hits: list = []
    if os.path.isfile(root):
        files = [root]
    else:
        files = []
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d not in SKIP]
            for f in fn:
                if include and not fnmatch.fnmatch(f, include):
                    continue
                files.append(os.path.join(dp, f))
                if len(files) > 2000:
                    return {"error": "too many files, narrow include"}
    for fp in files:
        try:
            with open(fp, encoding="utf-8", errors="strict") as f:
                for i, line in enumerate(f, 1):
                    if rx.search(line):
                        hits.append(f"{fp}:{i}:{line.strip()[:160]}")
                        if len(hits) >= 50:
                            return {"matches": hits, "truncated": True}
        except Exception:
            continue
    return {"matches": hits}

def glob(pattern: str, path: str | None = None) -> dict:
    import glob as _g
    base = os.path.realpath(os.getcwd())
    pat = os.path.realpath(pattern) if os.path.isabs(pattern) else os.path.join(os.path.realpath(path or os.getcwd()), pattern)
    try:
        anchor = os.path.dirname(pat.rstrip("*?[]")) or base
        if os.path.commonpath([os.path.realpath(anchor), base]) != base:
            return {"error": "glob confined to workdir"}
    except Exception:
        return {"error": "bad pattern"}
    hits = []
    for p in _g.glob(pat, recursive=True):
        try:
            rp = os.path.realpath(p)
            if os.path.isfile(rp) and os.path.commonpath([rp, base]) == base:
                hits.append(rp)
        except Exception:
            continue
        if len(hits) >= 100:
            return {"files": hits, "truncated": True}
    return {"files": hits}
