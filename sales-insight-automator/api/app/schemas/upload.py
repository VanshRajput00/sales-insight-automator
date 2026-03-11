# Lead Engineer Note: Pydantic v2 schemas act as our contract layer.
# Any data that doesn't match these shapes is rejected with a 422 error
# BEFORE it ever touches our business logic. This is the security gate.

from pydantic import BaseModel
from typing import Optional


class UploadResponse(BaseModel):
    """Response model for successful CSV uploads with AI analysis."""
    status: str
    filename: str
    rows_analyzed: int
    stats: dict
    ai_brief: str
    recipient_email: str
    email_status: str       # "sent" | "failed"
    message: str


class ErrorResponse(BaseModel):
    """Standardized error shape so the frontend always knows what to expect."""
    status: str = "error"
    detail: str
    error_code: Optional[str] = None
