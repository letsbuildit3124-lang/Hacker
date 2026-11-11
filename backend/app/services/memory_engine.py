from typing import Dict, Any, List, Optional
from backend.app.utils.logger import logger

class MemoryEngine:
    """
    Advanced Conversation Memory Engine.
    Maintains Short-Term Memory, Long-Term Session Facts, and Compact Summaries
    without dumping unbounded transcripts to LLM prompts.
    """

    @classmethod
    def initialize_memory(
        cls,
        scenario: str,
        persona_id: str,
        established_facts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates initial structured memory state for a new session."""
        return {
            "summary": f"Initialized {scenario} interaction for representative with {established_facts.get('organization', 'Demo Org')}.",
            "topicsDiscussed": [scenario],
            "questionsAskedByHoneypot": [],
            "fictionalAnswersProvided": [],
            "milestones": ["session_created"],
            "currentState": "initiating",
            "lastStrategy": "trust_building",
            "recentTurnsCount": 0
        }

    @classmethod
    def update_memory_turn(
        cls,
        current_memory: Dict[str, Any],
        attacker_message: str,
        honeypot_message: Optional[str],
        strategy: str,
        state: str,
        established_facts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Updates memory atomically after a completed exchange.
        Extracts questions, updates topics, and synthesizes compact ongoing summary.
        """
        memory = dict(current_memory or {})
        topics = list(memory.get("topicsDiscussed", []))
        questions = list(memory.get("questionsAskedByHoneypot", []))
        answers = list(memory.get("fictionalAnswersProvided", []))
        milestones = list(memory.get("milestones", []))

        # Check for honeypot questions
        if honeypot_message:
            hm_lower = honeypot_message.lower()
            if "?" in honeypot_message or any(w in hm_lower for w in ["who", "what", "which", "where", "why", "how", "can you"]):
                # Record question (compact preview)
                cleaned_q = honeypot_message.strip()[:100]
                if cleaned_q not in questions:
                    questions.append(cleaned_q)
                    # Keep questions list bounded
                    if len(questions) > 6:
                        questions.pop(0)

            # Detect key topics
            for kw, topic in [
                ("kyc", "KYC Verification"),
                ("account", "Account Status"),
                ("branch", "Branch Inquiry"),
                ("id", "Identity Verification"),
                ("otp", "Security Code"),
                ("pin", "Security PIN"),
                ("reward", "Reward Redemption"),
                ("fee", "Courier Charge"),
                ("police", "Legal Inquiry"),
                ("scam", "Suspicion of Fraud")
            ]:
                if kw in hm_lower and topic not in topics:
                    topics.append(topic)

        # Record attacker statement highlight
        answers.append(attacker_message[:90])
        if len(answers) > 6:
            answers.pop(0)

        # Update milestones
        if "identity_verified" not in milestones and any(k in attacker_message.lower() for k in ["employee id", "officer", "agent id"]):
            milestones.append("identity_presented")
        if "procedure_explained" not in milestones and any(k in attacker_message.lower() for k in ["portal", "reference", "deadline", "verify"]):
            milestones.append("procedure_explained")

        # Synthesize rolling compact summary
        org = established_facts.get("organization", "the institution")
        ref = established_facts.get("caseReference", "active ticket")
        rep = established_facts.get("representativeName", "the representative")
        
        summary = (
            f"{rep} from {org} ({ref}) engaged user regarding {topics[-1] if topics else 'the case'}. "
            f"User inquired about: {questions[-1] if questions else 'procedural details'}. "
            f"Representative responded using {strategy} under state '{state}'."
        )

        return {
            "summary": summary,
            "topicsDiscussed": topics[-8:],
            "questionsAskedByHoneypot": questions,
            "fictionalAnswersProvided": answers,
            "milestones": milestones,
            "currentState": state,
            "lastStrategy": strategy,
            "recentTurnsCount": memory.get("recentTurnsCount", 0) + 1
        }

    @classmethod
    def get_prompt_context(
        cls,
        conversation_history: List[Dict[str, Any]],
        memory: Dict[str, Any],
        max_recent_messages: int = 4
    ) -> Dict[str, Any]:
        """
        Extracts compact context for LLM prompt generation:
        recent messages + compact summary + pending user questions.
        Eliminates unbounded context bloat.
        """
        # Only take the most recent messages
        recent_messages = conversation_history[-max_recent_messages:] if conversation_history else []

        return {
            "compactSummary": memory.get("summary", ""),
            "recentMessages": recent_messages,
            "pendingQuestions": memory.get("questionsAskedByHoneypot", [])[-2:],
            "keyMilestones": memory.get("milestones", []),
            "currentState": memory.get("currentState", "conversing"),
            "lastStrategy": memory.get("lastStrategy", "trust_building")
        }

memory_engine = MemoryEngine()
