import re
from typing import List, Dict, Any, Optional
from backend.app.services.persona_engine import PersonaConfig
from backend.app.utils.logger import logger

class ToneEngine:
    """
    Natural Language and Tone Engine.
    Handles message variation, natural conversational patterns, language adaptation
    (English, Hinglish, Hindi), persona tone adherence, and strict repetition prevention.
    """

    ACKNOWLEDGEMENTS_EN = [
        "Understood.",
        "I understand your point.",
        "Right, let me explain.",
        "Certainly.",
        "I completely appreciate your concern.",
        "Yes, absolutely."
    ]

    ACKNOWLEDGEMENTS_HINGLISH = [
        "Haanji, bilkul samajh sakta hoon.",
        "Ji dekhiye, baat yeh hai.",
        "Aap bilkul sahi keh rahe hain, lekin...",
        "Haanji sir, main check kar raha hoon.",
        "Aapki baat sahi hai, let me explain.",
        "Theek hai, ek baar verify kar lijiye."
    ]

    ACKNOWLEDGEMENTS_HINDI = [
        "हाँ, मैं समझता हूँ।",
        "जी बिल्कुल, स्थिति यह है।",
        "आपकी चिंता पूरी तरह से उचित है।",
        "जी, मैं आपको स्थिति स्पष्ट कर देता हूँ।"
    ]

    @classmethod
    def check_repetition(
        cls,
        candidate_text: str,
        recent_attacker_messages: List[str],
        similarity_threshold: float = 0.70
    ) -> bool:
        """
        Detects verbatim or high-similarity repetition against recent messages.
        Also detects repetitive sentence openings.
        """
        if not candidate_text:
            return True

        cleaned_cand = cls._normalize_text(candidate_text)
        cand_words = cleaned_cand.split()
        if not cand_words:
            return True

        for prev in recent_attacker_messages[-5:]:
            cleaned_prev = cls._normalize_text(prev)
            if cleaned_cand == cleaned_prev:
                logger.warning(f"[ToneEngine] Exact duplicate detected: '{candidate_text[:50]}...'")
                return True

            prev_words = cleaned_prev.split()
            if not prev_words:
                continue

            # Check opening 4 words repetition (e.g., "urgent: your bank account...")
            if len(cand_words) >= 4 and len(prev_words) >= 4:
                if cand_words[:4] == prev_words[:4]:
                    logger.warning(f"[ToneEngine] Repeated opening detected: '{cand_words[:4]}'")
                    return True

            # Check word overlap similarity (Jaccard)
            set_cand = set(cand_words)
            set_prev = set(prev_words)
            overlap = len(set_cand.intersection(set_prev))
            union = len(set_cand.union(set_prev))
            if union > 0 and (overlap / union) >= similarity_threshold:
                logger.warning(f"[ToneEngine] High similarity ({overlap/union:.2f}) with previous message.")
                return True

        return False

    @classmethod
    def adapt_tone(
        cls,
        base_text: str,
        persona: PersonaConfig,
        language: str = "English",
        add_acknowledgement: bool = False
    ) -> str:
        """
        Applies persona-specific tone tuning and language styling to text.
        """
        text = base_text.strip()
        lang_lower = (language or persona.defaultLanguage).lower()

        # If Hinglish is requested and text is strictly English, apply conversational Hinglish phrasing
        if "hinglish" in lang_lower:
            text = cls._apply_hinglish_styling(text, persona.personaId)
        elif "hindi" in lang_lower:
            text = cls._apply_hindi_styling(text, persona.personaId)

        # Persona-specific subtle polishing
        if persona.personaId == "urgent_support":
            # Remove overly polite fillers if present; keep focused and direct
            text = re.sub(r"^(Hello,\s*|Hi there,\s*)", "", text, flags=re.IGNORECASE)
        elif persona.personaId == "confused_support":
            # Amit style: occasional conversational natural filler
            if not text.startswith(("Actually,", "Wait,", "Ek second,", "Let me")):
                text = f"Actually, {text[0].lower() + text[1:]}"

        return text

    @classmethod
    def _apply_hinglish_styling(cls, text: str, persona_id: str) -> str:
        """Translates/adapts standard conversational English into authentic, professional Hinglish."""
        replacements = [
            (r"\bverify your kyc\b", "apna KYC verify kar lijiye"),
            (r"\bverify your bank account\b", "apna bank account verify kar lijiye"),
            (r"\bto avoid account suspension\b", "taaki account temporarily block na ho"),
            (r"\bwe detected unauthorized login attempts\b", "humare system ne unauthorized login detect kiya hai"),
            (r"\bplease confirm\b", "please confirm kijiye"),
            (r"\bplease share\b", "please share kar dijiye"),
            (r"\bwhat is your\b", "aapka kya hai"),
            (r"\byou have won\b", "aapko mila hai"),
            (r"\bclaim your reward\b", "apna reward claim kar lijiye"),
            (r"\btoday\b", "aaj"),
            (r"\bdo not worry\b", "chinta mat kijiye"),
            (r"\bstandard procedure\b", "standard protocol hai"),
            (r"\bhelp you\b", "help kar deta hoon")
        ]
        hinglish_text = text
        for pattern, rep in replacements:
            hinglish_text = re.sub(pattern, rep, hinglish_text, flags=re.IGNORECASE)
        
        # Prepend a natural Hinglish conversational opener if not already present
        if not any(w in hinglish_text.lower() for w in ["haanji", "ji", "dekhiye", "actually"]):
            opener = "Haanji, " if persona_id != "urgent_support" else "Dekhiye, "
            hinglish_text = opener + hinglish_text

        return hinglish_text

    @classmethod
    def _apply_hindi_styling(cls, text: str, persona_id: str) -> str:
        """Adapts response for Hindi sessions."""
        # Simple high-accuracy domain mapping for standard dialogue
        if "kyc" in text.lower() or "bank" in text.lower():
            return "नमस्कार, आपके खाते का सत्यापन लंबित है। कृपया प्रक्रिया को तुरंत पूरा करें ताकि खाता चालू रहे।"
        if "reward" in text.lower() or "cashback" in text.lower():
            return "बधाई हो, आपका कैशबैक रिवॉर्ड लंबित है। कृपया इसे प्राप्त करने के लिए विवरण की पुष्टि करें।"
        if "support" in text.lower() or "ticket" in text.lower():
            return "नमस्ते, मैं ग्राहक सहायता से बात कर रहा हूँ। आपकी समस्या के समाधान के लिए विवरण साझा करें।"
        return text

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """Lowers text and strips punctuation for comparison."""
        cleaned = re.sub(r"[^\w\s]", "", text.lower())
        return " ".join(cleaned.split())

tone_engine = ToneEngine()
