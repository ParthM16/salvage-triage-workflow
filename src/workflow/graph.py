from langgraph.graph import StateGraph, END

from src.config import MAX_RETRIES
from src.workflow.state import WorkflowState
from src.workflow.nodes import vision_node, valuation_node, underwriter_node, guardrail_node


def should_retry(state: WorkflowState) -> str:
    if not state.get("qa_passed", True) and state.get("retry_count", 0) <= MAX_RETRIES:
        return "retry"
    return "end"


def next_node(node_name: str, state: WorkflowState) -> str | None:
    """Which node runs after node_name (used to emit node_start events)."""
    order = {"vision_node": "valuation_node", "valuation_node": "underwriter_node",
             "underwriter_node": "guardrail_node"}
    if node_name == "guardrail_node":
        return "underwriter_node" if should_retry(state) == "retry" else None
    return order.get(node_name)


def build_workflow():
    g = StateGraph(WorkflowState)
    g.add_node("vision_node", vision_node)
    g.add_node("valuation_node", valuation_node)
    g.add_node("underwriter_node", underwriter_node)
    g.add_node("guardrail_node", guardrail_node)
    g.set_entry_point("vision_node")
    g.add_edge("vision_node", "valuation_node")
    g.add_edge("valuation_node", "underwriter_node")
    g.add_edge("underwriter_node", "guardrail_node")
    g.add_conditional_edges("guardrail_node", should_retry,
                            {"retry": "underwriter_node", "end": END})
    return g.compile()


app_graph = build_workflow()
