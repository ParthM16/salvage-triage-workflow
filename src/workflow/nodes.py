import re
import time

from src.config import TOTAL_LOSS_THRESHOLD
from src.workflow.state import WorkflowState
from src.ml.vision_classifier import predict_severity
from src.ml.valuation_engine import predict_pav, compute_actuarial_rules
from src.ml.llm import generate_memo

DOLLAR_RE = re.compile(r"\$([0-9][0-9,]*(?:\.[0-9]+)?)")


def _timed(state: WorkflowState, name: str, t0: float) -> dict:
    return {**state["node_latencies"], name: (time.perf_counter() - t0) * 1000.0}


def vision_node(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    severity, confidence = predict_severity(state["image_bytes"])
    return {**state, "severity": severity, "confidence": confidence,
            "node_latencies": _timed(state, "vision_node", t0)}


def valuation_node(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    pav = predict_pav(state["car_meta"])
    rules = compute_actuarial_rules(pav, state["severity"])
    return {**state, **rules, "node_latencies": _timed(state, "valuation_node", t0)}


def underwriter_node(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    figures = {k: state[k] for k in ("pav", "repair_cost", "salvage_bid", "decision")}
    memo = generate_memo(figures, retry_count=state["retry_count"],
                         qa_errors=state.get("qa_errors") or [])
    return {**state, "memo": memo, "node_latencies": _timed(state, "underwriter_node", t0)}


def guardrail_node(state: WorkflowState) -> WorkflowState:
    t0 = time.perf_counter()
    memo = state["memo"] or ""
    pav, repair, salvage = state["pav"], state["repair_cost"], state["salvage_bid"]
    errors: list[str] = []

    ratio = repair / pav if pav else 0.0
    expected = "TOTAL_LOSS" if ratio >= TOTAL_LOSS_THRESHOLD else "REPAIRABLE"
    if state["decision"] != expected:
        errors.append(f"State decision {state['decision']} != recomputed {expected}.")
    if expected not in memo:
        errors.append(f"Decision {expected} missing from memo.")

    memo_figs = [float(m.replace(",", "")) for m in DOLLAR_RE.findall(memo)]
    exp_figs = {pav, repair, salvage}
    for e in exp_figs:
        if not any(abs(m - e) <= 1.0 for m in memo_figs):
            errors.append(f"Expected figure {e:.2f} not found in memo.")
    for m in memo_figs:
        if not any(abs(m - e) <= 1.0 for e in exp_figs):
            errors.append(f"Memo contains unverified amount {m:.2f}.")

    passed = not errors
    return {**state, "qa_passed": passed, "qa_errors": errors,
            "retry_count": state["retry_count"] + (0 if passed else 1),
            "node_latencies": _timed(state, "guardrail_node", t0)}
