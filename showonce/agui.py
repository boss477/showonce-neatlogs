"""Small AG-UI-shaped event stream for the demo control room.

The event names intentionally map to the protocol's event-driven model while
keeping the prototype dependency-free: the UI can consume these over SSE.
"""
import json
from dataclasses import asdict, dataclass

@dataclass
class Event:
    type: str
    name: str
    data: dict

def demo_events():
    return [
        Event("RUN_STARTED", "ShowOnce recovery", {"workflow": "Slack bug → fix → verify"}),
        Event("STEP_STARTED", "Slack intake", {"status": "complete", "provider": "MOCK Slack"}),
        Event("STEP_STARTED", "Linear issue", {"status": "complete", "provider": "MOCK Linear", "identifier": "SHOW-1"}),
        Event("STEP_STARTED", "Implement worker", {"status": "complete"}),
        Event("STEP_FINISHED", "Tests", {"status": "failed", "error": "AssertionError: add(2, 3) != 5"}),
        Event("TOOL_CALL", "Neatlogs MCP · search_traces", {"status": "complete", "query": "AssertionError", "mode": "MOCK"}),
        Event("TOOL_CALL", "Neatlogs MCP · get_trace_context", {"status": "complete", "trace_id": "local-showonce-failure", "mode": "MOCK"}),
        Event("MESSAGE", "Agent diagnosis", {"text": "The test failure is in the implementation step. Restore context and retry the fix."}),
        Event("CHECKPOINT", "Entire checkpoint", {"status": "ready", "path": "evidence/entire/retry-test-4.json"}),
        Event("APPROVAL_REQUEST", "Retry from checkpoint", {"action": "retry", "requires_human": True}),
        Event("STEP_FINISHED", "Tests", {"status": "passed", "tests": "1 passed"}),
        Event("APPROVAL_REQUEST", "Send updates", {"action": "send_slack_and_linear", "requires_human": True}),
        Event("RUN_FINISHED", "Recovery complete", {"status": "success"}),
    ]

def sse_events():
    for event in demo_events():
        yield f"event: {event.type}\ndata: {json.dumps(asdict(event))}\n\n"

