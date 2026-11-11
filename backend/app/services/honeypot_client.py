import asyncio
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import httpx
from backend.app.config import settings
from backend.app.services.response_adapter import ResponseAdapter, HoneypotResponseError, HoneypotAPIError
from backend.app.utils.logger import logger


def normalize_honeypot_url(raw_url: str) -> str:
    """
    Validates and normalizes a Honeypot base URL.
    Strips trailing slashes and an accidental '/honeypot' path suffix so the
    client consistently targets '<base_url>/honeypot'.
    """
    cleaned = (raw_url or "").strip().rstrip("/")
    if not cleaned:
        raise ValueError("Honeypot URL cannot be empty.")

    parsed = urlparse(cleaned)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Honeypot URL must be a valid http:// or https:// address.")

    if cleaned.lower().endswith("/honeypot"):
        cleaned = cleaned[:-len("/honeypot")].rstrip("/")

    return cleaned


class HoneypotClient:
    """
    Client for communicating asynchronously with the external Honeypot API.
    Handles dynamic target URLs, headers, timeouts, retries for cold-starts, and response parsing.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None
    ):
        self._explicit_base_url: Optional[str] = normalize_honeypot_url(base_url) if base_url else None
        self._explicit_api_key: Optional[str] = api_key
        self.timeout = timeout or settings.HONEYPOT_TIMEOUT_SECONDS
        self.max_retries = max_retries if max_retries is not None else settings.HONEYPOT_MAX_RETRIES

    @property
    def base_url(self) -> str:
        if self._explicit_base_url:
            return self._explicit_base_url
        return normalize_honeypot_url(settings.HONEYPOT_BASE_URL)

    @base_url.setter
    def base_url(self, value: str):
        self._explicit_base_url = normalize_honeypot_url(value) if value else None

    @property
    def api_key(self) -> Optional[str]:
        return self._explicit_api_key if self._explicit_api_key is not None else settings.HONEYPOT_API_KEY

    @api_key.setter
    def api_key(self, value: Optional[str]):
        self._explicit_api_key = value

    def _get_headers(self, override_api_key: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AgenticHoneypotSimulator/1.0"
        }
        key = override_api_key if override_api_key else self.api_key
        if key:
            headers["x-api-key"] = key
        return headers

    async def test_connection(
        self,
        candidate_url: str,
        candidate_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tests connectivity and authentication against a candidate Honeypot endpoint
        using a synthetic diagnostic ping without modifying active global settings.
        """
        try:
            normalized = normalize_honeypot_url(candidate_url)
        except ValueError as err:
            return {
                "reachable": False,
                "status_code": 0,
                "latency_ms": 0,
                "normalized_url": candidate_url,
                "sample_reply_preview": None,
                "error": str(err)
            }

        endpoint = f"{normalized}/honeypot"
        payload = {
            "sessionId": f"conn_probe_{int(time.time())}",
            "message": {
                "sender": "scammer",
                "text": "Hello, checking connection for simulation readiness.",
                "timestamp": int(time.time() * 1000)
            },
            "conversationHistory": [],
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
        }
        headers = self._get_headers(override_api_key=candidate_api_key)

        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)

            if response.status_code == 200:
                try:
                    resp_json = response.json()
                except Exception:
                    resp_json = response.text
                try:
                    reply = ResponseAdapter.extract_reply(resp_json)
                    return {
                        "reachable": True,
                        "status_code": 200,
                        "latency_ms": latency_ms,
                        "normalized_url": normalized,
                        "sample_reply_preview": reply[:120],
                        "error": None
                    }
                except HoneypotResponseError as parse_err:
                    return {
                        "reachable": False,
                        "status_code": 200,
                        "latency_ms": latency_ms,
                        "normalized_url": normalized,
                        "sample_reply_preview": None,
                        "error": f"Response schema error: {parse_err}"
                    }

            return {
                "reachable": False,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "normalized_url": normalized,
                "sample_reply_preview": None,
                "error": f"HTTP {response.status_code}: {response.text[:200]}"
            }
        except Exception as exc:
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            return {
                "reachable": False,
                "status_code": 0,
                "latency_ms": latency_ms,
                "normalized_url": normalized,
                "sample_reply_preview": None,
                "error": str(exc)
            }

    async def send_message(
        self,
        session_id: str,
        message_text: str,
        conversation_history: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[int] = None
    ) -> str:
        """
        Sends an attacker message to the Honeypot API and returns the extracted reply text.
        """
        endpoint = f"{self.base_url}/honeypot"
        current_time = timestamp or int(time.time() * 1000)

        payload = {
            "sessionId": str(session_id),
            "message": {
                "sender": "scammer",
                "text": message_text,
                "timestamp": current_time
            },
            "conversationHistory": [
                {
                    "sender": item.get("sender"),
                    "text": item.get("text"),
                    "timestamp": item.get("timestamp")
                }
                for item in conversation_history
            ],
            "metadata": metadata or {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }

        headers = self._get_headers()
        attempt = 0
        last_exception: Optional[Exception] = None

        while attempt <= self.max_retries:
            attempt += 1
            logger.info(
                f"[HoneypotClient] Sending message to {endpoint} (Attempt {attempt}/{self.max_retries + 1}), "
                f"Session: {session_id}, History Count: {len(conversation_history)}"
            )
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(endpoint, json=payload, headers=headers)

                status = response.status_code
                logger.info(f"[HoneypotClient] Received response {status} from Honeypot for session {session_id}")

                if status == 200:
                    try:
                        resp_json = response.json()
                    except Exception:
                        resp_json = response.text

                    extracted_reply = ResponseAdapter.extract_reply(resp_json)
                    logger.info(f"[HoneypotClient] Successfully extracted reply: '{extracted_reply[:80]}...'")
                    return extracted_reply

                elif status in (401, 403):
                    err_body = response.text
                    logger.error(f"[HoneypotClient] Authentication failed ({status}): {err_body}")
                    raise HoneypotAPIError(f"Honeypot API Authentication Failed ({status}): {err_body}", raw_data=err_body)

                elif status == 422:
                    err_body = response.text
                    logger.error(f"[HoneypotClient] Validation error ({status}): {err_body}")
                    raise HoneypotAPIError(f"Honeypot Request Validation Failed (422): {err_body}", raw_data=err_body)

                elif status >= 500:
                    err_body = response.text
                    logger.warning(f"[HoneypotClient] Server error ({status}) on attempt {attempt}: {err_body}")
                    last_exception = HoneypotAPIError(f"Honeypot Server Error ({status}): {err_body}", raw_data=err_body)

                else:
                    err_body = response.text
                    logger.error(f"[HoneypotClient] Unexpected status code {status}: {err_body}")
                    raise HoneypotAPIError(f"Honeypot returned status {status}: {err_body}", raw_data=err_body)

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                logger.warning(f"[HoneypotClient] Network/Timeout error on attempt {attempt}: {str(exc)}")
                last_exception = exc

            if attempt <= self.max_retries:
                backoff = 2 ** attempt
                logger.info(f"[HoneypotClient] Waiting {backoff}s before retry...")
                await asyncio.sleep(backoff)

        logger.error(f"[HoneypotClient] All {self.max_retries + 1} attempts exhausted for session {session_id}")
        if last_exception:
            raise HoneypotResponseError(f"Failed to communicate with Honeypot API after {attempt} attempts: {str(last_exception)}")
        raise HoneypotResponseError("Failed to communicate with Honeypot API.")


honeypot_client = HoneypotClient()
