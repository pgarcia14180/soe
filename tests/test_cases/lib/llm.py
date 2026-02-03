"""
LLM caller helpers for tests.

Provides a call_llm that can use either a stub or real model.
Verbose logging via --show=prompt,response

API Options:
- Copilot Chat API (default): Uses your Copilot subscription, much higher rate limits
- GitHub Models API: Strict rate limits, for occasional testing only

Set SOE_LLM_BACKEND=github_models to use GitHub Models API instead of Copilot.
"""

import os
import re
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Union, Set

# Global clients (lazy loaded)
_openai_client = None
_copilot_client = None

# Default model for Copilot Chat API
DEFAULT_MODEL = os.environ.get("SOE_TEST_MODEL", "gpt-4o")

# Which backend to use: "copilot" (default) or "github_models"
LLM_BACKEND = os.environ.get("SOE_LLM_BACKEND", "copilot")


def _get_verbose_flags() -> Set[str]:
    """Get enabled verbose flags from SOE_VERBOSE environment variable"""
    verbose = os.environ.get("SOE_VERBOSE", "")
    if not verbose:
        return set()
    return set(flag.strip() for flag in verbose.split(","))


def _validate_stub_response(result: Any) -> str:
    """
    Validate that a stub returns a valid JSON string.

    This ensures tests exercise the full Pydantic parsing pipeline.
    If a stub returns a Pydantic object or invalid JSON, tests will fail
    immediately rather than silently passing.
    """
    if not isinstance(result, str):
        raise TypeError(
            f"Stub must return a JSON string, got {type(result).__name__}. "
            f"If returning a Pydantic model, use .model_dump_json() instead. "
            f"Value: {result!r}"
        )

    # Validate it's parseable JSON
    try:
        json.loads(result)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Stub returned invalid JSON: {e}. "
            f"Response: {result[:200]}..."
        ) from e

    return result


def _wrap_with_verbose(call_llm_fn: Callable) -> Callable:
    """Wrap call_llm with verbose logging if enabled"""

    def wrapped(prompt: str, config: Dict[str, Any]) -> str:
        verbose_flags = _get_verbose_flags()
        log_prompt = "prompt" in verbose_flags
        log_response = "response" in verbose_flags

        if log_prompt:
            truncated = prompt[:2000] + "..." if len(prompt) > 2000 else prompt
            print(f"\n[PROMPT]\n{truncated}")

        result = call_llm_fn(prompt, config)

        if log_response:
            print(f"\n[RESPONSE]\n{result}")

        return result

    return wrapped


def _wrap_stub_with_validation(stub: Callable) -> Callable:
    """Wrap a stub to validate it returns valid JSON strings."""

    def validated_stub(prompt: str, config: Dict[str, Any]) -> str:
        result = stub(prompt, config)
        return _validate_stub_response(result)

    return validated_stub


def create_call_llm(
    stub: Optional[Callable[[str, Dict[str, Any]], str]] = None,
    model: Optional[Union[str, bool]] = None,
) -> Callable[[str, Dict[str, Any]], str]:
    """
    Create an LLM caller for tests.

    Uses stub for fast, predictable tests. Use model=True for real LLM calls.

    Args:
        stub: Function that returns mock responses for tests
        model: Model name. If True, uses DEFAULT_MODEL.

    Returns:
        A call_llm function

    Usage:
        # Test with stub (fast, predictable)
        def my_stub(prompt, config):
            return '{"action": "finish"}'
        call_llm = create_call_llm(stub=my_stub)

        # Use real model
        call_llm = create_call_llm(model=True)
    """
    if model is True:
        model = DEFAULT_MODEL

    if model:
        # Choose backend based on environment variable
        if LLM_BACKEND == "github_models":
            return _wrap_with_verbose(_create_github_model_caller(model))
        else:
            return _wrap_with_verbose(_create_copilot_caller(model))
    elif stub:
        # Wrap stub with validation to ensure it returns valid JSON strings
        # This guarantees tests exercise the full Pydantic parsing pipeline
        validated_stub = _wrap_stub_with_validation(stub)
        return _wrap_with_verbose(validated_stub)
    else:
        raise ValueError("Either stub or model must be provided")


