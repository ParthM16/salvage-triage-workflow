import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, JSON, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import DATABASE_URL
from src.workflow.state import WorkflowState

if DATABASE_URL.startswith("sqlite"):
    _dir = os.path.dirname(DATABASE_URL.replace("sqlite:///", ""))
    if _dir:
        os.makedirs(_dir, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AssessmentModel(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    year = Column(Integer)
    make = Column(String)
    model = Column(String)
    odometer = Column(Integer)
    severity = Column(String)
    confidence = Column(Float)
    pav = Column(Float)
    repair_cost = Column(Float)
    salvage_bid = Column(Float)
    decision = Column(String)
    qa_passed = Column(Boolean)
    qa_errors = Column(JSON)
    retry_count = Column(Integer)
    node_latencies = Column(JSON)
    memo = Column(String)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def save_assessment(state: WorkflowState) -> int:
    init_db()
    meta = state["car_meta"]
    with SessionLocal() as db:
        rec = AssessmentModel(
            year=meta.get("year"), make=meta.get("make"), model=meta.get("model"),
            odometer=meta.get("odometer"), severity=state["severity"],
            confidence=state["confidence"], pav=state["pav"],
            repair_cost=state["repair_cost"], salvage_bid=state["salvage_bid"],
            decision=state["decision"], qa_passed=state["qa_passed"],
            qa_errors=state["qa_errors"] or [], retry_count=state["retry_count"],
            node_latencies=state["node_latencies"], memo=state["memo"] or "",
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec.id
