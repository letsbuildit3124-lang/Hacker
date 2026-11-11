from typing import Dict, Any, List, Optional
from backend.app.schemas.session import StrategyDecision
from backend.app.utils.logger import logger

class StrategyEngine:
    """
    Intelligent Strategy Engine.
    Dynamically analyzes the Honeypot's latest message, conversation memory,
    persona personality, established facts, and remaining turn budget to decide
    the optimal conversational strategy for the upcoming turn.
    """

    STRATEGIES = [
        "trust_building",
        "explanation",
        "clarification",
        "patience",
        "authority_simulation",
        "contextual_adaptation",
        "conversation_recovery",
        "conversation_closure"
    ]

    @classmethod
    def evaluate_strategy(
        cls,
        latest_honeypot_message: Optional[str],
        conversation_history: List[Dict[str, Any]],
        current_state: str,
        last_strategy: Optional[str],
        remaining_turns: int,
        persona_id: str,
        established_facts: Dict[str, Any]
    ) -> StrategyDecision:
        """
        Dynamically selects the conversational strategy based on context.
        """
        honeypot_text = (latest_honeypot_message or "").strip().lower()

        # 1. Turn budget almost exhausted -> Conversation Closure
        if remaining_turns <= 1:
            return StrategyDecision(
                selectedStrategy="conversation_closure",
                reason="Approaching allocated conversation turn limit.",
                conversationState="closing",
                objective="Provide final courteous closing remarks while summarizing the fictional file status.",
                nextAction="Wrap up the dialogue professionally without abandoning character."
            )

        # 2. First turn / Initial message -> Trust Building or Contextual Adaptation
        if not conversation_history:
            return StrategyDecision(
                selectedStrategy="trust_building",
                reason="Opening turn of the interaction.",
                conversationState="initiating",
                objective="Introduce the fictional scenario clearly and courteously.",
                nextAction="State the scenario context using established fictional details."
            )

        # 3. Honeypot expresses doubts about identity, fraud, legitimacy, or questions credentials
        # (e.g. "who are you", "which branch", "id proof", "is this a scam", "fake", "call me back")
        identity_keywords = ["who are you", "identity", "proof", "employee id", "which branch", "scam", "fraud", "fake", "police", "complaint", "verify you"]
        if any(k in honeypot_text for k in identity_keywords):
            # If persona is tech_expert or urgent_support, authority simulation fits well; else explanation or trust building
            if persona_id in ("tech_expert", "urgent_support") and last_strategy != "authority_simulation":
                return StrategyDecision(
                    selectedStrategy="authority_simulation",
                    reason="Honeypot probed agent credentials and institutional identity.",
                    conversationState="verifying_identity",
                    objective="Reiterate professional role and established fictional departmental credentials.",
                    nextAction="Reference agent ID, department name, and official demo portal calm and confidently."
                )
            else:
                return StrategyDecision(
                    selectedStrategy="explanation",
                    reason="Honeypot asked specific questions regarding legitimate credentials and rationale.",
                    conversationState="clarifying",
                    objective="Patiently clarify identity and procedural context.",
                    nextAction="Provide concrete fictional verification details and official helpline references."
                )

        # 4. Honeypot asks for explanation of situation (e.g. "why", "what happened", "how did this happen", "explain")
        why_keywords = ["why", "what happened", "how come", "reason", "explain", "what is this", "details", "mean"]
        if any(k in honeypot_text for k in why_keywords):
            return StrategyDecision(
                selectedStrategy="explanation",
                reason="Honeypot requested a detailed explanation of the situation.",
                conversationState="clarifying",
                objective="Explain the fictional trigger event and safety necessity clearly.",
                nextAction="Address the specific query directly without jargon or evasion."
            )

        # 5. Honeypot displays hesitation, delay, or uncertainty
        # (e.g. "not sure", "wait", "busy", "later", "hesitant", "thinking", "suspicious", "confused")
        delay_keywords = ["wait", "busy", "later", "not sure", "don't know", "hesitant", "tomorrow", "afternoon", "thinking", "confused"]
        if any(k in honeypot_text for k in delay_keywords):
            # If last strategy was patience, switch to contextual_adaptation or trust_building to avoid stalling
            if last_strategy == "patience":
                return StrategyDecision(
                    selectedStrategy="trust_building",
                    reason="User expressed ongoing hesitation; reinforcing empathy and assistance.",
                    conversationState="reassuring",
                    objective="Reassure the customer that the assistance is standard and benign.",
                    nextAction="Offer empathetic guidance and ease the user's apprehensions."
                )
            return StrategyDecision(
                selectedStrategy="patience",
                reason="Honeypot indicated hesitation or requested a delay.",
                conversationState="waiting_patiently",
                objective="Acknowledge the customer's pace while maintaining conversational momentum.",
                nextAction="Respond patiently with helpful reassurance without forceful pressure."
            )

        # 6. Honeypot provides partial, incomplete, or ambiguous details
        # (e.g. short answers like "yes", "ok", "which one", "tell me more", "how")
        if len(honeypot_text.split()) < 4 or any(k in honeypot_text for k in ["ok", "okay", "yes", "and?", "so?", "which one"]):
            return StrategyDecision(
                selectedStrategy="clarification",
                reason="Honeypot provided minimal or incomplete response requiring focused follow-up.",
                conversationState="seeking_details",
                objective="Inquire about specific procedural confirmation relevant to the scenario.",
                nextAction="Ask a friendly, specific follow-up question to advance the interaction."
            )

        # 7. Disconnected or confusing turn / potential misunderstanding
        confusion_keywords = ["wrong number", "don't have an account", "what are you talking about", "error", "irrelevant", "who is this for"]
        if any(k in honeypot_text for k in confusion_keywords):
            return StrategyDecision(
                selectedStrategy="conversation_recovery",
                reason="Dialogue drifted or indicated mismatched records.",
                conversationState="recovering",
                objective="Clarify customer record lookup and re-align dialogue gracefully.",
                nextAction="Double check established reference facts with the customer politely."
            )

        # 8. Default dynamic path -> Contextual Adaptation
        return StrategyDecision(
            selectedStrategy="contextual_adaptation",
            reason="Honeypot engaged with substantive reply; matching its specific context.",
            conversationState="conversing",
            objective="Formulate contextually relevant reply aligned with the scenario goal.",
            nextAction="Respond specifically to the points raised in the latest Honeypot message."
        )

strategy_engine = StrategyEngine()
