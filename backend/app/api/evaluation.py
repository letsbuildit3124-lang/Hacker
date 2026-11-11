"""
Evaluation API router.
Provides endpoints for triggering, querying, and listing simulation evaluations.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from backend.app.services.evaluation_engine import evaluation_engine
from backend.app.database.mongodb import db

router = APIRouter(prefix="/api", tags=["Evaluation"])


@router.post("/sessions/{session_id}/evaluate", summary="Evaluate a simulation session")
async def evaluate_session(session_id: str):
    """
    Evaluates a completed simulation session against 10 core metrics,
    calculates intelligence extraction precision/recall/F1, and runs LLM judge analysis.
    """
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    messages = await db.get_messages(session_id)
    if len(messages) < 1:
        raise HTTPException(
            status_code=400,
            detail="Session has no messages to evaluate. Run at least one conversation turn first."
        )

    evaluation = await evaluation_engine.evaluate_session(session_id)
    return evaluation


@router.get("/sessions/{session_id}/evaluation", summary="Get session evaluation")
async def get_session_evaluation(session_id: str):
    """
    Retrieves the stored evaluation report for a given session.
    """
    evaluation = await db.get_evaluation(session_id)
    if not evaluation:
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation for session '{session_id}' not found. Run evaluation first."
        )
    return evaluation


@router.get("/evaluations", summary="List all evaluations")
async def list_evaluations(limit: int = Query(50, ge=1, le=200)):
    """
    Returns a list of recent session evaluations.
    """
    collection = db.get_collection("evaluations")
    docs = await collection.find({}).sort("evaluated_at", -1).to_list(length=limit)
    for doc in docs:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    return docs
