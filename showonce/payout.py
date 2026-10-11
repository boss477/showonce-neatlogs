"""Deterministic payout eligibility demo: code decides, the model would explain."""
from dataclasses import dataclass
from decimal import Decimal

RULES = {
    "ID": {"wise": False, "payoneer": True, "currency": "IDR"},
    "IN": {"wise": True, "payoneer": True, "currency": "INR"},
    "PH": {"wise": True, "payoneer": True, "currency": "PHP"},
}

@dataclass
class PayoutDecision:
    country: str
    provider: str
    eligible: bool
    reason: str
    evidence: list[str]
    status: str = "VERIFIED"

def decide(country: str, provider: str, amount_usd: str) -> PayoutDecision:
    country, provider = country.upper(), provider.lower()
    row = RULES.get(country)
    evidence = [f"rules://payout/{country}/{provider}", "rules://amount/usd"]
    if row is None:
        return PayoutDecision(country, provider, False, "UNCLEAR: no sourced country rule", evidence, "UNCLEAR")
    if provider not in row:
        return PayoutDecision(country, provider, False, "UNCLEAR: provider is not in the sourced rule sheet", evidence, "UNCLEAR")
    if not row[provider]:
        return PayoutDecision(country, provider, False, "REFUSE: this provider cannot receive the payout in this country", evidence)
    amount = Decimal(amount_usd)
    return PayoutDecision(country, provider, True, f"ACCEPT: route supports {row['currency']} receipt for ${amount:.2f} USD", evidence)

def provenance_guardrail(text: str, decision: PayoutDecision) -> dict:
    required = [decision.status, decision.provider, decision.country]
    passed = all(item.lower() in text.lower() for item in required)
    return {"passed": passed, "status": "OK" if passed else "WARN", "required": required, "evidence": decision.evidence}

