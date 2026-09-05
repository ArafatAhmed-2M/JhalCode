#!/usr/bin/env bash
# Jhal Code installer (Linux/macOS). Usage: ./install.sh
set -e
REPO="ArafatAhmed-2M/JhalCode"
command -v python3 >/dev/null || { echo "install python3 first"; exit 1; }
if [ -z "$GITHUB_TOKEN" ]; then
  if curl -fsSL "https://github.com/$REPO" >/dev/null 2>&1; then
    URL="git+https://github.com/$REPO.git"
  else
    echo "private repo — paste a GitHub PAT (read-only is enough):"
    read -rs GITHUB_TOKEN; echo
    URL="git+https://$GITHUB_TOKEN@github.com/$REPO.git"
  fi
else
  URL="git+https://$GITHUB_TOKEN@github.com/$REPO.git"
fi
python3 -m pip install --user "$URL"
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
     echo "added ~/.local/bin to PATH (restart terminal)";;
esac
echo "done — run: jcc"
