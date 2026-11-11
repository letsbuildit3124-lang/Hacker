from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class CreateSessionRequest(BaseModel):
    scenario: str = Field(default="fictional_bank_verification", description="Scenario type")
    personaId: str = Field(default="friendly_support", description="Attacker persona ID")
    channel: str = Field(default="SMS", description="Simulated channel e.g. SMS, WhatsApp, Email")
    language: str = Field(default="English", description="Language: English, Hinglish, Hindi")
    locale: str = Field(default="IN", description="Country/regional locale")
    maxTurns: int = Field(default=15, ge=1, le=50, description="Max conversation turns")
    initialMessage: Optional[str] = Field(default=None, description="Optional custom initial scam simulation message")

class MessageItem(BaseModel):
    sender: str
    text: str
    timestamp: Union[int, str]
    turnNumber: Optional[int] = None

class SessionResponse(BaseModel):
    sessionId: str
    status: str
    personaId: str
    scenario: str
    language: str = "English"
    totalMessages: int
    maxTurns: int
    errorMessage: Optional[str] = None
    metadata: Dict[str, Any]
    establishedFacts: Dict[str, Any] = {}
    conversationMemory: Dict[str, Any] = {}
    currentStrategy: Optional[Dict[str, Any]] = None
    consistencyStatus: Optional[Dict[str, Any]] = None
    createdAt: str
    updatedAt: str
    conversationHistory: List[MessageItem] = []

class SessionStatsResponse(BaseModel):
    totalSimulations: int
    runningSimulations: int
    completedSimulations: int
    failedSimulations: int
    stoppedSimulations: int
    totalMessages: int

class SessionActionResponse(BaseModel):
    sessionId: str
    status: str
    message: str

class StrategyDecision(BaseModel):
    selectedStrategy: str = Field(..., description="Selected strategy identifier")
    reason: str = Field(..., description="Brief rationale for the strategy")
    conversationState: str = Field(..., description="Current conversational state")
    objective: str = Field(..., description="Goal for the next turn")
    nextAction: str = Field(..., description="Actionable guideline for response synthesis")

class StructuredAttackerResponse(BaseModel):
    message: str = Field(..., description="The user-facing conversational response message")
    selectedStrategy: str = Field(..., description="The conversational strategy applied")
    conversationState: str = Field(..., description="Current conversation stage (e.g., initial, clarifying, persuading, closing)")
    referencedFacts: List[str] = Field(default_factory=list, description="Keys of established fictional facts referenced")
    shouldContinue: bool = Field(default=True, description="Whether the conversation should proceed to another turn")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Confidence score in the response generation")
