import os

COMPUTER_DEFS = [
    {"type": "function", "function": {"name": "screenshot", "description": "Take screenshot, return saved path. This is the agent's vision.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "mouse_move", "description": "Move mouse to x,y.",
        "parameters": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}, "required": ["x", "y"]}}},
    {"type": "function", "function": {"name": "mouse_click", "description": "Click at x,y. button: left/right/middle.",
        "parameters": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "button": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "key_press", "description": "Press key combo, e.g. ctrl+c, alt+tab, enter.",
        "parameters": {"type": "object", "properties": {"keys": {"type": "string"}}, "required": ["keys"]}}},
    {"type": "function", "function": {"name": "key_type", "description": "Type text as keyboard.",
        "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
]

def screenshot(path: str | None = None) -> dict:
    path = path or os.path.join(os.getcwd(), "screenshot.png")
    try:
        from mss import mss
        from PIL import Image
        with mss() as sct:
            shot = sct.grab(sct.monitors[0])
            Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX").save(path)
        return {"path": path}
    except Exception as e:
        return {"error": f"screenshot needs pip install jhal-code[gui]: {e}"}

def _gui():
    try:
        import pyautogui
        return pyautogui
    except Exception as e:
        raise RuntimeError(f"needs pip install jhal-code[gui]: {e}")

def mouse_move(x: int, y: int) -> dict:
    try:
        _gui().moveTo(x, y)
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)}

def mouse_click(x: int | None = None, y: int | None = None, button: str = "left") -> dict:
    try:
        g = _gui()
        if x is not None and y is not None:
            g.click(x=x, y=y, button=button)
        else:
            g.click(button=button)
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)}

def key_press(keys: str) -> dict:
    try:
        g = _gui()
        parts = [k.strip().lower() for k in keys.split("+")]
        if len(parts) > 1:
            g.hotkey(*parts)
        else:
            g.press(parts[0])
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)}

def key_type(text: str) -> dict:
    try:
        _gui().typewrite(text)
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)}
