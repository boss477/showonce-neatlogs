from .adapters import MockLinear, MockSlack, SampleRepo
from .recovery import RecoveryRunner
from .observability import init_tracing

def demo(sample_root="sample_repo"):
    init_tracing(); repo = SampleRepo(sample_root)
    adapters = {"linear.create_issue": MockLinear().create_issue, "slack.post": MockSlack().post, "repo.fix": repo.fix_code, "repo.test": repo.test}
    runner = RecoveryRunner(adapters)
    outputs = {}
    for step in [
        type("S", (), {"id": "issue", "tool": "linear.create_issue", "inputs": {"title": "Fix sample bug", "priority": "high"}})(),
        type("S", (), {"id": "fix", "tool": "repo.fix", "inputs": {}})(),
        type("S", (), {"id": "test", "tool": "repo.test", "inputs": {}})(),
        type("S", (), {"id": "reply", "tool": "slack.post", "inputs": {"message": "Fixed and verified. ETA: now."}})(),
    ]:
        outputs[step.id] = runner.run_step(step)
    return outputs

