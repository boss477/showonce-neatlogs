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
    # Without a key, stay local; neatlogs.init() requires api_key in released versions.
    api_key = os.getenv("NEATLOGS_PROJECT_KEY") or os.getenv("NEATLOGS_API_KEY")
    if neatlogs is None or not api_key:
        return
    try:
        neatlogs.init(api_key=api_key, tags=[os.getenv("NEATLOGS_PROJECT", "showonce")])
    except TypeError:
        neatlogs.init(api_key)

@contextlib.contextmanager
def span(name: str, **attributes):
    # neatlogs 1.x exposes span as a decorator, not a context manager.
    # Keep this context API for callers and use run_traced for the actual span.
    yield

def run_traced(name: str, fn, **attributes):
    if neatlogs is None or not hasattr(neatlogs, "trace"):
        return fn()
    traced = neatlogs.trace(name, kind="chain", **attributes)(fn)
    return traced()

def fingerprint(tool: str, inputs: dict) -> str:
    payload = json.dumps(inputs, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{tool}:{payload}".encode()).hexdigest()

def save_trace_note(path: str, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
