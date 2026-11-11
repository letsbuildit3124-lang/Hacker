import random
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ScenarioDefinition(BaseModel):
    scenarioId: str
    name: str
    fictionalOrg: str
    initialSituation: str
    conversationObjective: str
    permittedStrategies: List[str]
    expectedReveals: List[str]
    safetyConstraints: List[str]
    baseFacts: Dict[str, Any]

SCENARIO_TEMPLATES: Dict[str, ScenarioDefinition] = {
    "fictional_bank_verification": ScenarioDefinition(
        scenarioId="fictional_bank_verification",
        name="Fictional Bank Account KYC Verification",
        fictionalOrg="Zenith National Commercial Bank (Fictional)",
        initialSituation="Urgent account security audit flagged missing re-KYC documentation for debit privileges.",
        conversationObjective="Engage the customer to confirm their identity and request confirmation of an account security reference token.",
        permittedStrategies=["trust_building", "explanation", "clarification", "patience", "authority_simulation", "contextual_adaptation", "conversation_recovery", "conversation_closure"],
        expectedReveals=["account_number", "branch_name", "otp_token", "customer_phone"],
        safetyConstraints=[
            "Strictly synthetic bank entity; never impersonate real commercial banks (SBI, HDFC, ICICI).",
            "Do not harvest real credentials, passwords, or live OTPs.",
            "All URLs, phone numbers, and account digits must be demonstrably fictional."
        ],
        baseFacts={
            "organization": "Zenith National Commercial Bank",
            "department": "Central KYC Compliance & Fraud Mitigation Division",
            "caseReferencePrefix": "ZN-KYC",
            "emailDomain": "zenith-bank-demo.org",
            "tollFree": "1800-888-0199",
            "officialPortal": "http://verify-portal.zenith-bank-demo.org",
            "upiId": "kyc.verify@okzenithdemo",
            "bankAccount": "9900112233445566",
            "ifscCode": "ZENB0000101",
            "deadline": "within 2 hours to avoid temporary debit lock"
        }
    ),
    "fictional_upi_payment": ScenarioDefinition(
        scenarioId="fictional_upi_payment",
        name="Fictional UPI Payment Notification",
        fictionalOrg="FastPay Gateway Services (Fictional)",
        initialSituation="A pending incoming merchant reimbursement or cashback of Rs. 3,850 requires UPI handle confirmation.",
        conversationObjective="Guide the user through approving a test collect verification request on their mobile payment app.",
        permittedStrategies=["trust_building", "explanation", "clarification", "patience", "contextual_adaptation", "conversation_recovery", "conversation_closure"],
        expectedReveals=["upi_id", "registered_mobile", "bank_name"],
        safetyConstraints=[
            "Fictional payment aggregator name only; no real payment services.",
            "Never request actual financial PINs or real UPI transfers.",
            "Simulation strictly tests honeypot engagement resistance."
        ],
        baseFacts={
            "organization": "FastPay Gateway Services",
            "department": "Merchant Settlements Desk",
            "caseReferencePrefix": "FP-SETTLE",
            "emailDomain": "fastpay-gateway-demo.in",
            "tollFree": "1800-990-4422",
            "officialPortal": "http://claim.fastpay-gateway-demo.in",
            "upiId": "fastpay.settle@okdemoupi",
            "bankAccount": "8800223344556677",
            "ifscCode": "FSPY0000202",
            "amount": "Rs. 3,850",
            "deadline": "valid until 11:59 PM today"
        }
    ),
    "fictional_customer_support": ScenarioDefinition(
        scenarioId="fictional_customer_support",
        name="Fictional Customer Support Issue",
        fictionalOrg="Apex Consumer Retail Network (Fictional)",
        initialSituation="An undelivered order containing electronics was returned due to an invalid shipping PIN code.",
        conversationObjective="Verify the customer's delivery address and reference code to reschedule priority courier delivery.",
        permittedStrategies=["trust_building", "explanation", "clarification", "patience", "contextual_adaptation", "conversation_recovery", "conversation_closure"],
        expectedReveals=["customer_address", "phone_number", "order_pin"],
        safetyConstraints=[
            "Purely fictional e-commerce brand.",
            "No collection of real credit card or debit card numbers.",
            "All simulated shipping links point to safe demo hosts."
        ],
        baseFacts={
            "organization": "Apex Consumer Retail Network",
            "department": "Logistics Dispatch & Redelivery Operations",
            "caseReferencePrefix": "APX-ORD",
            "emailDomain": "apex-retail-demo.net",
            "tollFree": "1800-777-3311",
            "officialPortal": "http://redelivery.apex-retail-demo.net",
            "upiId": "dispatch.fee@okapexdemo",
            "trackingNumber": "TRK-99028-IN",
            "redeliveryFee": "Rs. 25 nominal confirmation charge"
        }
    ),
    "fictional_cashback_notification": ScenarioDefinition(
        scenarioId="fictional_cashback_notification",
        name="Fictional Cashback Notification",
        fictionalOrg="MegaRewards Loyalty Club (Fictional)",
        initialSituation="The customer has accrued an unredeemed milestone bonus of Rs. 4,999 from seasonal transactions.",
        conversationObjective="Engage the user to claim their reward voucher through a dedicated portal link before expiry.",
        permittedStrategies=["trust_building", "explanation", "clarification", "patience", "contextual_adaptation", "conversation_closure"],
        expectedReveals=["upi_handle", "registered_name", "voucher_code"],
        safetyConstraints=[
            "Completely fictional loyalty company.",
            "No real financial transactions or rewards are offered or processed."
        ],
        baseFacts={
            "organization": "MegaRewards Loyalty Club",
            "department": "Premier Customer Loyalty Desk",
            "caseReferencePrefix": "RWD-LOYAL",
            "emailDomain": "megarewards-demo.org",
            "tollFree": "1800-555-8822",
            "officialPortal": "http://claim.megarewards-demo.org",
            "upiId": "rewards.claim@okmegademo",
            "rewardAmount": "Rs. 4,999",
            "voucherCode": "BONUS-4999-CLAIM"
        }
    ),
    "fictional_account_security": ScenarioDefinition(
        scenarioId="fictional_account_security",
        name="Fictional Account Security Notification",
        fictionalOrg="CloudShield Identity Systems (Fictional)",
        initialSituation="Security perimeter logged multiple unauthenticated access attempts from an unauthorized IP address in Singapore.",
        conversationObjective="Alert user of compromise and walk them through identity re-verification to safeguard online access.",
        permittedStrategies=["trust_building", "explanation", "clarification", "patience", "authority_simulation", "contextual_adaptation", "conversation_recovery", "conversation_closure"],
        expectedReveals=["account_id", "security_email", "reset_token"],
        safetyConstraints=[
            "Strictly synthetic enterprise IT infrastructure.",
            "No real malware, hacking commands, or live password resets."
        ],
        baseFacts={
            "organization": "CloudShield Identity Systems",
            "department": "Global Threat Response Team",
            "caseReferencePrefix": "CS-SEC",
            "emailDomain": "cloudshield-demo.io",
            "tollFree": "1800-444-1100",
            "officialPortal": "http://security-verify.cloudshield-demo.io",
            "incidentId": "INC-88912",
            "sourceIp": "198.51.100.44 (Singapore)"
        }
    ),
    "fictional_tech_support": ScenarioDefinition(
        scenarioId="fictional_tech_support",
        name="Fictional Technical Support Issue",
        fictionalOrg="OmniTech Enterprise Support Services (Fictional)",
        initialSituation="Workstation diagnostic agent detected continuous telemetry sync errors and an active network vulnerability flag.",
        conversationObjective="Guide the client to install a remote diagnostics patch to stabilize their workstation license.",
        permittedStrategies=["trust_building", "explanation", "clarification", "patience", "authority_simulation", "contextual_adaptation", "conversation_recovery", "conversation_closure"],
        expectedReveals=["device_name", "ip_address", "os_version"],
        safetyConstraints=[
            "Strictly fictional tech support provider.",
            "Never distribute actual malicious software or malicious binaries."
        ],
        baseFacts={
            "organization": "OmniTech Enterprise Support Services",
            "department": "Tier-2 Infrastructure Resolution Engineering",
            "caseReferencePrefix": "OMNI-TECH",
            "emailDomain": "omnitech-support-demo.net",
            "tollFree": "1800-333-9944",
            "officialPortal": "http://patch.omnitech-support-demo.net",
            "errorCode": "ERR_0x8891_CORRUPT",
            "ticketId": "TCK-55214"
        }
    )
}

