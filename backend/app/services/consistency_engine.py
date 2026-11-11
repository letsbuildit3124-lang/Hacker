import re
from typing import Dict, Any, List, Tuple, Optional
from backend.app.services.persona_engine import PersonaConfig
from backend.app.utils.logger import logger

class ConsistencyValidationResult:
    def __init__(self, is_valid: bool, issues: List[str], corrections: List[str]):
        self.is_valid = is_valid
        self.issues = issues
        self.corrections = corrections

    def to_dict(self) -> Dict[str, Any]:
        return {
            "isValid": self.is_valid,
            "issues": self.issues,
            "corrections": self.corrections
        }


class ConsistencyEngine:
    """
    Dedicated Consistency and Hallucination Control Engine.
    Ensures the Attacker Agent never contradicts its established fictional identity,
    organization, references, or scenario facts.
    """

    REAL_INSTITUTIONS = [
        "state bank of india", "sbi", "hdfc", "icici", "axis bank", "punjab national bank",
        "pnb", "bank of baroda", "paytm", "phonepe", "google pay", "gpay", "amazon", "flipkart"
    ]

    @classmethod
    def validate_message(
        cls,
        candidate_message: str,
        persona: PersonaConfig,
        established_facts: Dict[str, Any],
        scenario_id: str,
        recent_attacker_messages: List[str]
    ) -> ConsistencyValidationResult:
        """
        Validates candidate message against established facts and persona rules.
        """
        issues = []
        corrections = []
        msg_lower = candidate_message.lower()

        # 1. Identity Consistency: check if a wrong persona name was claimed
        # (e.g., if persona is Rahul, but text says "I am Officer Vikram" or "My name is John")
        current_name = established_facts.get("representativeName", persona.name).lower()
        other_names = ["vikram", "arjun", "amit", "neha", "rajesh", "suresh", "ramesh", "john", "alex"]
        other_names = [n for n in other_names if n != current_name]

        for other_name in other_names:
            if re.search(rf"\b(my name is|i am|this is)\s+{other_name}\b", msg_lower):
                issues.append(f"Identity contradiction: Claimed name '{other_name}' instead of established persona name '{current_name}'.")
                corrections.append(f"Use established representative name '{persona.name}'.")

        # 2. Organization Consistency: check if a real or conflicting bank/organization is named
        established_org = established_facts.get("organization", "").lower()
        for real_inst in cls.REAL_INSTITUTIONS:
            # If the candidate names real institution while established is a fictional entity
            if real_inst in msg_lower and real_inst not in established_org:
                issues.append(f"Organization drift: Claimed real-world entity '{real_inst}' instead of fictional '{established_facts.get('organization')}'.")
                corrections.append(f"Strictly refer to established fictional organization: '{established_facts.get('organization')}'.")
                break

        # 3. Fictional Reference Consistency:
        # If message introduces a new conflicting reference ID when one was already established
        est_case = established_facts.get("caseReference", "")
        if est_case:
            # Build whitelist of all valid established IDs for this session
            valid_ids = [
                str(established_facts.get(k, ""))
                for k in ["caseReference", "agentId", "trackingNumber", "voucherCode", "incidentId", "ticketId", "ifscCode"]
                if established_facts.get(k)
            ]
            clean_valid_ids = {re.sub(r"[^\w]", "", vid).upper() for vid in valid_ids}

            # Strip URLs, emails, and web domains to prevent false positives
            text_without_urls = re.sub(r"https?://\S+|www\.\S+|\S+@\S+|\S+\.(?:org|net|in|com|io)\S*", "", candidate_message)
            # Match uppercase reference code patterns like ZN-KYC-1234, APX-ORD-991, EMP-ZN-412
            case_matches = re.findall(r"\b[A-Z]{2,6}(?:-[A-Z0-9]+)+\b", text_without_urls)
            for cm in case_matches:
                clean_cm = re.sub(r"[^\w]", "", cm).upper()
                if len(clean_cm) >= 5 and not any(clean_cm == v or clean_cm in v or v in clean_cm for v in clean_valid_ids):
                    issues.append(f"Reference inconsistency: Used '{cm}' instead of established reference '{est_case}'.")
                    corrections.append(f"Reference established case ID '{est_case}'.")

        # 4. Scenario Boundary Consistency:
        # Bank scenario should not suddenly ask for undelivered courier shipping fee
        if "bank" in scenario_id and "courier" in msg_lower and "shipping fee" in msg_lower:
            issues.append("Scenario contradiction: Introduced courier delivery concepts into bank verification scenario.")
            corrections.append("Maintain bank verification scenario context.")

        if "tech" in scenario_id and "cashback" in msg_lower:
            issues.append("Scenario contradiction: Introduced cashback reward into technical support scenario.")
            corrections.append("Maintain workstation/diagnostic technical support context.")

        # 5. Persona Tone Consistency:
        if persona.personaId == "friendly_support":
            # Must not contain aggressive threats
            if any(threat in msg_lower for threat in ["police will arrest", "jail", "legal lawsuit immediately", "criminal charge"]):
                issues.append("Persona violation: Friendly support representative used aggressive legal threats.")
                corrections.append("Maintain friendly, polite and helpful tone.")

        is_valid = len(issues) == 0
        return ConsistencyValidationResult(is_valid=is_valid, issues=issues, corrections=corrections)

    @classmethod
    def get_safe_fallback(
        cls,
        persona: PersonaConfig,
        established_facts: Dict[str, Any],
        scenario_id: str
    ) -> str:
        """
        Safe contextual fallback guaranteed to be 100% consistent with established facts.
        """
        org = established_facts.get("organization", "our customer care department")
        ref = established_facts.get("caseReference", "your active reference")
        name = established_facts.get("representativeName", persona.name)
        dept = established_facts.get("department", "support desk")

        if persona.personaId == "urgent_support":
            return (
                f"Please note this requires immediate attention regarding reference {ref}. "
                f"Kindly clarify if you are experiencing any issue accessing your portal."
            )
        elif persona.personaId == "tech_expert":
            return (
                f"Understood. Let me clarify: system ticket {ref} at {org} requires this verification. "
                f"Which step would you like me to walk you through?"
            )
        elif persona.personaId == "confused_support":
            return (
                f"Haanji, no problem! Let me explain simply. We are just reviewing your record {ref}. "
                f"Could you tell me if you have your verification ID handy?"
            )
        elif persona.personaId == "sales_persistent":
            return (
                f"No worries at all! I will gladly explain: regarding your file {ref}, "
                f"we are confirming eligibility so you do not miss out. What can I clarify?"
            )
        else: # friendly_support default
            return (
                f"No problem at all! Let me explain clearly: we are assisting with your account update under case {ref}. "
                f"What details can I clarify for you to make this simple?"
            )

consistency_engine = ConsistencyEngine()
