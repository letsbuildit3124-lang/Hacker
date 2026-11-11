import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from backend.app.services.response_adapter import (
    ResponseAdapter,
    UninterpretableResponseError,
    HoneypotAPIError
)
from backend.app.services.honeypot_client import HoneypotClient
from backend.app.services.attacker_engine import AttackerEngine
from backend.app.services.conversation_manager import ConversationManager
from backend.app.models.message import Message

@pytest.fixture
def test_conversation_manager():
    return ConversationManager()

@pytest.fixture
def attacker_engine():
    return AttackerEngine()

# Test 1: Successful Honeypot API communication & Response Parsing
@pytest.mark.asyncio
async def test_successful_honeypot_api_communication():
    client = HoneypotClient(base_url="https://mock-honeypot.local", api_key="test_key")
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "success",
        "reply": "Why do you need my bank account verification? Which branch are you calling from?"
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        reply = await client.send_message(
            session_id="sim_test_001",
            message_text="Your bank account is pending verification.",
            conversation_history=[]
        )
        assert "Why do you need my bank account" in reply
        assert mock_post.called
        # Verify headers
        call_headers = mock_post.call_args[1]["headers"]
        assert call_headers["x-api-key"] == "test_key"
        assert call_headers["Content-Type"] == "application/json"


# Test 2: Initial attacker message submission
@pytest.mark.asyncio
async def test_initial_attacker_message_submission(attacker_engine):
    initial_msg = await attacker_engine.generate_initial_message("fictional_bank_verification")
    assert isinstance(initial_msg, str)
    assert len(initial_msg) > 10
    assert "verification" in initial_msg.lower() or "bank" in initial_msg.lower()

    custom_msg = await attacker_engine.generate_initial_message(
        "fictional_bank_verification",
        custom_prompt="Custom alert: Please click here immediately."
    )
    assert custom_msg == "Custom alert: Please click here immediately."


# Test 3: Correct conversationHistory construction (excluding current message)
@pytest.mark.asyncio
async def test_correct_conversation_history_construction():
    client = HoneypotClient(base_url="https://mock-honeypot.local")
    
    # Existing history has 2 messages
    history = [
        {"sender": "scammer", "text": "Message 1", "timestamp": 1000},
        {"sender": "user", "text": "Response 1", "timestamp": 2000}
    ]
    current_attacker_text = "Message 2 (current)"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"reply": "Response 2"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        await client.send_message(
            session_id="sim_test_002",
            message_text=current_attacker_text,
            conversation_history=history
        )
        payload = mock_post.call_args[1]["json"]
        
        # Verify current message is in 'message' field
        assert payload["message"]["sender"] == "scammer"
        assert payload["message"]["text"] == current_attacker_text
        
        # Verify conversationHistory contains PREVIOUS messages only, excluding current message
        assert len(payload["conversationHistory"]) == 2
        assert payload["conversationHistory"][0]["text"] == "Message 1"
        assert payload["conversationHistory"][1]["text"] == "Response 1"
        assert current_attacker_text not in [m["text"] for m in payload["conversationHistory"]]


# Test 4: Correct sender identification ('scammer' and 'user')
def test_correct_sender_identification():
    msg_scammer = Message(sender="scammer", text="Simulated scammer message")
    msg_user = Message(sender="user", text="Simulated honeypot message")

    assert msg_scammer.sender == "scammer"
    assert msg_user.sender == "user"
    assert msg_scammer.to_honeypot_format()["sender"] == "scammer"
    assert msg_user.to_honeypot_format()["sender"] == "user"


# Test 5: Multi-turn communication progression
@pytest.mark.asyncio
async def test_multi_turn_communication(test_conversation_manager):
    session = await test_conversation_manager.create_session(
        scenario="fictional_bank_verification",
        max_turns=3
    )

    mock_replies = [
        "What is your employee id?",
        "I am not sharing my OTP with you.",
        "Stop contacting me."
    ]
    call_count = 0

    async def mock_send(session_id, message_text, conversation_history, metadata=None, timestamp=None):
        nonlocal call_count
        reply = mock_replies[min(call_count, len(mock_replies) - 1)]
        call_count += 1
        return reply

    with patch("backend.app.services.conversation_manager.honeypot_client.send_message", side_effect=mock_send):
        await test_conversation_manager.start_session(session.sessionId)
        # Wait for loop to finish turns
        for _ in range(50):
            s = await test_conversation_manager.get_session(session.sessionId)
            if s.status in ("completed", "failed"):
                break
            await asyncio.sleep(0.1)

        s = await test_conversation_manager.get_session(session.sessionId)
        assert s.status == "completed"
        # 3 turns = 3 scammer + 3 user = 6 total messages
        assert len(s.conversationHistory) == 6
        assert s.totalMessages == 6
        assert s.conversationHistory[0].sender == "scammer"
        assert s.conversationHistory[1].sender == "user"
        assert s.conversationHistory[2].sender == "scammer"
        assert s.conversationHistory[3].sender == "user"


