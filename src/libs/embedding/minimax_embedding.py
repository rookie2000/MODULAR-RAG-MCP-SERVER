"""MiniMax Embedding implementation."""

from __future__ import annotations

import os
from typing import Any, List, Optional

from src.libs.embedding.base_embedding import BaseEmbedding


class MiniMaxEmbeddingError(RuntimeError):
    """Raised when MiniMax Embeddings API call fails."""


class MiniMaxEmbedding(BaseEmbedding):
    """MiniMax Embedding provider implementation.

    This class implements the BaseEmbedding interface for MiniMax's Embeddings API.

    Attributes:
        api_key: The API key for authentication.
        base_url: The base URL for the API.
        model: The model identifier to use.
        dimensions: The embedding dimensions.

    Example:
        >>> from src.core.settings import load_settings
        >>> settings = load_settings('config/settings.yaml')
        >>> embedding = MiniMaxEmbedding(settings)
        >>> vectors = embedding.embed(["hello world", "test"])
    """

    DEFAULT_BASE_URL = "https://api.minimax.chat/v1"

    # MiniMax embedding models and their dimensions
    MODEL_DIMENSIONS = {
        "embo-01": 1536,
        "text-embedding-v03": 1536,
        "text-embedding-v03-moe": 1536,
    }

    def __init__(
        self,
        settings: Any,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the MiniMax Embedding provider.

        Args:
            settings: Application settings containing Embedding configuration.
            api_key: Optional API key override (falls back to settings.embedding.api_key or env var).
            base_url: Optional base URL override.
            **kwargs: Additional configuration overrides.

        Raises:
            ValueError: If API key is not provided.
        """
        self.model = settings.embedding.model

        # Extract optional dimensions setting
        self.dimensions = getattr(settings.embedding, 'dimensions', None)

        # API key: explicit > settings > env var
        settings_api_key = self._optional_str(getattr(settings.embedding, 'api_key', None))
        self.api_key = api_key or settings_api_key or os.environ.get("MINIMAX_API_KEY")

        if not self.api_key:
            raise ValueError(
                "MiniMax API key not provided. Set in settings.yaml (embedding.api_key), "
                "MINIMAX_API_KEY environment variable, or pass api_key parameter."
            )

        # Base URL
        if base_url:
            self.base_url = base_url
        else:
            settings_base_url = self._optional_str(getattr(settings.embedding, 'base_url', None))
            self.base_url = settings_base_url if settings_base_url else self.DEFAULT_BASE_URL

        # Store any additional kwargs for future use
        self._extra_config = kwargs

    def embed(
        self,
        texts: List[str],
        trace: Optional[Any] = None,
        **kwargs: Any,
    ) -> List[List[float]]:
        """Generate embeddings for a batch of texts using MiniMax API.

        Args:
            texts: List of text strings to embed. Must not be empty.
            trace: Optional TraceContext for observability.
            **kwargs: Override parameters.

        Returns:
            List of embedding vectors, where each vector is a list of floats.
            The length of the outer list matches len(texts).

        Raises:
            ValueError: If texts list is empty or contains invalid entries.
            MiniMaxEmbeddingError: If API call fails.
        """
        import httpx

        # Validate input
        self.validate_texts(texts)

        # Prepare request
        url = f"{self.base_url.rstrip('/')}/embeddings"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "texts": texts,
            "model": self.model,
            "type": kwargs.get("type", "db"),
        }

        # Add dimensions if specified
        dimensions = kwargs.get("dimensions", self.dimensions)
        if dimensions is not None:
            payload["dimensions"] = dimensions

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=payload, headers=headers)

                if response.status_code != 200:
                    error_detail = self._parse_error_response(response)
                    raise MiniMaxEmbeddingError(
                        f"[MiniMax] Embeddings API error (HTTP {response.status_code}): {error_detail}"
                    )

                response_data = response.json()
                base_resp = response_data.get("base_resp")
                if isinstance(base_resp, dict) and base_resp.get("status_code") != 0:
                    raise MiniMaxEmbeddingError(
                        f"[MiniMax] Embeddings API error: {base_resp}"
                    )

        except httpx.TimeoutException as e:
            raise MiniMaxEmbeddingError(
                f"[MiniMax] Request timed out after 60 seconds"
            ) from e
        except httpx.RequestError as e:
            raise MiniMaxEmbeddingError(
                f"[MiniMax] Connection failed: {type(e).__name__}: {e}"
            ) from e

        # Extract embeddings from response
        try:
            embeddings = response_data["vectors"]
        except (KeyError, TypeError) as e:
            raise MiniMaxEmbeddingError(
                f"Failed to parse MiniMax Embeddings API response: {e}"
            ) from e

        # Verify output matches input length
        if len(embeddings) != len(texts):
            raise MiniMaxEmbeddingError(
                f"Output length mismatch: expected {len(texts)}, got {len(embeddings)}"
            )

        return embeddings

    def get_dimension(self) -> Optional[int]:
        """Get the embedding dimension for the configured model.

        Returns:
            The embedding dimension, or None if not deterministic.
        """
        # If dimensions explicitly configured, return it
        if self.dimensions is not None:
            return self.dimensions

        return self.MODEL_DIMENSIONS.get(self.model)

    def _parse_error_response(self, response: Any) -> str:
        """Parse error details from API response.

        Args:
            response: The HTTP response object.

        Returns:
            Human-readable error message.
        """
        try:
            error_data = response.json()
            if "error" in error_data:
                error = error_data["error"]
                if isinstance(error, dict):
                    return error.get("message", str(error))
                return str(error)
            return response.text
        except Exception:
            return response.text or "Unknown error"

    @staticmethod
    def _optional_str(value: Any) -> Optional[str]:
        return value if isinstance(value, str) and value else None
