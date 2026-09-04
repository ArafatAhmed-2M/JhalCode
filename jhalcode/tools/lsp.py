"""LSP-lite: symbols, diagnostics, references without a language server."""
import ast
import os
import re

LSP_DEFS = [
    {"type": "function", "function": {"name": "symbols", "description": "List code symbols (functions/classes) in a file.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "diagnose", "description": "Syntax-check a file (python compile, node --check).",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "refs", "description": "Find references to a symbol name under a directory.",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "path": {"type": "string"}}, "required": ["name"]}}},
]

DEF_RX = re.compile(r"^\s*(?:function|class|def|const|let|var|export\s+(?:function|class|const)|sub|fn)\s+([A-Za-z_]\w*)|^\s*([A-Za-z_]\w*)\s*[:=]\s*(?:function|\(|=>)")

def symbols(path: str) -> dict:
    try:
        src = open(path, encoding="utf-8").read()
    except Exception as e:
        return {"error": str(e)[:200]}
    out = []
    if path.endswith(".py"):
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            return {"error": f"syntax error line {e.lineno}: {e.msg}"}
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.append(f"def {n.name}:{n.lineno}")
            elif isinstance(n, ast.ClassDef):
                out.append(f"class {n.name}:{n.lineno}")
        return {"symbols": out}
    for i, line in enumerate(src.splitlines(), 1):
        m = DEF_RX.match(line)
        if m:
            out.append(f"{m.group(1) or m.group(2)}:{i}")
    return {"symbols": out[:200]}

def diagnose(path: str) -> dict:
    import subprocess
    try:
        if path.endswith(".py"):
            src = open(path, encoding="utf-8").read()
            compile(src, path, "exec")
            return {"ok": "no syntax errors"}
        if path.endswith((".js", ".mjs", ".cjs")):
            p = subprocess.run(["node", "--check", path], capture_output=True, text=True, timeout=30)
            return {"ok": "no syntax errors"} if p.returncode == 0 else {"error": (p.stderr or p.stdout)[:500]}
        return {"note": "no checker for this extension; python/node supported"}
    except SyntaxError as e:
        return {"error": f"line {e.lineno}: {e.msg}"}
    except FileNotFoundError:
        return {"error": "checker runtime missing"}
    except Exception as e:
        return {"error": str(e)[:300]}

def refs(name: str, path: str | None = None) -> dict:
    from jhalcode.tools.search import grep
    rx = r"\b" + re.escape(name) + r"\b"
    r = grep(rx, path)
    defs = [h for h in r.get("matches", []) if re.search(r"(def|class|function)\s+" + re.escape(name), h)]
    uses = [h for h in r.get("matches", []) if h not in defs]
    return {"defs": defs[:10], "uses": uses[:40], "truncated": r.get("truncated", False)}
