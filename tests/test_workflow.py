import json

from src.workflow.graph import app_graph
from src.workflow.nodes import guardrail_node
from src.workflow.state import initial_state
from src.ml.llm import set_force_wrong_memo

FORM = {"year": 2022, "make": "Ford", "model": "F-150", "odometer": 15000}
FILES = {"image": ("test.jpg", b"fake_bytes", "image/jpeg")}


def _run():
    return app_graph.invoke(initial_state(b"x", {"year": 2021, "make": "Honda",
                                                 "model": "Civic", "odometer": 30000}))


def _gstate(memo, decision="REPAIRABLE"):
    # pav 20000, repair 8000 (ratio 0.40 -> REPAIRABLE), salvage 6000
    return {"memo": memo, "pav": 20000.0, "repair_cost": 8000.0, "salvage_bid": 6000.0,
            "decision": decision, "retry_count": 0, "node_latencies": {}}


def _parse_sse(text):
    events, name = [], None
    for line in text.splitlines():
        if line.startswith("event:"):
            name = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            events.append((name, json.loads(line.split(":", 1)[1].strip())))
    return events


def test_happy_path():
    s = _run()
    assert s["severity"] == "moderate" and s["qa_passed"] is True and s["retry_count"] == 0


def test_forced_wrong_figure_triggers_one_retry_then_passes():
    set_force_wrong_memo(True)
    s = _run()
    assert s["qa_passed"] is True
    assert s["retry_count"] == 1
    assert "99,999" not in s["memo"]


def test_guardrail_wrong_figure():
    r = guardrail_node(_gstate("PAV $25,000.00, repair $8,000.00, salvage $6,000.00. REPAIRABLE"))
    assert r["qa_passed"] is False


def test_guardrail_missing_figure():
    r = guardrail_node(_gstate("PAV $20,000.00, repair $8,000.00. REPAIRABLE"))
    assert r["qa_passed"] is False


def test_guardrail_wrong_decision():
    r = guardrail_node(_gstate("PAV $20,000, repair $8,000, salvage $6,000. TOTAL_LOSS",
                               decision="TOTAL_LOSS"))
    assert r["qa_passed"] is False  # recomputed decision is REPAIRABLE


def test_guardrail_accepts_figures_without_decimals():
    r = guardrail_node(_gstate("PAV $20,000, repair $8000, salvage $6,000.00. REPAIRABLE"))
    assert r["qa_passed"] is True, r["qa_errors"]


def test_api_assess(client):
    r = client.post("/api/assess", data=FORM, files=FILES)
    assert r.status_code == 200
    d = r.json()
    assert d["record_id"] and d["qa_passed"] is True


def test_stream_event_order_happy(client):
    ev = _parse_sse(client.post("/api/assess/stream", data=FORM, files=FILES).text)
    names = [n for n, _ in ev]
    nodes = [(n, p["node"]) for n, p in ev if n in ("node_start", "node_complete")]
    assert nodes == [
        ("node_start", "vision_node"), ("node_complete", "vision_node"),
        ("node_start", "valuation_node"), ("node_complete", "valuation_node"),
        ("node_start", "underwriter_node"), ("node_complete", "underwriter_node"),
        ("node_start", "guardrail_node"), ("node_complete", "guardrail_node"),
    ]
    assert "token" in names and names[-1] == "done"


def test_stream_retry_runs_underwriter_twice(client):
    set_force_wrong_memo(True)
    ev = _parse_sse(client.post("/api/assess/stream", data=FORM, files=FILES).text)
    uw_starts = [p for n, p in ev if n == "node_start" and p["node"] == "underwriter_node"]
    assert len(uw_starts) == 2
    assert ev[-1][0] == "done" and ev[-1][1]["retry_count"] == 1
