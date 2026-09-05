import platform

def get_backend():
    sys = platform.system()
    if sys == "Windows":
        from jhalcode.platform.windows import WindowsBackend
        return WindowsBackend()
    if sys in ("Linux", "Darwin"):
        from jhalcode.platform.unix import UnixBackend
        return UnixBackend()
    raise NotImplementedError(f"Jhal Code has no backend for {sys} yet.")
