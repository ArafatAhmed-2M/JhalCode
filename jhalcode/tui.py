RED = "#E8291C"
RED_LIGHT = "#FF4B3E"
GREEN = "#6BA53A"
INK = "#1A1420"

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.prompt import Prompt
    from rich import box
    console = Console()
    RICH = True
except Exception:
    console = None
    RICH = False

C = {"dim": "\x1b[2m", "b": "\x1b[1m", "r": "\x1b[38;2;232;41;28m", "g": "\x1b[38;2;107;165;58m", "y": "\x1b[33m", "x": "\x1b[0m"}

STEM_GREEN = "#6BA53A"
PEACH = "#FF9B7A"
DARK_RED = "#8A0F09"
MID_RED = "#C21A10"

def _load(name: str):
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    for p in [os.path.join(here, name), os.path.join(os.getcwd(), name), os.path.join(here, "..", "assets", name)]:
        try:
            if os.path.isfile(p):
                with open(p, encoding="utf-8") as f:
                    return f.read().splitlines()
        except Exception:
            pass
    return None

def _paint_mark(lines):
    out = []
    for i, l in enumerate(lines):
        seg, cur, buf = [], None, ""
        for ch in l:
            if not ch.strip():
                col = None
            elif i < 7:
                col = STEM_GREEN
            elif ch == "+":
                col = PEACH
            elif ch == "*":
                col = RED
            elif ch == "#":
                col = DARK_RED
            else:
                col = MID_RED
            if col != cur:
                if buf:
                    seg.append(f"[bold {cur}]{buf}[/]" if cur else buf)
                cur, buf = col, ch
            else:
                buf += ch
        if buf:
            seg.append(f"[bold {cur}]{buf}[/]" if cur else buf)
        out.append("".join(seg))
    return out

def _wordmark():
    try:
        import pyfiglet
        a = pyfiglet.figlet_format("JHAL", font="banner").splitlines()
        b = pyfiglet.figlet_format("CODE", font="banner").splitlines()
        n = max(len(a), len(b))
        a += [""] * (n - len(a))
        b += [""] * (n - len(b))
        return [f"[bold {RED}]{x.ljust(20)}[/]  [bold white]{y}[/]" for x, y in zip(a, b)]
    except Exception:
        return [f"[bold {RED}]JHAL[/] [bold white]CODE[/]"]

CMDS = "/connect /manager /roles /models /model /status /save /audit /clear /quit"

def banner(auto: bool, model: str):
    import os
    from jhalcode import __version__ as _v
    ver = f"v{_v}"
    sub = f"{model} · {'AUTO' if auto else 'ASK'} · {os.getcwd()}"
    if RICH:
        import random
        from rich.text import Text
        for l in _load("logo_name.txt") or ["Jhal Code"]:
            console.print(Text(l.rstrip() or " ", style=f"bold {RED}"), justify="center")
        console.print(Panel(f"[bold {RED}]Jhal Code[/] [dim]{ver}  ·  {sub}[/]\n[dim]{random.choice(TIPS)} · /help for commands[/]", box=box.ROUNDED, border_style=RED))
    else:
        print(f"{C['r']}{C['b']}JHAL CODE {ver}{C['x']} {C['dim']}{sub}{C['x']}")

def team_panel(roles: dict, auto: bool):
    import os
    from jhalcode import __version__ as _v
    if not RICH:
        for n, r in roles.items():
            print(f"  {n}: {r.get('model')}")
        return
    rows = "\n".join(f"[bold {RED}]{n}[/] [dim]{r.get('model')}[/]" for n, r in roles.items())
    console.print(Panel(f"[bold {RED}]Jhal Code[/] [dim]v{_v} · manager · {'AUTO' if auto else 'ASK'} · {os.getcwd()}[/]\n{rows}\n[dim]{CMDS}[/]", box=box.ROUNDED, border_style=RED))

def echo_user(text: str):
    if RICH:
        from rich.text import Text
        console.print(Text.assemble(("you ❯ ", "bold cyan"), (text, "")), style="on grey11")
    else:
        print(f"\n{C['b']}you ❯ {C['x']}{text}")

def assistant(text: str, stats: str = ""):
    if RICH:
        from rich.text import Text
        console.print()
        console.print(Text("jhal ❯", style=f"bold {RED}"))
        console.print(Markdown(text or "_no reply_"))
        if stats:
            console.print(Text(stats, style="dim"))
        console.print("[dim]" + "─" * 40 + "[/]")
    else:
        print(f"\n{C['r']}{C['b']}jhal ❯{C['x']}\n{text}" + (f"\n{stats}" if stats else ""))

def tool_ok(name: str, res: dict):
    short = {"write_file": "saved", "open_file": "opened", "browser_open": "opened",
             "screenshot": "captured"}.get(name, "done")
    extra = res.get("path", "") if isinstance(res, dict) else ""
    if RICH:
        console.print(f"[dim green]    ✓ {short} {extra}[/]")
    else:
        print(f"    ok {short} {extra}")

