"""
Analytics API Router.
Aggregates simulation outcomes, metric distributions, persona effectiveness, and scenario performance.
"""
from fastapi import APIRouter
from typing import Dict, Any, List
from backend.app.database.mongodb import db

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview", summary="Get global simulation and evaluation overview")
async def get_overview() -> Dict[str, Any]:
    """
    Returns platform-wide KPIs:
    - Total sessions, total turns, completed sessions
    - Average overall evaluation score
    - Detection rate & Intelligence extraction metrics
    """
    sessions_col = db.get_collection("sessions")
    evals_col = db.get_collection("evaluations")
    messages_col = db.get_collection("messages")

    sessions = await sessions_col.find({}).to_list(1000)
    evaluations = await evals_col.find({}).to_list(1000)
    total_messages = await messages_col.count_documents({})

    total_sessions = len(sessions)
    total_evaluations = len(evaluations)

    overall_scores = [e.get("overall_score") for e in evaluations if e.get("overall_score") is not None]
    avg_score = round(sum(overall_scores) / len(overall_scores), 2) if overall_scores else 0.0

    detection_scores = [
        e.get("metric_scores", {}).get("scam_detection")
        for e in evaluations
        if e.get("metric_scores", {}).get("scam_detection") is not None
    ]
    avg_detection = round(sum(detection_scores) / len(detection_scores), 2) if detection_scores else 0.0

    f1_scores = [
        e.get("intelligence_metrics", {}).get("f1_score")
        for e in evaluations
        if e.get("intelligence_metrics", {}).get("f1_score") is not None
    ]
    avg_f1 = round(sum(f1_scores) / len(f1_scores), 2) if f1_scores else 0.0

    # Count by status
    status_counts = {}
    for s in sessions:
        st = s.get("status", "unknown")
        status_counts[st] = status_counts.get(st, 0) + 1

    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "total_evaluated": total_evaluations,
        "status_distribution": status_counts,
        "average_score": avg_score,
        "average_scam_detection_score": avg_detection,
        "average_intelligence_f1": avg_f1
    }


@router.get("/scenarios", summary="Get performance breakdown by scenario")
async def get_scenario_analytics() -> List[Dict[str, Any]]:
    """
    Aggregates Honeypot performance metrics grouped by scenario.
    """
    evals_col = db.get_collection("evaluations")
    evaluations = await evals_col.find({}).to_list(1000)

    scenario_map: Dict[str, List[Dict[str, Any]]] = {}
    for ev in evaluations:
        sc = ev.get("scenario_id", "unknown")
        scenario_map.setdefault(sc, []).append(ev)

    results = []
    for sc, ev_list in scenario_map.items():
        scores = [e.get("overall_score", 0) for e in ev_list]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0
        det_scores = [e.get("metric_scores", {}).get("scam_detection", 0) for e in ev_list]
        avg_det = round(sum(det_scores) / len(det_scores), 2) if det_scores else 0

        results.append({
            "scenario_id": sc,
            "session_count": len(ev_list),
            "average_score": avg_score,
            "average_detection": avg_det
        })

    return results


@router.get("/personas", summary="Get performance breakdown by persona")
async def get_persona_analytics() -> List[Dict[str, Any]]:
    """
    Aggregates Honeypot performance metrics grouped by attacker persona.
    """
    evals_col = db.get_collection("evaluations")
    evaluations = await evals_col.find({}).to_list(1000)

    persona_map: Dict[str, List[Dict[str, Any]]] = {}
    for ev in evaluations:
        p = ev.get("persona_id", "unknown")
        persona_map.setdefault(p, []).append(ev)

    results = []
    for p, ev_list in persona_map.items():
        scores = [e.get("overall_score", 0) for e in ev_list]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0
        cont_scores = [e.get("metric_scores", {}).get("conversation_continuity", 0) for e in ev_list]
        avg_cont = round(sum(cont_scores) / len(cont_scores), 2) if cont_scores else 0

        results.append({
            "persona_id": p,
            "session_count": len(ev_list),
            "average_score": avg_score,
            "average_continuity": avg_cont
        })

    return results
