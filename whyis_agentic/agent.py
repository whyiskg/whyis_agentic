"""Core inference agent implementation with AI provider support."""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Supported AI provider types."""

    GITHUB = "github"
    # Future providers can be added here
    # OPENAI = "openai"
    # ANTHROPIC = "anthropic"


class Message(BaseModel):
    """A message in a conversation."""

    role: str = Field(..., description="Role of the message sender (system, user, assistant)")
    content: str = Field(..., description="Content of the message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ToolDefinition(BaseModel):
    """Definition of a tool that can be used by the agent."""

    model_config = {"arbitrary_types_allowed": True}

    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="JSON schema of tool parameters"
    )
    function: Optional[Callable] = Field(default=None, description="Callable function")


class AgentConfig(BaseModel):
    """Configuration for an inference agent."""

    name: str = Field(..., description="Agent name")
    provider: ProviderType = Field(..., description="AI provider to use")
    model: str = Field(default="gpt-4", description="Model identifier")
    system_prompt: str = Field(
        default="You are a helpful AI assistant.", description="System prompt for the agent"
    )
    tools: List[ToolDefinition] = Field(default_factory=list, description="Available tools")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens in response")
    api_key: Optional[str] = Field(default=None, description="API key for the provider")
    api_base: Optional[str] = Field(default=None, description="Custom API base URL")


class InferenceProvider(ABC):
    """Abstract base class for AI inference providers."""

    @abstractmethod
    def complete(
        self, messages: List[Message], tools: Optional[List[ToolDefinition]] = None, **kwargs
    ) -> Message:
        """
        Generate a completion from the provider.

        Args:
            messages: Conversation history
            tools: Available tools for the agent
            **kwargs: Provider-specific parameters

        Returns:
            Generated message response
        """
        pass

    @abstractmethod
    def stream_complete(
        self, messages: List[Message], tools: Optional[List[ToolDefinition]] = None, **kwargs
    ):
        """
        Stream completions from the provider.

        Args:
            messages: Conversation history
            tools: Available tools for the agent
            **kwargs: Provider-specific parameters

        Yields:
            Message chunks
        """
        pass


class InferenceAgent:
    """
    Gen AI inference agent with configurable prompts and tools.

    This agent can use various AI providers (GitHub Copilot, etc.) and supports
    tool calling for enhanced capabilities.
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize the inference agent.

        Args:
            config: Agent configuration
        """
        self.config = config
        self.conversation_history: List[Message] = []
        self.provider = self._initialize_provider()

        # Add system prompt to conversation
        if config.system_prompt:
            self.conversation_history.append(Message(role="system", content=config.system_prompt))

    def _initialize_provider(self) -> InferenceProvider:
        """Initialize the AI provider based on configuration."""
        if self.config.provider == ProviderType.GITHUB:
            from whyis_agentic.providers.github import GitHubProvider

            return GitHubProvider(
                api_key=self.config.api_key, api_base=self.config.api_base, model=self.config.model
            )
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a message to the conversation history.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        message = Message(role=role, content=content, metadata=metadata or {})
        self.conversation_history.append(message)

    def add_tool(self, tool: ToolDefinition):
        """
        Add a tool to the agent's available tools.

        Args:
            tool: Tool definition
        """
        if tool not in self.config.tools:
            self.config.tools.append(tool)

    def generate_response(self, user_message: str, record_thinking: bool = True) -> Message:
        """
        Generate a response to a user message.

        Args:
            user_message: User's input message
            record_thinking: Whether to record intermediate thinking steps

        Returns:
            Agent's response message
        """
        # Add user message to history
        self.add_message("user", user_message)

        try:
            # Generate response from provider
            response = self.provider.complete(
                messages=self.conversation_history,
                tools=self.config.tools if self.config.tools else None,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            # Add response to history
            self.conversation_history.append(response)

            # Handle tool calls if present
            if response.metadata.get("tool_calls"):
                response = self._handle_tool_calls(response, record_thinking)

            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            error_message = Message(
                role="assistant",
                content=f"I encountered an error: {str(e)}",
                metadata={"error": True},
            )
            self.conversation_history.append(error_message)
            return error_message

    def _handle_tool_calls(self, message: Message, record_thinking: bool) -> Message:
        """
        Handle tool calls in a message.

        Args:
            message: Message containing tool calls
            record_thinking: Whether to record tool execution as thinking

        Returns:
            Final response after tool execution
        """
        tool_calls = message.metadata.get("tool_calls", [])
        tool_results = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("arguments", {})

            # Ensure tool_args is a dictionary
            if not isinstance(tool_args, dict):
                logger.error(f"Tool arguments must be a dictionary, got {type(tool_args)}")
                tool_results.append({"tool": tool_name, "error": "Invalid arguments format"})
                continue

            # Find the tool
            tool = next((t for t in self.config.tools if t.name == tool_name), None)

            if tool and tool.function:
                try:
                    result = tool.function(**tool_args)
                    tool_results.append({"tool": tool_name, "result": result})

                    if record_thinking:
                        # Record tool execution as thinking
                        self.add_message(
                            "assistant",
                            f"[Thinking: Used {tool_name} with args {tool_args}]",
                            metadata={"thinking": True, "tool_call": True},
                        )
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}")
                    tool_results.append({"tool": tool_name, "error": str(e)})

        # If we executed tools, generate a final response
        if tool_results:
            self.add_message(
                "user", f"Tool results: {tool_results}", metadata={"tool_results": True}
            )
            return self.provider.complete(
                messages=self.conversation_history,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

        return message

    def reset_conversation(self):
        """Reset the conversation history, keeping only the system prompt."""
        system_messages = [msg for msg in self.conversation_history if msg.role == "system"]
        self.conversation_history = system_messages

    def get_conversation_history(self) -> List[Message]:
        """Get the full conversation history."""
        return self.conversation_history.copy()

    def get_thinking_steps(self) -> List[Message]:
        """Get only the thinking/research messages from conversation history."""
        return [msg for msg in self.conversation_history if msg.metadata.get("thinking", False)]
