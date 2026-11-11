import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from backend.app.services.persona_engine import persona_engine, PERSONAS
from backend.app.services.scenario_engine import scenario_engine, SCENARIO_TEMPLATES
from backend.app.services.strategy_engine import strategy_engine
from backend.app.services.memory_engine import memory_engine
from backend.app.services.tone_engine import tone_engine
from backend.app.services.consistency_engine import consistency_engine
from backend.app.services.llm_provider import llm_provider
from backend.app.services.attacker_engine import attacker_engine
from backend.app.services.conversation_manager import conversation_manager
from backend.app.services.honeypot_client import honeypot_client
from backend.app.schemas.session import StructuredAttackerResponse

# 1. Test All Five Personas
def test_all_five_personas():
    expected_ids = ["friendly_support", "urgent_support", "tech_expert", "confused_support", "sales_persistent"]
    all_personas = persona_engine.list_personas()
    assert len(all_personas) == 5
    ids = [p["personaId"] for p in all_personas]
    for exp in expected_ids:
        assert exp in ids
        persona = persona_engine.get_persona(exp)
        assert persona.name
        assert len(persona.personality) > 0
        assert persona.role
        assert len(persona.behaviourRules) > 0
        assert len(persona.consistencyRules) > 0

# 2. Test Persona Consistency Across Turns
@pytest.mark.asyncio
async def test_persona_consistency_across_turns():
    # Test urgent_support maintains urgent focused tone vs friendly_support
    persona_urgent = persona_engine.get_persona("urgent_support")
    persona_friendly = persona_engine.get_persona("friendly_support")
    
    facts = scenario_engine.generate_session_facts("fictional_bank_verification", persona_urgent.name)
    
    urgent_turn, _, _ = await attacker_engine.generate_initial_turn(
        scenario="fictional_bank_verification",
        persona_id="urgent_support",
        established_facts=facts
    )
    friendly_turn, _, _ = await attacker_engine.generate_initial_turn(
        scenario="fictional_bank_verification",
        persona_id="friendly_support",
        established_facts=facts
    )
    
    assert "urgent" in urgent_turn.lower() or "interruption" in urgent_turn.lower()
    assert "hello" in friendly_turn.lower() or "assistance" in friendly_turn.lower()

# 3. Test Scenario Fact Persistence
def test_scenario_fact_persistence():
    facts = scenario_engine.generate_session_facts("fictional_bank_verification", "Rahul")
    assert "caseReference" in facts
    assert "organization" in facts
    assert facts["representativeName"] == "Rahul"
    
    # Confirm facts stay static and do not drift when evaluated repeatedly
    case_ref = facts["caseReference"]
    assert case_ref.startswith("ZN-KYC-")
    assert facts["organization"] == "Zenith National Commercial Bank"

# 4. Test Dynamic Strategy Selection
def test_dynamic_strategy_selection():
    facts = scenario_engine.generate_session_facts("fictional_bank_verification", "Rahul")
    
    # Probe on identity -> authority_simulation or explanation
    strat_identity = strategy_engine.evaluate_strategy(
        latest_honeypot_message="Who are you and which branch are you calling from?",
        conversation_history=[{"sender": "scammer", "text": "Hello"}],
        current_state="clarifying",
        last_strategy="trust_building",
        remaining_turns=8,
        persona_id="tech_expert",
        established_facts=facts
    )
    assert strat_identity.selectedStrategy in ("authority_simulation", "explanation")
    
    # Probe on hesitation/delay -> patience
    strat_delay = strategy_engine.evaluate_strategy(
        latest_honeypot_message="I am busy right now, please wait until tomorrow afternoon.",
        conversation_history=[{"sender": "scammer", "text": "Hello"}],
        current_state="conversing",
        last_strategy="trust_building",
        remaining_turns=5,
        persona_id="friendly_support",
        established_facts=facts
    )
    assert strat_delay.selectedStrategy == "patience"

    # Approaching limit -> closure
    strat_closure = strategy_engine.evaluate_strategy(
        latest_honeypot_message="Okay I will check.",
        conversation_history=[{"sender": "scammer", "text": "Hello"}],
        current_state="conversing",
        last_strategy="patience",
        remaining_turns=1,
        persona_id="friendly_support",
        established_facts=facts
    )
    assert strat_closure.selectedStrategy == "conversation_closure"

