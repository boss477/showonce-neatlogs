"""NVIDIA-assisted sample fix recorded in a real Linear issue."""
import json
import os
import re
import shutil
import tempfile
import urllib.request
from pathlib import Path

from .adapters import SampleRepo
from .integrations import Linear
from .observability import init_tracing, run_traced

DEFAULT_MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b"


def _suggest_patch(source, test, failure):
    key = os.environ["NVIDIA_API_KEY"]
    model = os.getenv("NVIDIA_MODEL", DEFAULT_MODEL)
    base = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip("/")
    prompt = ("Fix the Python function so the test passes. Reply with only the corrected return line.\n\n"
              f"buggy.py:\n{source}\n\ntest_buggy.py:\n{test}\n\nFailure:\n{failure[-1000:]}")
    body = {"model": model, "messages": [{"role": "system", "content": "You repair one Python return statement. Output one line only."},
                                           {"role": "user", "content": prompt}], "temperature": 0.2,
            "max_tokens": 512, "stream": False}
    request = urllib.request.Request(f"{base}/chat/completions", data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read())
    answer = result["choices"][0]["message"]["content"].strip()
    if not re.fullmatch(r"return\s+a\s*\+\s*b", answer):
        raise ValueError("NVIDIA did not return the expected safe one-line repair")
    return answer, result.get("usage", {})


def run_live_linear_demo(existing_issue_id=None):
    if not os.getenv("NVIDIA_API_KEY") or not os.getenv("LINEAR_API_KEY"):
        raise RuntimeError("NVIDIA_API_KEY and LINEAR_API_KEY are required")
    init_tracing()
    source = Path(__file__).resolve().parents[1] / "sample_repo"
    with tempfile.TemporaryDirectory(prefix="showonce-live-") as directory:
        root = Path(directory)
        for name in ("buggy.py", "test_buggy.py"):
            shutil.copy2(source / name, root / name)
        repo = SampleRepo(str(root))
        repo.inject_bug()
        before = repo.test()
        if before["passed"]:
            raise RuntimeError("The injected bug did not fail the real test")
        linear = Linear()
        if existing_issue_id:
            issue = linear._graphql("query($id: String!){ issue(id:$id){ id identifier url title } }",
                                    {"id": existing_issue_id})["issue"]
            if not issue: raise RuntimeError("Linear issue not found")
        else:
            issue = linear.create_issue("ShowOnce live demo: add(2, 3) returns -1 instead of 5", priority="high",
                                        description="Synthetic sample-repo bug for a live NVIDIA-assisted repair demo. "
                                                    "The real subprocess test fails before the attempted fix. "
                                                    "No Slack message was ingested for this run.")
        outcome = {"issue": issue, "model": os.getenv("NVIDIA_MODEL", DEFAULT_MODEL),
                   "model_calls": 0, "test_before": "FAIL", "test_after": "NOT RUN", "status": "open"}
        try:
            outcome["model_calls"] = 1
            patch, usage = run_traced("showonce.live_demo.model_patch", lambda: _suggest_patch(
                (root / "buggy.py").read_text(), (root / "test_buggy.py").read_text(), before["output"]),
                tool_name="nvidia.chat.completions")
            outcome["usage"] = usage
            target = root / "buggy.py"
            target.write_text(target.read_text().replace("return a - b", patch), encoding="utf-8")
            after = run_traced("showonce.live_demo.test", repo.test, tool_name="repo.test")
            outcome["test_after"] = "PASS" if after["passed"] else "FAIL"
            if not after["passed"]:
                raise RuntimeError(after["output"][-500:])
            linear.close_issue(issue["id"], "NVIDIA suggested `" + patch + "`. Real subprocess test: FAIL before, PASS after. "
                               "Fix ran in a temporary sample-repo copy; no production repository was changed.")
            outcome["status"] = "Done"
            outcome["patch"] = patch
        except Exception as error:
            linear.comment(issue["id"], "Automated demo did not verify; leaving issue open. " + str(error)[:500])
            outcome["error"] = str(error)[:500]
        return outcome