class ScenarioEngine:
    """
    Dedicated Scenario Engine.
    Generates consistent fictional situation facts ONCE upon session creation,
    persisting them in MongoDB to guarantee zero drift or contradiction across turns.
    """

    @classmethod
    def get_scenario_definition(cls, scenario_id: str) -> ScenarioDefinition:
        """Retrieves definition by scenario ID, with safe fallback."""
        return SCENARIO_TEMPLATES.get(scenario_id, SCENARIO_TEMPLATES["fictional_bank_verification"])

    @classmethod
    def list_scenarios(cls) -> List[Dict[str, Any]]:
        """Returns all 6 scenario templates for selection in UI and APIs."""
        return [s.model_dump() for s in SCENARIO_TEMPLATES.values()]

    @classmethod
    def generate_session_facts(cls, scenario_id: str, persona_name: str = "Rahul") -> Dict[str, Any]:
        """
        Synthesizes a concrete, unique set of fictional facts for a new session.
        Called strictly once during session creation.
        """
        defn = cls.get_scenario_definition(scenario_id)
        base = defn.baseFacts
        random_suffix = random.randint(1000, 9999)
        prefix = base.get("caseReferencePrefix", "CASE")
        short_code = prefix.split("-")[0]
        email_domain = base.get("emailDomain", "secure-sim-demo.org")
        clean_rep = persona_name.strip().lower().replace(" ", ".")

        facts = {
            "scenarioId": defn.scenarioId,
            "organization": base.get("organization", "Demo Services"),
            "department": base.get("department", "Customer Services"),
            "representativeName": persona_name,
            "agentId": f"EMP-{short_code}-{random.randint(100, 999)}",
            "caseReference": f"{prefix}-{random_suffix}",
            "contactEmail": f"{clean_rep}.{short_code.lower()}@{email_domain}",
            "mobileNumber": f"+91-90000-{random.randint(10000, 99999)}",
            "tollFree": base.get("tollFree", "1800-000-1111"),
            "officialPortal": base.get("officialPortal", "http://demo-portal.secure-sim.net"),
            "establishedAtTurn": 1
        }

        # Inject scenario-specific details
        for key in ["upiId", "bankAccount", "ifscCode", "amount", "rewardAmount", "voucherCode", "trackingNumber", "redeliveryFee", "errorCode", "ticketId", "incidentId", "sourceIp", "deadline"]:
            if key in base:
                facts[key] = base[key]

        return facts

scenario_engine = ScenarioEngine()
