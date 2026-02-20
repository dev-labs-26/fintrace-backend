"""
API Routes – /analyze endpoint
"""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.models.schemas import AnalysisResponse
from app.services.csv_parser import parse_csv
from app.services.graph_builder import build_graph, get_degree_map
from app.services.json_formatter import build_response
from app.services.pattern_detector import run_all_detectors
from app.services.scoring_engine import compute_ring_risk_scores, score_accounts

router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analyze financial transactions for money muling patterns",
    description=(
        "Upload a CSV or Excel file containing transaction records. "
        "The engine builds a directed graph, runs cycle / smurfing / "
        "layered-shell detection, scores each account, and returns a "
        "structured fraud report. Supports CSV, TSV, XLSX, XLS formats."
    ),
    responses={
        200: {"description": "Successful fraud analysis report"},
        400: {"description": "Invalid or malformed file"},
        500: {"description": "Internal server error"},
    },
)
async def analyze_transactions(
    file: Annotated[UploadFile, File(description="Transaction file (CSV, TSV, XLSX, XLS)")],
) -> AnalysisResponse:
    """
    POST /analyze
    ─────────────
    Accepts a multipart/form-data file upload with field name ``file``.
    Returns a JSON fraud report matching the Fintrace exact schema.
    """
    start_time = time.perf_counter()

    # ── 1. Validate file type ─────────────────────────────────────────────────
    allowed_extensions = {'.csv', '.tsv', '.xlsx', '.xls'}
    filename = file.filename or "file.csv"
    file_ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: CSV, TSV, XLSX, XLS. Got: {filename}",
        )

    # ── 2. Parse & validate file ──────────────────────────────────────────────
    df = parse_csv(file.file, filename)

    # ── 3. Build directed transaction graph ───────────────────────────────────
    G = build_graph(df)
    degree_map = get_degree_map(G)

    # ── 4. Detect patterns ────────────────────────────────────────────────────
    all_rings = run_all_detectors(G, df, degree_map)

    # ── 5. Score accounts ─────────────────────────────────────────────────────
    score_map, pattern_map, account_ring_map = score_accounts(all_rings, G, df)

    # ── 6. Enrich rings with risk scores ──────────────────────────────────────
    all_rings = compute_ring_risk_scores(all_rings, score_map)

    # ── 7. Assemble response ──────────────────────────────────────────────────
    elapsed = time.perf_counter() - start_time
    response = build_response(
        all_rings=all_rings,
        score_map=score_map,
        pattern_map=pattern_map,
        account_ring_map=account_ring_map,
        G=G,
        processing_time=elapsed,
        df=df,
    )

    return response


@router.get(
    "/health",
    summary="Health check endpoint",
    description="Returns service status and version information",
)
async def health_check():
    """
    GET /health
    ───────────
    Simple health check to verify the service is running.
    """
    return {
        "status": "healthy",
        "service": "Financial Forensics Engine",
        "version": "1.0.0",
    }


@router.post(
    "/export/csv",
    summary="Export analysis results as CSV",
    description="Converts analysis results to CSV format for download",
)
async def export_to_csv(analysis: AnalysisResponse):
    """
    POST /export/csv
    ────────────────
    Accepts an AnalysisResponse and returns CSV formatted data.
    """
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write suspicious accounts
    writer.writerow(["Suspicious Accounts"])
    writer.writerow(["Account ID", "Suspicion Score", "Detected Patterns", "Ring ID"])
    for account in analysis.suspicious_accounts:
        writer.writerow([
            account.account_id,
            account.suspicion_score,
            ", ".join(account.detected_patterns),
            account.ring_id or "N/A"
        ])
    
    writer.writerow([])
    
    # Write fraud rings
    writer.writerow(["Fraud Rings"])
    writer.writerow(["Ring ID", "Pattern Type", "Risk Score", "Member Accounts"])
    for ring in analysis.fraud_rings:
        writer.writerow([
            ring.ring_id,
            ring.pattern_type,
            ring.risk_score,
            ", ".join(ring.member_accounts)
        ])
    
    writer.writerow([])
    
    # Write summary
    writer.writerow(["Summary"])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Accounts Analyzed", analysis.summary.total_accounts_analyzed])
    writer.writerow(["Suspicious Accounts Flagged", analysis.summary.suspicious_accounts_flagged])
    writer.writerow(["Fraud Rings Detected", analysis.summary.fraud_rings_detected])
    writer.writerow(["Processing Time (seconds)", analysis.summary.processing_time_seconds])
    
    from fastapi.responses import StreamingResponse
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fraud_analysis.csv"}
    )
