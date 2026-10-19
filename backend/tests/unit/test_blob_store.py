"""Local blob round-trip and a mocked S3 client."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import boto3
import pytest

from docu.storage.blob_store import BlobMissingError, LocalBlobStore, S3BlobStore

SECRET = "test-secret-key-32-bytes-minimum!!"


def test_local_round_trip_and_delete(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path, secret=SECRET)
    store.put("present", b"hello", content_type="text/plain")
    assert store.get("present") == b"hello"
    store.delete("present")
    with pytest.raises(BlobMissingError):
        store.get("present")


def test_local_missing_key_raises_blob_missing(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path, secret=SECRET)
    with pytest.raises(BlobMissingError):
        store.get("gone")


def test_local_presign_urls(tmp_path: Path) -> None:
    store = LocalBlobStore(tmp_path, secret=SECRET)
    signed = store.presigned_put("pic", "image/png", 1024)
    assert signed["url"].startswith("/v1/_local-upload/pic?sig=")
    get_url = store.presigned_get("pic", "pic.png")
    assert get_url.startswith("/v1/_local-upload/pic?sig=")


def test_s3_store_uses_mocked_client(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    client.head_bucket.return_value = {}
    client.generate_presigned_post.return_value = {"url": "http://s3/put", "fields": {}}
    client.generate_presigned_url.return_value = "http://s3/get"

    def _client(**kwargs: Any) -> MagicMock:
        assert kwargs["service_name"] == "s3"
        return client

    monkeypatch.setattr(boto3, "client", _client)
    store = S3BlobStore(
        bucket="docu",
        region="us-east-1",
        endpoint_url="http://localhost:9000",
        access_key="minio",
        secret_key="minio12345",
    )
    signed = store.presigned_put("k", "image/png", 100)
    assert signed["url"] == "http://s3/put"
    conditions = client.generate_presigned_post.call_args.kwargs["Conditions"]
    assert ["content-length-range", 1, 100] in conditions
    assert store.presigned_get("k", "k.png") == "http://s3/get"
