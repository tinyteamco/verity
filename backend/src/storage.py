"""Object storage abstraction layer for audio files."""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error


class StorageClient(ABC):
    """Abstract base class for object storage clients."""

    @abstractmethod
    async def upload_file(
        self,
        bucket: str,
        object_name: str,
        file_data: BinaryIO,
        content_type: str | None = None,
        file_size: int | None = None,
    ) -> str:
        """Upload a file and return the URI."""

    @abstractmethod
    async def get_download_url(self, bucket: str, object_name: str, expires_in: int = 3600) -> str:
        """Generate a presigned download URL."""

    @abstractmethod
    async def delete_file(self, bucket: str, object_name: str) -> None:
        """Delete a file."""


class MinIOClient(StorageClient):
    """MinIO client implementation."""

    def __init__(
        self, endpoint: str, access_key: str, secret_key: str, secure: bool = False
    ) -> None:
        self.client = Minio(
            endpoint=endpoint.replace("http://", "").replace("https://", ""),
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self.endpoint = endpoint

    async def upload_file(
        self,
        bucket: str,
        object_name: str,
        file_data: BinaryIO,
        content_type: str | None = None,
        file_size: int | None = None,
    ) -> str:
        """Upload a file and return the URI."""
        try:
            # Ensure bucket exists
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)

            # Upload the file
            self.client.put_object(
                bucket,
                object_name,
                file_data,
                length=file_size or -1,
                content_type=content_type,
            )

            # Return the URI
            return f"{self.endpoint}/{bucket}/{object_name}"

        except S3Error as e:
            raise RuntimeError(f"Failed to upload file to MinIO: {e}") from e

    async def get_download_url(self, bucket: str, object_name: str, expires_in: int = 3600) -> str:
        """Generate a presigned download URL."""
        try:
            from datetime import timedelta

            return self.client.presigned_get_object(
                bucket, object_name, expires=timedelta(seconds=expires_in)
            )
        except S3Error as e:
            raise RuntimeError(f"Failed to generate download URL: {e}") from e

    async def delete_file(self, bucket: str, object_name: str) -> None:
        """Delete a file."""
        try:
            self.client.remove_object(bucket, object_name)
        except S3Error as e:
            raise RuntimeError(f"Failed to delete file: {e}") from e


def get_storage_client() -> StorageClient:
    """Get the configured storage client."""
    endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    secure = endpoint.startswith("https://")

    return MinIOClient(endpoint, access_key, secret_key, secure)


def generate_audio_object_name(interview_id: int, filename: str) -> str:
    """Generate a consistent object name for audio files."""
    # Clean filename and add interview ID prefix
    clean_filename = Path(filename).name
    return f"interviews/{interview_id}/audio/{clean_filename}"