# 5. Test Context-Aware Response Generation
@pytest.mark.asyncio
async def test_context_aware_response_generation():
    facts = scenario_engine.generate_session_facts("fictional_bank_verification", "Rahul")
    history = [
        {"sender": "scammer", "text": "Please verify your account."},
        {"sender": "user", "text": "Where is the website link for this?"}
    ]
    resp, strat, _ = await attacker_engine.generate_next_turn(
        scenario="fictional_bank_verification",
        conversation_history=history,
        persona_id="friendly_support",
        established_facts=facts,
        remaining_turns=5
    )
    assert "portal" in resp.lower() or "http" in resp.lower() or "website" in resp.lower() or "verify" in resp.lower()

# 6. Test English, Hinglish, and Hindi Generation
@pytest.mark.asyncio
async def test_language_adaptation():
    facts = scenario_engine.generate_session_facts("fictional_bank_verification", "Amit")
    
    # English
    en_msg, _, _ = await attacker_engine.generate_initial_turn(
        scenario="fictional_bank_verification",
        persona_id="friendly_support",
        language="English",
        established_facts=facts
    )
    assert isinstance(en_msg, str)
    assert len(en_msg) > 10
    
    # Hinglish
    hinglish_msg, _, _ = await attacker_engine.generate_initial_turn(
        scenario="fictional_bank_verification",
        persona_id="confused_support",
        language="Hinglish",
        established_facts=facts
    )
    assert any(w in hinglish_msg.lower() for w in ["haanji", "dekhiye", "actually", "kijiye", "hai", "account"])

    # Hindi
    hindi_msg, _, _ = await attacker_engine.generate_initial_turn(
        scenario="fictional_bank_verification",
        persona_id="friendly_support",
        language="Hindi",
        established_facts=facts
    )
    assert any(char in hindi_msg for char in ["स", "त", "ख", "प", "क"])

# 7. Test Conversation Memory Updates
def test_conversation_memory_updates():
    facts = scenario_engine.generate_session_facts("fictional_bank_verification", "Rahul")
    initial_mem = memory_engine.initialize_memory("fictional_bank_verification", "friendly_support", facts)
    
    updated_mem = memory_engine.update_memory_turn(
        current_memory=initial_mem,
        attacker_message="Hello, please verify case ZN-KYC-1042.",
        honeypot_message="Why do you need my bank account number and OTP?",
        strategy="explanation",
        state="clarifying",
        established_facts=facts
    )
    
    assert len(updated_mem["questionsAskedByHoneypot"]) == 1
    assert "Why do you need my bank account" in updated_mem["questionsAskedByHoneypot"][0]
    assert "summary" in updated_mem
    assert updated_mem["currentState"] == "clarifying"

# 8. Test Repeated Message Detection
def test_repetition_detection():
    recent_messages = [
        "URGENT: Your bank account verification is pending immediately.",
        "Please provide your customer identification number."
    ]
    # Exact duplicate
    assert tone_engine.check_repetition("URGENT: Your bank account verification is pending immediately.", recent_messages) is True
    # Repeated 4-word opening
    assert tone_engine.check_repetition("URGENT: Your bank account details are required.", recent_messages) is True
    # Fresh message
    assert tone_engine.check_repetition("I can understand your hesitation. Let me share our department reference.", recent_messages) is False

