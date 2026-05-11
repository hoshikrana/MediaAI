import io
import re
import uuid
import logging
import unicodedata
from pathlib import Path
from dataclasses import dataclass
from fastapi import UploadFile
import magic
from PIL import Image

from backend.core.config import settings
from backend.core.exceptions import (
    FileTooLargeError, InvalidFileTypeError, InvalidFileError, 
    SecurityError, PromptInjectionError, ValidationError, PathTraversalError
)

logger = logging.getLogger(__name__)

@dataclass
class ImageMetadata:
    filename: str
    size_bytes: int
    mime_type: str
    width: int
    height: int
    mode: str
    content: bytes

class ImageValidator:
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/dicom"}
    MAX_SIZE_BYTES = 10 * 1024 * 1024
    MIN_DIMENSION = 64
    MAX_DIMENSION = 4096
    
    @staticmethod
    async def validate(file: UploadFile) -> ImageMetadata:
        max_size = settings.max_upload_bytes
        content = await file.read(max_size + 1)
        if len(content) > max_size:
            raise FileTooLargeError(f"Max file size is {settings.MAX_UPLOAD_SIZE_MB}MB")
        await file.seek(0)
        
        # Verify Mime via Magic Bytes
        mime = magic.from_buffer(content[:2048], mime=True)
        if mime not in ImageValidator.ALLOWED_MIME_TYPES:
            raise InvalidFileTypeError(f"File type '{mime}' not supported. Allowed: {', '.join(ImageValidator.ALLOWED_MIME_TYPES)}")
            
        try:
            with Image.open(io.BytesIO(content)) as img:
                width, height = img.size
                mode = img.mode
        except Exception:
            raise InvalidFileError("File is corrupted or cannot be read as an image")
            
        if width < ImageValidator.MIN_DIMENSION or height < ImageValidator.MIN_DIMENSION:
            raise InvalidFileError(f"Image too small (min {ImageValidator.MIN_DIMENSION}px)")
        if width > ImageValidator.MAX_DIMENSION or height > ImageValidator.MAX_DIMENSION:
            raise InvalidFileError(f"Image too large (max {ImageValidator.MAX_DIMENSION}px)")
            
        # EXIF script injection check
        first_2kb = content[:2048].decode('utf-8', errors='ignore').lower()
        if any(bad in first_2kb for bad in ["<script", "javascript:", "eval("]):
            logger.error("Security alert: Script payload detected in image bytes")
            raise SecurityError("Invalid file content detected")
            
        return ImageMetadata(
            filename=file.filename or "unknown.png", size_bytes=len(content),
            mime_type=mime, width=width, height=height, mode=mode, content=content
        )

def sanitize_symptoms_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"<[^>]+>", "", text)
    
    INJECTION_PATTERNS = [
        r"ignore\s+(previous|all|above)\s+instructions",
        r"you\s+are\s+now\s+(a|an)",
        r"system\s*:",
        r"assistant\s*:",
        r"jailbreak",
        r"DAN\s+mode",
        r"pretend\s+you\s+are"
    ]
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"Prompt injection detected in input", extra={"pattern": pattern})
            raise PromptInjectionError("Input contains disallowed content. Please describe symptoms naturally.")
            
    MAX_LENGTH = 2000
    if len(text) > MAX_LENGTH:
        text = text[:MAX_LENGTH]
        
    return " ".join(text.split()).strip()

def validate_patient_id(patient_id: str) -> str:
    if not patient_id:
        return ""
    if not re.match(r"^[a-zA-Z0-9_-]{1,50}$", patient_id):
        raise ValidationError("Patient ID must be 1-50 characters: letters, numbers, hyphens, underscores only")
    return patient_id

def validate_chat_message(message: str) -> str:
    if not message or not message.strip():
        raise ValidationError("Message cannot be empty")
    if len(message) > 500:
        raise ValidationError("Message too long (max 500 characters)")
    return sanitize_symptoms_text(message)

def safe_temp_path(filename: str) -> Path:
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", Path(filename).name)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    temp_path = settings.TEMP_DIR / unique_name
    
    resolved = temp_path.resolve()
    temp_dir_resolved = settings.TEMP_DIR.resolve()
    if not str(resolved).startswith(str(temp_dir_resolved)):
        raise PathTraversalError(f"Invalid path detected: {filename}")
        
    return temp_path
