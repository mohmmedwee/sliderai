"""Byte storage for uploaded files — local disk or S3/MinIO.

Postgres keeps metadata and ownership; this layer only holds opaque blobs keyed
by `storage_key`. Local mode is the default for single-node / dev; S3 mode is
what multi-pod deploys need so every replica sees the same bytes.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Protocol

from itsdangerous import URLSafeTimedSerializer

__all__ = [
    "BlobMissingError",
    "BlobStore",
    "LocalBlobStore",
    "S3BlobStore",
    "build_blob_store",
]

logger = logging.getLogger(__name__)


class BlobMissingError(LookupError):
    """The metadata row exists but its bytes are gone (e.g. lost local disk)."""


class BlobStore(Protocol):
    def put(self, key: str, data: bytes, *, content_type: str | None = None) -> None: ...

    def get(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...

    def presigned_put(
        self, key: str, content_type: str, max_bytes: int, expires: int = 900
    ) -> dict[str, Any]: ...

    def presigned_get(self, key: str, filename: str, expires: int = 86400) -> str: ...


class LocalBlobStore:
    def __init__(self, directory: Path, *, secret: str) -> None:
        self._directory = directory
        self._secret = secret
        self._directory.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self._directory / key

    def _serializer(self) -> URLSafeTimedSerializer:
        return URLSafeTimedSerializer(self._secret, salt="docu-local-upload")

    def put(self, key: str, data: bytes, *, content_type: str | None = None) -> None:
        del content_type  # unused on disk
        self._path(key).write_bytes(data)

    def get(self, key: str) -> bytes:
        try:
            return self._path(key).read_bytes()
        except FileNotFoundError as exc:
            raise BlobMissingError(key) from exc

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def presigned_put(
        self, key: str, content_type: str, max_bytes: int, expires: int = 900
    ) -> dict[str, Any]:
        sig = self._serializer().dumps(
            {"op": "put", "key": key, "content_type": content_type, "max_bytes": max_bytes}
        )
        return {"url": f"/v1/_local-upload/{key}?sig={sig}", "fields": {"expires": expires}}

    def presigned_get(self, key: str, filename: str, expires: int = 86400) -> str:
        sig = self._serializer().dumps({"op": "get", "key": key, "filename": filename})
        return f"/v1/_local-upload/{key}?sig={sig}&exp={expires}"


class S3BlobStore:
    """S3-compatible object storage (AWS S3, MinIO, Garage, …)."""

    def __init__(
        self,
        *,
        bucket: str,
        region: str,
        endpoint_url: str | None,
        access_key: str,
        secret_key: str,
    ) -> None:
        import boto3  # type: ignore[import-untyped]
        from botocore.client import Config  # type: ignore[import-untyped]

        self._bucket = bucket
        kwargs: dict[str, Any] = {
            "service_name": "s3",
            "region_name": region,
            "config": Config(signature_version="s3v4"),
        }
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        if access_key:
            kwargs["aws_access_key_id"] = access_key
        if secret_key:
            kwargs["aws_secret_access_key"] = secret_key
        self._client: Any = boto3.client(**kwargs)
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except Exception:
            logger.info("creating object-storage bucket %s", self._bucket)
            self._client.create_bucket(Bucket=self._bucket)

    def put(self, key: str, data: bytes, *, content_type: str | None = None) -> None:
        extra: dict[str, Any] = {}
        if content_type:
            extra["ContentType"] = content_type
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, **extra)

    def get(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except self._client.exceptions.NoSuchKey as exc:
            raise BlobMissingError(key) from exc
        return bytes(response["Body"].read())

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def presigned_put(
        self, key: str, content_type: str, max_bytes: int, expires: int = 900
    ) -> dict[str, Any]:
        result: dict[str, Any] = self._client.generate_presigned_post(
            Bucket=self._bucket,
            Key=key,
            Fields={"Content-Type": content_type},
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 1, max_bytes],
            ],
            ExpiresIn=expires,
        )
        return result

    def presigned_get(self, key: str, filename: str, expires: int = 86400) -> str:
        url: str = self._client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self._bucket,
                "Key": key,
                "ResponseContentDisposition": f'attachment; filename="{filename}"',
            },
            ExpiresIn=expires,
        )
        return url


def build_blob_store(settings: Any, upload_dir: Path) -> BlobStore:
    """Pick local or S3 from ``settings.storage``."""
    storage = settings.storage
    backend = (storage.file_storage or "local").lower()
    if backend == "s3":
        bucket = storage.s3_bucket or ""
        if not bucket:
            raise ValueError("file_storage=s3 requires s3_bucket")
        logger.info(
            "file storage: s3 bucket=%s endpoint=%s",
            bucket,
            storage.s3_endpoint_url or "aws-default",
        )
        return S3BlobStore(
            bucket=bucket,
            region=storage.s3_region or "us-east-1",
            endpoint_url=storage.s3_endpoint_url or None,
            access_key=storage.s3_access_key or "",
            secret_key=storage.s3_secret_key or "",
        )
    logger.info("file storage: local dir=%s", upload_dir)
    return LocalBlobStore(upload_dir, secret=settings.auth.secret_key)
