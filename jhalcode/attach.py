import os
import re

PAT = re.compile(r'@"([^"]+)"|@(\S+)')
MAX_CHARS = 12000
READ_CAP = 65536
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}
SENSITIVE = {".env", ".jhalcode.env", "credentials.json"}
SENSITIVE_EXTS = {".pem", ".key"}
SENSITIVE_NAMES = ("id_rsa", "id_ed25519", "secrets", ".env.")


def _sensitive(p: str) -> bool:
    b = os.path.basename(p).lower()
    return b in SENSITIVE or os.path.splitext(b)[1] in SENSITIVE_EXTS or any(k in b for k in SENSITIVE_NAMES)


def _confined(p: str, cwd: str) -> bool:
    try:
        return os.path.commonpath([os.path.realpath(p), os.path.realpath(cwd)]) == os.path.realpath(cwd)
    except Exception:
        return False


def _redact(text: str) -> str:
    key = os.environ.get("JHAL_API_KEY", "")
    if key and len(key) > 8:
        text = text.replace(key, "***KEY***")
    return text


def _size(p: str) -> str:
    try:
        n = os.path.getsize(p)
        return f"{n // 1024}KB" if n >= 1024 else f"{n}B"
    except Exception:
        return "?"


def expand(task: str, cwd: str | None = None) -> tuple[str, list, list]:
    cwd = cwd or os.getcwd()
    notes: list = []
    images: list = []

    def sub(m):
        raw = (m.group(1) or m.group(2)).rstrip(",.:;!?")
        p = raw if os.path.isabs(raw) else os.path.join(cwd, raw)
        rp = os.path.realpath(p)
        if _sensitive(rp):
            notes.append(f"x {raw}: refused (sensitive file)")
            return "[refused: sensitive file]"
        if not _confined(rp, cwd):
            notes.append(f"x {raw}: outside workdir")
            return "[blocked: outside workdir]"
        if os.path.isfile(rp):
            ext = os.path.splitext(rp)[1].lower()
            if ext in IMAGE_EXTS:
                images.append(rp)
                notes.append(f"+ {raw} (image, {_size(rp)})")
                return f"\n[attached image: {rp} — you can SEE it]\n"
            if ext in VIDEO_EXTS | AUDIO_EXTS:
                notes.append(f"+ {raw} ({ext[1:]} media, {_size(rp)})")
                return f"\n[attached media: {rp} ({ext[1:]}, {_size(rp)}) — you cannot play it; use open_file to show it, or ask the user]\n"
            try:
                with open(rp, "rb") as f:
                    raw_b = f.read(READ_CAP + 1)
                if len(raw_b) > READ_CAP:
                    notes.append(f"x {raw}: too large ({_size(rp)}), skipped")
                    return f"[skipped large file: {rp} ({_size(rp)})]"
                if b"\x00" in raw_b:
                    try:
                        body = _redact(raw_b.decode("utf-16"))
                    except Exception:
                        raise UnicodeDecodeError("bin", b"", 0, 1, "null byte")
                else:
                    body = _redact(raw_b.decode("utf-8"))
                if len(body) > MAX_CHARS:
                    body = body[:MAX_CHARS] + "\n...[truncated]"
                notes.append(f"+ {raw} ({len(body)} chars)")
                return f"\n<file path=\"{rp}\">\n{body}\n</file>"
            except UnicodeDecodeError:
                notes.append(f"+ {raw} (binary, {_size(rp)})")
                return f"\n[attached binary file: {rp} ({_size(rp)}) — describe from name/type only]\n"
            except Exception as e:
                notes.append(f"x {raw}: {str(e)[:100]}")
                return raw
        if os.path.isdir(rp):
            try:
                names = sorted(os.listdir(rp))[:200]
                notes.append(f"+ {raw}/ (dir)")
                return f"\n<dir path=\"{rp}\">\n" + "\n".join(names) + "\n</dir>"
            except Exception as e:
                notes.append(f"x {raw}: {str(e)[:100]}")
                return raw
        notes.append(f"? {raw} not found")
        return raw

    return PAT.sub(sub, task), notes, images
