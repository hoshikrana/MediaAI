import hashlib
import mimetypes
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from backend.core.config import settings


@dataclass(frozen=True)
class StoredFile:
    key: str
    url: str | None
    backend: str
    sha256: str
    size_bytes: int


class FileStorage:
    """Stores original uploads locally or in Cloudflare R2.

    The analysis queue still works from a temporary local processing file.
    This class keeps a durable copy for audit/history/download flows.
    """

    @staticmethod
    def save_upload(content: bytes, filename: str, user_id: str | None = None) -> StoredFile:
        digest = hashlib.sha256(content).hexdigest()
        safe_name = Path(filename or "upload.bin").name.replace(" ", "_")
        date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        owner = user_id or "anonymous"
        key = f"uploads/{owner}/{date_prefix}/{digest[:16]}_{safe_name}"

        if settings.STORAGE_BACKEND == "r2":
            return FileStorage._save_r2(content, key, digest)
        return FileStorage._save_local(content, key, digest)

    @staticmethod
    def _save_local(content: bytes, key: str, digest: str) -> StoredFile:
        target = settings.LOCAL_STORAGE_DIR / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return StoredFile(
            key=key,
            url=str(target),
            backend="local",
            sha256=digest,
            size_bytes=len(content),
        )

    @staticmethod
    def _save_r2(content: bytes, key: str, digest: str) -> StoredFile:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required when STORAGE_BACKEND=r2") from exc

        content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
        client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        client.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=content,
            ContentType=content_type,
            Metadata={"sha256": digest},
        )
        public_base = settings.R2_PUBLIC_BASE_URL.rstrip("/")
        return StoredFile(
            key=key,
            url=f"{public_base}/{key}" if public_base else None,
            backend="r2",
            sha256=digest,
            size_bytes=len(content),
        )

    @staticmethod
    def copy_to_temp(stored: StoredFile, temp_path: Path) -> Path:
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        if stored.backend == "local":
            source = Path(stored.url or "")
            if not source.exists():
                raise FileNotFoundError(f"Local file not found: {source}")
            shutil.copyfile(source, temp_path)
        
        elif stored.backend == "r2":
            try:
                import boto3
            except ImportError as exc:
                raise RuntimeError("boto3 is required when STORAGE_BACKEND=r2") from exc

            client = boto3.client(
                "s3",
                endpoint_url=settings.R2_ENDPOINT_URL,
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                region_name="auto",
            )
            client.download_file(settings.R2_BUCKET_NAME, stored.key, str(temp_path))
        
        else:
            raise ValueError(f"Unsupported storage backend: {stored.backend}")

        return temp_path
