"""
Replay Engine for Honeypot Simulations.

Supports:
1. Step-by-step deterministic transcript replay of historical sessions.
2. Re-running historical scenarios under identical or modified configurations (e.g. different persona).
3. Side-by-side comparison of two simulation runs (turns, latency, strategies, evaluation scores).
"""
import uuid
import time
from typing import Dict, Any, List, Optional
from backend.app.database.mongodb import db
from backend.app.services.conversation_manager import conversation_manager
from backend.app.services.evaluation_engine import evaluation_engine
from backend.app.utils.logger import logger


class ReplayEngine:
    """Manages session replay, scenario re-running, and side-by-side comparisons."""

    async def get_replay_transcript(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieves the complete historical transcript for step-by-step playback.
        Includes computed inter-message delays and turn indices.
        """
        session = await db.get_session(session_id)
        if not session:
            return {"error": f"Session '{session_id}' not found."}

        messages = await db.get_messages(session_id)
        evaluation = await db.get_evaluation(session_id)

        # Build replay steps with timing deltas
        steps: List[Dict[str, Any]] = []
        last_ts = None

        for idx, msg in enumerate(messages):
            ts = msg.get("timestamp")
            # Parse timestamp if it's integer milliseconds or ISO string
            ts_int = None
            if isinstance(ts, (int, float)):
                ts_int = int(ts)
            elif isinstance(ts, str) and ts.isdigit():
                ts_int = int(ts)

            delay_from_prev_ms = 0
            if last_ts is not None and ts_int is not None:
                delay_from_prev_ms = max(0, ts_int - last_ts)
            last_ts = ts_int

            steps.append({
                "step_index": idx + 1,
                "sender": msg.get("sender"),
                "text": msg.get("text"),
                "timestamp": ts,
                "delay_from_prev_ms": min(delay_from_prev_ms, 5000),  # Cap display delay for replay UI
                "metadata": msg.get("metadata", {})
            })

        return {
            "session_id": session_id,
            "persona_id": session.get("persona_id"),
            "scenario_id": session.get("scenario_id"),
            "language": session.get("language", "English"),
            "status": session.get("status"),
            "total_turns": session.get("turn_count", len(messages) // 2),
            "created_at": session.get("created_at"),
            "steps": steps,
            "has_evaluation": evaluation is not None,
            "overall_score": evaluation.get("overall_score") if evaluation else None
        }

    async def rerun_simulation(
        self,
        source_session_id: str,
        new_persona_id: Optional[str] = None,
        max_turns: Optional[int] = None,
        run_autonomous: bool = True
    ) -> Dict[str, Any]:
        """
        Clones an existing simulation's scenario, language, and parameters to launch a new run.
        Optionally swaps the persona or sets new turn limits.
        """
        source_session = await db.get_session(source_session_id)
        if not source_session:
            return {"error": f"Source session '{source_session_id}' not found."}

        scenario_id = source_session.get("scenario_id", "banking_kyc_verification")
        persona_id = new_persona_id or source_session.get("persona_id", "friendly_support")
        language = source_session.get("language", "English")
        locale = source_session.get("locale", "IN")
        channel = source_session.get("channel", "SMS")
        turns = max_turns or source_session.get("max_turns", 5)

        new_session_id = f"rerun_{uuid.uuid4().hex[:8]}"

        created_session = await conversation_manager.create_session(
            session_id=new_session_id,
            scenario_id=scenario_id,
            persona_id=persona_id,
            language=language,
            locale=locale,
            channel=channel,
            max_turns=turns
        )

        result = {
            "new_session_id": new_session_id,
            "source_session_id": source_session_id,
            "scenario_id": scenario_id,
            "persona_id": persona_id,
            "language": language,
            "status": "created"
        }

        if run_autonomous:
            # Run the conversation autonomously
            run_result = await conversation_manager.run_autonomous_loop(
                session_id=new_session_id,
                max_turns=turns,
                turn_delay_seconds=0.5
            )
            result["status"] = run_result.get("status")
            result["turn_count"] = run_result.get("turns_completed")
            result["messages_count"] = len(run_result.get("messages", []))

            # Auto evaluate rerun
            try:
                eval_res = await evaluation_engine.evaluate_session(new_session_id)
                result["evaluation_score"] = eval_res.get("overall_score")
            except Exception as e:
                logger.warning(f"Auto-eval failed for rerun {new_session_id}: {e}")

        return result

    async def compare_sessions(self, session_id_1: str, session_id_2: str) -> Dict[str, Any]:
        """
        Compares two simulation sessions side-by-side across transcript turns,
        latencies, intelligence disclosed/extracted, and evaluation scores.
        """
        s1 = await db.get_session(session_id_1)
        s2 = await db.get_session(session_id_2)

        if not s1:
            return {"error": f"Session 1 '{session_id_1}' not found."}
        if not s2:
            return {"error": f"Session 2 '{session_id_2}' not found."}

        m1 = await db.get_messages(session_id_1)
        m2 = await db.get_messages(session_id_2)

        e1 = await db.get_evaluation(session_id_1)
        e2 = await db.get_evaluation(session_id_2)

        # Pair messages side-by-side by turn index
        max_len = max(len(m1), len(m2))
        paired_turns = []

        for i in range(max_len):
            msg1 = m1[i] if i < len(m1) else None
            msg2 = m2[i] if i < len(m2) else None

            paired_turns.append({
                "turn_index": (i // 2) + 1,
                "role": "attacker" if (i % 2 == 0) else "honeypot",
                "session_1": {
                    "sender": msg1.get("sender") if msg1 else None,
                    "text": msg1.get("text") if msg1 else None,
                    "timestamp": msg1.get("timestamp") if msg1 else None
                } if msg1 else None,
                "session_2": {
                    "sender": msg2.get("sender") if msg2 else None,
                    "text": msg2.get("text") if msg2 else None,
                    "timestamp": msg2.get("timestamp") if msg2 else None
                } if msg2 else None
            })

        # Metric comparisons
        score_comparison = None
        if e1 and e2:
            metrics_diff = {}
            for k in e1.get("metric_scores", {}):
                val1 = e1.get("metric_scores", {}).get(k, 0)
                val2 = e2.get("metric_scores", {}).get(k, 0)
                metrics_diff[k] = {
                    "session_1": val1,
                    "session_2": val2,
                    "diff": round(val2 - val1, 2)
                }

            score_comparison = {
                "overall_1": e1.get("overall_score"),
                "overall_2": e2.get("overall_score"),
                "overall_diff": round(e2.get("overall_score", 0) - e1.get("overall_score", 0), 2),
                "metrics_breakdown": metrics_diff
            }

        return {
            "session_1": {
                "session_id": session_id_1,
                "persona_id": s1.get("persona_id"),
                "scenario_id": s1.get("scenario_id"),
                "language": s1.get("language"),
                "turns": s1.get("turn_count", len(m1) // 2),
                "status": s1.get("status")
            },
            "session_2": {
                "session_id": session_id_2,
                "persona_id": s2.get("persona_id"),
                "scenario_id": s2.get("scenario_id"),
                "language": s2.get("language"),
                "turns": s2.get("turn_count", len(m2) // 2),
                "status": s2.get("status")
            },
            "turn_comparison": paired_turns,
            "score_comparison": score_comparison
        }


replay_engine = ReplayEngine()
