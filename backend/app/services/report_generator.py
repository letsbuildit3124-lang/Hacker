"""
Report Generator for Honeypot Simulations.

Generates comprehensive evaluation and dialogue reports in:
1. Structured JSON format (including full metadata, transcript, intelligence metrics, 10-score matrix, and LLM judge qualitative recommendations)
2. Formatted CSV format (dialogue turns and metrics summary)
"""
import io
import csv
import json
import time
from typing import Dict, Any, Optional
from backend.app.config import settings
from backend.app.database.mongodb import db
from backend.app.services.evaluation_engine import evaluation_engine
from backend.app.utils.logger import logger


class ReportGenerator:
    """Generates structured downloadable reports in JSON and CSV formats."""

    async def generate_json_report(self, session_id: str) -> Dict[str, Any]:
        """
        Builds a comprehensive JSON report for a given session.
        If an evaluation does not exist yet, it triggers an evaluation first.
        """
        session = await db.get_session(session_id)
        if not session:
            return {"error": f"Session '{session_id}' not found."}

        messages = await db.get_messages(session_id)
        evaluation = await db.get_evaluation(session_id)

        if not evaluation and len(messages) >= 2:
            try:
                evaluation = await evaluation_engine.evaluate_session(session_id)
            except Exception as ex:
                logger.warning(f"Could not automatically compute evaluation for report: {ex}")

        # Construct full report document
        report = {
            "report_metadata": {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "platform": "Agentic Honeypot AI Red-Team Simulation Platform",
                "version": "3.0.0",
                "target_honeypot": settings.HONEYPOT_BASE_URL
            },
            "session_summary": {
                "session_id": session_id,
                "scenario_id": session.get("scenario_id"),
                "persona_id": session.get("persona_id"),
                "language": session.get("language", "English"),
                "locale": session.get("locale", "IN"),
                "channel": session.get("channel", "SMS"),
                "status": session.get("status"),
                "total_turns": session.get("turn_count", len(messages) // 2),
                "total_messages": len(messages),
                "created_at": session.get("created_at"),
                "updated_at": session.get("updated_at")
            },
            "evaluation": evaluation if evaluation else {
                "status": "not_evaluated",
                "message": "Evaluation has not been performed for this session yet."
            },
            "transcript": [
                {
                    "turn_index": (idx // 2) + 1,
                    "sender": msg.get("sender"),
                    "text": msg.get("text"),
                    "timestamp": msg.get("timestamp"),
                    "metadata": msg.get("metadata", {})
                }
                for idx, msg in enumerate(messages)
            ]
        }

        return report

    async def generate_csv_report(self, session_id: str) -> str:
        """
        Generates a tabular CSV text report containing transcript turns and evaluation metrics.
        """
        report_data = await self.generate_json_report(session_id)
        if "error" in report_data:
            return f"Error: {report_data['error']}"

        output = io.StringIO()
        writer = csv.writer(output)

        # Header section
        writer.writerow(["=== AGENTIC HONEYPOT SIMULATION REPORT ==="])
        writer.writerow(["Session ID", report_data["session_summary"]["session_id"]])
        writer.writerow(["Scenario", report_data["session_summary"]["scenario_id"]])
        writer.writerow(["Persona", report_data["session_summary"]["persona_id"]])
        writer.writerow(["Language", report_data["session_summary"]["language"]])
        writer.writerow(["Total Turns", report_data["session_summary"]["total_turns"]])
        writer.writerow(["Total Messages", report_data["session_summary"]["total_messages"]])
        writer.writerow(["Generated At", report_data["report_metadata"]["generated_at"]])
        writer.writerow([])

        # Evaluation metrics section
        eval_data = report_data.get("evaluation", {})
        if eval_data.get("overall_score") is not None:
            writer.writerow(["=== EVALUATION METRICS SUMMARY ==="])
            writer.writerow(["Overall Score", f"{eval_data.get('overall_score', 0)} / 100", f"Tier: {eval_data.get('performance_tier', 'N/A')}"])
            writer.writerow(["Metric Name", "Score (0-100)", "Weight (%)"])

            weights = {
                "scam_detection": "15%",
                "conversation_continuity": "15%",
                "persona_consistency": "10%",
                "intelligence_extraction": "15%",
                "context_retention": "10%",
                "response_relevance": "10%",
                "hallucination_resistance": "10%",
                "conversation_naturalness": "5%",
                "api_reliability": "5%",
                "completion": "5%"
            }

            for metric, score in eval_data.get("metric_scores", {}).items():
                writer.writerow([metric, score, weights.get(metric, "N/A")])

            writer.writerow([])
            writer.writerow(["=== INTELLIGENCE EXTRACTION METRICS ==="])
            intel = eval_data.get("intelligence_metrics", {})
            writer.writerow(["Disclosed Artifacts Count", intel.get("disclosed_count", 0)])
            writer.writerow(["Extracted Artifacts Count", intel.get("extracted_count", 0)])
            writer.writerow(["Extraction Precision", f"{intel.get('precision', 0):.2f}"])
            writer.writerow(["Extraction Recall", f"{intel.get('recall', 0):.2f}"])
            writer.writerow(["Extraction F1 Score", f"{intel.get('f1_score', 0):.2f}"])
            writer.writerow([])

        # Transcript section
        writer.writerow(["=== CONVERSATION TRANSCRIPT ==="])
        writer.writerow(["Turn", "Sender", "Timestamp", "Message Text"])

        for msg in report_data.get("transcript", []):
            writer.writerow([
                msg.get("turn_index"),
                msg.get("sender"),
                msg.get("timestamp"),
                msg.get("text")
            ])

        return output.getvalue()


report_generator = ReportGenerator()
