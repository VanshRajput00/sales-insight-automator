# Lead Engineer Note: The router is now an orchestrator — it delegates to
# processor.py and ai_engine.py, handles all their exceptions, and maps them
# to correct HTTP status codes. This is the "thin controller" pattern.

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.schemas.upload import UploadResponse, ErrorResponse
from app.services.processor import process_sales_csv
from app.services.ai_engine import generate_sales_brief
from app.services.mailer import send_report_email
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Sales Data"])

ALLOWED_CONTENT_TYPES = {"text/csv", "application/vnd.ms-excel", "text/plain"}
MAX_FILE_SIZE_MB = 10


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file or malformed CSV"},
        502: {"model": ErrorResponse, "description": "AI service unavailable"},
    },
    summary="Upload Sales CSV for AI Analysis",
    description=(
        "Accepts a CSV file containing sales data and a recipient email address. "
        "Returns AI-generated executive summary with key metrics."
    ),
)
async def upload_sales_csv(
    file: UploadFile = File(..., description="Sales data in CSV format"),
    recipient_email: str = Form(..., description="Email address to receive the AI-generated report"),
):
    """
    Lead Engineer Note: UploadFile gives us a SpooledTemporaryFile under the hood —
    it holds small files in memory and only spills to disk when they exceed a threshold.
    This keeps the API fast without risking OOM errors on large uploads.
    """

    # --- Gate 1: File type ---
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Only CSV files are accepted.",
        )

    # --- Gate 2: File size ---
    raw_bytes = await file.read()
    if len(raw_bytes) / (1024 * 1024) > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {MAX_FILE_SIZE_MB}MB limit.",
        )

    # --- Stage 1: Data Processing ---
    try:
        stats = process_sales_csv(raw_bytes)
    except ValueError as e:
        # Malformed CSV or missing columns — client's fault → 400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # --- Stage 2: AI Generation ---
    try:
        ai_brief = generate_sales_brief(stats["summary_string"])
    except RuntimeError as e:
        # AI service failure — not client's fault → 502 Bad Gateway
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )

    # Stage 3: Email Delivery
    # Lead Engineer Note: We don't let email failure block the API response.
    # If the inbox send fails (SMTP down, wrong password), the user still gets
    # their JSON result. We log the failure for ops visibility.
    email_status = "sent"
    try:
        await send_report_email(recipient_email, ai_brief, dict(stats))
    except RuntimeError as e:
        logger.warning(f"Email delivery failed for {recipient_email}: {e}")
        email_status = "failed"

    return UploadResponse(
        status="success",
        filename=file.filename,
        rows_analyzed=stats["row_count"],
        stats={
            "total_revenue": stats["total_revenue"],
            "total_units_sold": stats["total_units_sold"],
            "top_category": stats["top_category"],
            "top_category_revenue": stats["top_category_revenue"],
        },
        ai_brief=ai_brief,
        recipient_email=recipient_email,
        email_status=email_status,
        message=(
            f"Report sent to {recipient_email} ✓"
            if email_status == "sent"
            else "Analysis complete. Email delivery failed — check SMTP config."
        ),
    )


@router.get("/health", summary="Health Check", description="Lightweight liveness probe for Docker and load balancers.")
async def health_check():
    return {"status": "healthy", "service": "sales-insight-automator-api", "version": "1.0.0"}
