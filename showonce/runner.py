from .adapters import SampleRepo
from .integrations import Linear, Slack
from .recovery import RecoveryRunner
from .observability import init_tracing
from .neatlogs_mcp import NeatlogsMCP

def demo(sample_root="sample_repo"):
    init_tracing(); repo = SampleRepo(sample_root)
    test_calls = {"count": 0}
    def flaky_test():
        test_calls["count"] += 1
        if test_calls["count"] == 1:
            raise AssertionError("MOCK injected failure: test expected add(2, 3) == 5")
        return repo.test()
    linear, slack = Linear(), Slack()
    adapters = {"linear.create_issue": linear.create_issue, "slack.post": slack.post, "repo.fix": repo.fix_code, "repo.test": flaky_test}
    runner = RecoveryRunner(adapters)
    neatlogs_mcp = NeatlogsMCP()
    outputs = {}
    for step in [
        type("S", (), {"id": "issue", "tool": "linear.create_issue", "inputs": {"title": "Fix sample bug", "priority": "high"}})(),
        type("S", (), {"id": "fix", "tool": "repo.fix", "inputs": {}})(),
        type("S", (), {"id": "test", "tool": "repo.test", "inputs": {}})(),
        type("S", (), {"id": "reply", "tool": "slack.post", "inputs": {"message": "Fixed and verified. ETA: now."}})(),
    ]:
        try:
            outputs[step.id] = runner.run_step(step)
        except Exception as failure:
            trace = neatlogs_mcp.inspect_failure(str(failure))
            outputs["neatlogs_investigation"] = trace
            outputs["recovery"] = runner.recover(step, failure, repo.fix_code)
            outputs[step.id] = runner.run_step(step, attempt=1)
            outputs["approval"] = {"status": "DRAFT", "message": "Linear update and Slack reply require human approval"}
    return outputs
