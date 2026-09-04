import webbrowser

BROWSER_DEFS = [
    {"type": "function", "function": {"name": "browser_open", "description": "Open URL in default browser.",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "browser_act", "description": "Playwright action: snapshot/click/type/goto. Requires playwright install.",
        "parameters": {"type": "object", "properties": {"action": {"type": "string"}, "selector": {"type": "string"}, "text": {"type": "string"}, "url": {"type": "string"}}, "required": ["action"]}}},
]

def browser_open(url: str) -> dict:
    try:
        webbrowser.open(url)
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)}

def browser_act(action: str, selector: str | None = None, text: str | None = None, url: str | None = None) -> dict:
    return {"error": "browser_act needs pip install jhal-code[browser] and Playwright setup. Use browser_open + screenshot + mouse/keyboard for now."}