def tool_line(name: str, short: str):
    if RICH:
        console.print(f"[dim]  . [{GREEN}]{name}[/] {short}[/]")
    else:
        print(f"{C['dim']}  . {name} {short}{C['x']}")

def tool_err(msg: str):
    if RICH:
        console.print(f"[bold {RED}]    ! {msg[:200]}[/]")
    else:
        print(f"{C['r']}    ! {msg[:200]}{C['x']}")

def blocked(reason: str):
    if RICH:
        console.print(f"[bold {RED}]  x blocked: {reason}[/]")
    else:
        print(f"{C['r']}  x blocked: {reason}{C['x']}")

def thinking():
    if RICH:
        return console.status(f"[bold {RED}]thinking...[/]", spinner="dots")
    from contextlib import nullcontext
    return nullcontext()

def approval(tool: str, short: str, risk: str, preview: str = "") -> str:
    if RICH:
        from rich.markup import escape
        color = GREEN if risk == "low" else "yellow" if risk == "medium" else RED
        body = f"[bold {color}]> {escape(tool)}[/] {escape(short)} [dim][{escape(risk)}][/]"
        if preview:
            body += f"\n[dim]{escape(preview[:400])}[/]"
        console.print(Panel(body, box=box.ROUNDED, border_style=color))
        return Prompt.ask("[dim]Allow?[/]", choices=["y", "n", "always"], default="n").strip().lower()
    print(f"\n{C['r']}{C['b']}> {tool}{C['x']} {short} {C['dim']}[{risk}]{C['x']}")
    if preview:
        print(f"{C['dim']}{preview[:400]}{C['x']}")
    return input(f"{C['dim']}Allow? [y/N/always]: {C['x']}").strip().lower()

try:
    from prompt_toolkit import PromptSession as _Session
    from prompt_toolkit.completion import Completer as _Completer, Completion as _Completion
    PT = True
except Exception:
    PT = False

COMMANDS = {
    "/connect": "connect Zen API key",
    "/manager": "orchestrate specialist team",
    "/solo": "single agent mode",
    "/roles": "list team roles + models",
    "/role add ": "add role: name model | tools | prompt",
    "/agents": "live specialist status",
    "/models": "browse Zen models (/models free)",
    "/auto": "no approval prompts",
    "/ask": "approve medium/high tools",
    "/model ": "switch model",
    "/status": "session info",
    "/save ": "save session",
    "/load ": "resume session",
    "/audit": "recent audit log",
    "/clear": "clear screen",
    "/quit": "exit",
    "/help": "this list",
}

TIPS = [
    "Tip: @file attaches contents · @folder lists it",
    "Tip: /manager fans work out to coder, designer, tester",
    "Tip: /models free shows what costs nothing",
    "Tip: /model role coder <id> retargets one role",
    "Tip: Ctrl+C cancels a running task, never kills jcc",
]

class JhalCompleter(_Completer if PT else object):
    def get_completions(self, document, complete_event):
        import os, re
        before = document.text_before_cursor
        if before.lstrip().startswith("/") and "@" not in before:
            frag = before.strip()
            for c, desc in COMMANDS.items():
                if c.startswith(frag) and c.rstrip() != frag.rstrip():
                    yield _Completion(c, start_position=-len(frag), display=c, display_meta=desc)
            return
        m = re.search(r'@"([^"]*)$|@(\S*)$', before)
        if not m:
            return
        frag = m.group(1) if m.group(1) is not None else m.group(2)
        base, part = os.path.split(frag)
        root = base if os.path.isabs(base) else os.path.join(os.getcwd(), base or ".")
        try:
            names = sorted(os.listdir(root))
        except Exception:
            return
        for n in names:
            if not n.lower().startswith(part.lower()):
                continue
            full = os.path.join(base, n) if base else n
            if os.path.isdir(os.path.join(root, n)):
                full += os.sep
            if " " in full and not before[m.start()].endswith('"'):
                text = f'@"{full}"'
                yield _Completion(text, start_position=-(len(before) - m.start()), display=n + os.sep)
            else:
                yield _Completion("@" + full, start_position=-(len(before) - m.start()), display=n + (os.sep if full.endswith(os.sep) else ""))

_session = None

def _keys():
    from prompt_toolkit.key_binding import KeyBindings
    kb = KeyBindings()

    @kb.add("enter", eager=True)
    def _(event):
        buf = event.current_buffer
        st = buf.complete_state
        if st and st.completions:
            buf.apply_completion(st.current_completion or list(st.completions)[0])
        else:
            buf.validate_and_handle()

    return kb

def ask_task() -> str:
    global _session
    if PT:
        from prompt_toolkit.formatted_text import HTML
        if _session is None:
            _session = _Session(completer=JhalCompleter(), complete_while_typing=True,
                key_bindings=_keys(), bottom_toolbar=" @file attach · /command · enter picks · ctrl+c cancels task ")
        return _session.prompt(HTML("\n<b><ansicyan>you:</ansicyan></b> ")).strip()
    if RICH:
        return Prompt.ask(f"\n[bold cyan]you[/]").strip()
    return input("\nyou> ").strip()
