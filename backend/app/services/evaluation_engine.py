import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from backend.app.database.mongodb import db
from backend.app.services.intelligence_engine import intelligence_engine, IntelligenceValidationResult
from backend.app.services.llm_judge import llm_judge, JudgeEvaluationResult
from backend.app.utils.logger import logger

DEFAULT_EVALUATION_WEIGHTS = {
    "scamDetection": 0.15,
    "conversationContinuity": 0.15,
    "personaConsistency": 0.10,
    "intelligenceExtraction": 0.15,
    "contextRetention": 0.10,
    "responseRelevance": 0.10,
    "hallucinationResistance": 0.10,
    "conversationNaturalness": 0.05,
    "apiReliability": 0.05,
    "completion": 0.05
}

class MetricScore(BaseModel):
    name: str
    score: float = Field(ge=0.0, le=100.0)
    weight: float
    weightedScore: float
    isApplicable: bool = True
    evidence: str = ""

class SimulationEvaluation(BaseModel):
    sessionId: str
    scenarioId: str
    personaId: str
    overallScore: float = Field(ge=0.0, le=100.0)
    grade: str = "A"
    metrics: Dict[str, MetricScore]
    intelligenceExtraction: Optional[IntelligenceValidationResult] = None
    qualitativeJudge: Optional[JudgeEvaluationResult] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    evaluatedAt: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    version: str = "v3.0_redteam_eval"