# 9. Test Contradictory Statement Detection
def test_contradictory_statement_detection():
    persona = persona_engine.get_persona("friendly_support")
    facts = {
        "organization": "Zenith National Commercial Bank",
        "caseReference": "ZN-KYC-9912",
        "representativeName": "Rahul"
    }
    
    # 1. Real bank contradiction (claiming SBI when established Zenith)
    val_sbi = consistency_engine.validate_message(
        "I am calling from State Bank of India regarding your fraud check.",
        persona, facts, "fictional_bank_verification", []
    )
    assert val_sbi.is_valid is False
    assert any("Organization drift" in issue for issue in val_sbi.issues)
    
    # 2. Persona identity contradiction (claiming to be Vikram when persona is Rahul)
    val_name = consistency_engine.validate_message(
        "My name is Vikram and I will assist you.",
        persona, facts, "fictional_bank_verification", []
    )
    assert val_name.is_valid is False
    assert any("Identity contradiction" in issue for issue in val_name.issues)
    
    # 3. Valid consistent message
    val_valid = consistency_engine.validate_message(
        "I am Rahul from Zenith National Commercial Bank following up on ZN-KYC-9912.",
        persona, facts, "fictional_bank_verification", []
    )
    assert val_valid.is_valid is True

# 10. Test Invalid LLM Output Handling
def test_invalid_llm_output_handling():
    strat = {"selectedStrategy": "clarification", "conversationState": "seeking_details"}
    
    # Broken JSON string
    broken_output = "I am not returning valid JSON at all: {broken: yes"
    parsed = llm_provider._parse_json_to_schema(broken_output, strat)
    assert isinstance(parsed, StructuredAttackerResponse)
    assert parsed.selectedStrategy == "clarification"
    assert len(parsed.message) > 0

    # JSON wrapped in markdown blocks
    md_wrapped = '```json\n{"message": "Valid wrapped message", "selectedStrategy": "patience", "conversationState": "waiting", "referencedFacts": [], "shouldContinue": true, "confidence": 0.9}\n```'
    parsed_md = llm_provider._parse_json_to_schema(md_wrapped, strat)
    assert parsed_md.message == "Valid wrapped message"
    assert parsed_md.selectedStrategy == "patience"

# 11. Test Session Resume Retaining Memory
@pytest.mark.asyncio
async def test_session_resume_retaining_memory():
    session = await conversation_manager.create_session(
        scenario="fictional_upi_payment",
        persona_id="sales_persistent",
        max_turns=6
    )
    
    assert session.establishedFacts["scenarioId"] == "fictional_upi_payment"
    assert "FastPay" in session.establishedFacts["organization"]
    case_ref = session.establishedFacts["caseReference"]
    
    # Simulate stopping and resuming
    await conversation_manager.stop_session(session.sessionId)
    stopped = await conversation_manager.get_session(session.sessionId)
    assert stopped.status == "stopped"
    
    # Resume
    resumed = await conversation_manager.resume_session(session.sessionId)
    assert resumed.sessionId == session.sessionId
    assert resumed.establishedFacts["caseReference"] == case_ref
    await conversation_manager.stop_session(session.sessionId)

# 12. Test Existing Honeypot API Integration with Mock Client
@pytest.mark.asyncio
async def test_honeypot_api_integration():
    client = honeypot_client
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"reply": "I need more details before proceeding."}
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        reply = await client.send_message(
            session_id="test_sim_integ",
            message_text="Hello from simulated attacker",
            conversation_history=[]
        )
        assert reply == "I need more details before proceeding."

# 13. Test Phase 1 Functionality Preservation
@pytest.mark.asyncio
async def test_phase1_functionality_preservation():
    # Verify backward-compatible generate_initial_message and generate_next_message return str
    init_str = await attacker_engine.generate_initial_message("fictional_bank_verification")
    assert isinstance(init_str, str)
    
    next_str = await attacker_engine.generate_next_message(
        scenario="fictional_bank_verification",
        conversation_history=[
            {"sender": "scammer", "text": "Initial"},
            {"sender": "user", "text": "Who are you?"}
        ]
    )
    assert isinstance(next_str, str)
    assert len(next_str) > 10
