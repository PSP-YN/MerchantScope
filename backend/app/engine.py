"""Deterministic synthetic merchant data and explainable heuristic scoring."""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any

SCENARIOS = {
    "stable": {"name": "Stable neighbourhood bakery", "description": "A steady merchant with consistent ticket size and low refunds."},
    "seasonal": {"name": "Festival-season bakery", "description": "Higher order volume with stable refunds and ticket-size distribution."},
    "shift": {"name": "Behaviour-shift bakery", "description": "A sudden change in volume, refund behaviour, ticket size, and operating hours."},
}


def _merchant(mid: str, name: str, scenario: str, volume: int, avg: float, refund: float, night: float, concentration: float) -> dict[str, Any]:
    return {"id": mid, "name": name, "category": "Bakery & Food", "scenario": scenario,
            "daily_transactions": volume, "avg_ticket": round(avg, 2), "refund_rate": refund,
            "night_activity_rate": night, "top_instrument_share": concentration,
            "baseline_daily_transactions": 42, "baseline_avg_ticket": 360.0,
            "baseline_refund_rate": 0.025, "baseline_night_activity_rate": 0.04,
            "baseline_top_instrument_share": 0.18}

MERCHANTS = [
    _merchant("m-1001", "Mysuru Oven House", "stable", 44, 355, 0.021, 0.03, 0.16),
    _merchant("m-1002", "Festival Crust Co.", "seasonal", 108, 372, 0.024, 0.05, 0.19),
    _merchant("m-1003", "QuickBite Bakery", "shift", 164, 1180, 0.176, 0.39, 0.71),
    _merchant("m-1004", "Cornerstone Bakes", "stable", 38, 410, 0.018, 0.02, 0.14),
    _merchant("m-1005", "The Daily Loaf", "seasonal", 87, 348, 0.027, 0.04, 0.21),
]


def score_merchant(m: dict[str, Any]) -> dict[str, Any]:
    signals: list[dict[str, Any]] = []
    def add(key: str, label: str, points: int, detail: str) -> None:
        signals.append({"key": key, "label": label, "points": points, "detail": detail})
    vol = m["daily_transactions"] / max(1, m["baseline_daily_transactions"])
    if vol >= 3.0: add("volume", "Transaction volume surge", 24, f"{vol:.1f}× merchant baseline")
    elif vol >= 2.0: add("volume", "Elevated transaction volume", 12, f"{vol:.1f}× merchant baseline")
    ticket = m["avg_ticket"] / max(1, m["baseline_avg_ticket"])
    if ticket >= 2.5 or ticket <= 0.35: add("ticket", "Average ticket-size shift", 20, f"{ticket:.1f}× baseline average")
    elif ticket >= 1.6 or ticket <= 0.6: add("ticket", "Moderate ticket-size shift", 10, f"{ticket:.1f}× baseline average")
    refund_delta = m["refund_rate"] - m["baseline_refund_rate"]
    if refund_delta >= 0.10: add("refund", "Refund-rate deterioration", 25, f"{m['refund_rate']:.1%} current vs {m['baseline_refund_rate']:.1%} baseline")
    elif refund_delta >= 0.04: add("refund", "Refund rate above baseline", 12, f"{m['refund_rate']:.1%} current vs {m['baseline_refund_rate']:.1%} baseline")
    night_delta = m["night_activity_rate"] - m["baseline_night_activity_rate"]
    if night_delta >= 0.25: add("hours", "Unusual late-hour activity", 16, f"{m['night_activity_rate']:.1%} late-hour share")
    elif night_delta >= 0.10: add("hours", "Late-hour activity increase", 8, f"{m['night_activity_rate']:.1%} late-hour share")
    if m["top_instrument_share"] >= 0.60: add("concentration", "Payment-instrument concentration", 15, f"Top instrument share {m['top_instrument_share']:.1%}")
    elif m["top_instrument_share"] >= 0.35: add("concentration", "Elevated instrument concentration", 7, f"Top instrument share {m['top_instrument_share']:.1%}")
    score = min(100, sum(s["points"] for s in signals))
    level = "high" if score >= 60 else "medium" if score >= 30 else "low"
    return {"risk_score": score, "risk_level": level, "signals": signals,
            "explanation": "No material deviation detected against the demo baseline." if not signals else f"{len(signals)} explainable signal(s) contributed to this heuristic score."}


def get_dashboard() -> dict[str, Any]:
    enriched = [{**m, **score_merchant(m)} for m in MERCHANTS]
    tx_count = sum(m["daily_transactions"] for m in MERCHANTS)
    high = sum(m["risk_level"] == "high" for m in enriched)
    medium = sum(m["risk_level"] == "medium" for m in enriched)
    return {"data_mode": "SYNTHETIC DEMO DATA", "generated_at": datetime.now(timezone.utc).isoformat(),
            "metrics": {"merchants_monitored": len(enriched), "transactions_today": tx_count,
                        "high_risk_merchants": high, "review_queue": high + medium},
            "merchants": enriched, "scenarios": SCENARIOS}


def get_transactions(merchant_id: str | None = None) -> list[dict[str, Any]]:
    rows = []
    now = datetime.now(timezone.utc)
    for idx, m in enumerate(MERCHANTS):
        if merchant_id and m["id"] != merchant_id: continue
        count = min(12, max(5, m["daily_transactions"] // 10))
        for j in range(count):
            suspicious = m["scenario"] == "shift" and j >= count - 4
            rows.append({"id": f"tx-{idx+1:02d}-{j+1:03d}", "merchant_id": m["id"], "merchant_name": m["name"],
                         "amount": round((m["avg_ticket"] * (1.0 + ((j % 5) - 2) * 0.11)), 2),
                         "status": "refunded" if suspicious and j % 2 == 0 else "settled",
                         "channel": "card" if j % 3 else "upi", "hour": 1 + j if suspicious else 9 + (j % 11),
                         "created_at": (now - timedelta(minutes=idx * 17 + j * 23)).isoformat(),
                         "synthetic": True})
    return sorted(rows, key=lambda x: x["created_at"], reverse=True)


def get_relationships() -> dict[str, Any]:
    return {"nodes": [{"id": m["id"], "label": m["name"], "kind": "merchant"} for m in MERCHANTS] +
            [{"id": "fp-device-77", "label": "Device fingerprint · 77", "kind": "fingerprint"},
             {"id": "fp-ip-12", "label": "Network fingerprint · 12", "kind": "fingerprint"}],
            "edges": [{"source": "m-1003", "target": "fp-device-77", "relation": "shared device"},
                      {"source": "m-1002", "target": "fp-device-77", "relation": "shared device"},
                      {"source": "m-1003", "target": "fp-ip-12", "relation": "shared network"},
                      {"source": "m-1005", "target": "fp-ip-12", "relation": "shared network"}],
            "notice": "Synthetic relationship fingerprints for interface demonstration only."}
