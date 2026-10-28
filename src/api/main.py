import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from sse_starlette.sse import EventSourceResponse

from src.workflow.state import initial_state
from src.workflow.graph import app_graph, next_node
from src.db.repository import init_db, save_assessment


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Salvage Underwriting Workflow API", version="1.0.0", lifespan=lifespan)

RESULT_KEYS = ("severity", "confidence", "pav", "repair_cost", "salvage_bid",
               "decision", "qa_passed", "qa_errors", "retry_count", "node_latencies", "memo")


def _event(name: str, payload: dict) -> dict:
    return {"event": name, "data": json.dumps(payload)}


@app.post("/api/assess")
async def assess(image: UploadFile = File(...), year: int = Form(...),
                 make: str = Form(...), model: str = Form(...), odometer: int = Form(...)):
    state = initial_state(await image.read(),
                          {"year": year, "make": make, "model": model, "odometer": odometer})
    try:
        final = await asyncio.to_thread(app_graph.invoke, state)
        record_id = await asyncio.to_thread(save_assessment, final)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))
    return {"record_id": record_id, **{k: final.get(k) for k in RESULT_KEYS}}


@app.post("/api/assess/stream")
async def assess_stream(image: UploadFile = File(...), year: int = Form(...),
                        make: str = Form(...), model: str = Form(...), odometer: int = Form(...)):
    state = initial_state(await image.read(),
                          {"year": year, "make": make, "model": model, "odometer": odometer})
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def emit(item):
        loop.call_soon_threadsafe(queue.put_nowait, item)

    def worker():
        try:
            emit(_event("node_start", {"node": "vision_node"}))
            current = state
            for update in app_graph.stream(state, stream_mode="updates"):
                for node_name, node_state in update.items():
                    current = node_state
                    emit(_event("node_complete", {
                        "node": node_name,
                        "latency_ms": node_state["node_latencies"].get(node_name),
                        "qa_passed": node_state.get("qa_passed"),
                    }))
                    nxt = next_node(node_name, node_state)
                    if nxt:
                        emit(_event("node_start", {"node": nxt}))
            record_id = save_assessment(current)
            # TODO Phase 3: stream real LLM tokens from the underwriter node.
            memo = current["memo"] or ""
            for i in range(0, len(memo), 20):
                emit(_event("token", {"token": memo[i:i + 20]}))
            emit(_event("done", {"record_id": record_id,
                                 **{k: current.get(k) for k in
                                    ("decision", "qa_passed", "pav", "repair_cost",
                                     "salvage_bid", "retry_count")}}))
        except Exception as e:  # noqa: BLE001
            emit(_event("error", {"message": str(e)}))
        finally:
            emit(None)

    loop.run_in_executor(None, worker)

    async def generator():
        while (item := await queue.get()) is not None:
            yield item

    return EventSourceResponse(generator())
