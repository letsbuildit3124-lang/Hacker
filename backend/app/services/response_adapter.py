import json
from typing import Any, Optional, Dict
from backend.app.utils.logger import logger

class HoneypotResponseError(Exception):
    """Base exception for Honeypot response errors."""
    def __init__(self, message: str, raw_data: Any = None):
        super().__init__(message)
        self.raw_data = raw_data

class UninterpretableResponseError(HoneypotResponseError):
    """Raised when Honeypot response schema cannot be interpreted."""
    pass

class HoneypotAPIError(HoneypotResponseError):
    """Raised when Honeypot response indicates an API or validation error."""
    pass


class ResponseAdapter:
    """
    Dedicated adapter to interpret and parse responses from the Honeypot API safely.
    Adheres strictly to the guidelines:
    - Never blindly assumes 'reply' field exists.
    - Inspects multiple common schemas (reply, message, text, response, content, data).
    - Preserves raw response in debugging logs if uninterpretable.
    - Never silently generates a fake Honeypot response.
    """

    @classmethod
    def extract_reply(cls, raw_response: Any) -> str:
        """
        Extracts the textual response from a raw Honeypot API response.
        Raises UninterpretableResponseError or HoneypotAPIError on failure.
        """
        if raw_response is None:
            logger.error("Honeypot returned None or empty response.")
            raise UninterpretableResponseError("Honeypot API returned an empty response.", raw_data=None)

        # If response is string, try decoding as JSON first
        parsed_data = raw_response
        if isinstance(raw_response, str):
            raw_str = raw_response.strip()
            if not raw_str:
                logger.error("Honeypot returned an empty string.")
                raise UninterpretableResponseError("Honeypot API returned an empty string.", raw_data=raw_response)
            try:
                parsed_data = json.loads(raw_str)
            except json.JSONDecodeError:
                # Might be a raw text response
                if len(raw_str) > 0 and not raw_str.startswith(("{", "<", "[")):
                    logger.info("Interpreting raw string as Honeypot response text.")
                    return raw_str
                logger.error(f"Failed to parse non-JSON string response: {raw_str}")
                raise UninterpretableResponseError(
                    f"Received uninterpretable text response from Honeypot: {raw_str[:200]}",
                    raw_data=raw_response
                )

        if isinstance(parsed_data, dict):
            # 1. Check for explicit error responses
            if "detail" in parsed_data:
                detail = parsed_data["detail"]
                logger.error(f"Honeypot returned error detail: {detail}")
                raise HoneypotAPIError(f"Honeypot API Error: {detail}", raw_data=parsed_data)
            
            if "error" in parsed_data:
                err = parsed_data["error"]
                logger.error(f"Honeypot returned error: {err}")
                raise HoneypotAPIError(f"Honeypot API Error: {err}", raw_data=parsed_data)

            # 2. Check candidate keys
            candidate_keys = ["reply", "message", "text", "response", "content", "output", "answer"]
            
            for key in candidate_keys:
                if key in parsed_data and parsed_data[key] is not None:
                    val = parsed_data[key]
                    extracted = cls._extract_from_value(val)
                    if extracted:
                        return extracted

            # 3. Check nested 'data' or 'result' dictionary
            for container in ["data", "result", "payload"]:
                if container in parsed_data and isinstance(parsed_data[container], dict):
                    nested = parsed_data[container]
                    for key in candidate_keys:
                        if key in nested and nested[key] is not None:
                            extracted = cls._extract_from_value(nested[key])
                            if extracted:
                                return extracted

        # If we reached here, the response format could not be interpreted
        logger.error(f"Uninterpretable Honeypot response structure. Preserving raw response: {parsed_data}")
        raise UninterpretableResponseError(
            f"Unable to parse Honeypot response. Expected text/reply field in response object.",
            raw_data=parsed_data
        )

    @classmethod
    def _extract_from_value(cls, val: Any) -> Optional[str]:
        """Safely extract string text from a value which may be a string or sub-dict."""
        if isinstance(val, str):
            cleaned = val.strip()
            if cleaned:
                return cleaned
        elif isinstance(val, dict):
            for sub_key in ["text", "message", "content", "body"]:
                sub_val = val.get(sub_key)
                if isinstance(sub_val, str) and sub_val.strip():
                    return sub_val.strip()
        return None
