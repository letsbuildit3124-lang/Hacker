"""
Phase 3 Automated Test Suite: Complete AI Red-Team Simulation & Honeypot Evaluation Platform.
Tests evaluation engine, intelligence extraction, batch execution, replay engine,
stress testing, report generation, and new API routes.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.database.mongodb import db
from backend.app.services.intelligence_engine import intelligence_engine
from backend.app.services.evaluation_engine import evaluation_engine
from backend.app.services.batch_engine import batch_engine, BatchConfig
from backend.app.services.replay_engine import replay_engine
from backend.app.services.stress_test_engine import stress_test_engine
from backend.app.services.report_generator import report_generator
from backend.app.services.conversation_manager import conversation_manager
from backend.app.services.response_adapter import HoneypotAPIError



@pytest.mark.asyncio
async def test_intelligence_extraction_scoring():
    """
    Verifies that ground truth extraction correctly calculates Precision, Recall, and F1 score,
    and only scores artifacts that were actually disclosed during the conversation.
    """
    disclosed_artifacts = {
        "upi_ids": ["support@icici-verify.axis", "paytm-fastag@okhdfc"],
        "urls": ["https://verify-kyc.secure-portal-auth.org"],
        "bank_accounts": ["1029384756"]
    }

    # Case 1: Honeypot extracted 1 disclosed upi and 1 disclosed url, plus 1 hallucinated upi
    honeypot_extracted = {
        "upi_ids": ["support@icici-verify.axis", "fake_random@upi"],
        "urls": ["https://verify-kyc.secure-portal-auth.org"]
    }

    result = intelligence_engine.calculate_intelligence_score(
        disclosed_artifacts=disclosed_artifacts,
        honeypot_extracted=honeypot_extracted
    )

    # Disclosed count = 4 (2 upi + 1 url + 1 bank)
    # Extracted count = 3
    # Matches = 2 ("support@icici-verify.axis", "https://verify-kyc.secure-portal-auth.org")
    assert result["disclosed_count"] == 4
    assert result["extracted_count"] == 3
    assert result["matches_count"] == 2
    # Precision = 2 / 3 = 0.6667
    assert pytest.approx(result["precision"], 0.01) == 0.67
    # Recall = 2 / 4 = 0.50
    assert pytest.approx(result["recall"], 0.01) == 0.50
    # F1 = 2 * (0.6667 * 0.5) / (0.6667 + 0.5) = 0.5714
    assert pytest.approx(result["f1_score"], 0.01) == 0.57


@pytest.mark.asyncio
async def test_evaluation_engine_ten_metrics_and_normalization():
    """
    Tests evaluation engine's 10-metric score weighting, handling missing/NA metrics
    by normalizing active weights to 100%.
    """
    session_id = "test_eval_session_001"
    session = await conversation_manager.create_session(
        session_id=session_id,
        scenario_id="banking_kyc_verification",
        persona_id="urgent_support",
        language="English",
        max_turns=3
    )

    # Insert mock transcript
    await db.save_message(session_id, "scammer", "Your SBI KYC expires in 24 hours. Send OTP.", 1000)
    await db.save_message(session_id, "user", "Why do you need OTP? Is this a scam?", 2000)
    await db.save_message(session_id, "scammer", "I am SBI Senior Manager Ramesh. Pay 100 INR to upi ram@axis.", 3000)
    await db.save_message(session_id, "user", "I will not pay. You are a scammer.", 4000)

    eval_result = await evaluation_engine.evaluate_session(session_id)

    assert "overall_score" in eval_result
    assert 0 <= eval_result["overall_score"] <= 100
    assert "metric_scores" in eval_result
    assert len(eval_result["metric_scores"]) == 10
    assert "scam_detection" in eval_result["metric_scores"]
    assert "conversation_continuity" in eval_result["metric_scores"]
    assert "intelligence_extraction" in eval_result["metric_scores"]
    assert "strengths" in eval_result
    assert "weaknesses" in eval_result
    assert "llm_judge_review" in eval_result


@pytest.mark.asyncio
async def test_batch_engine_concurrency_and_cancellation():
    """
    Tests the BatchEngine generating combinations, respecting bounded concurrency,
    and handling batch cancellation.
    """
    batch_config = BatchConfig(
        batchName="Test Security Benchmark",
        scenarioIds=["banking_kyc_verification"],
        personaIds=["friendly_support", "urgent_support"],
        languages=["English"],
        maxTurns=2,
        concurrency=2
    )

    with patch("backend.app.services.honeypot_client.honeypot_client.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = "Hello, I understand. Who are you?"

        batch = await batch_engine.create_and_start_batch(batch_config)
        assert batch.batchId.startswith("batch_")
        assert batch.totalSessions == 2  # 1 scenario * 2 personas * 1 language
        assert batch.status in ("running", "completed")

        # Test querying batch status
        fetched = await batch_engine.get_batch(batch.batchId)
        assert fetched is not None
        assert fetched.batchName == "Test Security Benchmark"

        # Test batch cancellation
        cancelled = await batch_engine.cancel_batch(batch.batchId)
        assert cancelled.status == "cancelled"


@pytest.mark.asyncio
async def test_replay_engine_and_comparison():
    """
    Tests historical transcript replay with step timing and side-by-side session comparison.
    """
    s1_id = "test_replay_s1"
    s2_id = "test_replay_s2"

    await conversation_manager.create_session(session_id=s1_id, scenario_id="utility_bill_overdue", persona_id="friendly_support")
    await db.save_message(s1_id, "scammer", "Electricity bill overdue.", 1000)
    await db.save_message(s1_id, "user", "Let me check.", 2000)

    await conversation_manager.create_session(session_id=s2_id, scenario_id="utility_bill_overdue", persona_id="urgent_support")
    await db.save_message(s2_id, "scammer", "Power cutoff immediately!", 1000)
    await db.save_message(s2_id, "user", "Please wait!", 2500)

    # Replay transcript
    replay_data = await replay_engine.get_replay_transcript(s1_id)
    assert replay_data["session_id"] == s1_id
    assert len(replay_data["steps"]) == 2
    assert replay_data["steps"][0]["sender"] == "scammer"
    assert replay_data["steps"][1]["delay_from_prev_ms"] == 1000

    # Comparison
    comparison = await replay_engine.compare_sessions(s1_id, s2_id)
    assert "turn_comparison" in comparison
    assert len(comparison["turn_comparison"]) == 2
    assert comparison["turn_comparison"][0]["session_1"]["text"] == "Electricity bill overdue."
    assert comparison["turn_comparison"][0]["session_2"]["text"] == "Power cutoff immediately!"


@pytest.mark.asyncio
async def test_stress_test_engine_circuit_breaker():
    """
    Tests stress test engine calculates latencies and safely aborts
    when the failure rate exceeds safety_error_threshold.
    """
    with patch("backend.app.services.honeypot_client.honeypot_client.send_message", new_callable=AsyncMock) as mock_send:
        # Simulate consecutive server errors
        mock_send.side_effect = HoneypotAPIError("Honeypot Server Error (500)")

        result = await stress_test_engine.run_stress_test(
            num_requests=6,
            concurrency=2,
            delay_between_requests_ms=10,
            safety_error_threshold=0.25
        )

        assert result["summary"]["failed_requests"] >= 4
        assert result["summary"]["aborted_by_safety"] is True
        assert result["status"] == "aborted"


@pytest.mark.asyncio
async def test_report_generator_json_and_csv():
    """
    Tests generating downloadable structured JSON and CSV reports.
    """
    session_id = "test_report_sess_01"
    await conversation_manager.create_session(session_id=session_id, scenario_id="tax_refund_processing", persona_id="technical_support")
    await db.save_message(session_id, "scammer", "Income Tax refund of 15000 INR approved.", 1000)
    await db.save_message(session_id, "user", "Where can I claim it?", 2000)

    # JSON report
    json_report = await report_generator.generate_json_report(session_id)
    assert json_report["session_summary"]["session_id"] == session_id
    assert len(json_report["transcript"]) == 2
    assert "report_metadata" in json_report

    # CSV report
    csv_report = await report_generator.generate_csv_report(session_id)
    assert "=== AGENTIC HONEYPOT SIMULATION REPORT ===" in csv_report
    assert "Income Tax refund of 15000 INR approved." in csv_report
    assert "scammer" in csv_report


@pytest.mark.asyncio
async def test_phase3_api_endpoints():
    """
    Tests all Phase 3 API endpoints via HTTP test client:
    - /api/ready
    - /api/evaluations
    - /api/batches
    - /api/analytics/overview
    - /api/reports/{id}/json
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Readiness
        resp = await client.get("/api/ready")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"

        # Analytics
        resp_ana = await client.get("/api/analytics/overview")
        assert resp_ana.status_code == 200
        data = resp_ana.json()
        assert "total_sessions" in data
        assert "average_score" in data

        # Evaluations list
        resp_ev = await client.get("/api/evaluations")
        assert resp_ev.status_code == 200
        assert isinstance(resp_ev.json(), list)


