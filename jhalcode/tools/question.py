QUESTION_DEFS = [
    {"type": "function", "function": {"name": "question", "description": "Ask the user a multiple-choice question mid-task. Use when ambiguous instead of guessing.",
        "parameters": {"type": "object", "properties": {"ask": {"type": "string"}, "options": {"type": "string", "description": "comma-separated options"}}, "required": ["ask", "options"]}}},
]

def question(ask: str, options: str) -> dict:
    opts = [o.strip() for o in options.split(",") if o.strip()]
    try:
        from jhalcode import tui as T
        if T.RICH:
            T.console.print(f"\n[bold yellow]? {ask}[/]")
            for i, o in enumerate(opts, 1):
                T.console.print(f"  [cyan]{i}[/]. {o}")
            ans = T.console.input("  pick [1-%d]: " % len(opts)).strip()
        else:
            print(f"\n? {ask}")
            for i, o in enumerate(opts, 1):
                print(f"  {i}. {o}")
            ans = input("  pick: ").strip()
        if ans.isdigit() and 1 <= int(ans) <= len(opts):
            return {"answer": opts[int(ans) - 1]}
        return {"answer": ans}
    except Exception as e:
        return {"error": f"question skipped: {e}"}
