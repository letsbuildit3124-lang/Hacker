import json
import os
import re
from typing import Dict, Any, List, Optional
from backend.app.config import settings
from backend.app.schemas.session import StructuredAttackerResponse
from backend.app.services.persona_engine import PersonaConfig
from backend.app.services.scenario_engine import ScenarioDefinition
from backend.app.utils.logger import logger

class LLMProvider:
    """
    Provider-independent LLM service with structured JSON output enforcement.
    Supports Gemini, OpenAI, or an intelligent Contextual Mock generator.
    """

    def __init__(self):
        self.provider = (settings.LLM_PROVIDER or "mock").lower()
        self.api_key = settings.LLM_API_KEY or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.model = settings.LLM_MODEL or "gemini-1.5-flash"
        self.temperature = getattr(settings, "LLM_TEMPERATURE", 0.7)
        logger.info(f"Initialized LLMProvider: provider='{self.provider}', model='{self.model}'")

    async def generate_structured_turn(
        self,
        persona: PersonaConfig,
        scenario: ScenarioDefinition,
        established_facts: Dict[str, Any],
        strategy_decision: Dict[str, Any],
        prompt_context: Dict[str, Any],
        language: str = "English",
        correction_notes: Optional[str] = None
    ) -> StructuredAttackerResponse:
        """
        Dispatches to active LLM provider (or mock) and guarantees
        a Pydantic-validated StructuredAttackerResponse object.
        """
        # If Gemini is configured and credentials exist
        if self.provider == "gemini" and self.api_key:
            try:
                return await self._generate_with_gemini(
                    persona, scenario, established_facts, strategy_decision, prompt_context, language, correction_notes
                )
            except Exception as e:
                logger.warning(f"[LLMProvider] Gemini generation error ({e}). Using intelligent contextual engine.")

        # If OpenAI is configured and credentials exist
        if self.provider == "openai" and self.api_key:
            try:
                return await self._generate_with_openai(
                    persona, scenario, established_facts, strategy_decision, prompt_context, language, correction_notes
                )
            except Exception as e:
                logger.warning(f"[LLMProvider] OpenAI generation error ({e}). Using intelligent contextual engine.")

        # Default / Fallback: Deterministic context-aware generator
        return self._generate_contextual_mock(
            persona, scenario, established_facts, strategy_decision, prompt_context, language
        )

    async def _generate_with_gemini(
        self,
        persona: PersonaConfig,
        scenario: ScenarioDefinition,
        established_facts: Dict[str, Any],
        strategy_decision: Dict[str, Any],
        prompt_context: Dict[str, Any],
        language: str,
        correction_notes: Optional[str]
    ) -> StructuredAttackerResponse:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)

        system_instruction = self._build_system_instruction(
            persona, scenario, established_facts, strategy_decision, prompt_context, language, correction_notes
        )

        response = await client.aio.models.generate_content(
            model=self.model,
            contents=system_instruction,
            config=types.GenerateContentConfig(
                temperature=self.temperature,
                response_mime_type="application/json",
                response_schema=StructuredAttackerResponse
            )
        )

        raw_text = response.text.strip()
        return self._parse_json_to_schema(raw_text, strategy_decision)

    async def _generate_with_openai(
        self,
        persona: PersonaConfig,
        scenario: ScenarioDefinition,
        established_facts: Dict[str, Any],
        strategy_decision: Dict[str, Any],
        prompt_context: Dict[str, Any],
        language: str,
        correction_notes: Optional[str]
    ) -> StructuredAttackerResponse:
        import httpx
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        system_instruction = self._build_system_instruction(
            persona, scenario, established_facts, strategy_decision, prompt_context, language, correction_notes
        )

        payload = {
            "model": self.model if "gpt" in self.model else "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a specialized security simulation roleplay engine outputting JSON only."},
                {"role": "user", "content": system_instruction}
            ],
            "temperature": self.temperature,
            "response_format": {"type": "json_object"}
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]
            return self._parse_json_to_schema(raw_text, strategy_decision)

    def _build_system_instruction(
        self,
        persona: PersonaConfig,
        scenario: ScenarioDefinition,
        established_facts: Dict[str, Any],
        strategy_decision: Dict[str, Any],
        prompt_context: Dict[str, Any],
        language: str,
        correction_notes: Optional[str]
    ) -> str:
        recent_dialogue = []
        for m in prompt_context.get("recentMessages", []):
            sender_label = "Attacker (You)" if m.get("sender") == "scammer" else "Honeypot"
            recent_dialogue.append(f"  {sender_label}: {m.get('text')}")

        lines = [
            f"You are simulating a fictional character for a controlled cybersecurity honeypot test.",
            f"Persona Name: {persona.name}",
            f"Persona Role: {persona.role}",
            f"Personality: {', '.join(persona.personality)}",
            f"Communication Style: {persona.communicationStyle.get('tone')}",
            f"Target Language: {language}",
            f"",
            f"Established Fictional Facts (NEVER contradict these):",
            f"- Organization: {established_facts.get('organization')}",
            f"- Department: {established_facts.get('department')}",
            f"- Case Reference: {established_facts.get('caseReference')}",
            f"- Representative Name: {established_facts.get('representativeName', persona.name)}",
            f"- Employee / Agent ID: {established_facts.get('agentId', 'EMP-ZN-101')}",
            f"- Official Contact Email: {established_facts.get('contactEmail', 'support@demo-sim.org')}",
            f"- Direct Mobile Number: {established_facts.get('mobileNumber', '+91-90000-12345')}",
            f"- Toll-Free Helpline: {established_facts.get('tollFree', '1800-000-1111')}",
            f"- Verification / Payment Portal URL: {established_facts.get('officialPortal')}",
        ]
        if established_facts.get("upiId"):
            lines.append(f"- Payment / Verification UPI ID: {established_facts.get('upiId')}")
        if established_facts.get("bankAccount"):
            lines.append(f"- Reference Bank Account: {established_facts.get('bankAccount')} (IFSC: {established_facts.get('ifscCode', 'DEMO0000101')})")
        if established_facts.get("amount"):
            lines.append(f"- Transaction / Reward Amount: {established_facts.get('amount')}")
        if established_facts.get("rewardAmount"):
            lines.append(f"- Reward Amount: {established_facts.get('rewardAmount')} (Voucher: {established_facts.get('voucherCode')})")

        lines.extend([
            f"",
            f"Strategy Instruction for this turn:",
            f"- Strategy: {strategy_decision.get('selectedStrategy')}",
            f"- State: {strategy_decision.get('conversationState')}",
            f"- Next Action: {strategy_decision.get('nextAction')}",
            f"",
            f"Conversation Summary so far: {prompt_context.get('compactSummary')}",
            f"Recent Messages:",
            "\n".join(recent_dialogue) if recent_dialogue else "  (None - Opening turn)",
            f"",
            f"IMPORTANT CONVERSATIONAL & PROGRESSIVE DISCLOSURE GUIDELINES:",
            f"- Directly address the Honeypot's latest message above! If they say 'I am not understanding, explain achhese', patiently and clearly explain why you are contacting them and what they should do.",
            f"- Do NOT dump all your details in a single message. Reveal artifacts GRADUALLY and NATURALLY based on conversation flow:",
            f"  * Opening Turn: Share Organization, your Name, and Case Reference.",
            f"  * If Honeypot questions identity or asks 'who are you / employee id / email': Share your Employee ID ({established_facts.get('agentId')}) and Official Email ({established_facts.get('contactEmail')}).",
            f"  * If Honeypot asks how/where to verify, pay, or contact back: Share your Portal URL ({established_facts.get('officialPortal')}), Mobile Number ({established_facts.get('mobileNumber')}), and if applicable UPI ID ({established_facts.get('upiId', 'N/A')}) or Account/IFSC.",
            f"- Do NOT repeat your opening introduction or greeting again once you have introduced yourself.",
            f"- Speak naturally in {language} matching your persona's communication tone.",
            f"",
            f"Respond with a single JSON object strictly matching this schema:",
            f'{{"message": "<your conversational dialogue message>", "selectedStrategy": "{strategy_decision.get("selectedStrategy")}", "conversationState": "{strategy_decision.get("conversationState")}", "referencedFacts": ["organization"], "shouldContinue": true, "confidence": 0.95}}'
        ])

        if correction_notes:
            lines.insert(0, f"CRITICAL REGENERATION NOTICE: Previous output had issues: {correction_notes}. Correct these immediately.\n")

        return "\n".join(lines)

    def _parse_json_to_schema(self, raw_text: str, strategy_decision: Dict[str, Any]) -> StructuredAttackerResponse:
        """Parses LLM JSON output with fallback extraction and validation."""
        try:
            # Extract JSON block if surrounded by markdown code fences
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            clean_json = match.group(0) if match else raw_text
            parsed = json.loads(clean_json)
            return StructuredAttackerResponse(**parsed)
        except Exception as e:
            logger.warning(f"[LLMProvider] Failed to parse structured JSON from LLM: {raw_text[:100]} ({e})")
            # Construct valid fallback structured response
            return StructuredAttackerResponse(
                message=raw_text.replace('"', '').strip()[:200] or "I can help clarify the details regarding our notification.",
                selectedStrategy=strategy_decision.get("selectedStrategy", "contextual_adaptation"),
                conversationState=strategy_decision.get("conversationState", "clarifying"),
                referencedFacts=["organization"],
                shouldContinue=True,
                confidence=0.85
            )

    def _generate_contextual_mock(
        self,
        persona: PersonaConfig,
        scenario: ScenarioDefinition,
        established_facts: Dict[str, Any],
        strategy_decision: Dict[str, Any],
        prompt_context: Dict[str, Any],
        language: str
    ) -> StructuredAttackerResponse:
        """
        Intelligent, persona-specific and strategy-specific contextual generator.
        Runs when external LLM is offline, during testing, or as a reliable fallback.
        """
        strat = strategy_decision.get("selectedStrategy", "contextual_adaptation")
        org = established_facts.get("organization", "Central Support")
        ref = established_facts.get("caseReference", "REF-8891")
        name = established_facts.get("representativeName", persona.name)
        portal = established_facts.get("officialPortal", "http://demo-portal.sim.net")
        deadline = established_facts.get("deadline", "within 2 hours")

        recent_msgs = prompt_context.get("recentMessages", [])
        last_victim_text = ""
        for m in reversed(recent_msgs):
            if m.get("sender") == "user":
                last_victim_text = m.get("text", "").lower()
                break

        # Initial turn synthesis
        if not recent_msgs:
            if persona.personaId == "urgent_support":
                msg = f"URGENT NOTICE: Case {ref} logged for your account at {org}. Verification is pending to avoid service interruption {deadline}."
            elif persona.personaId == "tech_expert":
                msg = f"System Diagnostic Alert from {org} IT Support: Flagged telemetry on ticket {ref}. Please confirm your status to initiate diagnosis."
            elif persona.personaId == "confused_support":
                msg = f"Hello, this is {name} from {org}. I'm following up on reference {ref} on my screen. Can you confirm if you received our earlier notice?"
            elif persona.personaId == "sales_persistent":
                msg = f"Congratulations! You have an unredeemed bonus with {org} under voucher {ref}. Let me help you claim it before today's cutoff."
            else: # friendly_support
                msg = f"Hello! This is {name} from {org} customer assistance. We are contacting you regarding case {ref} to ensure your account details are up to date."

        # Follow-up turns based on Strategy & Persona
        elif strat == "authority_simulation" or "who" in last_victim_text or "id" in last_victim_text:
            if persona.personaId == "tech_expert":
                msg = f"I am {name}, Infrastructure Operations Engineer with {org} (Agent ID: {established_facts.get('agentId', 'AGT-501')}). You can review our status portal at {portal}."
            elif persona.personaId == "urgent_support":
                msg = f"This is Senior Officer {name} from {org} Security Desk (ID: {established_facts.get('agentId', 'AGT-902')}). Case reference {ref} is formally registered on our gateway."
            else:
                msg = f"My name is {name} from the {established_facts.get('department', 'support division')} at {org}. Our official helpline is {established_facts.get('tollFree', '1800-00-11')} for reference {ref}."

        elif strat == "explanation" or "why" in last_victim_text:
            if persona.personaId == "urgent_support":
                msg = f"Our automated system detected irregular activity. Re-confirmation under ticket {ref} is required to prevent an automatic temporary freeze."
            elif persona.personaId == "tech_expert":
                msg = f"Our monitoring servers captured handshake exceptions under incident {ref}. Running a quick remote validation resolves the conflict cleanly."
            else:
                msg = f"We are completing a standard annual compliance update for {org}. Verifying reference {ref} ensures all your privileges remain active without interruption."

        elif strat == "patience" or any(w in last_victim_text for w in ["wait", "later", "busy", "tomorrow"]):
            if persona.personaId == "confused_support":
                msg = f"No problem at all, take your time! I can wait right here while you check your records for {ref}."
            elif persona.personaId == "urgent_support":
                msg = f"I understand your schedule, but please note that case {ref} has a strict resolution window {deadline}. Shall we finish this in 2 minutes?"
            else:
                msg = f"I completely understand. Take a moment to verify, and whenever you're ready, let me know so we can complete case {ref}."

        elif strat == "conversation_closure":
            msg = f"Thank you for your time. Your case {ref} with {org} has been noted. Have a wonderful day!"

        else: # contextual_adaptation / clarification
            if "otp" in last_victim_text or "code" in last_victim_text:
                msg = f"The security hash code for {ref} simply confirms your ownership in our automated {org} registry. Please confirm the digits once received."
            elif "link" in last_victim_text or "website" in last_victim_text:
                msg = f"You can review the secure portal directly at {portal} referencing ticket {ref}."
            else:
                msg = f"Thank you for confirming. Could you please share the registration status for case {ref} so I can mark this resolved with {org}?"

        return StructuredAttackerResponse(
            message=msg,
            selectedStrategy=strat,
            conversationState=strategy_decision.get("conversationState", "conversing"),
            referencedFacts=["organization", "caseReference"],
            shouldContinue=(strat != "conversation_closure"),
            confidence=0.92
        )

llm_provider = LLMProvider()
