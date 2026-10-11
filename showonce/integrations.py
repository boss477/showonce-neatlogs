"""Optional live integrations with safe MOCK fallbacks."""
import json
import os
import urllib.request

def _request(url, data, headers):
    request = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read())

class Slack:
    def __init__(self):
        self.token = os.getenv("SLACK_BOT_TOKEN")
        self.channel = os.getenv("SLACK_CHANNEL", "#showonce-demo")
    @property
    def live(self): return bool(self.token)
    def post(self, message):
        if not self.token:
            return {"mock": True, "provider": "Slack", "channel": self.channel, "message": message, "status": "DRAFT"}
        return _request("https://slack.com/api/chat.postMessage", {"channel": self.channel, "text": message}, {"Authorization": f"Bearer {self.token}"})

class Linear:
    def __init__(self): self.key = os.getenv("LINEAR_API_KEY")
    @property
    def live(self): return bool(self.key)
    def create_issue(self, title, priority=None):
        if not self.key:
            return {"mock": True, "provider": "Linear", "identifier": "SHOW-1", "title": title, "priority": priority, "status": "DRAFT"}
        query = "mutation($input: IssueCreateInput!){ issueCreate(input:$input){ success issue { identifier url title } } }"
        variables = {"input": {"title": title, "priority": 1 if priority == "urgent" else 2}}
        return _request("https://api.linear.app/graphql", {"query": query, "variables": variables}, {"Authorization": self.key})

