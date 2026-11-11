"""
Stress Testing API Router.
Provides controlled endpoints for testing Honeypot API reliability, latency percentiles, and circuit-breaking.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.services.stress_test_engine import stress_test_engine

router = APIRouter(prefix="/api/stress-tests", tags=["Stress Testing & Reliability"])


class StressTestRequest(BaseModel):
    num_requests: int = Field(default=10, ge=1, le=100)
    concurrency: int = Field(default=2, ge=1, le=10)
    delay_between_requests_ms: int = Field(default=200, ge=0, le=5000)
    safety_error_threshold: float = Field(default=0.25, ge=0.05, le=1.0)


@router.post("", summary="Run a controlled stress test against the Honeypot")
async def run_stress_test(req: StressTestRequest):
    """
    Executes a controlled burst of requests to calculate P50/P95/P99 latency,
    HTTP status distribution, and verifies automatic circuit breaker thresholds.
    """
    result = await stress_test_engine.run_stress_test(
        num_requests=req.num_requests,
        concurrency=req.concurrency,
        delay_between_requests_ms=req.delay_between_requests_ms,
        safety_error_threshold=req.safety_error_threshold
    )
    return result


@router.get("/{test_id}", summary="Get stress test results")
async def get_stress_test(test_id: str):
    """Retrieves metrics and latency percentiles for a previous stress test run."""
    result = stress_test_engine.get_test_status(test_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Stress test '{test_id}' not found.")
    return result
