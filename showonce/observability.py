"""neatlogs integration with a safe local fallback for offline demos."""
import contextlib
import hashlib
import json
import os
from pathlib import Path

try:
    import neatlogs
except ImportError:  # pragma: no cover - enables the offline test path
    neatlogs = None

def init_tracing() -> None:
    if neatlogs is not None:
        try:
            neatlogs.init(project=os.getenv("NEATLOGS_PROJECT", "showonce"))
        except TypeError:
            neatlogs.init()

@contextlib.contextmanager
def span(name: str, **attributes):
    if neatlogs is not None and hasattr(neatlogs, "span"):
        with neatlogs.span(name, **attributes):
            yield
    else:
        yield

def fingerprint(tool: str, inputs: dict) -> str:
    payload = json.dumps(inputs, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{tool}:{payload}".encode()).hexdigest()

def save_trace_note(path: str, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

