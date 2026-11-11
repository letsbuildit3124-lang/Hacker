"""
Replay and Comparison API router.
Supports historical transcript replay, scenario re-running with new personas/settings, and side-by-side comparison.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.services.replay_engine import replay_engine

router = APIRouter(prefix="/api", tags=["Replay & Comparison"])


class RerunRequest(BaseModel):
    new_persona_id: Optional[str] = None
    max_turns: Optional[int] = Field(default=5, ge=1, le=50)
    run_autonomous: bool = True


class CompareRequest(BaseModel):
    session_id_1: str
    session_id_2: str


@router.get("/sessions/{session_id}/replay", summary="Get transcript replay data")
async def get_session_replay(session_id: str):
    """
    Returns step-by-step transcript data with timing deltas for deterministic historical playback.
    """
    result = await replay_engine.get_replay_transcript(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/sessions/{session_id}/rerun", summary="Re-run a historical scenario")
async def rerun_simulation(session_id: str, req: RerunRequest):
    """
    Clones the source session's scenario and language to launch a fresh simulation,
    optionally swapping the attacker persona.
    """
    result = await replay_engine.rerun_simulation(
        source_session_id=session_id,
        new_persona_id=req.new_persona_id,
        max_turns=req.max_turns,
        run_autonomous=req.run_autonomous
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/compare", summary="Compare two simulation sessions side-by-side")
async def compare_sessions(req: CompareRequest):
    """
    Compares two simulation sessions side-by-side across turns, latencies,
    and evaluation score breakdowns.
    """
    result = await replay_engine.compare_sessions(
        session_id_1=req.session_id_1,
        session_id_2=req.session_id_2
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
