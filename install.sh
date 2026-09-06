#!/usr/bin/env bash
# Jhal Code installer (Linux/macOS). Usage: ./install.sh
set -e
REPO="ArafatAhmed-2M/JhalCode"
command -v python3 >/dev/null || { echo "install python3 first"; exit 1; }
command -v curl >/dev/null || { echo "install curl first"; exit 1; }
if curl -fsSL "https://raw.githubusercontent.com/$REPO/beta/pyproject.toml" -o /tmp/jhal-pyproject.toml 2>/dev/null; then
  URL="https://github.com/$REPO/archive/beta.zip"
else
  if [ -z "$GITHUB_TOKEN" ]; then
    echo "private repo — paste a GitHub PAT (read-only is enough):"
    read -rs GITHUB_TOKEN; echo
  fi
  URL="https://$GITHUB_TOKEN@github.com/$REPO/archive/beta.zip"
fi
if [ "$(id -u)" = "0" ]; then
  python3 -m pip install --force-reinstall "$URL"
else
  python3 -m pip install --user --force-reinstall "$URL"
  case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) for rc in "$HOME/.bashrc" "$HOME/.profile"; do
         [ -f "$rc" ] && grep -q '.local/bin' "$rc" || echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
       done
       export PATH="$HOME/.local/bin:$PATH"
       echo "added ~/.local/bin to PATH";;
  esac
fi
command -v jcc >/dev/null && echo "done — run: jcc" || echo "installed but jcc not on PATH — restart terminal, then run: jcc"