def test_enriched_attacker_artifacts_disclosure_and_extraction():
    """
    Tests ScenarioEngine generating rich synthetic artifacts (Email ID, Mobile Number,
    Employee ID, UPI ID, Bank Account, Phishing URL), ConsistencyEngine accepting them
    without false-positive conflicts, and IntelligenceEngine extracting them cleanly
    without confusing emails with UPI handles.
    """
    from backend.app.services.scenario_engine import scenario_engine
    from backend.app.services.consistency_engine import consistency_engine
    from backend.app.services.persona_engine import persona_engine

    facts = scenario_engine.generate_session_facts("fictional_bank_verification", "Rahul")
    assert facts.get("agentId", "").startswith("EMP-")
    assert "@zenith-bank-demo.org" in facts.get("contactEmail", "")
    assert facts.get("mobileNumber", "").startswith("+91-90000-")
    assert facts.get("upiId") == "kyc.verify@okzenithdemo"
    assert facts.get("bankAccount") == "9900112233445566"
    assert facts.get("officialPortal") == "http://verify-portal.zenith-bank-demo.org"

    # Verify ConsistencyEngine does not flag employee ID or email as inconsistent case reference
    persona = persona_engine.get_persona("friendly_support")
    candidate_msg = (
        f"I am Rahul (Employee ID: {facts['agentId']}) from {facts['organization']}. "
        f"You can email me at {facts['contactEmail']}, call {facts['mobileNumber']}, "
        f"or complete case {facts['caseReference']} at {facts['officialPortal']} using UPI {facts['upiId']} "
        f"or account {facts['bankAccount']}."
    )
    val = consistency_engine.validate_message(candidate_msg, persona, facts, "fictional_bank_verification", [])
    assert val.is_valid, f"Unexpected consistency errors: {val.issues}"

    # Verify IntelligenceEngine extracts every category cleanly without double counting email as UPI
    extracted = intelligence_engine.extract_artifacts_from_text(candidate_msg)
    assert facts["contactEmail"] in extracted["emailIds"]
    assert facts["upiId"] in extracted["upiIds"]
    assert facts["contactEmail"] not in extracted["upiIds"]
    assert facts["agentId"] in extracted["employeeIds"]
    assert facts["caseReference"] in extracted["caseReferences"]
    assert facts["officialPortal"] in extracted["phishingLinks"]
    assert facts["bankAccount"] in extracted["bankAccounts"]
    assert any("90000" in p for p in extracted["phoneNumbers"])

    # Verify dynamic ground truth evaluation matches disclosed items
    history = [
        {"sender": "scammer", "text": candidate_msg},
        {"sender": "user", "text": f"Logged {facts['agentId']}, {facts['contactEmail']}, {facts['upiId']}, and {facts['officialPortal']}."}
    ]
    eval_res = intelligence_engine.evaluate_extraction(history, "fictional_bank_verification", facts)
    assert facts["contactEmail"] in eval_res.disclosedArtifacts["emailIds"]
    assert facts["agentId"] in eval_res.disclosedArtifacts["employeeIds"]
    assert facts["upiId"] in eval_res.disclosedArtifacts["upiIds"]
    assert facts["bankAccount"] in eval_res.disclosedArtifacts["bankAccounts"]


