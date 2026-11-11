"""
Reports API Router.
Generates downloadable evaluation reports in JSON and CSV formats.
"""
from fastapi import APIRouter, HTTPException, Response
from backend.app.services.report_generator import report_generator

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/{session_id}/json", summary="Download JSON Evaluation Report")
async def get_json_report(session_id: str):
    """
    Returns a comprehensive JSON document containing session metadata,
    transcript turns, intelligence extraction metrics, and LLM evaluation recommendations.
    """
    report = await report_generator.generate_json_report(session_id)
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    return report


@router.get("/{session_id}/csv", summary="Download CSV Evaluation Report")
async def get_csv_report(session_id: str):
    """
    Generates a tabular CSV file including dialogue turns, timing, and metric breakdown.
    """
    csv_content = await report_generator.generate_csv_report(session_id)
    if csv_content.startswith("Error:"):
        raise HTTPException(status_code=404, detail=csv_content)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="honeypot_report_{session_id}.csv"'
        }
    )
