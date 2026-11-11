import pytest
from backend.app.config import settings
from backend.app.services.attacker_engine import attacker_engine
from backend.app.services.llm_provider import llm_provider

@pytest.fixture(autouse=True)
def force_mock_llm_in_tests(monkeypatch):
    """
    Ensure automated tests mock external LLMs and run instantaneously
    as required: 'Mock external APIs in automated tests.'
    """
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    monkeypatch.setattr(settings, "LLM_API_KEY", None)
    monkeypatch.setattr(attacker_engine, "provider", "mock")
    monkeypatch.setattr(attacker_engine, "api_key", None)
    monkeypatch.setattr(llm_provider, "provider", "mock")
    monkeypatch.setattr(llm_provider, "api_key", None)
