"""
Batch Simulations API Router.
Handles creation, status polling, cancellation, and listing of multi-agent batch simulations.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.app.services.batch_engine import batch_engine, BatchConfig, BatchRecord

router = APIRouter(prefix="/api/batches", tags=["Batch Simulations"])


@router.post("", summary="Create and start a batch simulation")
async def create_batch(config: BatchConfig):
    """
    Creates multiple parallel attacker-versus-honeypot simulations across
    the selected scenario, persona, and language combinations.
    """
    if not config.scenarioIds:
        raise HTTPException(status_code=400, detail="At least one scenarioId must be provided.")
    if not config.personaIds:
        raise HTTPException(status_code=400, detail="At least one personaId must be provided.")

    batch = await batch_engine.create_and_start_batch(config)
    return batch


@router.get("", summary="List recent batch runs")
async def list_batches(limit: int = Query(50, ge=1, le=200)):
    """Lists recent multi-agent batch simulations."""
    batches = await batch_engine.list_batches(limit=limit)
    return batches


@router.get("/{batch_id}", summary="Get batch run details and progress")
async def get_batch(batch_id: str):
    """Retrieves real-time progress and session summaries for a batch run."""
    batch = await batch_engine.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch '{batch_id}' not found.")
    return batch


@router.post("/{batch_id}/cancel", summary="Cancel a running batch")
async def cancel_batch(batch_id: str):
    """Cancels all pending and in-progress sessions in the batch."""
    batch = await batch_engine.cancel_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch '{batch_id}' not found.")
    return batch
