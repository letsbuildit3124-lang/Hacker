from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.schemas.session import (
    CreateSessionRequest,
    SessionResponse,
    MessageItem,
    SessionStatsResponse,
    SessionActionResponse
)
from backend.app.services.persona_engine import persona_engine
from backend.app.services.scenario_engine import scenario_engine
from backend.app.services.conversation_manager import conversation_manager
from backend.app.utils.logger import logger

router = APIRouter(prefix="/api/sessions", tags=["Simulations"])

@router.get("/personas", response_model=List[Dict[str, Any]])
async def list_personas():
    """Get all 5 configurable fictional attacker personas."""
    return persona_engine.list_personas()

@router.get("/scenarios", response_model=List[Dict[str, Any]])
async def list_scenarios():
    """Get all 6 fictional simulation scenario templates."""
    return scenario_engine.list_scenarios()

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_simulation(req: CreateSessionRequest):
    """Create a new simulation session with established scenario facts."""
    try:
        session = await conversation_manager.create_session(
            scenario=req.scenario,
            persona_id=req.personaId,
            channel=req.channel,
            language=req.language,
            locale=req.locale,
            max_turns=req.maxTurns,
            initial_message=req.initialMessage
        )
        return session.model_dump()
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[SessionResponse])
async def list_simulations(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200)
):
    """Get all simulation sessions."""
    try:
        sessions = await conversation_manager.list_sessions(status=status_filter, limit=limit)
        return [s.model_dump() for s in sessions]
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=SessionStatsResponse)
async def get_simulation_stats():
    """Get aggregated overview statistics for the dashboard."""
    try:
        stats = await conversation_manager.get_session_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return SessionStatsResponse(
            totalSimulations=0,
            runningSimulations=0,
            completedSimulations=0,
            failedSimulations=0,
            stoppedSimulations=0,
            totalMessages=0
        )

@router.get("/{session_id}", response_model=SessionResponse)
async def get_simulation(session_id: str):
    """Get session details by ID."""
    session = await conversation_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Simulation session {session_id} not found")
    return session.model_dump()

@router.post("/{session_id}/start", response_model=SessionActionResponse)
async def start_simulation(session_id: str):
    """Start autonomous conversation between the Attacker Agent and Honeypot API."""
    try:
        session = await conversation_manager.start_session(session_id)
        return SessionActionResponse(
            sessionId=session.sessionId,
            status=session.status,
            message="Simulation started successfully."
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting simulation {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/stop", response_model=SessionActionResponse)
async def stop_simulation(session_id: str):
    """Stop the running simulation."""
    try:
        session = await conversation_manager.stop_session(session_id)
        return SessionActionResponse(
            sessionId=session.sessionId,
            status=session.status,
            message="Simulation stopped successfully."
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error stopping simulation {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/resume", response_model=SessionActionResponse)
async def resume_simulation(session_id: str):
    """Resume simulation from the current state without resetting history or memory."""
    try:
        session = await conversation_manager.resume_session(session_id)
        return SessionActionResponse(
            sessionId=session.sessionId,
            status=session.status,
            message="Simulation resumed successfully."
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error resuming simulation {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/messages", response_model=List[MessageItem])
async def get_simulation_messages(session_id: str):
    """Get complete chronological conversation history for a session."""
    session = await conversation_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Simulation session {session_id} not found")
    return [m.model_dump() for m in session.conversationHistory]
