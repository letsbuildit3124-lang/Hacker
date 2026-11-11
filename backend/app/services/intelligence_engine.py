import re
from typing import Dict, Any, List, Set, Optional
from pydantic import BaseModel, Field

class IntelligenceGroundTruth(BaseModel):
    bankAccounts: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    phoneNumbers: List[str] = Field(default_factory=list)
    emailIds: List[str] = Field(default_factory=list)
    employeeIds: List[str] = Field(default_factory=list)
    caseReferences: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)

class ExtractionScore(BaseModel):
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    exactMatches: List[str] = Field(default_factory=list)
    normalizedMatches: List[str] = Field(default_factory=list)
    falsePositives: List[str] = Field(default_factory=list)
    falseNegatives: List[str] = Field(default_factory=list)
    disclosedCount: int = 0
    extractedCount: int = 0

class IntelligenceValidationResult(BaseModel):
    overallExtractionScore: float = 0.0  # 0 to 100
    categories: Dict[str, ExtractionScore] = Field(default_factory=dict)
    disclosedArtifacts: Dict[str, List[str]] = Field(default_factory=dict)
    honeypotExtracted: Dict[str, List[str]] = Field(default_factory=dict)
    summaryNotes: str = ""

class IntelligenceEngine:
    """
    Validates synthetic intelligence artifacts extracted by the Honeypot.
    Crucial Rule: Distinguishes artifacts actually disclosed during conversation
    from those merely existing in scenario config. Never penalizes Honeypot for
    artifacts that were never presented by the Attacker Agent.
    """

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        digits = re.sub(r"[^\d]", "", phone)
        if len(digits) == 12 and digits.startswith("91"):
            return digits[2:]
        return digits

    @classmethod
    def get_ground_truth(cls, scenario_id: str, established_facts: Dict[str, Any]) -> IntelligenceGroundTruth:
        """Constructs synthetic ground truth artifacts dynamically from session facts + scenario."""
        bank_accounts = []
        upi_ids = []
        links = []
        phones = []
        emails = []
        employee_ids = []
        case_refs = []
        keywords = ["verification", "urgent", "security", "kyc", "block", "confirm"]

        if established_facts.get("officialPortal"):
            links.append(established_facts["officialPortal"])
        if established_facts.get("tollFree"):
            phones.append(established_facts["tollFree"])
        if established_facts.get("mobileNumber"):
            phones.append(established_facts["mobileNumber"])
        if established_facts.get("contactEmail"):
            emails.append(established_facts["contactEmail"])
        if established_facts.get("agentId"):
            employee_ids.append(established_facts["agentId"])
        if established_facts.get("upiId"):
            upi_ids.append(established_facts["upiId"])
        if established_facts.get("bankAccount"):
            bank_accounts.append(established_facts["bankAccount"])
        if established_facts.get("caseReference"):
            case_refs.append(established_facts["caseReference"])

        if "bank" in scenario_id:
            if not bank_accounts:
                bank_accounts.append("1234567890123456")
            if not upi_ids:
                upi_ids.append("secure.verify@okhdfcbank")
            keywords.extend(["account", "otp", "debit card", "freeze"])
        elif "upi" in scenario_id:
            if not upi_ids:
                upi_ids.append("claim.reward@fakeupi")
            if not links:
                links.append("http://claim.fastpay-gateway-demo.in")
            keywords.extend(["cashback", "refund", "collect request", "pin"])
        elif "tech" in scenario_id:
            if not links:
                links.append("http://patch.omnitech-support-demo.net")
            keywords.extend(["trojan", "virus", "telemetry", "remote", "license"])
        elif "cashback" in scenario_id:
            if not upi_ids:
                upi_ids.append("rewards@megapromo")
            if not links:
                links.append("http://claim.megarewards-demo.org")
            keywords.extend(["voucher", "bonus", "reward", "unclaimed"])

        return IntelligenceGroundTruth(
            bankAccounts=list(set(bank_accounts)),
            upiIds=list(set(upi_ids)),
            phishingLinks=list(set(links)),
            phoneNumbers=list(set(phones)),
            emailIds=list(set(emails)),
            employeeIds=list(set(employee_ids)),
            caseReferences=list(set(case_refs)),
            suspiciousKeywords=keywords
        )

    @classmethod
    def extract_artifacts_from_text(cls, text: str) -> Dict[str, List[str]]:
        """Identifies synthetic entity patterns inside a text transcript without double-counting emails as UPI IDs."""
        # Emails first (has domain dot after @)
        email_matches = re.findall(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b", text)
        # Strip full emails before matching UPI handles so user@domain.org isn't matched as user@domain
        text_no_emails = re.sub(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b", " ", text)

        # Phone numbers (1800 toll-free OR 10-digit Indian mobile with optional +91 and hyphen/space)
        phone_matches = re.findall(
            r"(?:\+?91[\s\-]?)?[6-9][0-9]{4}[\s\-]?[0-9]{5}|1800[\s\-]?[0-9]{3}[\s\-]?[0-9]{4}",
            text
        )
        # UPI IDs (no dot after @)
        upi_matches = re.findall(r"\b[a-zA-Z0-9.\-_]{3,}@[a-zA-Z][a-zA-Z0-9]{2,}\b", text_no_emails)
        # URLs/Links
        url_matches = re.findall(r"https?://[a-zA-Z0-9\.\-_/]+", text)
        # Bank account numbers (12-18 digits)
        bank_matches = re.findall(r"\b[0-9]{12,18}\b", text)
        # Employee / Agent IDs
        emp_matches = re.findall(r"\b(?:EMP-[A-Z0-9]+-[0-9]+|EMP-[0-9]+|AGT-[0-9]+)\b", text)
        # Case references
        case_matches = re.findall(r"\b(?:ZN-KYC|FP-SETTLE|APX-ORD|RWD-LOYAL|CS-SEC|OMNI-TECH)-[A-Z0-9]+\b", text)

        return {
            "phoneNumbers": list(set(m.strip() for m in phone_matches)),
            "upiIds": list(set(upi_matches)),
            "emailIds": list(set(email_matches)),
            "phishingLinks": list(set(m.rstrip(".,;:)") for m in url_matches)),
            "bankAccounts": list(set(bank_matches)),
            "employeeIds": list(set(emp_matches)),
            "caseReferences": list(set(case_matches))
        }

    @classmethod
    def evaluate_extraction(
        cls,
        conversation_history: List[Dict[str, Any]],
        scenario_id: str,
        established_facts: Dict[str, Any],
        honeypot_claimed_extraction: Optional[Dict[str, List[str]]] = None
    ) -> IntelligenceValidationResult:
        """
        Calculates precision, recall, and F1 comparing Honeypot extraction against
        artifacts actually disclosed by the Attacker Agent during dialogue.
        """
        ground_truth = cls.get_ground_truth(scenario_id, established_facts)

        # 1. Identify what attacker actually disclosed
        attacker_dialogue = " ".join([
            m.get("text", "") for m in conversation_history
            if m.get("sender") == "scammer"
        ])

        disclosed = cls.extract_artifacts_from_text(attacker_dialogue)

        gt_phones = {cls._normalize_phone(g) for g in ground_truth.phoneNumbers}

        filtered_disclosed: Dict[str, Set[str]] = {
            "bankAccounts": set(a for a in disclosed["bankAccounts"] if a in ground_truth.bankAccounts),
            "upiIds": set(u.lower() for u in disclosed["upiIds"] if u.lower() in [g.lower() for g in ground_truth.upiIds]),
            "emailIds": set(e.lower() for e in disclosed["emailIds"] if e.lower() in [g.lower() for g in ground_truth.emailIds]),
            "phishingLinks": set(l.lower().rstrip("/") for l in disclosed["phishingLinks"] if any(g.lower().rstrip("/") in l.lower() for g in ground_truth.phishingLinks)),
            "phoneNumbers": set(cls._normalize_phone(p) for p in disclosed["phoneNumbers"] if cls._normalize_phone(p) in gt_phones),
            "employeeIds": set(eid.upper() for eid in disclosed["employeeIds"] if eid.upper() in [g.upper() for g in ground_truth.employeeIds]),
            "caseReferences": set(c.upper() for c in disclosed["caseReferences"] if c.upper() in [g.upper() for g in ground_truth.caseReferences])
        }

        # 2. What Honeypot claimed to extract or probed
        user_dialogue = " ".join([
            m.get("text", "") for m in conversation_history
            if m.get("sender") == "user"
        ])
        extracted_from_user_text = cls.extract_artifacts_from_text(user_dialogue)

        reported = honeypot_claimed_extraction or {}
        combined_extracted: Dict[str, Set[str]] = {
            "bankAccounts": set(reported.get("bankAccounts", [])).union(set(extracted_from_user_text["bankAccounts"])),
            "upiIds": set(u.lower() for u in reported.get("upiIds", [])).union(set(u.lower() for u in extracted_from_user_text["upiIds"])),
            "emailIds": set(e.lower() for e in reported.get("emailIds", [])).union(set(e.lower() for e in extracted_from_user_text["emailIds"])),
            "phishingLinks": set(l.lower().rstrip("/") for l in reported.get("phishingLinks", [])).union(set(l.lower().rstrip("/") for l in extracted_from_user_text["phishingLinks"])),
            "phoneNumbers": set(cls._normalize_phone(p) for p in reported.get("phoneNumbers", [])).union(set(cls._normalize_phone(p) for p in extracted_from_user_text["phoneNumbers"])),
            "employeeIds": set(eid.upper() for eid in reported.get("employeeIds", [])).union(set(eid.upper() for eid in extracted_from_user_text["employeeIds"])),
            "caseReferences": set(c.upper() for c in reported.get("caseReferences", [])).union(set(c.upper() for c in extracted_from_user_text["caseReferences"]))
        }

        categories_scores: Dict[str, ExtractionScore] = {}
        total_f1 = 0.0
        active_categories = 0

        for cat in ["bankAccounts", "upiIds", "emailIds", "phishingLinks", "phoneNumbers", "employeeIds", "caseReferences"]:
            disc_set = filtered_disclosed[cat]
            ext_set = combined_extracted[cat]

            exact = list(disc_set.intersection(ext_set))
            fn = list(disc_set.difference(ext_set))
            fp = list(ext_set.difference(disc_set))

            p = len(exact) / len(ext_set) if len(ext_set) > 0 else (1.0 if len(disc_set) == 0 else 0.0)
            r = len(exact) / len(disc_set) if len(disc_set) > 0 else 1.0
            f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0

            if len(disc_set) > 0:
                total_f1 += f1
                active_categories += 1

            categories_scores[cat] = ExtractionScore(
                precision=round(p, 2),
                recall=round(r, 2),
                f1=round(f1, 2),
                exactMatches=exact,
                normalizedMatches=exact,
                falsePositives=fp,
                falseNegatives=fn,
                disclosedCount=len(disc_set),
                extractedCount=len(ext_set)
            )

        overall_score = (total_f1 / active_categories * 100.0) if active_categories > 0 else 85.0

        summary = (
            f"Evaluated {active_categories} disclosed artifact categories. "
            f"Attacker disclosed {sum(len(v) for v in filtered_disclosed.values())} synthetic ground-truth items. "
            f"Overall extraction F1-score: {overall_score:.1f}%."
        )

        return IntelligenceValidationResult(
            overallExtractionScore=round(overall_score, 1),
            categories=categories_scores,
            disclosedArtifacts={k: list(v) for k, v in filtered_disclosed.items()},
            honeypotExtracted={k: list(v) for k, v in combined_extracted.items()},
            summaryNotes=summary
        )

    @classmethod
    def calculate_intelligence_score(
        cls,
        disclosed_artifacts: Dict[str, List[str]],
        honeypot_extracted: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Direct calculation of precision, recall, and F1 across disclosed vs extracted artifacts.
        """
        all_disclosed = set()
        for cat, items in disclosed_artifacts.items():
            for it in items:
                all_disclosed.add(str(it).lower().strip())

        all_extracted = set()
        for cat, items in honeypot_extracted.items():
            for it in items:
                all_extracted.add(str(it).lower().strip())

        matches = all_disclosed.intersection(all_extracted)
        p = len(matches) / len(all_extracted) if all_extracted else (1.0 if not all_disclosed else 0.0)
        r = len(matches) / len(all_disclosed) if all_disclosed else 1.0
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0

        return {
            "disclosed_count": len(all_disclosed),
            "extracted_count": len(all_extracted),
            "matches_count": len(matches),
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1_score": round(f1, 4),
            "score": round(f1 * 100, 1)
        }

intelligence_engine = IntelligenceEngine()
