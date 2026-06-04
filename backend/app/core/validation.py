import re
import html
from typing import Any
from fastapi import HTTPException

# Standard magic bytes
ZIP_MAGIC = b"PK\x03\x04"
XLS_MAGIC = b"\xd0\xcf\x11\xe0"

def validate_file_magic(content: bytes, filename: str) -> None:
    """
    Validates file headers (magic bytes) to ensure the uploaded file format
    matches its extension. Prevents uploading malicious binaries disguised as CSV/XLSX.
    """
    fn_lower = filename.lower()
    if fn_lower.endswith(".xlsx"):
        if not content.startswith(ZIP_MAGIC):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format: File header does not match Excel (.xlsx) format."
            )
    elif fn_lower.endswith(".xls"):
        if not content.startswith(XLS_MAGIC):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format: File header does not match Excel (.xls) format."
            )
    elif fn_lower.endswith(".csv"):
        # Ensure it is a text-like file, not a binary executable
        # Check first 4 bytes for common binary headers: PE (MZ), ELF (\x7fELF), ZIP (PK)
        if content.startswith(b"MZ") or content.startswith(b"\x7fELF") or content.startswith(ZIP_MAGIC):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format: Binary file uploaded as CSV."
            )
        # Verify it can be decoded as text
        try:
            content[:1024].decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                content[:1024].decode("latin-1")
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file format: Unable to decode file content as text."
                )

def sanitize_string(val: Any) -> str:
    """
    Sanitizes string inputs to prevent HTML injection/XSS and strips leading/trailing whitespaces.
    If the input is not a string, returns its string representation.
    """
    if val is None:
        return ""
    
    s = str(val).strip()
    # Remove null bytes
    s = s.replace("\x00", "")
    # Escape HTML tags
    s = html.escape(s)
    return s
