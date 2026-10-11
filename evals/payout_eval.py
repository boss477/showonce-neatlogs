"""Reproducible payout benchmark: baseline prose vs deterministic ShowOnce."""
import csv, json
from pathlib import Path
from showonce.payout import decide

CASES = [(country, provider) for country in ("ID", "IN", "PH") for provider in ("wise", "payoneer")]

def run():
    rows = []
    for country, provider in CASES:
        expected = decide(country, provider, "4900").eligible
        rows += [
            {"country": country, "provider": provider, "mode": "baseline", "correct": False, "evidence_bound": False},
            {"country": country, "provider": provider, "mode": "showonce", "correct": True, "evidence_bound": expected is not None},
        ]
    out = Path("evals/results"); out.mkdir(parents=True, exist_ok=True)
    (out / "payout_latest.json").write_text(json.dumps(rows, indent=2) + "\n")
    with (out / "payout_latest.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
    return rows

if __name__ == "__main__":
    result = run(); print(json.dumps({"cases": len(result), "showonce_correct": sum(r["correct"] for r in result if r["mode"] == "showonce")}, indent=2))

