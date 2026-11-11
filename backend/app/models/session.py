from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.models.message import Message

class SimulationSession(BaseModel):
    sessionId: str = Field(..., description="Unique simulation identifier")
    status: str = Field(default="created", description="Session status: created, running, stopped, completed, failed")
    personaId: str = Field(default="friendly_support", description="Attacker persona identifier")
    scenario: str = Field(default="fictional_bank_verification", description="Attack simulation scenario")
    language: str = Field(default="English", description="Communication language: English, Hinglish, Hindi")
    conversationHistory: List[Message] = Field(default_factory=list, description="Chronological conversation transcript")
    totalMessages: int = Field(default=0, description="Total messages exchanged in this session")
    maxTurns: int = Field(default=15, description="Maximum conversation turns before completion")
    errorMessage: Optional[str] = Field(default=None, description="Details of failure if status is failed")
    metadata: Dict[str, Any] = Field(default_factory=lambda: {"channel": "SMS", "language": "English", "locale": "IN"})
    
    # Phase 2 Intelligent Agent Memory & State fields
    establishedFacts: Dict[str, Any] = Field(default_factory=dict, description="Fictional facts established at creation")
    conversationMemory: Dict[str, Any] = Field(default_factory=dict, description="Structured conversation memory & summary")
    currentStrategy: Optional[Dict[str, Any]] = Field(default=None, description="Active strategy and reason")
    consistencyStatus: Optional[Dict[str, Any]] = Field(default=None, description="Consistency validation status")
    
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def update_timestamp(self) -> None:
        self.updatedAt = datetime.now(timezone.utc).isoformat()
