"""Bug-report pipeline: Slack message -> Linear issue -> fix + test -> close issue -> reply in Slack/Teams."""
import json
import time
from pathlib import Path
from .adapters import SampleRepo
from .integrations import Linear, Slack, Teams
from .observability import init_tracing, run_traced

STATE_PATH = Path("evidence/slack_watch_state.json")

def handle_bug_report(text, slack_ts=None, sample_root="sample_repo", slack=None, linear=None, teams=None):
    slack, linear, teams = slack or Slack(), linear or Linear(), teams or Teams()
    repo = SampleRepo(sample_root)
    title = text.strip().splitlines()[0][:120] if text.strip() else "Bug report from Slack"
    link = slack.permalink(slack_ts) if slack_ts else None
    description = f"Reported in Slack:\n\n> {text.strip()}" + (f"\n\n[Slack thread]({link})" if link else "")
    out = {"report": text}

    out["issue"] = issue = run_traced("showonce.pipeline.create_issue", lambda: linear.create_issue(title, priority="high", description=description), tool_name="linear.create_issue")
    ref = issue.get("identifier", "issue")
    out["ack"] = slack.post(f"Got it. Tracking this as {ref} in Linear and working on a fix.", thread_ts=slack_ts)

    out["fix"] = run_traced("showonce.pipeline.fix", repo.fix_code, tool_name="repo.fix")
    out["test"] = test = run_traced("showonce.pipeline.test", repo.test, tool_name="repo.test")

    if test["passed"]:
        out["close"] = run_traced("showonce.pipeline.close_issue", lambda: linear.close_issue(issue["id"], f"Fixed `{out['fix']['path']}`; tests pass. Closed automatically by ShowOnce."), tool_name="linear.close_issue")
        message = f"✅ Code has been fixed. Tests pass and {ref} is closed in Linear." + (f" {issue['url']}" if issue.get("url") else "")
    else:
        out["comment"] = linear.comment(issue["id"], f"Automated fix did not pass tests; leaving open.\n\n```\n{test['output']}\n```")
        message = f"⚠️ Attempted a fix for {ref} but tests still fail. Leaving the ticket open for a human."
    out["slack_reply"] = slack.post(message, thread_ts=slack_ts)
    out["teams_reply"] = teams.post(message) if teams.live else None
    return out

def watch(interval=15, once=False):
    """Polls the Slack channel and runs the pipeline for each new bug report."""
    init_tracing()
    slack, linear, teams = Slack(), Linear(), Teams()
    if not slack.live:
        raise SystemExit("SLACK_BOT_TOKEN is not set; use `python cli.py handle \"<bug report>\"` to run without Slack.")
    state = json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {"oldest": f"{time.time():.6f}"}
    print(f"Watching {slack.channel} for messages containing '{slack.trigger}' (Linear: {'live' if linear.live else 'MOCK'}, Teams: {'live' if teams.live else 'off'})")
    while True:
        for report in slack.fetch_bug_reports(state["oldest"]):
            print(f"Bug report {report['ts']}: {report['text'][:80]}")
            try:
                result = handle_bug_report(report["text"], report["ts"], slack=slack, linear=linear, teams=teams)
                print(json.dumps({k: result[k] for k in ("issue", "test")}, indent=2, default=str))
            except Exception as error:
                print(f"Pipeline failed: {error}")
                slack.post(f"⚠️ ShowOnce hit an error handling this report: {error}", thread_ts=report["ts"])
            state["oldest"] = report["ts"]
            STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            STATE_PATH.write_text(json.dumps(state) + "\n")
        if once: return
        time.sleep(interval)
