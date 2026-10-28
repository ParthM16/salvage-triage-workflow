import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./data/salvage_audit.db"
TOTAL_LOSS_THRESHOLD = float(os.getenv("TOTAL_LOSS_THRESHOLD") or "0.75")
MAX_RETRIES = int(os.getenv("MAX_RETRIES") or "1")
USE_STUBS = (os.getenv("USE_STUBS") or "true").lower() == "true"
OLLAMA_HOST = os.getenv("OLLAMA_HOST") or "http://localhost:11434"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL") or "llama3.2:3b"

# Simulated assumptions (illustrative, NOT industry data)
SEVERITY_FACTOR = {"minor": 0.12, "moderate": 0.40, "severe": 0.85}
SALVAGE_FRACTION = {"minor": 0.60, "moderate": 0.40, "severe": 0.25}
