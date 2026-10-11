import argparse
import json
from dotenv import load_dotenv
from showonce.runner import demo
from showonce.pipeline import handle_bug_report, watch
from showonce.adapters import SampleRepo
from showonce.payout import decide

if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="offline recovery demo")
    w = sub.add_parser("watch", help="poll Slack for bug reports and run the fix pipeline")
    w.add_argument("--interval", type=int, default=15); w.add_argument("--once", action="store_true")
    h = sub.add_parser("handle", help="run the pipeline for one bug report without reading Slack")
    h.add_argument("text")
    sub.add_parser("inject-bug", help="put the bug back into sample_repo/buggy.py")
    p = sub.add_parser("payout", help="run the deterministic payout eligibility demo")
    p.add_argument("country", choices=["ID", "IN", "PH"]); p.add_argument("provider", choices=["wise", "payoneer"]); p.add_argument("amount_usd")
    args = parser.parse_args()
    if args.command == "demo": print(demo())
    elif args.command == "watch": watch(args.interval, args.once)
    elif args.command == "handle": print(json.dumps(handle_bug_report(args.text), indent=2, default=str))
    elif args.command == "inject-bug": print(SampleRepo("sample_repo").inject_bug())
    elif args.command == "payout": print(json.dumps(decide(args.country, args.provider, args.amount_usd).__dict__, indent=2))
