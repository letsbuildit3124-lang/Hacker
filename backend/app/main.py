from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.sessions import router as sessions_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.batches import router as batches_router
from backend.app.api.replay import router as replay_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.reports import router as reports_router
from backend.app.api.stress_test import router as stress_test_router
from backend.app.api.settings import router as settings_router, HONEYPOT_CONFIG_KEY
from backend.app.config import settings
from backend.app.database.mongodb import db
from backend.app.services.honeypot_client import honeypot_client, normalize_honeypot_url
from backend.app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to MongoDB
    logger.info("Initializing Agentic Honeypot AI Red-Team Platform Backend...")
    await db.connect()

    # Load persisted Honeypot target config if present
    try:
        settings_col = db.get_collection("system_settings")
        saved_cfg = await settings_col.find_one({"configKey": HONEYPOT_CONFIG_KEY})
        if saved_cfg and saved_cfg.get("honeypot_base_url"):
            settings.HONEYPOT_BASE_URL = normalize_honeypot_url(saved_cfg["honeypot_base_url"])
            honeypot_client._explicit_base_url = None
            if saved_cfg.get("honeypot_api_key"):
                settings.HONEYPOT_API_KEY = saved_cfg["honeypot_api_key"]
                honeypot_client._explicit_api_key = None
            logger.info(f"Loaded persisted target Honeypot URL: {settings.HONEYPOT_BASE_URL}")
    except Exception as exc:
        logger.warning(f"Could not restore persisted honeypot settings: {exc}")

    # Mark any dangling 'running' sessions from prior process restarts as 'stopped'
    try:
        sess_col = db.get_collection("sessions")
        dangling = await sess_col.find({"status": "running"}).to_list(100)
        for d in dangling:
            await sess_col.update_one({"sessionId": d["sessionId"]}, {"$set": {"status": "stopped"}})
    except Exception as exc:
        logger.warning(f"Could not cleanup dangling sessions: {exc}")

    yield
    # Shutdown: close MongoDB connection
    logger.info("Shutting down Agentic Honeypot AI Red-Team Platform Backend...")
    await db.close()


app = FastAPI(
    title="Agentic Honeypot AI Red-Team Simulation Platform - Attacker Simulator & Evaluation API",
    description="Backend API orchestrating autonomous Attacker Agent interactions, batch simulations, automated multi-metric evaluations, transcript replay, and performance benchmarking for an external AI Honeypot.",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes
app.include_router(sessions_router)
app.include_router(evaluation_router)
app.include_router(batches_router)
app.include_router(replay_router)
app.include_router(analytics_router)
app.include_router(reports_router)
app.include_router(stress_test_router)
app.include_router(settings_router)


@app.get("/api/health", tags=["System"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "Agentic Honeypot Attacker Simulator & Evaluator",
        "version": "3.0.0",
        "database": "connected" if db.is_connected else "fallback_in_memory",
        "honeypot_target": settings.HONEYPOT_BASE_URL,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL
    }


@app.get("/api/ready", tags=["System"])
async def readiness_check():
    """System readiness check confirming readiness to process simulation workloads."""
    return {
        "status": "ready",
        "database_ready": True,
        "llm_configured": bool(settings.LLM_API_KEY or settings.LLM_PROVIDER == "mock"),
        "honeypot_url": settings.HONEYPOT_BASE_URL,
        "features": {
            "autonomous_simulation": True,
            "multimetric_evaluation": True,
            "batch_execution": True,
            "transcript_replay": True,
            "stress_testing": True,
            "reporting": True
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True
    )
