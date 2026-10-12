"""Read-only integration checks. Prints pass/fail, names and non-secret IDs only.

Never creates issues or sends messages, so it is safe to run before a live demo.
"""
import json
import os
import urllib.error
import urllib.request
from .integrations import Linear, Slack

REQUIRED = ["OPENAI_API_KEY", "NEATLOGS_PROJECT_KEY", "SLACK_BOT_TOKEN", "SLACK_CHANNEL", "LINEAR_API_KEY"]

def _line(name, ok, info=""):
    print(f"{'PASS' if ok else 'FAIL' if ok is False else 'SKIP'}  {name:24} {info}")
    return ok is not False

def check_env():
    ok = True
    for key in REQUIRED:
        present = bool(os.getenv(key) or (key == "NEATLOGS_PROJECT_KEY" and os.getenv("NEATLOGS_API_KEY")))
        ok &= _line(key,present or None, "present" if present else "missing (MOCK fallback)")
    return ok

def check_openai():
    key = os.getenv("OPENAI_API_KEY")
    if not key: return _line("OpenAI", None, "no key")
    request = urllib.request.Request("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return _line("OpenAI", True, f"{len(json.loads(response.read())['data'])} models visible")
    except urllib.error.HTTPError as error:
        return _line("OpenAI", False, f"HTTP {error.code}")

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
    results = [check_env(), check_openai(), check_slack(), check_linear()]
    print("All live checks passed." if all(results) else "Some checks failed; fix them before running watch.")
    return all(results)
