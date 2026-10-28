# Salvage Underwriting Workflow (Phase 1: stubbed skeleton)

4-node LangGraph workflow (vision -> valuation -> underwriter -> guardrail) behind FastAPI with Server-Sent Events.
Repair cost, salvage bid and total-loss decision are a rule-based SIMULATION (illustrative assumptions, not industry data).

## Setup (Windows PowerShell)
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    copy .env.example .env

## Test
    pytest -v

## Run
    uvicorn src.api.main:app --reload

## Watch the SSE stream
    curl.exe -N -X POST http://localhost:8000/api/assess/stream -F "image=@data/sample_images/moderate.jpg" -F "year=2020" -F "make=Toyota" -F "model=Camry" -F "odometer=45000"
