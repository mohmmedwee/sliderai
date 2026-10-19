"""Blob storage settings face."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

__all__ = ["STORAGE_FLAT", "StorageSettings"]


class StorageSettings(BaseModel):
    """Local directory or S3-compatible blob store."""

    file_storage: Literal["local", "s3"] = "local"
    upload_dir: Path = Field(default=Path("uploads"))
    s3_bucket: str = Field(default="docu")
    s3_endpoint_url: str = Field(default="")
    s3_region: str = Field(default="us-east-1")
    s3_access_key: str = Field(default="")
    s3_secret_key: str = Field(default="")
    max_upload_bytes: int = Field(default=26_214_400, gt=0)


STORAGE_FLAT: dict[str, str] = {
    "file_storage": "file_storage",
    "upload_dir": "upload_dir",
    "s3_bucket": "s3_bucket",
    "s3_endpoint_url": "s3_endpoint_url",
    "s3_region": "s3_region",
    "s3_access_key": "s3_access_key",
    "s3_secret_key": "s3_secret_key",
    "max_upload_bytes": "max_upload_bytes",
}