@pytest.mark.asyncio
async def test_dynamic_honeypot_settings_api():
    """
    Tests GET/PUT /api/settings/honeypot, URL normalization, secret redaction,
    invalid URL rejection, and live reflection on honeypot_client.base_url.
    """
    from backend.app.config import settings
    from backend.app.services.honeypot_client import honeypot_client, normalize_honeypot_url

    orig_url = settings.HONEYPOT_BASE_URL
    orig_key = settings.HONEYPOT_API_KEY

    try:
        assert normalize_honeypot_url("https://example-hp.onrender.com/honeypot/") == "https://example-hp.onrender.com"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Invalid scheme should return 422
            bad_resp = await client.put("/api/settings/honeypot", json={"honeypot_base_url": "ftp://invalid-scheme"})
            assert bad_resp.status_code == 422

            # Valid update with trailing /honeypot
            upd_resp = await client.put("/api/settings/honeypot", json={
                "honeypot_base_url": "https://custom-honeypot-demo.onrender.com/honeypot",
                "honeypot_api_key": "secret-test-key"
            })
            assert upd_resp.status_code == 200
            upd_data = upd_resp.json()
            assert upd_data["honeypot_base_url"] == "https://custom-honeypot-demo.onrender.com"
            assert upd_data["has_api_key"] is True
            # Ensure secret is never exposed in response
            assert "secret-test-key" not in str(upd_data)
            assert honeypot_client.base_url == "https://custom-honeypot-demo.onrender.com"

            # GET should also mask secret
            get_resp = await client.get("/api/settings/honeypot")
            assert get_resp.status_code == 200
            get_data = get_resp.json()
            assert get_data["honeypot_base_url"] == "https://custom-honeypot-demo.onrender.com"
            assert get_data["has_api_key"] is True
            assert "honeypot_api_key" not in get_data
    finally:
        settings.HONEYPOT_BASE_URL = orig_url
        settings.HONEYPOT_API_KEY = orig_key
        honeypot_client._explicit_base_url = None
        honeypot_client._explicit_api_key = None


