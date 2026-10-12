"""Read-only integration checks. Prints pass/fail, names and non-secret IDs only.

Never creates issues or sends messages, so it is safe to run before a live demo.
"""
import json
import os
import urllib.error
import urllib.request
from .integrations import Linear, Slack

REQUIRED = ["model provider", "NEATLOGS_PROJECT_KEY", "SLACK_BOT_TOKEN", "SLACK_CHANNEL", "LINEAR_API_KEY"]

def _line(name, ok, info=""):
    print(f"{'PASS' if ok else 'FAIL' if ok is False else 'SKIP'}  {name:24} {info}")
    return ok is not False

def check_env():
    ok = True
    for key in REQUIRED:
        if key == "model provider":
            present = bool(os.getenv("OPENAI_API_KEY") or os.getenv("NVIDIA_API_KEY"))
        elif key == "NEATLOGS_PROJECT_KEY":
            present = bool(os.getenv("NEATLOGS_PROJECT_KEY") or os.getenv("NEATLOGS_API_KEY") or os.getenv("NEATLOGS_http_ingest_KEY"))
        else:
            present = bool(os.getenv(key))
        ok &= _line(key,present or None, "present" if present else "missing (MOCK fallback)")
    return ok

def check_model_provider():
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    provider, key, base_url = (
        ("NVIDIA", nvidia_key, os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"))
        if nvidia_key else ("OpenAI", os.getenv("OPENAI_API_KEY"), "https://api.openai.com/v1")
    )
    if not key: return _line("Model provider", None, "no key")
    request = urllib.request.Request(f"{base_url.rstrip('/')}/models", headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            model_count = len(json.loads(response.read())["data"])
            return _line(provider, True, f"{model_count} models visible")
    except urllib.error.HTTPError as error:
        return _line(provider, False, f"HTTP {error.code}")

def check_neatlogs():
    key = (os.getenv("NEATLOGS_PROJECT_KEY") or os.getenv("NEATLOGS_API_KEY")
           or os.getenv("NEATLOGS_http_ingest_KEY"))
    if not key: return _line("Neatlogs MCP", None, "no project API key")
    url = os.getenv("NEATLOGS_MCP_URL", "https://ingest.neatlogs.com/mcp")
    payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2024-11-05", "capabilities": {},
        "clientInfo": {"name": "showonce-doctor", "version": "1.0"},
    }}
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST", headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    })
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return _line("Neatlogs MCP", True, f"initialize HTTP {response.status}")
    except urllib.error.HTTPError as error:
        return _line("Neatlogs MCP", False, f"HTTP {error.code}")
    except urllib.error.URLError as error:
        return _line("Neatlogs MCP", False, f"network error: {error.reason}")

def check_slack():
    slack = Slack()
    if not slack.live: return _line("Slack", None, "no token")
    try:
        auth = slack._api("auth.test")
        _line("Slack auth", True, f"workspace={auth['team']} ({auth['team_id']}) bot={auth['user']}")
        channel = slack._api("conversations.info", {"channel": slack.channel_id()})["channel"]
        _line("Slack channel", channel.get("is_member"), f"{slack.channel} -> {channel['id']} member={channel.get('is_member')}")
        slack._api("conversations.history", {"channel": channel["id"], "limit": 1})
        return _line("Slack read", True, "conversations.history ok")
    except Exception as error:
        hint = " (add channels:read or set SLACK_CHANNEL to the channel ID)" if "missing_scope" in str(error) else " (run /invite @<bot> in the channel)" if "not_in_channel" in str(error) else ""
        return _line("Slack", False, f"{error}{hint}")

def check_linear():
    linear = Linear()
    if not linear.live: return _line("Linear", None, "no key")
    try:
        data = linear._graphql("{ viewer { name } organization { name } teams { nodes { id key name } } }")
        teams = ", ".join(f"{t['key']}={t['id']}" for t in data["teams"]["nodes"])
        return _line("Linear", True, f"viewer={data['viewer']['name']} org={data['organization']['name']} teams: {teams}")
    except Exception as error:
        return _line("Linear", False, str(error))

def run():
    results = [check_env(), check_model_provider(), check_neatlogs(), check_slack(), check_linear()]
    print("All live checks passed." if all(results) else "Some checks failed; fix them before running watch.")
    return all(results)
