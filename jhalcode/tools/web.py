import urllib.request, urllib.parse, html, os, sys

WEB_DEFS = [
    {"type": "function", "function": {"name": "web_search", "description": "Search web (DuckDuckGo), return titles+urls.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "open_file", "description": "Open file/URL with default Windows app.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "webfetch", "description": "Fetch URL and return text content (HTML stripped).",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
]

def web_search(query: str) -> dict:
    try:
        q = urllib.parse.urlencode({"q": query})
        req = urllib.request.Request(f"https://html.duckduckgo.com/html/?{q}", headers={"User-Agent": "Jhal-Code/0.2.0"})
        raw = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
        import re
        out = []
        for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', raw):
            out.append({"url": html.unescape(m.group(1)), "title": html.unescape(re.sub("<.*?>", "", m.group(2)))})
            if len(out) >= 8:
                break
        return {"results": out}
    except Exception as e:
        return {"error": str(e)[:300]}

EXEC_EXTS = {".exe", ".bat", ".cmd", ".ps1", ".vbs", ".msi", ".com", ".scr", ".reg", ".lnk", ".jar"}

def open_file(path: str) -> dict:
    import subprocess
    try:
        clean = urllib.parse.urlparse(path).path if "://" in path else path
        if os.path.splitext(clean)[1].lower() in EXEC_EXTS:
            return {"error": "executables blocked in open_file; use run_shell with approval"}
        target = os.path.realpath(path)
        if os.name == "nt":
            os.startfile(target)  # type: ignore
        elif sys.platform == "darwin":
            subprocess.run(["open", target], timeout=15)
        else:
            subprocess.run(["xdg-open", target], timeout=15)
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)[:300]}

def _host_bad(hostname: str) -> bool:
    import ipaddress
    import socket
    try:
        infos = socket.getaddrinfo(hostname, None)
    except Exception:
        return True
    addrs = {i[4][0] for i in infos}
    if not addrs:
        return True
    for a in addrs:
        try:
            ip = ipaddress.ip_address(a)
        except Exception:
            return True
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            return True
    return False


class _GuardRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u = urllib.parse.urlparse(newurl)
        if u.scheme not in ("http", "https") or not u.hostname or _host_bad(u.hostname):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _safe_url(url: str) -> str | None:
    u = urllib.parse.urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        return "only http/https with a hostname"
    if _host_bad(u.hostname):
        return "private/internal hosts blocked"
    return None

def webfetch(url: str) -> dict:
    import re
    problem = _safe_url(url)
    if problem:
        return {"error": problem}
    try:
        opener = urllib.request.build_opener(_GuardRedirect)
        req = urllib.request.Request(url, headers={"User-Agent": "Jhal-Code/0.2.0"})
        raw = opener.open(req, timeout=30).read(2_000_001).decode("utf-8", "ignore")
        raw = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", raw)
        text = re.sub(r"<[^>]+>", " ", raw)
        text = html.unescape(re.sub(r"\s+", " ", text)).strip()
        return {"content": text[:12000] + ("...[truncated]" if len(text) > 12000 else "")}
    except Exception as e:
        return {"error": str(e)[:300]}
