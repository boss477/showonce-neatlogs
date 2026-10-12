"""Offline pipeline tests: fake Slack/Linear, real subprocess test run on a temp copy of sample_repo."""
import shutil
import tempfile
import unittest
from pathlib import Path
from showonce.pipeline import handle_bug_report

SAMPLE = Path(__file__).resolve().parents[1] / "sample_repo"

class FakeSlack:
    def __init__(self): self.posts = []
    def permalink(self, ts): return f"https://slack.example/{ts}"
    def post(self, message, thread_ts=None): self.posts.append((thread_ts, message)); return {"ok": True}

class FakeLinear:
    def __init__(self): self.closed, self.comments = [], []
    def create_issue(self, title, priority=None, description=None):
        self.created = {"title": title, "description": description}
        return {"id": "issue-1", "identifier": "TEST-1", "url": "https://linear.example/TEST-1"}
    def comment(self, issue_id, body): self.comments.append(body); return {"success": True}
    def close_issue(self, issue_id, comment=None): self.closed.append(issue_id); return {"state": {"name": "Done"}}

class FakeTeams:
    live = False

class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="showonce-test-"))
        for name in ("buggy.py", "test_buggy.py"): shutil.copy(SAMPLE / name, self.root / name)
        self.slack, self.linear = FakeSlack(), FakeLinear()

    def tearDown(self): shutil.rmtree(self.root, ignore_errors=True)

    def run_pipeline(self):
        return handle_bug_report("bug: add is wrong", "123.456", sample_root=str(self.root), slack=self.slack, linear=self.linear, teams=FakeTeams())

    def test_fix_passes_closes_issue_and_replies_in_thread(self):
        (self.root / "buggy.py").write_text("def add(a, b):\n    return a - b\n")
        result = self.run_pipeline()
        self.assertTrue(result["test"]["passed"])
        self.assertEqual(self.linear.closed, ["issue-1"])
        self.assertIn("https://slack.example/123.456", self.linear.created["description"])
        self.assertEqual([ts for ts, _ in self.slack.posts], ["123.456", "123.456"])
        self.assertIn("Code has been fixed", self.slack.posts[-1][1])

    def test_failed_fix_leaves_issue_open_with_output(self):
        (self.root / "buggy.py").write_text("def add(a, b):\n    return a * b\n")  # not the bug the fixer knows
        result = self.run_pipeline()
        self.assertFalse(result["test"]["passed"])
        self.assertEqual(self.linear.closed, [])
        self.assertIn("AssertionError", self.linear.comments[0])
        self.assertIn("tests still fail", self.slack.posts[-1][1])

if __name__ == "__main__":
    unittest.main()
