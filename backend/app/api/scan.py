from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.db import get_db
from ..core.validation import validate_file_magic
from ..api.deps import get_current_user
from ..models.db import User
from ..services.scanner import scanner_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scan", tags=["Document Scanning"])

@router.post("")
async def scan_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a receipt/invoice document (PDF or Image) and extract transaction sales records.
    """
    filename = file.filename or ""
    mime_type = file.content_type or ""
    
    # Simple extension verification
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ["pdf", "jpg", "jpeg", "png", "webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Supported: .pdf, .jpg, .jpeg, .png, .webp"
        )

    content = await file.read()
    # Validate magic bytes to prevent malicious/corrupt file uploads
    validate_file_magic(content, filename)
    # 10 MB cap check
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds 10 MB limit."
        )

    try:
        # Determine actual mime type if empty
        if not mime_type:
            if ext == "pdf":
                mime_type = "application/pdf"
            elif ext in ["jpg", "jpeg"]:
                mime_type = "image/jpeg"
            else:
                mime_type = f"image/{ext}"

        extracted_items = await scanner_service.scan_invoice(content, mime_type)
        return {
            "success": True,
            "filename": filename,
            "items": extracted_items,
            "message": f"Successfully parsed document. Found {len(extracted_items)} items."
        }
    except Exception as e:
        logger.exception("Failed to scan invoice document")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI scanner failed to extract transaction details: {str(e)}"
        )
