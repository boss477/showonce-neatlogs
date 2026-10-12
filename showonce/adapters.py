"""Clearly labelled MOCK adapters used by the demo."""
import subprocess
import sys
from pathlib import Path

class MockSlack:
    def post(self, message: str) -> dict:
        return {"mock": True, "channel": "#demo", "message": message}

class MockLinear:
    def create_issue(self, title: str, priority: str | None = None) -> dict:
        return {"mock": True, "identifier": "SHOW-1", "title": title, "priority": priority}

class SampleRepo:
    def __init__(self, root: str): self.root = Path(root)
    def fix_code(self) -> dict:
        target = self.root / "buggy.py"
        target.write_text(target.read_text().replace("return a - b", "return a + b"), encoding="utf-8")
        return {"fixed": True, "path": str(target)}
    def inject_bug(self) -> dict:
        target = self.root / "buggy.py"
        target.write_text(target.read_text().replace("return a + b", "return a - b"), encoding="utf-8")
        return {"injected": True, "path": str(target)}
    def test(self) -> dict:
        # Run the repo's real test in a fresh interpreter so the edited module is re-imported.
        result = subprocess.run([sys.executable, "-B", "-c", "import test_buggy; test_buggy.test_add()"], cwd=self.root, capture_output=True, text=True)
        return {"passed": result.returncode == 0, "output": (result.stdout + result.stderr).strip()[-500:]}

