"""
System Settings API Router.
Allows viewing (with masked credentials), testing, updating, and persisting
the target Honeypot API URL and optional API key at runtime.
"""
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from backend.app.config import settings
from backend.app.database.mongodb import db
from backend.app.services.honeypot_client import honeypot_client, normalize_honeypot_url
from backend.app.utils.logger import logger

router = APIRouter(prefix="/api/settings", tags=["Settings"])

HONEYPOT_CONFIG_KEY = "honeypot_config"


class HoneypotSettingsResponse(BaseModel):
    honeypot_base_url: str
    has_api_key: bool
    timeout_seconds: int


class UpdateHoneypotSettingsRequest(BaseModel):
    honeypot_base_url: str = Field(..., min_length=1, description="Base URL of target Honeypot service")
    honeypot_api_key: Optional[str] = Field(default=None, description="Optional x-api-key (leave blank to retain current key)")
    clear_api_key: bool = Field(default=False, description="Set true to remove stored x-api-key")

    @field_validator("honeypot_base_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        try:
            return normalize_honeypot_url(v)
        except ValueError as exc:
            raise ValueError(str(exc))


class TestHoneypotConnectionRequest(BaseModel):
    honeypot_base_url: str = Field(..., min_length=1)
    honeypot_api_key: Optional[str] = None

    @field_validator("honeypot_base_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        try:
            return normalize_honeypot_url(v)
        except ValueError as exc:
            raise ValueError(str(exc))


@router.get("/honeypot", response_model=HoneypotSettingsResponse, summary="Get active Honeypot endpoint configuration")
async def get_honeypot_settings():
    """
    Returns active target Honeypot URL and whether an API key is configured.
    Never exposes raw API keys to clients.
    """
    return HoneypotSettingsResponse(
        honeypot_base_url=honeypot_client.base_url,
        has_api_key=bool(honeypot_client.api_key),
        timeout_seconds=settings.HONEYPOT_TIMEOUT_SECONDS
    )


@router.put("/honeypot", response_model=HoneypotSettingsResponse, summary="Update target Honeypot URL and API key")
async def update_honeypot_settings(req: UpdateHoneypotSettingsRequest):
    """
    Validates and updates the active Honeypot target URL (and optional API key) in memory
    and persists it to MongoDB so it survives restarts.
    """
    normalized_url = req.honeypot_base_url
    settings.HONEYPOT_BASE_URL = normalized_url
    honeypot_client._explicit_base_url = None  # Follow live settings.HONEYPOT_BASE_URL

    if req.clear_api_key:
        settings.HONEYPOT_API_KEY = None
        honeypot_client._explicit_api_key = None
    elif req.honeypot_api_key is not None and req.honeypot_api_key.strip():
        settings.HONEYPOT_API_KEY = req.honeypot_api_key.strip()
        honeypot_client._explicit_api_key = None

    # Persist to MongoDB system_settings collection
    try:
        coll = db.get_collection("system_settings")
        doc = {
            "configKey": HONEYPOT_CONFIG_KEY,
            "honeypot_base_url": settings.HONEYPOT_BASE_URL,
            "honeypot_api_key": settings.HONEYPOT_API_KEY,
            "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        await coll.update_one({"configKey": HONEYPOT_CONFIG_KEY}, {"$set": doc}, upsert=True)
    except Exception as exc:
        logger.warning(f"[Settings] Could not persist honeypot settings to DB: {exc}")

    logger.info(f"[Settings] Updated active target Honeypot URL to: {settings.HONEYPOT_BASE_URL}")
    return HoneypotSettingsResponse(
        honeypot_base_url=honeypot_client.base_url,
        has_api_key=bool(honeypot_client.api_key),
        timeout_seconds=settings.HONEYPOT_TIMEOUT_SECONDS
    )


@router.post("/honeypot/test", summary="Test connectivity to a candidate Honeypot endpoint")
async def test_honeypot_connection(req: TestHoneypotConnectionRequest) -> Dict[str, Any]:
    """
    Sends a synthetic probe to the candidate Honeypot URL to confirm reachability,
    authentication, and response schema compatibility before saving.
    """
    api_key = req.honeypot_api_key.strip() if req.honeypot_api_key and req.honeypot_api_key.strip() else None
    result = await honeypot_client.test_connection(
        candidate_url=req.honeypot_base_url,
        candidate_api_key=api_key
    )
    return result
