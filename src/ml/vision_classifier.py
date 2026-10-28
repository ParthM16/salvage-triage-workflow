from src.config import USE_STUBS


def predict_severity(image_bytes: bytes) -> tuple[str, float]:
    """Node 1: returns (severity, confidence). Stub in Phase 1."""
    if USE_STUBS:
        return "moderate", 0.88
    raise NotImplementedError("Real vision classifier arrives in Phase 2.")
