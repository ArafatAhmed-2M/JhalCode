import argparse, os
from jhalcode.config import JhalConfig
from jhalcode.agent import JhalAgent
from jhalcode import attach as At
from jhalcode import tui as T

def _run(agent, task: str):
    import threading
    task, notes, images = At.expand(task)
    for n in notes:
        print(f"  {n}")
    out = {}
    def _target():
        try:
            out["r"] = agent.run(task, images=images or None)
        except BaseException as e:
            out["e"] = e
    th = threading.Thread(target=_target, daemon=True)
    th.start()
    try:
        while th.is_alive():
            th.join(0.1)
    except KeyboardInterrupt:
        agent.cancel.set()
        print("\ncancelling...")
        th.join(2.0)
        from jhalcode.audit import log
        log(agent.cfg.audit_log, {"event": "cancelled"})
        print("task cancelled — back to prompt")
        return
    if "e" in out:
        raise out["e"]

def _connect(cfg) -> bool:
    import urllib.request, json
    try:
        from prompt_toolkit import prompt as _pt
        key = _pt("Zen API key: ", is_password=True).strip()
    except Exception:
        try:
            import getpass
            key = getpass.getpass("Zen API key: ").strip()
        except Exception:
            key = input("Zen API key: ").strip()
    if not key:
        print("cancelled")
        return False
    base = (input(f"Base URL [{cfg.base_url}]: ").strip() or cfg.base_url).rstrip("/")
    try:
        if "openrouter" in base:
            req = urllib.request.Request(f"{base}/auth/key",
                headers={"Authorization": f"Bearer {key}", "User-Agent": "Jhal-Code/0.2.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                info = json.loads(r.read().decode()).get("data", {})
            n = f"key ok ({info.get('label', 'no label')})"
        else:
            req = urllib.request.Request(f"{base}/models",
                headers={"Authorization": f"Bearer {key}", "User-Agent": "Jhal-Code/0.2.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                n = f"{len(json.loads(r.read().decode()).get('data', []))} models"
    except Exception as e:
        print(f"key rejected: {str(e)[:150]}")
        return False
    cfg.api_key, cfg.base_url = key, base
    cfg.models = ""
    os.environ["JHAL_API_KEY"], os.environ["JHAL_BASE_URL"] = key, base
    try:
        del os.environ["JHAL_MODELS"]
    except KeyError:
        pass
    try:
        p = os.path.join(os.path.expanduser("~"), ".jhalcode.env")
        lines = []
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                lines = [l for l in f.read().splitlines() if not l.startswith(("JHAL_API_KEY=", "JHAL_BASE_URL="))]
        lines += [f"JHAL_API_KEY={key}", f"JHAL_BASE_URL={base}"]
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        if os.name == "nt":
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, "JHAL_API_KEY", 0, winreg.REG_SZ, key)
                winreg.SetValueEx(k, "JHAL_BASE_URL", 0, winreg.REG_SZ, base)
    except Exception as e:
        print(f"saved for session only: {str(e)[:100]}")
    print(f"connected: {n} · key ...{key[-4:]}")
    print("note: model IDs are provider-specific — pick one from this provider")
    return True


def _manager_agent(cfg) -> JhalAgent:
    from jhalcode import roles as R
    roles = R.load()
    print("  checking team models...")
    for n in R.resolve_live(roles, cfg.base_url, cfg.api_key):
        print(f"  {n}")
    return JhalAgent(cfg, role="manager", roles=roles)

def main():
    p = argparse.ArgumentParser(prog="jhal-code", description="Jhal Code - human-like PC agent")
    p.add_argument("task", nargs="*", help="Task")
    p.add_argument("--auto", action="store_true")
    p.add_argument("--once", action="store_true")
    p.add_argument("--manager", action="store_true", help="Manager mode: orchestrates specialist team")
    p.add_argument("--model", default=None)
    p.add_argument("--base-url", default=None)
    a = p.parse_args()
    cfg = JhalConfig.from_env()
    if a.auto:
        cfg.auto_mode = True
    if a.model:
        cfg.model = a.model
        cfg.models = a.model
    if a.base_url:
        cfg.base_url = a.base_url
    mgr = None
    if a.manager:
        mgr = _manager_agent(cfg)
    agent = mgr or JhalAgent(cfg)
    T.banner(cfg.auto_mode, (mgr.roles["manager"]["model"] if mgr else cfg.model_list()[0]))
    if a.task:
        _run(agent, " ".join(a.task))
        if a.once:
            return
    while True:
        try:
            task = T.ask_task()
        except EOFError:
            print("\nBye.")
            break
        except KeyboardInterrupt:
            print("\n(clean prompt — type exit to quit)")
            continue
        if not task:
            continue
        low = task.lower()
        if low in ("exit", "quit", "q", "/quit"):
            print("Bye.")
            break
        if task == "/auto":
            cfg.auto_mode = True
            print("auto mode on — no prompts")
            continue
        if task == "/ask":
            cfg.auto_mode = False
            print("ask mode on — approves medium/high")
            continue
        if task == "/model" or task.startswith("/model "):
            from jhalcode import roles as R
            _, _, v = task.partition(" ")
            v = v.strip()
            is_mgr = getattr(agent, "role", None) == "manager"
            if v.startswith("role "):
                try:
                    _, role, mid = v.split(None, 2)
                except ValueError:
                    print("use: /model role <name> <model-id>")
                    continue
                roles = R.load()
                if role not in roles:
                    print(f"unknown role. Known: {sorted(roles)}")
                    continue
                roles[role]["model"] = mid
                R.save(roles)
                agent.roles = roles
                if getattr(agent, "role", None) == role and hasattr(agent, "set_model"):
                    agent.set_model(mid)
                print(f"{role} -> {mid} (saved)")
            elif v:
                if is_mgr:
                    roles = R.load()
                    roles["manager"]["model"] = v
                    R.save(roles)
                    agent.roles = roles
                    agent.set_model(v)
                    print(f"manager -> {v} (saved)")
                else:
                    cfg.model = v
                    cfg.models = v
                    agent.set_model(v)
                    print(f"solo -> {v}")
            else:
                if is_mgr:
                    for n, r in agent.roles.items():
                        mark = "*" if n == "manager" else " "
                        print(f"{mark} {n}: {r.get('model')}")
                    print("use: /model <id> (manager) or /model role <name> <id>")
                else:
                    print(f"solo models: {cfg.model_list()}")
            continue
        if task == "/manager":
            mgr = _manager_agent(cfg)
            agent = mgr
            print("manager mode on — talk, it delegates")
            T.team_panel(agent.roles, cfg.auto_mode)
            continue
        if task == "/solo":
            agent = JhalAgent(cfg)
            print("solo mode on")
            T.banner(cfg.auto_mode, cfg.model_list()[0])
            continue
        if task == "/roles":
            from jhalcode import roles as R
            for n, r in R.load().items():
                print(f"{n}: {r.get('model')} [{','.join(r.get('tools', []))}]")
            continue
        if task.startswith("/models"):
            from jhalcode import catalog as Cat
            _, _, v = task.partition(" ")
            if "openrouter" in cfg.base_url:
                import urllib.request, json
                try:
                    req = urllib.request.Request(f"{cfg.base_url.rstrip('/')}/models",
                        headers={"Authorization": f"Bearer {cfg.api_key}", "User-Agent": "Jhal-Code/0.2.0"})
                    with urllib.request.urlopen(req, timeout=30) as r:
                        ids = sorted(m["id"] for m in json.loads(r.read().decode()).get("data", []))
                    if "free" in v:
                        ids = [i for i in ids if i.endswith(":free")]
                    for i in ids[:120]:
                        print(f"  {i}")
                    print(f"({len(ids)} total — use /model <id>)")
                except Exception as e:
                    print(f"catalog failed: {str(e)[:150]}")
                continue
            try:
                rows = Cat.table(free_only=("free" in v))
            except Exception as e:
                print(f"catalog failed: {e}")
                continue
            if T.RICH:
                from rich.table import Table
                t = Table(title=f"Zen models ({len(rows)})")
                for h in ("model", "in", "out", "tools", "ctx", "price", "via"):
                    t.add_column(h)
                for r in rows:
                    style = "bold green" if r["free"] else ""
                    t.add_row(r["id"], r["in"], r["out"], r["tools"], str(r["ctx"]), r["price"], r["via"], style=style)
                T.console.print(t)
            else:
                for r in rows:
                    print(f"{r['id']} | in:{r['in']} out:{r['out']} tools:{r['tools']} ctx:{r['ctx']} {r['price']} via:{r['via']}")
            continue
        if task.startswith("/role add"):
            from jhalcode import roles as R
            parts = task.split(None, 3)
            if len(parts) < 4 or parts[3].count("|") < 2:
                print('use: /role add <name> <model> | tool1,tool2 | system prompt')
                continue
            name_model, tools, system = [s.strip() for s in parts[3].split("|", 2)]
            nm = name_model.split()
            print(R.add_role(nm[0], nm[1] if len(nm) > 1 else cfg.model, [t.strip() for t in tools.split(",") if t.strip()], system))
            continue
        if task == "/agents":
            from jhalcode import team as Tm
            print(Tm.ACTIVE or "no specialists active")
            continue
        if task == "/status":
            who = getattr(agent, "role", None) or "solo"
            mid = getattr(agent, "model", cfg.model_list()[0])
            print(f"who={who} model={mid} mode={'AUTO' if cfg.auto_mode else 'ASK'} turns={len(agent.messages)} audit={cfg.audit_log}")
            continue
        if task.startswith("/save"):
            _, _, v = task.partition(" ")
            name = os.path.basename(v.strip() or "jhal-session.json")
            if not name.endswith(".json"):
                print("session files must end .json")
                continue
            print(f"saved: {agent.save(name)}")
            continue
        if task.startswith("/load"):
            _, _, v = task.partition(" ")
            name = os.path.basename(v.strip() or "jhal-session.json")
            if not name.endswith(".json"):
                print("session files must end .json")
                continue
            print(f"loaded turns: {agent.load(name)}")
            continue
        if task == "/connect":
            _connect(cfg)
            continue
        if task == "/audit":
            from collections import deque
            try:
                with open(cfg.audit_log, encoding="utf-8") as f:
                    print("\n".join(deque(f, 8)).strip() or "empty audit")
            except Exception as e:
                print(f"no audit: {e}")
            continue
        if task == "/clear":
            os.system("cls" if os.name == "nt" else "clear")
            continue
        if task in ("/help", "help"):
            print("Tip: @file or @\"my file\" attaches contents. @folder lists it.")
            print("/connect /manager /solo /roles /role add /agents /models [free] /auto /ask /model /status /save /load /audit /clear /quit")
            continue
        try:
            _run(agent, task)
        except Exception as e:
            T.tool_err(str(e))

if __name__ == "__main__":
    main()