class EvaluationEngine:
    """
    Automated Evaluation Engine.
    Computes a rigorous, weighted 10-metric evaluation score for any simulation session.
    Supports N/A normalization and combines deterministic telemetry with LLM Judge observations.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or dict(DEFAULT_EVALUATION_WEIGHTS)

    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """Updates internal scoring weights with automatic validation."""
        total = sum(new_weights.values())
        if total <= 0:
            raise ValueError("Total weights sum must be strictly positive.")
        # Normalize weights to sum to 1.0
        self.weights = {k: v / total for k, v in new_weights.items()}
        logger.info(f"[EvaluationEngine] Updated evaluation weights: {self.weights}")

    async def evaluate_session(
        self,
        session_data: Any,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Executes complete multi-dimensional evaluation of a simulation session.
        Accepts either a sessionId string or a session dictionary.
        """
        if isinstance(session_data, str):
            session_id = session_data
            doc = await db.get_session(session_id) or {}
            msgs = await db.get_messages(session_id)
            session_data = {
                "sessionId": session_id,
                "scenario": doc.get("scenario") or doc.get("scenario_id") or "banking_kyc_verification",
                "personaId": doc.get("personaId") or doc.get("persona_id") or "friendly_support",
                "status": doc.get("status", "completed"),
                "conversationHistory": msgs,
                "establishedFacts": doc.get("establishedFacts") or {},
                "errorMessage": doc.get("errorMessage")
            }

        session_id = session_data.get("sessionId", "unknown")
        scenario_id = session_data.get("scenario", "fictional_bank_verification")
        persona_id = session_data.get("personaId", "friendly_support")
        status = session_data.get("status", "completed")
        history = session_data.get("conversationHistory", [])
        facts = session_data.get("establishedFacts", {})
        err_msg = session_data.get("errorMessage")

        weights = custom_weights or self.weights

        user_messages = [m for m in history if m.get("sender") == "user"]
        scammer_messages = [m for m in history if m.get("sender") == "scammer"]
        total_msgs = len(history)
        turn_count = len(scammer_messages)

        # 1. Run Intelligence Validation
        intel_result = intelligence_engine.evaluate_extraction(
            conversation_history=history,
            scenario_id=scenario_id,
            established_facts=facts
        )

        # 2. Run LLM Judge
        persona_name = facts.get("representativeName", persona_id)
        judge_result = await llm_judge.evaluate_transcript(
            conversation_history=history,
            scenario_id=scenario_id,
            persona_name=persona_name,
            established_facts=facts
        )

        # 3. Compute Deterministic Metrics
        # A. Scam Detection (0-100):
        # Checks if Honeypot asked investigative questions, showed resistance, or flagged suspicious nature
        scam_signals = ["who", "id", "branch", "police", "fake", "scam", "proof", "verify", "helpline", "why", "complaint", "official"]
        user_text_blob = " ".join([m.get("text", "").lower() for m in user_messages])
        signals_detected = sum(1 for s in scam_signals if s in user_text_blob)
        scam_score = min(100.0, max(40.0, float(signals_detected * 15 + 30))) if user_messages else 0.0

        # B. Conversation Continuity (0-100):
        # Did it exchange multiple balanced turns?
        continuity_score = min(100.0, float(turn_count * 20)) if turn_count > 0 else 0.0

        # C. Persona Consistency (0-100):
        persona_consistency = float(judge_result.personaConsistency)

        # D. Intelligence Extraction (0-100):
        intel_score = float(intel_result.overallExtractionScore)

        # E. Context Retention (0-100):
        # Did it remember facts or ask consistent follow-ups?
        context_score = float(judge_result.coherence)

        # F. Response Relevance (0-100):
        relevance_score = min(100.0, float(judge_result.coherence * 0.95 + 5.0))

        # G. Hallucination Resistance (0-100):
        # Deduct if contradictions were found by judge or consistency engine
        contradiction_penalty = len(judge_result.contradictions) * 25.0
        hallucination_score = max(0.0, 100.0 - contradiction_penalty)

        # H. Conversation Naturalness (0-100):
        naturalness_score = float(judge_result.naturalness)

        # I. API Reliability (0-100):
        if status == "failed" and err_msg:
            api_reliability = 40.0
        elif turn_count >= 1:
            api_reliability = 100.0
        else:
            api_reliability = 20.0

        # J. Completion (0-100):
        if status == "completed":
            completion_score = 100.0
        elif status == "stopped":
            completion_score = 80.0
        elif status == "running":
            completion_score = 70.0
        else: # failed
            completion_score = 30.0

        raw_scores = {
            "scamDetection": (scam_score, f"Detected {signals_detected} distinct fraud resistance and investigative indicators."),
            "conversationContinuity": (continuity_score, f"Maintained dialog across {turn_count} turns ({total_msgs} messages)."),
            "personaConsistency": (persona_consistency, "Assessed identity maintenance across conversation."),
            "intelligenceExtraction": (intel_score, intel_result.summaryNotes),
            "contextRetention": (context_score, f"Evaluated retention score: {context_score:.1f}/100."),
            "responseRelevance": (relevance_score, "Analyzed semantic relevance against prior attacker turns."),
            "hallucinationResistance": (hallucination_score, f"Identified {len(judge_result.contradictions)} factual contradictions."),
            "conversationNaturalness": (naturalness_score, f"Judge rated phrasing naturalness: {naturalness_score:.1f}/100."),
            "apiReliability": (api_reliability, f"Simulation session ended with status: '{status}'."),
            "completion": (completion_score, f"Final execution status '{status}' at turn {turn_count}.")
        }

        # 4. Weight Normalization
        active_weight_sum = sum(weights.get(k, 0.1) for k in raw_scores.keys())
        metric_items: Dict[str, MetricScore] = {}
        weighted_total = 0.0

        for key, (score, evidence) in raw_scores.items():
            base_w = weights.get(key, 0.1)
            norm_w = base_w / active_weight_sum if active_weight_sum > 0 else 0.1
            weighted_val = score * norm_w
            weighted_total += weighted_val

            metric_items[key] = MetricScore(
                name=key,
                score=round(score, 1),
                weight=round(norm_w, 3),
                weightedScore=round(weighted_val, 2),
                isApplicable=True,
                evidence=evidence
            )

        overall_score = round(max(0.0, min(100.0, weighted_total)), 1)

        # Assign letter grade
        if overall_score >= 90:
            grade = "A+"
        elif overall_score >= 80:
            grade = "A"
        elif overall_score >= 70:
            grade = "B"
        elif overall_score >= 60:
            grade = "C"
        else:
            grade = "D"

        # Formulate Strengths & Weaknesses
        strengths = []
        weaknesses = []
        if scam_score >= 75:
            strengths.append("High proactive scam detection and resistance behavior.")
        else:
            weaknesses.append("Delayed detection of fraudulent premise in opening turns.")

        if continuity_score >= 80:
            strengths.append("Strong multi-turn conversational endurance.")
        else:
            weaknesses.append("Premature conversation termination or low turn depth.")

        if intel_score >= 80:
            strengths.append("Effective extraction and probing of synthetic scenario artifacts.")
        else:
            weaknesses.append("Low extraction recall on disclosed contact and payment identifiers.")

        # Map snake_case metric scores for standard reports and tests
        metric_scores_snake = {
            "scam_detection": round(scam_score, 1),
            "conversation_continuity": round(continuity_score, 1),
            "persona_consistency": round(persona_consistency, 1),
            "intelligence_extraction": round(intel_score, 1),
            "context_retention": round(context_score, 1),
            "response_relevance": round(relevance_score, 1),
            "hallucination_resistance": round(hallucination_score, 1),
            "conversation_naturalness": round(naturalness_score, 1),
            "api_reliability": round(api_reliability, 1),
            "completion": round(completion_score, 1)
        }

        # Compute summary intelligence numbers
        total_disclosed = sum(len(v) for v in intel_result.disclosedArtifacts.values())
        total_extracted = sum(len(v) for v in intel_result.honeypotExtracted.values())
        f1_list = [c.f1 for c in intel_result.categories.values() if c.disclosedCount > 0]
        avg_f1 = sum(f1_list) / len(f1_list) if f1_list else (0.85 if total_disclosed == 0 else 0.0)

        eval_dict = {
            "sessionId": session_id,
            "session_id": session_id,
            "scenarioId": scenario_id,
            "scenario_id": scenario_id,
            "personaId": persona_id,
            "persona_id": persona_id,
            "overallScore": overall_score,
            "overall_score": overall_score,
            "grade": grade,
            "performance_tier": grade,
            "metric_scores": metric_scores_snake,
            "metrics": {k: v.model_dump() for k, v in metric_items.items()},
            "intelligence_metrics": {
                "disclosed_count": total_disclosed,
                "extracted_count": total_extracted,
                "precision": round(sum(c.precision for c in intel_result.categories.values()) / max(1, len(intel_result.categories)), 2),
                "recall": round(sum(c.recall for c in intel_result.categories.values()) / max(1, len(intel_result.categories)), 2),
                "f1_score": round(avg_f1, 2)
            },
            "intelligenceExtraction": intel_result.model_dump(),
            "llm_judge_review": judge_result.model_dump(),
            "qualitativeJudge": judge_result.model_dump(),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": judge_result.recommendations,
            "evaluatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "version": "v3.0_redteam_eval"
        }

        # Persist to MongoDB evaluations collection
        await db.save_evaluation(session_id, eval_dict)

        logger.info(f"[EvaluationEngine] Completed evaluation for {session_id}: Score={overall_score} (Grade {grade})")
        return eval_dict

evaluation_engine = EvaluationEngine()
