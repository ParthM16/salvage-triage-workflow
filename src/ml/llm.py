from src.config import USE_STUBS

_force_wrong_memo = False


def set_force_wrong_memo(val: bool) -> None:
    """Test hook: first attempt quotes a wrong figure."""
    global _force_wrong_memo
    _force_wrong_memo = val


def build_correction_prompt(qa_errors: list | None) -> str:
    """Instruction sent to a REAL LLM on retry. Never appended to the memo text."""
    if not qa_errors:
        return ""
    return ("Your previous memo failed validation: " + "; ".join(qa_errors)
            + ". Rewrite it quoting the exact figures provided.")


def generate_memo(figures: dict, retry_count: int = 0, qa_errors: list | None = None) -> str:
    pav, repair = figures["pav"], figures["repair_cost"]
    salvage, decision = figures["salvage_bid"], figures["decision"]

    if _force_wrong_memo and retry_count == 0:
        return (f"Vehicle PAV is $99,999 with estimated repair cost of ${repair:,.2f}. "
                f"Salvage bid is ${salvage:,.2f}. Decision: {decision}.")

    if USE_STUBS:
        # Phase 3: send build_correction_prompt(qa_errors) to the real LLM here.
        return (f"Underwriting summary: pre-accident value (PAV) is ${pav:,.2f}. "
                f"Estimated repair cost is ${repair:,.2f}. "
                f"Expected salvage bid is ${salvage:,.2f}. "
                f"Recommended disposition: {decision}. (Simulated assumptions.)")
    raise NotImplementedError("Real LLM client arrives in Phase 3.")
