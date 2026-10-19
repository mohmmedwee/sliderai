"""Upload / blob-store settings face (local dir or S3)."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

__all__ = ["FILES_FLAT", "FilesSettings"]


class FilesSettings(BaseModel):
    """Where user uploads live and how large a read slice may be."""

    upload_dir: Path = Field(default=Path("uploads"))
    file_storage: str = Field(default="local")
    s3_endpoint_url: str | None = Field(default=None)
    s3_bucket: str = Field(default="docu")
    s3_access_key: str = Field(default="")
    s3_secret_key: str = Field(default="")
    s3_region: str = Field(default="us-east-1")
    max_upload_bytes: int = Field(default=26_214_400, gt=0)
    max_file_chars: int = Field(default=12_000, gt=0)


FILES_FLAT: dict[str, str] = {
    "max_file_chars": "max_file_chars",
}
