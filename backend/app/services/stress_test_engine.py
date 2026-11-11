"""
Stress Testing & Reliability Engine for Honeypot API.

Conducts controlled, safe performance testing against the Honeypot endpoint:
- Bounded concurrency with asyncio.Semaphore
- Measures latency (Min, Mean, P50, P95, P99, Max)
- HTTP status code distribution tracking
- Safety circuit-breaker: aborts if error threshold (e.g. 20%) is exceeded
"""
import asyncio
import time
import uuid
import statistics
from typing import Dict, Any, List, Optional
from backend.app.services.honeypot_client import honeypot_client
from backend.app.services.response_adapter import HoneypotResponseError
from backend.app.utils.logger import logger


class StressTestEngine:
    """Orchestrates controlled load and reliability benchmarking against the Honeypot."""

    def __init__(self):
        self._test_results: Dict[str, Dict[str, Any]] = {}

    async def run_stress_test(
        self,
        num_requests: int = 10,
        concurrency: int = 2,
        delay_between_requests_ms: int = 200,
        safety_error_threshold: float = 0.25,
        test_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a controlled batch of requests with latency tracking and automatic circuit breaker.
        """
        test_id = test_id or f"stress_{uuid.uuid4().hex[:8]}"
        semaphore = asyncio.Semaphore(max(1, min(concurrency, 10)))  # Cap max concurrency safely at 10

        latencies_ms: List[float] = []
        status_codes: Dict[int, int] = {}
        errors: List[str] = []
        successful_requests = 0
        failed_requests = 0
        aborted = False

        record = {
            "test_id": test_id,
            "target_url": honeypot_client.base_url,
            "total_requested": num_requests,
            "concurrency": concurrency,
            "status": "running",
            "start_time": time.time(),
            "completed_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "latencies_ms": latencies_ms,
            "status_codes": status_codes,
            "errors": errors,
            "summary": {}
        }
        self._test_results[test_id] = record

        async def worker(idx: int):
            nonlocal successful_requests, failed_requests, aborted

            if aborted:
                return

            async with semaphore:
                if aborted:
                    return

                if delay_between_requests_ms > 0 and idx > 0:
                    await asyncio.sleep(delay_between_requests_ms / 1000.0)

                t0 = time.perf_counter()
                synthetic_session_id = f"stress_probe_{test_id}_{idx}"
                synthetic_text = "Hello, this is a diagnostic verification ping."

                try:
                    reply = await honeypot_client.send_message(
                        session_id=synthetic_session_id,
                        message_text=synthetic_text,
                        conversation_history=[],
                        metadata={"source": "reliability_probe", "index": idx}
                    )
                    latency = (time.perf_counter() - t0) * 1000
                    latencies_ms.append(round(latency, 2))
                    status_codes[200] = status_codes.get(200, 0) + 1
                    successful_requests += 1

                except HoneypotResponseError as ex:
                    latency = (time.perf_counter() - t0) * 1000
                    latencies_ms.append(round(latency, 2))
                    failed_requests += 1
                    # Extract status code if present in message
                    code = 500
                    if "401" in str(ex) or "403" in str(ex):
                        code = 403
                    elif "422" in str(ex):
                        code = 422
                    status_codes[code] = status_codes.get(code, 0) + 1
                    errors.append(f"Honeypot Error: {str(ex)}")

                except Exception as ex:
                    latency = (time.perf_counter() - t0) * 1000
                    latencies_ms.append(round(latency, 2))
                    failed_requests += 1
                    status_codes[0] = status_codes.get(0, 0) + 1
                    errors.append(f"Network/Client Exception: {str(ex)}")

                total_done = successful_requests + failed_requests
                record["completed_requests"] = total_done
                record["successful_requests"] = successful_requests
                record["failed_requests"] = failed_requests

                # Check circuit breaker safety threshold
                if total_done >= 4:
                    err_rate = failed_requests / total_done
                    if err_rate > safety_error_threshold:
                        aborted = True
                        logger.error(
                            f"Stress test {test_id} aborted by safety circuit breaker: error rate {err_rate:.2%} > threshold {safety_error_threshold:.2%}"
                        )

        # Launch worker tasks
        tasks = [asyncio.create_task(worker(i)) for i in range(num_requests)]
        await asyncio.gather(*tasks, return_exceptions=True)

        record["end_time"] = time.time()
        record["duration_seconds"] = round(record["end_time"] - record["start_time"], 2)
        record["status"] = "aborted" if aborted else "completed"

        # Calculate statistics
        summary = {
            "total_requests": len(latencies_ms),
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "error_rate": round(failed_requests / len(latencies_ms), 4) if latencies_ms else 0.0,
            "aborted_by_safety": aborted,
            "status_code_distribution": status_codes
        }

        if latencies_ms:
            sorted_latencies = sorted(latencies_ms)
            summary["latency_min_ms"] = sorted_latencies[0]
            summary["latency_max_ms"] = sorted_latencies[-1]
            summary["latency_mean_ms"] = round(statistics.mean(sorted_latencies), 2)
            summary["latency_p50_ms"] = round(statistics.median(sorted_latencies), 2)

            def get_percentile(data: List[float], p: float) -> float:
                k = (len(data) - 1) * p
                f = int(k)
                c = min(f + 1, len(data) - 1)
                d = k - f
                return round(data[f] + d * (data[c] - data[f]), 2)

            summary["latency_p95_ms"] = get_percentile(sorted_latencies, 0.95)
            summary["latency_p99_ms"] = get_percentile(sorted_latencies, 0.99)
        else:
            summary["latency_min_ms"] = 0
            summary["latency_max_ms"] = 0
            summary["latency_mean_ms"] = 0
            summary["latency_p50_ms"] = 0
            summary["latency_p95_ms"] = 0
            summary["latency_p99_ms"] = 0

        record["summary"] = summary
        return record

    def get_test_status(self, test_id: str) -> Optional[Dict[str, Any]]:
        return self._test_results.get(test_id)


stress_test_engine = StressTestEngine()