# Test 6: Session persistence
@pytest.mark.asyncio
async def test_session_persistence(test_conversation_manager):
    session = await test_conversation_manager.create_session(
        scenario="upi_cashback_reward",
        channel="WhatsApp",
        max_turns=5
    )
    fetched = await test_conversation_manager.get_session(session.sessionId)
    assert fetched is not None
    assert fetched.sessionId == session.sessionId
    assert fetched.scenario == "upi_cashback_reward"
    assert fetched.metadata.get("channel") == "WhatsApp"


# Test 7: Stop and resume behaviour (resuming does NOT reset history)
@pytest.mark.asyncio
async def test_stop_and_resume_behaviour(test_conversation_manager):
    session = await test_conversation_manager.create_session(
        scenario="tech_support_alert",
        max_turns=6
    )

    turn_counter = 0
    async def slow_mock_send(session_id, message_text, conversation_history, metadata=None, timestamp=None):
        nonlocal turn_counter
        turn_counter += 1
        await asyncio.sleep(0.05)
        return f"Honeypot Response {turn_counter}"

    with patch("backend.app.services.conversation_manager.honeypot_client.send_message", side_effect=slow_mock_send):
        # Start session
        await test_conversation_manager.start_session(session.sessionId)
        await asyncio.sleep(0.2)
        
        # Stop session
        await test_conversation_manager.stop_session(session.sessionId)
        
        stopped_session = await test_conversation_manager.get_session(session.sessionId)
        assert stopped_session.status == "stopped"
        count_at_stop = len(stopped_session.conversationHistory)
        assert count_at_stop > 0

        # Resume session
        await test_conversation_manager.resume_session(session.sessionId)
        await asyncio.sleep(0.2)
        
        # Stop again
        await test_conversation_manager.stop_session(session.sessionId)
        
        resumed_session = await test_conversation_manager.get_session(session.sessionId)
        # History must NOT have been reset
        assert len(resumed_session.conversationHistory) >= count_at_stop
        assert resumed_session.conversationHistory[0].text == stopped_session.conversationHistory[0].text


# Test 8: API timeout and retry handling
@pytest.mark.asyncio
async def test_api_timeout_and_retry_handling():
    client = HoneypotClient(base_url="https://mock-honeypot.local", max_retries=1)

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timed out")):
        with pytest.raises(Exception) as exc_info:
            await client.send_message(
                session_id="sim_timeout_test",
                message_text="Test timeout message",
                conversation_history=[]
            )
        assert "Read timed out" in str(exc_info.value) or "communicate" in str(exc_info.value)


# Test 9: Invalid Honeypot response handling (dedicated ResponseAdapter)
def test_invalid_honeypot_response_handling():
    # 1. Non-empty uninterpretable dict
    with pytest.raises(UninterpretableResponseError) as exc:
        ResponseAdapter.extract_reply({"unexpected_field": 12345, "another": True})
    assert exc.value.raw_data == {"unexpected_field": 12345, "another": True}

    # 2. None response
    with pytest.raises(UninterpretableResponseError):
        ResponseAdapter.extract_reply(None)

    # 3. Explicit Honeypot error detail
    with pytest.raises(HoneypotAPIError) as exc:
        ResponseAdapter.extract_reply({"detail": "Invalid API key"})
    assert "Invalid API key" in str(exc.value)

    # 4. Valid alternate fields
    assert ResponseAdapter.extract_reply({"message": "I am a user"}) == "I am a user"
    assert ResponseAdapter.extract_reply({"text": "Hello honeypot"}) == "Hello honeypot"
    assert ResponseAdapter.extract_reply({"data": {"reply": "Nested reply"}}) == "Nested reply"
    assert ResponseAdapter.extract_reply({"reply": {"text": "Deep reply text"}}) == "Deep reply text"


# Test 10: LLM provider failure fallback
@pytest.mark.asyncio
async def test_llm_provider_failure_fallback(attacker_engine):
    # Simulate Gemini failure
    with patch.object(attacker_engine, "_generate_with_gemini", side_effect=Exception("Gemini Quota Exceeded")):
        attacker_engine.provider = "gemini"
        attacker_engine.api_key = "fake_key"
        
        # When Gemini fails, it should catch the exception and fall back to the contextual engine safely
        result = await attacker_engine.generate_next_message(
            scenario="fictional_bank_verification",
            conversation_history=[
                {"sender": "scammer", "text": "Your account is locked."},
                {"sender": "user", "text": "Who are you and which bank is this?"}
            ]
        )
        assert isinstance(result, str)
        assert len(result) > 10
        # Contextual reactive text for bank verification
        assert "officer" in result.lower() or "bank" in result.lower() or "security" in result.lower()
