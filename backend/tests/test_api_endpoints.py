import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "honeypot_target" in data

@pytest.mark.asyncio
async def test_session_creation_and_lifecycle_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create Session
        create_payload = {
            "scenario": "fictional_bank_verification",
            "channel": "SMS",
            "language": "English",
            "locale": "IN",
            "maxTurns": 10
        }
        res = await ac.post("/api/sessions", json=create_payload)
        assert res.status_code == 201
        session_data = res.json()
        session_id = session_data["sessionId"]
        assert session_data["status"] == "created"
        assert session_data["scenario"] == "fictional_bank_verification"

        # 2. Get Session Details
        res_get = await ac.get(f"/api/sessions/{session_id}")
        assert res_get.status_code == 200
        assert res_get.json()["sessionId"] == session_id

        # 3. Get Empty Messages
        res_msgs = await ac.get(f"/api/sessions/{session_id}/messages")
        assert res_msgs.status_code == 200
        assert res_msgs.json() == []

        # 4. Get Stats
        res_stats = await ac.get("/api/sessions/stats")
        assert res_stats.status_code == 200
        stats = res_stats.json()
        assert stats["totalSimulations"] >= 1
