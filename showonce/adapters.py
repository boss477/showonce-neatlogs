"""Clearly labelled MOCK adapters used by the demo."""
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
    def test(self) -> dict:
        return {"passed": (self.root / "buggy.py").read_text(encoding="utf-8").find("return a + b") >= 0}

