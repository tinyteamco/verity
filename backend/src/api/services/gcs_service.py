"""GCS service for streaming interview artifacts."""

import os
from collections.abc import AsyncGenerator

from google.cloud import storage
from google.oauth2 import service_account


class GCSService:
    """Service for streaming artifacts from Google Cloud Storage."""

    def __init__(self) -> None:
        """Initialize GCS client with credentials."""
        # For MVP: Use default credentials or service account
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = storage.Client(credentials=credentials)
        else:
            # Use default credentials (works in GCP environments)
            self.client = storage.Client()

    async def stream_artifact(
        self, bucket_name: str, object_path: str, chunk_size: int = 1024 * 1024
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream an artifact from GCS.

        Args:
            bucket_name: GCS bucket name
            object_path: Path to object in bucket
            chunk_size: Size of chunks to read (default 1MB)

        Yields:
            Chunks of bytes from the artifact

        Raises:
            google.cloud.exceptions.NotFound: If bucket or object doesn't exist
        """
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(object_path)

        # Download in chunks
        # Note: google-cloud-storage doesn't have native async support
        # For MVP, we'll read the entire file and yield in chunks
        # In production, consider using aiogoogle or similar
        content = blob.download_as_bytes()

        # Yield in chunks
        for i in range(0, len(content), chunk_size):
            yield content[i : i + chunk_size]

    def get_content_type(self, filename: str) -> str:
        """
        Get content type based on filename extension.

        Args:
            filename: Name of the file

        Returns:
            MIME type string
        """
        if filename.endswith(".txt"):
            return "text/plain; charset=utf-8"
        elif filename.endswith(".wav"):
            return "audio/wav"
        elif filename.endswith(".mp3"):
            return "audio/mpeg"
        elif filename.endswith(".json"):
            return "application/json"
        else:
            return "application/octet-stream"
