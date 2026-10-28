from src.config import USE_STUBS, SEVERITY_FACTOR, SALVAGE_FRACTION, TOTAL_LOSS_THRESHOLD


def predict_pav(car_meta: dict) -> float:
    """Node 2: pre-accident value. Stub formula in Phase 1."""
    if USE_STUBS:
        mileage = car_meta.get("odometer", 50000)
        year = car_meta.get("year", 2020)
        return float(max(5000.0, 20000.0 - (2022 - year) * 1000 - (mileage / 10000) * 500))
    raise NotImplementedError("Real valuation model arrives in Phase 2.")


def compute_actuarial_rules(pav: float, severity: str) -> dict:
    """Rule-based SIMULATION. Not a learned prediction."""
    repair_cost = pav * SEVERITY_FACTOR.get(severity, 0.40)
    salvage_bid = pav * SALVAGE_FRACTION.get(severity, 0.40)
    decision = "TOTAL_LOSS" if repair_cost / pav >= TOTAL_LOSS_THRESHOLD else "REPAIRABLE"
    return {
        "pav": round(pav, 2),
        "repair_cost": round(repair_cost, 2),
        "salvage_bid": round(salvage_bid, 2),
        "decision": decision,
    }
