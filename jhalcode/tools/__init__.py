from jhalcode.tools.shell import SHELL_DEF, run_shell
from jhalcode.tools.filesystem import FS_DEFS, list_dir, read_file, write_file
from jhalcode.tools.edit import EDIT_DEFS, edit_file
from jhalcode.tools.search import SEARCH_DEFS, grep, glob
from jhalcode.tools.computer import COMPUTER_DEFS, screenshot, mouse_move, mouse_click, key_press, key_type
from jhalcode.tools.browser import BROWSER_DEFS, browser_open, browser_act
from jhalcode.tools.web import WEB_DEFS, web_search, open_file, webfetch
from jhalcode.tools.question import QUESTION_DEFS, question
from jhalcode.tools.todo import TODO_DEFS, todo, plan
from jhalcode.tools.lsp import LSP_DEFS, symbols, diagnose, refs

ALL_DEFS = SHELL_DEF + FS_DEFS + EDIT_DEFS + SEARCH_DEFS + COMPUTER_DEFS + BROWSER_DEFS + WEB_DEFS + QUESTION_DEFS + TODO_DEFS + LSP_DEFS

DISPATCH = {
    "run_shell": run_shell, "list_dir": list_dir, "read_file": read_file,
    "write_file": write_file, "edit_file": edit_file, "grep": grep, "glob": glob,
    "screenshot": screenshot, "mouse_move": mouse_move,
    "mouse_click": mouse_click, "key_press": key_press, "key_type": key_type,
    "browser_open": browser_open, "browser_act": browser_act,
    "web_search": web_search, "open_file": open_file, "webfetch": webfetch,
    "question": question, "todo": todo, "plan": plan,
    "symbols": symbols, "diagnose": diagnose, "refs": refs,
}
