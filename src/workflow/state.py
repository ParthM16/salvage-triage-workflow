from typing import TypedDict, Optional, List, Dict, Any


class WorkflowState(TypedDict):
    image_bytes: bytes
    car_meta: Dict[str, Any]
    severity: Optional[str]
    confidence: Optional[float]
    pav: Optional[float]
    repair_cost: Optional[float]
    salvage_bid: Optional[float]
    decision: Optional[str]
    memo: Optional[str]
    qa_passed: Optional[bool]
    qa_errors: Optional[List[str]]
    retry_count: int
    node_latencies: Dict[str, float]
    record_id: Optional[int]


def initial_state(image_bytes: bytes, car_meta: dict) -> WorkflowState:
    return {
        "image_bytes": image_bytes, "car_meta": car_meta, "severity": None,
        "confidence": None, "pav": None, "repair_cost": None, "salvage_bid": None,
        "decision": None, "memo": None, "qa_passed": None, "qa_errors": None,
        "retry_count": 0, "node_latencies": {}, "record_id": None,
    }
