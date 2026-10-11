"""Executed fixture benchmark. Scores come from subprocess test exit codes."""
import csv, json, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from showonce.repair_demo import run_repair

def run():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    rows = []
    for task in range(10):
        for mode in ("baseline", "showonce"):
            result = run_repair(mode == "showonce", offset=task)
            rows.append({"task": task, "mode": mode, **{k:v for k,v in result.items() if k != "events"}})
    out = Path("evals/results"); out.mkdir(parents=True, exist_ok=True)
    with (out / f"{stamp}.json").open("x") as f:
        json.dump(rows, f, indent=2)
    with (out / f"{stamp}.csv").open("x", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
    return rows

if __name__ == "__main__": print(json.dumps(run(), indent=2))
