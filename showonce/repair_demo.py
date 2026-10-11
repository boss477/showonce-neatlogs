"""Executed offline repair fixture with independent subprocess verification."""
import difflib
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TESTS = 'from buggy import add\nassert add(2,3)==5\nassert add(-2,3)==1\nassert add(0,0)==0\n'

def run_repair(recovery=True, offset=0):
    events = []
    def emit(name, **data):
        events.append({"name": name, "data": data})
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="showonce-") as directory:
        root = Path(directory)
        source = root / "buggy.py"
        source.write_text(f"def add(a, b):\n    return a - b + {offset}\n")
        (root / "verify.py").write_text(TESTS)
        def verify():
            result = subprocess.run([sys.executable, "-B", "verify.py"], cwd=root, capture_output=True, text=True, timeout=10)
            return {"passed": result.returncode == 0, "output": result.stderr or result.stdout}
        emit("Report", text="Addition returns incorrect results", mode="offline deterministic fixture")
        initial = verify()
        emit("Reproduced bug", **initial)
        source.write_text("def add(a, b):\n    return 5\n")
        failed = verify()
        emit("First patch verification", **failed)
        checkpoint = {"source": source.read_text(), "failure": failed, "contract": TESTS}
        retries = 0
        final = failed
        if recovery and not failed["passed"]:
            emit("Read local failure context", output=checkpoint["failure"]["output"], hosted_neatlogs=False)
            source.write_text(checkpoint["source"])
            assert source.read_text() == checkpoint["source"]
            emit("Restored local checkpoint", restored=True, entire_checkpoint=False)
            before = source.read_text()
            source.write_text("def add(a, b):\n    return a + b\n")
            emit("Apply deterministic repair", diff="".join(difflib.unified_diff(before.splitlines(True), source.read_text().splitlines(True), fromfile="before", tofile="after")))
            retries = 1
            final = verify()
            emit("Independent test verification", **final)
        emit("Draft resolution", status="DRAFT", text="Tests verified; ETA: ready for review", external_sent=False)
    return {"events": events, "solved": final["passed"], "initial_failed": not initial["passed"], "retries": retries, "latency_ms": round((time.perf_counter()-started)*1000, 2), "model_calls": 0, "tokens": 0, "cost": 0, "fixture": "offline deterministic addition"}
