"""Neon Object Storage client — S3-compatible storage for model artifacts.

Neon Object Storage is S3-compatible but uses **dedicated** credentials that
are separate from the PostgreSQL database password. These credentials are
issued per-branch and can be retrieved via:

  - Neon Console  →  Project  →  Object Storage  →  Credentials
  - Neon CLI:  neon env pull   (populates AWS_* vars in your .env)

Required environment variables
--------------------------------
  NEON_S3_ACCESS_KEY_ID      Branch S3 access key  (from Neon Console / env pull)
  NEON_S3_SECRET_ACCESS_KEY  Branch S3 secret key
  NEON_S3_ENDPOINT_URL       Branch S3 endpoint URL
                             e.g. https://s3.us-east-2.aws.neon.tech
  NEON_S3_REGION             AWS region code, e.g. us-east-2  (optional,
                             auto-parsed from endpoint URL if omitted)

These are set in config.py and read from .env / Render environment variables.

The bucket is created automatically at first startup if it does not exist.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import IO

logger = logging.getLogger(__name__)

_REGION_FROM_ENDPOINT_RE = re.compile(r"s3\.([a-z0-9-]+)\.aws\.neon\.tech")


def _region_from_endpoint(endpoint_url: str) -> str:
    """Parse the AWS region out of a Neon S3 endpoint URL.

    e.g. https://s3.ap-southeast-1.aws.neon.tech  →  ap-southeast-1
    """
    m = _REGION_FROM_ENDPOINT_RE.search(endpoint_url)
    return m.group(1) if m else "us-east-1"


class NeonStorageClient:
    """Thin wrapper around a boto3 S3 client pre-configured for Neon Object Storage.

    Parameters
    ----------
    access_key_id:
        Neon branch S3 access key  (NEON_S3_ACCESS_KEY_ID).
    secret_access_key:
        Neon branch S3 secret key  (NEON_S3_SECRET_ACCESS_KEY).
    endpoint_url:
        Neon branch S3 endpoint URL  (NEON_S3_ENDPOINT_URL).
    bucket_name:
        Target bucket name.  Created automatically by :meth:`ensure_bucket`.
    region:
        AWS region string.  Derived from *endpoint_url* when not supplied.
    """

    def __init__(
        self,
        *,
        access_key_id: str,
        secret_access_key: str,
        endpoint_url: str,
        bucket_name: str,
        region: str | None = None,
    ) -> None:
        self._bucket = bucket_name
        self._endpoint = endpoint_url.rstrip("/")
        self._region = region or _region_from_endpoint(self._endpoint)

        try:
            import boto3
            from botocore.config import Config
        except ImportError as exc:
            raise ImportError(
                "boto3 is required for Neon Object Storage. "
                "Add 'boto3' to requirements.txt and reinstall."
            ) from exc

        self._s3 = boto3.client(
            "s3",
            endpoint_url=self._endpoint,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=self._region,
            config=Config(
                s3={"addressing_style": "path"},  # Neon requires path-style
                connect_timeout=30,
                read_timeout=120,
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )
        logger.info(
            "NeonStorageClient ready — endpoint=%s  bucket=%s  region=%s",
            self._endpoint,
            self._bucket,
            self._region,
        )

    @classmethod
    def from_settings(cls, settings: object) -> "NeonStorageClient":
        """Construct from a Settings instance (reads NEON_S3_* fields)."""
        return cls(
            access_key_id=str(settings.neon_s3_access_key_id),  # type: ignore[attr-defined]
            secret_access_key=str(settings.neon_s3_secret_access_key),  # type: ignore[attr-defined]
            endpoint_url=str(settings.neon_s3_endpoint_url),  # type: ignore[attr-defined]
            bucket_name=str(settings.neon_bucket_name),  # type: ignore[attr-defined]
            region=str(settings.neon_s3_region) if settings.neon_s3_region else None,  # type: ignore[attr-defined]
        )

    # ------------------------------------------------------------------ bucket
    def ensure_bucket(self) -> None:
        """Create the bucket if it does not already exist (idempotent)."""
        from botocore.exceptions import ClientError

        try:
            self._s3.head_bucket(Bucket=self._bucket)
            logger.debug("Neon bucket '%s' already exists.", self._bucket)
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code in ("404", "NoSuchBucket"):
                logger.info("Creating Neon bucket '%s'…", self._bucket)
                self._s3.create_bucket(Bucket=self._bucket)
                logger.info("Neon bucket '%s' created.", self._bucket)
            else:
                raise RuntimeError(
                    f"Unexpected error checking Neon bucket '{self._bucket}': {exc}"
                ) from exc

    # ------------------------------------------------------------------ upload
    def upload_file(self, local_path: Path, key: str) -> None:
        """Upload *local_path* to the bucket at *key* (overwrites silently)."""
        local_path = Path(local_path)
        if not local_path.is_file():
            raise FileNotFoundError(f"Cannot upload — file not found: {local_path}")
        logger.info("Uploading %s → s3://%s/%s", local_path.name, self._bucket, key)
        self._s3.upload_file(str(local_path), self._bucket, key)
        logger.info("Upload complete: %s", key)

    def upload_fileobj(self, fileobj: IO[bytes], key: str) -> None:
        """Upload a file-like object to the bucket at *key*."""
        logger.info("Uploading stream → s3://%s/%s", self._bucket, key)
        self._s3.upload_fileobj(fileobj, self._bucket, key)

    # ---------------------------------------------------------------- download
    def download_file(self, key: str, dest_path: Path) -> None:
        """Download the object at *key* to *dest_path* (creates parents)."""
        from botocore.exceptions import ClientError

        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            logger.info("Downloading s3://%s/%s → %s", self._bucket, key, dest_path.name)
            self._s3.download_file(self._bucket, key, str(dest_path))
            logger.info("Download complete: %s", dest_path.name)
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code in ("404", "NoSuchKey"):
                raise FileNotFoundError(
                    f"Object not found in Neon bucket '{self._bucket}': {key}"
                ) from exc
            raise

    def download_fileobj(self, key: str) -> bytes:
        """Download *key* and return its content as bytes."""
        from botocore.exceptions import ClientError
        from io import BytesIO

        buf = BytesIO()
        try:
            self._s3.download_fileobj(self._bucket, key, buf)
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code in ("404", "NoSuchKey"):
                raise FileNotFoundError(
                    f"Object not found in Neon bucket '{self._bucket}': {key}"
                ) from exc
            raise
        return buf.getvalue()

    # ------------------------------------------------------------------- misc
    def object_exists(self, key: str) -> bool:
        """Return True if the object at *key* exists in the bucket."""
        from botocore.exceptions import ClientError

        try:
            self._s3.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise

    def list_keys(self, prefix: str = "") -> list[str]:
        """List all object keys under *prefix*."""
        paginator = self._s3.get_paginator("list_objects_v2")
        keys: list[str] = []
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        return keys

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def endpoint_url(self) -> str:
        return self._endpoint

