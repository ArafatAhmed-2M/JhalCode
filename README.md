# Jhal Code — Beta v1.0.0

Human-like PC harness for AI agents. Windows + Linux, expanding later.
Agents do anything a person can do: shell, files, mouse/keyboard, screenshots (vision), browser, web.

Type `jcc` and talk. That's it.

> **Beta install** — this README is for the `beta` branch. For stable, see `master`.

## Install — Beta

Windows (one line):
```powershell
powershell -c "irm https://raw.githubusercontent.com/ArafatAhmed-2M/JhalCode/beta/install.ps1 | iex"
```
Linux/macOS (one line):
```bash
curl -fsSL https://raw.githubusercontent.com/ArafatAhmed-2M/JhalCode/beta/install.sh | bash
```
Then: `jcc` (restart the terminal first so PATH applies).

From source (beta):
```bash
git clone -b beta https://github.com/ArafatAhmed-2M/JhalCode.git
cd JhalCode
python -m pip install -e .
```

Update anytime (beta): `pip install --force-reinstall https://github.com/ArafatAhmed-2M/JhalCode/archive/beta.zip`
(or `/update` inside jcc on Linux, when available on beta).

Extras: `pip install "jhal-code[gui]"` (mouse/screenshot), `[browser]` (Playwright).

On first run: `/connect` and paste your provider key (Zen, OpenRouter, etc).

## Beta highlights

- **Themes**: `jhal` (red), `ember`, `ghost` — `/theme <name>`
- **Providers**: `zen`, `openrouter`, `ollama`, `lmstudio`, `openai`, `gemini` — `/connect` provider picker
- **Diff approvals**: `write_file`/`edit_file` shows red/green diff
- **`/compact`** summarize context, **`/cost`** token usage, **`/theme`**, improved `/status`

## Usage

```
jcc                          # interactive, stays open
jcc "make a site" --auto     # one task, no prompts
jcc --manager "build X"      # team mode from the start
```

`@file` attaches contents, `@image.png` shows the picture to the model,
`@folder` lists it. Tab/Enter picks from the popup menu.

## Commands

| Command | What |
|---|---|
| `/connect` | connect provider API key (zen/openrouter/ollama/...) |
| `/theme <name>` | switch theme (jhal/ember/ghost) |
| `/manager` `/solo` | team mode / single-agent mode |
| `/roles` `/role add` `/agents` | team management + live status |
| `/models` `/models free` | browse Zen models: modalities, tools, price |
| `/model` `/model role coder <id>` | switch models (saved) |
| `/compact` `/cost` | shrink context / show tokens |
| `/auto` `/ask` | prompt-free vs approval mode |
| `/status` `/save` `/load` `/audit` | session controls |
| `/clear` `/quit` | screen / exit |

## Team mode

Manager (full PC powers) plans, picks parallel fan-out or step-by-step itself,
delegates to pinned specialists (planner, coder, sub-coder, designer, tester),
then verifies the result before reporting done. New roles need your approval —
even in `--auto`. Roles live in `jhalcode/roles.yaml`.

## Safety

- Low-risk tools auto-run; medium/high ask (unless `--auto`)
- Hard blocks: system wipes, protected paths, `..` escapes, SSRF to internal hosts, executables via opener
- `@` attachments confined to workdir, secrets refused + redacted
- Everything logged to `jhal-audit.jsonl`

## Config (`JHAL_*` env)

`JHAL_API_KEY` · `JHAL_BASE_URL` · `JHAL_PROVIDER` · `JHAL_MODEL`/`JHAL_MODELS`
· `JHAL_AUTO` · `JHAL_MAX_STEPS` · `JHAL_AUDIT`

## Layout

`jhalcode/agent.py` loop · `team.py` specialists · `roles.yaml` team ·
`tools/` 23 PC tools · `platform/` OS backends · `tui.py` terminal UI ·
`providers.py` presets · `themes.yaml`

## License

Proprietary — all rights reserved. See LICENSE.
