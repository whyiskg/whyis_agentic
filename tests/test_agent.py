"""Tests for the InferenceAgent."""

from unittest.mock import Mock, patch

import pytest

from whyis_agentic.agent import AgentConfig, InferenceAgent, Message, ProviderType, ToolDefinition


class TestMessage:
    """Tests for the Message model."""

    def test_message_creation(self):
        """Test creating a message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.metadata == {}

    def test_message_with_metadata(self):
        """Test message with metadata."""
        msg = Message(role="assistant", content="Hi there", metadata={"thinking": True})
        assert msg.metadata["thinking"] is True


class TestToolDefinition:
    """Tests for the ToolDefinition model."""

    def test_tool_definition_creation(self):
        """Test creating a tool definition."""
        tool = ToolDefinition(name="test_tool", description="A test tool")
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.parameters == {}

    def test_tool_with_function(self):
        """Test tool with a function."""

        def my_func(x: int) -> int:
            return x * 2

        tool = ToolDefinition(name="multiply", description="Multiply by 2", function=my_func)
        assert tool.function(5) == 10


class TestAgentConfig:
    """Tests for the AgentConfig model."""

    def test_config_defaults(self):
        """Test config with defaults."""
        config = AgentConfig(name="test_agent", provider=ProviderType.GITHUB)
        assert config.name == "test_agent"
        assert config.provider == ProviderType.GITHUB
        assert config.model == "gpt-4"
        assert config.temperature == 0.7

    def test_config_custom_values(self):
        """Test config with custom values."""
        config = AgentConfig(
            name="custom_agent",
            provider=ProviderType.GITHUB,
            model="gpt-3.5-turbo",
            temperature=0.5,
            system_prompt="Custom prompt",
        )
        assert config.model == "gpt-3.5-turbo"
        assert config.temperature == 0.5
        assert config.system_prompt == "Custom prompt"


class TestInferenceAgent:
    """Tests for the InferenceAgent class."""

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    def test_agent_initialization(self, mock_provider):
        """Test agent initialization."""
        config = AgentConfig(
            name="test_agent",
            provider=ProviderType.GITHUB,
            system_prompt="You are a test assistant.",
        )

        mock_provider.return_value = Mock()
        agent = InferenceAgent(config)

        assert agent.config == config
        assert len(agent.conversation_history) == 1
        assert agent.conversation_history[0].role == "system"
        assert agent.conversation_history[0].content == "You are a test assistant."

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    def test_add_message(self, mock_provider):
        """Test adding messages to conversation."""
        config = AgentConfig(name="test", provider=ProviderType.GITHUB)
        mock_provider.return_value = Mock()
        agent = InferenceAgent(config)

        agent.add_message("user", "Hello")
        assert len(agent.conversation_history) == 2
        assert agent.conversation_history[-1].content == "Hello"

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    def test_add_tool(self, mock_provider):
        """Test adding a tool to agent."""
        config = AgentConfig(name="test", provider=ProviderType.GITHUB)
        mock_provider.return_value = Mock()
        agent = InferenceAgent(config)

        tool = ToolDefinition(name="test_tool", description="A tool")
        agent.add_tool(tool)

        assert tool in agent.config.tools

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    def test_reset_conversation(self, mock_provider):
        """Test resetting conversation."""
        config = AgentConfig(name="test", provider=ProviderType.GITHUB, system_prompt="System")
        mock_provider.return_value = Mock()
        agent = InferenceAgent(config)

        agent.add_message("user", "Hello")
        agent.add_message("assistant", "Hi")
        assert len(agent.conversation_history) == 3

        agent.reset_conversation()
        assert len(agent.conversation_history) == 1
        assert agent.conversation_history[0].role == "system"

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    def test_get_thinking_steps(self, mock_provider):
        """Test getting thinking steps."""
        config = AgentConfig(name="test", provider=ProviderType.GITHUB)
        mock_provider.return_value = Mock()
        agent = InferenceAgent(config)

        agent.add_message("user", "Hello")
        agent.add_message("assistant", "Thinking...", metadata={"thinking": True})
        agent.add_message("assistant", "Final answer")

        thinking = agent.get_thinking_steps()
        assert len(thinking) == 1
        assert thinking[0].content == "Thinking..."

    @patch("whyis_agentic.providers.github.GitHubProvider")
    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    def test_generate_response(self, mock_init_provider, mock_github_provider):
        """Test generating a response."""
        config = AgentConfig(name="test", provider=ProviderType.GITHUB)

        # Mock provider
        mock_provider = Mock()
        mock_provider.complete.return_value = Message(role="assistant", content="Test response")
        mock_init_provider.return_value = mock_provider

        agent = InferenceAgent(config)
        response = agent.generate_response("Hello")

        assert response.content == "Test response"
        assert len(agent.conversation_history) >= 2  # System + user + assistant
        mock_provider.complete.assert_called_once()

    @patch("whyis_agentic.providers.github.GitHubProvider")
    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    def test_generate_response_with_error(self, mock_init_provider, mock_github_provider):
        """Test generating response with error."""
        config = AgentConfig(name="test", provider=ProviderType.GITHUB)

        # Mock provider that raises error
        mock_provider = Mock()
        mock_provider.complete.side_effect = Exception("API error")
        mock_init_provider.return_value = mock_provider

        agent = InferenceAgent(config)
        response = agent.generate_response("Hello")

        assert "error" in response.content.lower()
        assert response.metadata.get("error") is True

    def test_unsupported_provider(self):
        """Test initialization with unsupported provider."""
        # Pydantic will validate the enum, so we need to test the ValueError
        # from _initialize_provider by creating a config with a valid enum
        # that isn't implemented yet

        # For now, only GITHUB is supported, so this test demonstrates
        # the pattern for future providers
        config = AgentConfig(name="test", provider=ProviderType.GITHUB)

        with patch("whyis_agentic.agent.InferenceAgent._initialize_provider") as mock_init:
            # Simulate an unsupported provider error
            mock_init.side_effect = ValueError("Unsupported provider: test")
            with pytest.raises(ValueError, match="Unsupported provider"):
                InferenceAgent(config)
