from jhalcode.tools.shell import SHELL_DEF, BG_DEFS, BG_KILL_DEFS, run_shell, run_bg, bg_kill
from jhalcode.tools.filesystem import FS_DEFS, list_dir, read_file, write_file
from jhalcode.tools.edit import EDIT_DEFS, edit_file
from jhalcode.tools.search import SEARCH_DEFS, grep, glob
from jhalcode.tools.computer import COMPUTER_DEFS, screenshot, mouse_move, mouse_click, key_press, key_type
from jhalcode.tools.browser import BROWSER_DEFS, browser_open, browser_act
from jhalcode.tools.web import WEB_DEFS, web_search, open_file, webfetch
from jhalcode.tools.question import QUESTION_DEFS, question
from jhalcode.tools.todo import TODO_DEFS, todo, plan
from jhalcode.tools.lsp import LSP_DEFS, symbols, diagnose, refs

def _have(mod: str) -> bool:
    try:
        __import__(mod)
        return True
    except Exception:
        return False

GUI_OK = _have("pyautogui") and _have("mss") and _have("PIL")
BROWSER_OK = _have("playwright")

ALL_DEFS = (SHELL_DEF + BG_DEFS + BG_KILL_DEFS + FS_DEFS + EDIT_DEFS + SEARCH_DEFS
            + (COMPUTER_DEFS if GUI_OK else []) + (BROWSER_DEFS if BROWSER_OK else [])
            + WEB_DEFS + QUESTION_DEFS + TODO_DEFS + LSP_DEFS)

DISPATCH = {
    "run_shell": run_shell, "run_bg": run_bg, "bg_kill": bg_kill,
    "list_dir": list_dir, "read_file": read_file,
    "write_file": write_file, "edit_file": edit_file, "grep": grep, "glob": glob,
    "screenshot": screenshot, "mouse_move": mouse_move,
    "mouse_click": mouse_click, "key_press": key_press, "key_type": key_type,
    "browser_open": browser_open, "browser_act": browser_act,
    "web_search": web_search, "open_file": open_file, "webfetch": webfetch,
    "question": question, "todo": todo, "plan": plan,
    "symbols": symbols, "diagnose": diagnose, "refs": refs,
}
