import os
from dataclasses import dataclass, field
from pathlib import Path

def _int(v: str, default: int, lo: int, hi: int) -> int:
    try:
        return min(hi, max(lo, int(str(v).strip())))
    except Exception:
        return default


def _load_dotenv():
    for p in [Path.cwd() / ".env", Path.home() / ".jhalcode.env"]:
        try:
            if p.is_file() and p.stat().st_size < 1_000_000:
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("export "):
                        line = line[7:].strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    v = v.strip()
                    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                        v = v[1:-1]
                    os.environ.setdefault(k.strip(), v)
        except Exception:
            pass
_load_dotenv()

@dataclass
class JhalConfig:
    model: str = field(default_factory=lambda: os.getenv("JHAL_MODEL", "ling-3.0-flash-fin-free"))
    models: str = field(default_factory=lambda: os.getenv("JHAL_MODELS", "ling-3.0-flash-fin-free,nemotron-3.5-lightning-free,nemotron-3-ultra-free"))
    base_url: str = field(default_factory=lambda: os.getenv("JHAL_BASE_URL", "https://opencode.ai/zen/v1"))
    api_key: str = field(default_factory=lambda: os.getenv("JHAL_API_KEY", ""))
    auto_mode: bool = field(default_factory=lambda: os.getenv("JHAL_AUTO", "0").strip().lower() in ("1", "true", "yes"))
    max_steps: int = field(default_factory=lambda: _int(os.getenv("JHAL_MAX_STEPS", "30"), 30, 1, 200))
    workdir: str = field(default_factory=lambda: os.getenv("JHAL_WORKDIR", os.getcwd()))
    audit_log: str = field(default_factory=lambda: os.getenv("JHAL_AUDIT", "jhal-audit.jsonl"))

    def model_list(self) -> list:
        ms = [m.strip() for m in (self.models or self.model or "").split(",") if m.strip()]
        return ms or ["ling-3.0-flash-fin-free"]

    def __post_init__(self):
        if self.audit_log and not os.path.isabs(self.audit_log):
            self.audit_log = os.path.abspath(os.path.join(self.workdir, self.audit_log))

    @classmethod
    def from_env(cls) -> "JhalConfig":
        return cls()

