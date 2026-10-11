"""Optional live integrations with safe MOCK fallbacks."""
import json
import os
import urllib.parse
import urllib.request

def _request(url, data, headers):
    request = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read()
        return json.loads(body) if body.strip().startswith((b"{", b"[")) else {"ok": True, "status": response.status}

def _get(url, params, headers):
    request = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}", headers=headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read())

class Slack:
    """Reads bug reports from a channel and replies in their threads.

    Bot scopes: chat:write, channels:history, channels:read (groups:* for private channels).
    """
    def __init__(self):
        self.token = os.getenv("SLACK_BOT_TOKEN")
        self.channel = os.getenv("SLACK_CHANNEL", "#showonce-demo")
        self.trigger = os.getenv("SLACK_TRIGGER", "bug").lower()
        self._channel_id = None
    @property
    def live(self): return bool(self.token)
    def _api(self, method, params=None, body=None):
        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"https://slack.com/api/{method}"
        result = _request(url, body, headers) if body is not None else _get(url, params or {}, headers)
        if not result.get("ok"):
            raise RuntimeError(f"Slack {method} failed: {result.get('error')}")
        return result
    def channel_id(self):
        """conversations.history needs an ID; resolve '#name' once."""
        if self._channel_id: return self._channel_id
        if not self.channel.startswith("#"):
            self._channel_id = self.channel; return self._channel_id
        name, cursor = self.channel[1:], None
        while True:
            page = self._api("conversations.list", {"types": "public_channel,private_channel", "limit": 200, **({"cursor": cursor} if cursor else {})})
            for channel in page["channels"]:
                if channel["name"] == name:
                    self._channel_id = channel["id"]; return self._channel_id
            cursor = page.get("response_metadata", {}).get("next_cursor")
            if not cursor: raise RuntimeError(f"Slack channel {self.channel} not found; invite the bot or set SLACK_CHANNEL to the channel ID")
    def fetch_bug_reports(self, oldest):
        """Human, top-level messages newer than `oldest` that mention the trigger word, oldest first."""
        if not self.token: return []
        history = self._api("conversations.history", {"channel": self.channel_id(), "oldest": oldest, "limit": 100})
        reports = [
            {"ts": m["ts"], "text": m.get("text", ""), "user": m.get("user")}
            for m in history["messages"]
            if not m.get("bot_id") and not m.get("subtype") and m.get("thread_ts", m["ts"]) == m["ts"]
            and self.trigger in m.get("text", "").lower()
        ]
        return sorted(reports, key=lambda r: float(r["ts"]))
    def permalink(self, ts):
        if not self.token: return None
        return self._api("chat.getPermalink", {"channel": self.channel_id(), "message_ts": ts}).get("permalink")
    def post(self, message, thread_ts=None):
        if not self.token:
            return {"mock": True, "provider": "Slack", "channel": self.channel, "thread_ts": thread_ts, "message": message, "status": "DRAFT"}
        return self._api("chat.postMessage", body={"channel": self.channel_id(), "text": message, **({"thread_ts": thread_ts} if thread_ts else {})})

class Teams:
    """Posts to a Microsoft Teams channel through an incoming webhook (or a Workflows webhook)."""
    def __init__(self): self.webhook = os.getenv("TEAMS_WEBHOOK_URL")
    @property
    def live(self): return bool(self.webhook)
    def post(self, message):
        if not self.webhook:
            return {"mock": True, "provider": "Teams", "message": message, "status": "DRAFT"}
        card = {"type": "AdaptiveCard", "$schema": "http://adaptivecards.io/schemas/adaptive-card.json", "version": "1.4",
                "body": [{"type": "TextBlock", "text": message, "wrap": True}]}
        return _request(self.webhook, {"type": "message", "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive", "content": card}]}, {})

class Linear:
    def __init__(self):
        self.key = os.getenv("LINEAR_API_KEY")
        self.team_id = os.getenv("LINEAR_TEAM_ID")
    @property
    def live(self): return bool(self.key)
    def _graphql(self, query, variables=None):
        result = _request("https://api.linear.app/graphql", {"query": query, "variables": variables or {}}, {"Authorization": self.key})
        if result.get("errors"):
            raise RuntimeError(f"Linear API error: {result['errors'][0].get('message')}")
        return result["data"]
    def _team(self):
        """Uses LINEAR_TEAM_ID, or the first team the key can see."""
        if not self.team_id:
            teams = self._graphql("{ teams(first: 1) { nodes { id key } } }")["teams"]["nodes"]
            if not teams: raise RuntimeError("Linear: no teams visible to this API key")
            self.team_id = teams[0]["id"]
        return self.team_id
    def create_issue(self, title, priority=None, description=None):
        if not self.key:
            return {"mock": True, "provider": "Linear", "id": "mock-show-1", "identifier": "SHOW-1", "title": title, "priority": priority, "status": "DRAFT"}
        query = "mutation($input: IssueCreateInput!){ issueCreate(input:$input){ success issue { id identifier url title } } }"
        variables = {"input": {"teamId": self._team(), "title": title, "priority": 1 if priority == "urgent" else 2, **({"description": description} if description else {})}}
        return self._graphql(query, variables)["issueCreate"]["issue"]
    def comment(self, issue_id, body):
        if not self.key:
            return {"mock": True, "provider": "Linear", "issue": issue_id, "comment": body, "status": "DRAFT"}
        query = "mutation($input: CommentCreateInput!){ commentCreate(input:$input){ success } }"
        return self._graphql(query, {"input": {"issueId": issue_id, "body": body}})["commentCreate"]
    def close_issue(self, issue_id, comment=None):
        """Moves the issue to the team's first 'completed' workflow state (usually Done)."""
        if not self.key:
            return {"mock": True, "provider": "Linear", "issue": issue_id, "state": "Done", "comment": comment, "status": "DRAFT"}
        if comment: self.comment(issue_id, comment)
        states = self._graphql(
            "query($team: ID!){ workflowStates(filter: { team: { id: { eq: $team } }, type: { eq: \"completed\" } }) { nodes { id name position } } }",
            {"team": self._team()},
        )["workflowStates"]["nodes"]
        if not states: raise RuntimeError("Linear: team has no completed workflow state")
        done = min(states, key=lambda s: s["position"])
        query = "mutation($id: String!, $state: String!){ issueUpdate(id:$id, input:{ stateId:$state }){ success issue { identifier url state { name } } } }"
        return self._graphql(query, {"id": issue_id, "state": done["id"]})["issueUpdate"]["issue"]
