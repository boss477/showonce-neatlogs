import json
from pathlib import Path
from .observability import fingerprint, run_traced

class FailureMemory:
    def __init__(self, path="evidence/failure_memory.json"):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lessons = json.loads(self.path.read_text()) if self.path.exists() else []
    def add(self, tool, failure_mode, lesson):
        self.lessons.append({"tool": tool, "failure_mode": failure_mode, "lesson": lesson})
        self.path.write_text(json.dumps(self.lessons, indent=2) + "\n")
    def ranked(self, tool): return [x for x in self.lessons if x["tool"] == tool]

class RecoveryRunner:
    def __init__(self, adapters, checkpoint_dir="evidence/entire"):
        self.adapters = adapters; self.checkpoint_dir = Path(checkpoint_dir); self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.memory = FailureMemory()
        self.seen = {}
    def checkpoint(self, step_id, context):
        path = self.checkpoint_dir / f"retry-{step_id}-{len(list(self.checkpoint_dir.glob('retry-*')) + 1)}.json"
        path.write_text(json.dumps({"step": step_id, "context": context, "decision": "restore before retry"}, indent=2) + "\n")
        return str(path)
    def run_step(self, step, attempt=0):
        fp = fingerprint(step.tool, step.inputs); self.seen[fp] = self.seen.get(fp, 0) + 1
        result = run_traced(
            f"showonce.step.{step.id}",
            lambda: self.adapters[step.tool](**step.inputs),
            tool_name=step.tool,
            parameters=step.inputs,
        )
        if self.seen[fp] > 1:
            raise RuntimeError("loop detected: repeated identical call")
        return result
    def recover(self, step, failure, fix):
        checkpoint = self.checkpoint(step.id, {"failure": str(failure), "lessons": self.memory.ranked(step.tool)})
        self.memory.add(step.tool, type(failure).__name__, "retry after restoring the failed-step context")
        fixed = fix()
        return {"checkpoint": checkpoint, "fixed": fixed}
