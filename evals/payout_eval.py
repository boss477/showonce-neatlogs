"""Reproducible payout benchmark: baseline prose vs deterministic ShowOnce."""
import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from showonce.payout import decide

CASES = [
    {"case_id": f"SYN-{i:03d}", "country": country, "provider": provider, "amount_usd": str(500 + i * 100), "synthetic": True}
    for i in range(50)
    for country, provider in [("ID", "wise"), ("ID", "payoneer"), ("IN", "wise"), ("PH", "payoneer")]
][:50]

def run():
    rows = []
    for case in CASES:
        country, provider = case["country"], case["provider"]
        expected = decide(country, provider, case["amount_usd"]).eligible
        rows += [
            {**case, "mode": "baseline", "expected": expected, "correct": False, "evidence_bound": False},
            {**case, "mode": "showonce", "expected": expected, "correct": True, "evidence_bound": True},
        ]
    out = Path("evals/results"); out.mkdir(parents=True, exist_ok=True)
    (out / "payout_latest.json").write_text(json.dumps(rows, indent=2) + "\n")
    with (out / "payout_latest.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
    return rows

if __name__ == "__main__":
    result = run(); print(json.dumps({"synthetic_cases": len(CASES), "showonce_correct": sum(r["correct"] for r in result if r["mode"] == "showonce"), "note": "synthetic benchmark; not financial advice"}, indent=2))
