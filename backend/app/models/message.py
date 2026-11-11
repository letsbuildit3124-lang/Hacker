import time
from typing import Optional, Union, Dict, Any
from pydantic import BaseModel, Field

class Message(BaseModel):
    sender: str = Field(..., description="'scammer' for attacker, 'user' for honeypot")
    text: str = Field(..., description="Message text content")
    timestamp: Union[int, str] = Field(default_factory=lambda: int(time.time() * 1000))
    turnNumber: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_honeypot_format(self) -> dict:
        """Format as expected by Honeypot API conversationHistory and message object."""
        return {
            "sender": self.sender,
            "text": self.text,
            "timestamp": self.timestamp
        }
