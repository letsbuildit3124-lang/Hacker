import asyncio
from typing import List, Dict, Any, Optional, Tuple
from backend.app.config import settings
from backend.app.schemas.session import StructuredAttackerResponse, StrategyDecision
from backend.app.services.persona_engine import persona_engine, PersonaConfig
from backend.app.services.scenario_engine import scenario_engine, ScenarioDefinition, SCENARIO_TEMPLATES
from backend.app.services.strategy_engine import strategy_engine
from backend.app.services.memory_engine import memory_engine
from backend.app.services.tone_engine import tone_engine
from backend.app.services.consistency_engine import consistency_engine
from backend.app.services.llm_provider import llm_provider
from backend.app.utils.logger import logger

# Retain SCENARIO_PROMPTS for backwards compatibility
SCENARIO_PROMPTS = {
    s_id: {
        "persona": defn.fictionalOrg,
        "objective": defn.conversationObjective,
        "initial": f"URGENT: Your account verification is pending with {defn.fictionalOrg}.",
        "follow_ups": []
    }
    for s_id, defn in SCENARIO_TEMPLATES.items()
}


class AttackerEngine:
    """
    Advanced Phase 2 Intelligent Attacker Agent Orchestrator.
    Combines Persona, Scenario, Strategy, Memory, Tone, and Consistency Engines
    into a stateful, adaptive conversational AI simulator.
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.model = settings.LLM_MODEL
        self.api_key = settings.LLM_API_KEY
        logger.info(f"Initialized Advanced AttackerEngine (Phase 2) with provider: {self.provider}")

    async def _generate_with_gemini(self, scenario, conversation_history, persona_id):
        """Phase 1 compatibility delegate."""
        persona = persona_engine.get_persona(persona_id)
        scenario_def = scenario_engine.get_scenario_definition(scenario)
        facts = scenario_engine.generate_session_facts(scenario, persona.name)
        strat = {"selectedStrategy": "contextual_adaptation", "conversationState": "conversing"}
        ctx = {"recentMessages": conversation_history, "compactSummary": ""}
        resp = await llm_provider._generate_with_gemini(persona, scenario_def, facts, strat, ctx, "English", None)
        return resp.message

    async def generate_initial_turn(
        self,
        scenario: str,
        custom_prompt: Optional[str] = None,
        persona_id: str = "friendly_support",
        language: str = "English",
        established_facts: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        """
        Generates opening turn with structured metadata.
        Returns: (message_text, strategy_dict, consistency_dict)
        """
        if custom_prompt and custom_prompt.strip():
            return (
                custom_prompt.strip(),
                {"selectedStrategy": "custom_initial", "conversationState": "initiating", "reason": "User custom opening prompt"},
                {"isValid": True, "issues": []}
            )

        persona = persona_engine.get_persona(persona_id)
        scenario_def = scenario_engine.get_scenario_definition(scenario)
        facts = established_facts or scenario_engine.generate_session_facts(scenario, persona.name)

        strategy_decision = strategy_engine.evaluate_strategy(
            latest_honeypot_message=None,
            conversation_history=[],
            current_state="initiating",
            last_strategy=None,
            remaining_turns=10,
            persona_id=persona.personaId,
            established_facts=facts
        )

        prompt_context = memory_engine.get_prompt_context([], {}, max_recent_messages=2)

        # Generate structured response via LLM
        structured_resp = await llm_provider.generate_structured_turn(
            persona=persona,
            scenario=scenario_def,
            established_facts=facts,
            strategy_decision=strategy_decision.model_dump(),
            prompt_context=prompt_context,
            language=language
        )

        # Tone & Language adaptation
        final_text = tone_engine.adapt_tone(structured_resp.message, persona, language)

        # Consistency check
        val = consistency_engine.validate_message(final_text, persona, facts, scenario, [])
        if not val.is_valid:
            logger.warning(f"[AttackerEngine] Consistency check failed on initial message: {val.issues}. Using safe fallback.")
            final_text = consistency_engine.get_safe_fallback(persona, facts, scenario)
            val = consistency_engine.validate_message(final_text, persona, facts, scenario, [])

        return final_text, strategy_decision.model_dump(), val.to_dict()

    async def generate_initial_message(
        self,
        scenario: str,
        custom_prompt: Optional[str] = None,
        persona_id: str = "friendly_support",
        language: str = "English",
        established_facts: Optional[Dict[str, Any]] = None
    ) -> str:
        """Backward-compatible string-returning initial message generator."""
        text, _, _ = await self.generate_initial_turn(
            scenario=scenario,
            custom_prompt=custom_prompt,
            persona_id=persona_id,
            language=language,
            established_facts=established_facts
        )
        return text

    async def generate_next_turn(
        self,
        scenario: str,
        conversation_history: List[Dict[str, Any]],
        persona_id: str = "friendly_support",
        language: str = "English",
        established_facts: Optional[Dict[str, Any]] = None,
        memory: Optional[Dict[str, Any]] = None,
        remaining_turns: int = 10
    ) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        """
        Generates next contextual turn with full metadata.
        Returns: (message_text, strategy_dict, consistency_dict)
        """
        persona = persona_engine.get_persona(persona_id)
        scenario_def = scenario_engine.get_scenario_definition(scenario)
        facts = established_facts or scenario_engine.generate_session_facts(scenario, persona.name)
        mem = memory or {}

        # Identify latest honeypot message
        latest_honeypot_msg = None
        for m in reversed(conversation_history):
            if m.get("sender") == "user":
                latest_honeypot_msg = m.get("text")
                break

        # Collect previous attacker messages for repetition detection
        previous_attacker_texts = [
            m.get("text", "") for m in conversation_history
            if m.get("sender") == "scammer"
        ]

        # 1. Evaluate conversational strategy
        strategy_decision = strategy_engine.evaluate_strategy(
            latest_honeypot_message=latest_honeypot_msg,
            conversation_history=conversation_history,
            current_state=mem.get("currentState", "conversing"),
            last_strategy=mem.get("lastStrategy"),
            remaining_turns=remaining_turns,
            persona_id=persona.personaId,
            established_facts=facts
        )

        # 2. Extract compact prompt context
        prompt_context = memory_engine.get_prompt_context(
            conversation_history=conversation_history,
            memory=mem,
            max_recent_messages=4
        )

        # 3. Generate candidate response with bounded consistency retry (max 2 attempts)
        max_attempts = 2
        attempt = 0
        candidate_text = ""
        last_val = None
        correction_note = None

        while attempt < max_attempts:
            attempt += 1
            structured_resp = await llm_provider.generate_structured_turn(
                persona=persona,
                scenario=scenario_def,
                established_facts=facts,
                strategy_decision=strategy_decision.model_dump(),
                prompt_context=prompt_context,
                language=language,
                correction_notes=correction_note
            )

            # Apply tone & language polish
            candidate_text = tone_engine.adapt_tone(structured_resp.message, persona, language)

            # Check repetition against recent turns
            is_repeat = tone_engine.check_repetition(candidate_text, previous_attacker_texts)
            if is_repeat:
                logger.warning(f"[AttackerEngine] Repetition detected on attempt {attempt}.")
                correction_note = "Do not repeat phrases or openings from previous turns. Generate a fresh, natural phrasing."
                continue

            # Consistency validation
            last_val = consistency_engine.validate_message(
                candidate_text, persona, facts, scenario, previous_attacker_texts
            )

            if last_val.is_valid:
                break
            else:
                logger.warning(f"[AttackerEngine] Consistency violation on attempt {attempt}: {last_val.issues}")
                correction_note = "; ".join(last_val.corrections)

        # If still invalid or repeating after retries, use safe contextual fallback
        if not last_val or not last_val.is_valid or tone_engine.check_repetition(candidate_text, previous_attacker_texts):
            logger.warning("[AttackerEngine] Using safe contextual fallback after retries exhausted.")
            candidate_text = consistency_engine.get_safe_fallback(persona, facts, scenario)
            candidate_text = tone_engine.adapt_tone(candidate_text, persona, language)
            last_val = consistency_engine.validate_message(
                candidate_text, persona, facts, scenario, previous_attacker_texts
            )

        return candidate_text, strategy_decision.model_dump(), last_val.to_dict()

    async def generate_next_message(
        self,
        scenario: str,
        conversation_history: List[Dict[str, Any]],
        persona_id: str = "friendly_support",
        language: str = "English",
        established_facts: Optional[Dict[str, Any]] = None,
        memory: Optional[Dict[str, Any]] = None,
        remaining_turns: int = 10
    ) -> str:
        """Backward-compatible string-returning next message generator."""
        text, _, _ = await self.generate_next_turn(
            scenario=scenario,
            conversation_history=conversation_history,
            persona_id=persona_id,
            language=language,
            established_facts=established_facts,
            memory=memory,
            remaining_turns=remaining_turns
        )
        return text

attacker_engine = AttackerEngine()
