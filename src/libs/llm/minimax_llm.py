"""MiniMax LLM implementation.

This module provides the MiniMax LLM implementation that uses the
OpenAI-compatible API format.
"""

from __future__ import annotations

from typing import Any, List, Optional

from src.libs.llm.base_llm import BaseLLM, ChatResponse, Message


class MiniMaxLLMError(RuntimeError):
    """Raised when MiniMax API call fails."""


class MiniMaxLLM(BaseLLM):
    """MiniMax LLM provider implementation.

    This class implements the BaseLLM interface for MiniMax's chat completion API.
    MiniMax provides OpenAI-compatible API endpoints.

    Attributes:
        api_key: The API key for authentication.
        base_url: The base URL for the API.
        model: The model identifier to use.
        default_temperature: Default temperature for generation.
        default_max_tokens: Default max tokens for generation.

    Example:
        >>> from src.core.settings import load_settings
        >>> settings = load_settings('config/settings.yaml')
        >>> llm = MiniMaxLLM(settings)
        >>> response = llm.chat([Message(role='user', content='Hello')])
    """

    DEFAULT_BASE_URL = "https://api.minimax.chat/v1"

    # MiniMax model mapping to their correct model names
    MODEL_ALIASES = {
        "abab6.5s-chat": "abab6.5s-chat",
        "abab6.5g-chat": "abab6.5g-chat",
        "abab5.5s-chat": "abab5.5s-chat",
        "abab5.5g-chat": "abab5.5g-chat",
    }

    def __init__(
        self,
        settings: Any,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the MiniMax LLM provider.

        Args:
            settings: Application settings containing LLM configuration.
            api_key: Optional API key override (falls back to settings.llm.api_key or env var).
            base_url: Optional base URL override.
            **kwargs: Additional configuration overrides.

        Raises:
            ValueError: If API key is not provided.
        """
        self.model = settings.llm.model
        self.default_temperature = settings.llm.temperature
        self.default_max_tokens = settings.llm.max_tokens

        # API key: explicit > settings > env var
        self.api_key = (
            api_key
            or getattr(settings.llm, 'api_key', None)
            or settings.llm.get('api_key')
            or None
        )
        if not self.api_key:
            # Try environment variable
            import os
            self.api_key = os.environ.get("MINIMAX_API_KEY")

        if not self.api_key:
            raise ValueError(
                "MiniMax API key not provided. Set in settings.yaml (llm.api_key), "
                "MINIMAX_API_KEY environment variable, or pass api_key parameter."
            )

        # Base URL
        if base_url:
            self.base_url = base_url
        else:
            # Use settings base_url or default
            self.base_url = getattr(settings.llm, 'base_url', None) or self.DEFAULT_BASE_URL

        # Store any additional kwargs for future use
        self._extra_config = kwargs

    def chat(
        self,
        messages: List[Message],
        trace: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Generate a chat completion using MiniMax API.

        Args:
            messages: List of conversation messages.
            trace: Optional TraceContext for observability (reserved for Stage F).
            **kwargs: Override parameters (temperature, max_tokens, etc.).

        Returns:
            ChatResponse with generated content and metadata.

        Raises:
            ValueError: If messages are invalid.
            MiniMaxLLMError: If API call fails.
        """
        # Validate input
        self.validate_messages(messages)

        # Prepare request parameters
        temperature = kwargs.get("temperature", self.default_temperature)
        max_tokens = kwargs.get("max_tokens", self.default_max_tokens)
        model = kwargs.get("model", self.model)

        # Convert messages to API format
        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        # Make API call
        try:
            response_data = self._call_api(
                messages=api_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Parse response - MiniMax returns in similar format to OpenAI
            content = response_data["choices"][0]["message"]["content"]
            usage = response_data.get("usage")

            return ChatResponse(
                content=content,
                model=response_data.get("model", model),
                usage=usage,
                raw_response=response_data,
            )
        except KeyError as e:
            raise MiniMaxLLMError(
                f"[MiniMax] Unexpected response format: missing key {e}"
            ) from e
        except Exception as e:
            if isinstance(e, MiniMaxLLMError):
                raise
            raise MiniMaxLLMError(
                f"[MiniMax] API call failed: {type(e).__name__}: {e}"
            ) from e

    def _call_api(
        self,
        messages: List[dict],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> dict:
        """Make the actual API call to MiniMax.

        Args:
            messages: Messages in API format.
            model: Model identifier.
            temperature: Generation temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Raw API response as dictionary.

        Raises:
            MiniMaxLLMError: If the API call fails.
        """
        import httpx

        # Use the correct endpoint format for MiniMax
        url = f"{self.base_url.rstrip('/')}/text/chatcompletion_v2"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=payload, headers=headers)

                if response.status_code != 200:
                    error_detail = self._parse_error_response(response)
                    raise MiniMaxLLMError(
                        f"[MiniMax] API error (HTTP {response.status_code}): {error_detail}"
                    )

                return response.json()
        except httpx.TimeoutException as e:
            raise MiniMaxLLMError(
                f"[MiniMax] Request timed out after 60 seconds"
            ) from e
        except httpx.RequestError as e:
            raise MiniMaxLLMError(
                f"[MiniMax] Connection failed: {type(e).__name__}: {e}"
            ) from e

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