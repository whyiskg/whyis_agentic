"""GitHub Copilot provider using OpenAI SDK."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from whyis_agentic.agent import InferenceProvider, Message, ToolDefinition

logger = logging.getLogger(__name__)


class GitHubProvider(InferenceProvider):
    """
    GitHub Copilot provider using the OpenAI SDK.

    GitHub Copilot chat models are accessible through the OpenAI SDK with
    custom API endpoints.
    """

    def __init__(
        self, api_key: Optional[str] = None, api_base: Optional[str] = None, model: str = "gpt-4"
    ):
        """
        Initialize GitHub provider.

        Args:
            api_key: GitHub API key or token (defaults to GITHUB_TOKEN env var)
            api_base: API base URL (defaults to GitHub Copilot endpoint)
            model: Model identifier

        Raises:
            ValueError: If no API key is provided or found in environment
        """
        self.api_key = api_key or os.getenv("GITHUB_TOKEN")
        if not self.api_key:
            raise ValueError(
                "GitHub API key is required. Provide api_key parameter or set GITHUB_TOKEN "
                "environment variable."
            )
        self.api_base = api_base or "https://api.githubcopilot.com"
        self.model = model
        self._client = None

    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self.api_key, base_url=self.api_base)
            except ImportError:
                raise ImportError(
                    "OpenAI SDK is required for GitHub provider. "
                    "Install with: pip install openai"
                )
        return self._client

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Convert internal Message format to OpenAI format."""
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def _convert_tools(
        self, tools: Optional[List[ToolDefinition]]
    ) -> Optional[List[Dict[str, Any]]]:
        """Convert internal ToolDefinition format to OpenAI format."""
        if not tools:
            return None

        openai_tools = []
        for tool in tools:
            openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters
                        or {
                            "type": "object",
                            "properties": {},
                        },
                    },
                }
            )
        return openai_tools

    def complete(
        self, messages: List[Message], tools: Optional[List[ToolDefinition]] = None, **kwargs
    ) -> Message:
        """
        Generate a completion using GitHub Copilot.

        Args:
            messages: Conversation history
            tools: Available tools
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Generated message
        """
        client = self._get_client()

        openai_messages = self._convert_messages(messages)
        openai_tools = self._convert_tools(tools)

        try:
            completion_args = {
                "model": self.model,
                "messages": openai_messages,
            }

            if openai_tools:
                completion_args["tools"] = openai_tools

            # Add optional parameters
            if "temperature" in kwargs:
                completion_args["temperature"] = kwargs["temperature"]
            if "max_tokens" in kwargs and kwargs["max_tokens"]:
                completion_args["max_tokens"] = kwargs["max_tokens"]

            response = client.chat.completions.create(**completion_args)

            choice = response.choices[0]
            message_content = choice.message.content or ""

            # Extract tool calls if present
            tool_calls = []
            if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    # Parse arguments JSON string to dictionary
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(
                            f"Failed to parse tool call arguments: {tool_call.function.arguments}"
                        )
                        arguments = {}

                    tool_calls.append(
                        {
                            "id": tool_call.id,
                            "name": tool_call.function.name,
                            "arguments": arguments,
                        }
                    )

            return Message(
                role="assistant",
                content=message_content,
                metadata={
                    "model": self.model,
                    "finish_reason": choice.finish_reason,
                    "tool_calls": tool_calls if tool_calls else None,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                },
            )

        except Exception as e:
            logger.error(f"GitHub provider error: {e}")
            raise

    def stream_complete(
        self, messages: List[Message], tools: Optional[List[ToolDefinition]] = None, **kwargs
    ):
        """
        Stream completions using GitHub Copilot.

        Args:
            messages: Conversation history
            tools: Available tools
            **kwargs: Additional parameters

        Yields:
            Message chunks
        """
        client = self._get_client()

        openai_messages = self._convert_messages(messages)
        openai_tools = self._convert_tools(tools)

        try:
            completion_args = {
                "model": self.model,
                "messages": openai_messages,
                "stream": True,
            }

            if openai_tools:
                completion_args["tools"] = openai_tools

            if "temperature" in kwargs:
                completion_args["temperature"] = kwargs["temperature"]
            if "max_tokens" in kwargs and kwargs["max_tokens"]:
                completion_args["max_tokens"] = kwargs["max_tokens"]

            stream = client.chat.completions.create(**completion_args)

            for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield Message(
                            role="assistant",
                            content=delta.content,
                            metadata={"stream": True, "chunk": True},
                        )

        except Exception as e:
            logger.error(f"GitHub provider streaming error: {e}")
            raise
