"""Minimal Neatlogs MCP client used by the implement worker.

With NEATLOGS_PROJECT_KEY it queries the hosted MCP server. Without a key the
demo returns a clearly labelled local trace so the recovery story is runnable.
"""
import json
import os
import urllib.request

class NeatlogsMCP:
    def __init__(self, endpoint=None, api_key=None):
        self.endpoint = endpoint or os.getenv("NEATLOGS_MCP_URL", "https://ingest.neatlogs.com/mcp")
        self.api_key = api_key or os.getenv("NEATLOGS_PROJECT_KEY")

    @property
    def live(self):
        return bool(self.api_key)

    def call(self, name, arguments):
        if not self.api_key:
            return {"mock": True, "tool": name, "message": "MOCK Neatlogs trace context", "arguments": arguments}
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}).encode()
        request = urllib.request.Request(self.endpoint, data=body, headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read())

    def inspect_failure(self, query):
        found = self.call("search_traces", {"query": query, "filters": {"status": "error"}})
        trace_id = None
        if isinstance(found, dict):
            traces = found.get("result", {}).get("traces", []) or found.get("traces", [])
            if traces: trace_id = traces[0].get("trace_id")
        context = self.call("get_trace_context", {"trace_id": trace_id or "local-showonce-failure"})
        return {"search": found, "context": context, "trace_id": trace_id or "local-showonce-failure"}

