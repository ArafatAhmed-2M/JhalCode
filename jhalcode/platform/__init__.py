import platform
from jhalcode.platform.windows import WindowsBackend

def get_backend():
    if platform.system() == "Windows":
        return WindowsBackend()
    raise NotImplementedError("Jhal Code v0.1 is Windows-only. Linux/macOS backends plug in here.")