class CopilotChatClient:
    """
    Client for the Copilot Chat API - the same API that VS Code and CopilotChat.nvim use.
    Much higher rate limits than GitHub Models API since it's part of your Copilot subscription.
    """

    TOKEN_ENDPOINT = "https://api.github.com/copilot_internal/v2/token"
    CHAT_ENDPOINT = "https://api.githubcopilot.com/chat/completions"

    def __init__(self):
        self.oauth_token = self._load_oauth_token()
        self._api_token = None
        self._token_expires_at = 0

    def _load_oauth_token(self) -> str:
        """Load the OAuth token from Copilot's config files."""
        config_paths = [
            Path.home() / ".config/github-copilot/hosts.json",
            Path.home() / ".config/github-copilot/apps.json",
        ]

        # Also check XDG_CONFIG_HOME
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            config_paths.insert(0, Path(xdg_config) / "github-copilot/hosts.json")
            config_paths.insert(1, Path(xdg_config) / "github-copilot/apps.json")

        for path in config_paths:
            if path.exists():
                try:
                    data = json.loads(path.read_text())
                    for key, value in data.items():
                        if "github.com" in key and isinstance(value, dict):
                            if "oauth_token" in value:
                                return value["oauth_token"]
                except (json.JSONDecodeError, KeyError):
                    continue

        raise RuntimeError(
            "No Copilot OAuth token found. "
            "Run ':Copilot setup' in Neovim or sign in to Copilot in VS Code first.\n"
            "Token is expected in ~/.config/github-copilot/hosts.json or apps.json"
        )

    def _get_api_token(self) -> str:
        """Exchange OAuth token for short-lived API token."""
        import requests

        if self._api_token and time.time() < self._token_expires_at - 60:
            return self._api_token

        response = requests.get(
            self.TOKEN_ENDPOINT,
            headers={"Authorization": f"Token {self.oauth_token}"}
        )
        response.raise_for_status()
        data = response.json()

        self._api_token = data["token"]
        self._token_expires_at = data["expires_at"]

        return self._api_token

    def chat(self, messages: list, model: str = "gpt-4o") -> str:
        """Send a chat completion request to Copilot API."""
        import requests

        token = self._get_api_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Editor-Version": "Neovim/0.10.0",
            "Editor-Plugin-Version": "soe-tests/1.0.0",
            "Copilot-Integration-Id": "vscode-chat",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 2048,
            "temperature": 0.7,
        }

        response = requests.post(
            self.CHAT_ENDPOINT,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]


def _create_copilot_caller(model: str) -> Callable[[str, Dict[str, Any]], str]:
    """Create a call_llm using Copilot Chat API (same as VS Code/CopilotChat.nvim)."""

    def call_llm(prompt: str, config: Dict[str, Any]) -> str:
        global _copilot_client

        # Lazy load the client
        if _copilot_client is None:
            _copilot_client = CopilotChatClient()

        result_text = _copilot_client.chat(
            messages=[{"role": "user", "content": prompt}],
            model=model
        )

        # Clean the output: remove markdown code blocks if present
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(1)
        else:
            start = result_text.find('{')
            end = result_text.rfind('}')
            if start != -1 and end != -1:
                result_text = result_text[start:end+1]

        return result_text

    return call_llm


def _create_github_model_caller(model: str) -> Callable[[str, Dict[str, Any]], str]:
    """Create a call_llm using GitHub Models API (strict rate limits)."""

    def call_llm(prompt: str, config: Dict[str, Any]) -> str:
        global _openai_client

        # Lazy load the client
        if _openai_client is None:
            from openai import OpenAI

            github_token = os.environ.get("GITHUB_TOKEN")
            if not github_token:
                raise ValueError("GITHUB_TOKEN environment variable required for GitHub Models API")

            _openai_client = OpenAI(
                base_url="https://models.github.ai/inference/v1",
                api_key=github_token
            )

        response = _openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content

        # Clean the output: remove markdown code blocks if present
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(1)
        else:
            start = result_text.find('{')
            end = result_text.rfind('}')
            if start != -1 and end != -1:
                result_text = result_text[start:end+1]

        return result_text

    return call_llm
