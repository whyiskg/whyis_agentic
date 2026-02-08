"""Tests for the DialogAgent."""

from unittest.mock import Mock, patch

from whyis_agentic.agent import AgentConfig, Message, ProviderType
from whyis_agentic.dialog_agent import ActivityStreamPost, DialogAgent, SubConversation


class TestActivityStreamPost:
    """Tests for ActivityStreamPost model."""

    def test_post_creation(self):
        """Test creating an activity stream post."""
        post = ActivityStreamPost(id="post1", content="Hello world", actor="user1")
        assert post.id == "post1"
        assert post.content == "Hello world"
        assert post.type == "Note"

    def test_post_with_reply(self):
        """Test post with reply information."""
        post = ActivityStreamPost(
            id="post2",
            content="Reply content",
            actor="user2",
            in_reply_to="post1",
            conversation="conv1",
        )
        assert post.in_reply_to == "post1"
        assert post.conversation == "conv1"


class TestSubConversation:
    """Tests for SubConversation model."""

    def test_subconversation_creation(self):
        """Test creating a sub-conversation."""
        subconv = SubConversation(id="sub1", parent_post_id="post1", purpose="thinking")
        assert subconv.id == "sub1"
        assert subconv.parent_post_id == "post1"
        assert subconv.messages == []


class TestDialogAgent:
    """Tests for the DialogAgent class."""

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    def test_dialog_agent_initialization(self, mock_provider):
        """Test dialog agent initialization."""
        config = AgentConfig(name="dialog_test", provider=ProviderType.GITHUB)
        mock_provider.return_value = Mock()

        agent = DialogAgent(config)
        assert agent.config.name == "dialog_test"
        assert agent.post_callback is None
        assert agent.sub_conversations == {}

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    def test_dialog_agent_with_callback(self, mock_provider):
        """Test dialog agent with post callback."""
        config = AgentConfig(name="dialog_test", provider=ProviderType.GITHUB)
        mock_provider.return_value = Mock()
        callback = Mock()

        agent = DialogAgent(config, post_callback=callback)
        assert agent.post_callback is callback

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    def test_is_question_with_question_mark(self, mock_provider):
        """Test detecting questions with question mark."""
        config = AgentConfig(name="dialog_test", provider=ProviderType.GITHUB)
        mock_provider.return_value = Mock()
        agent = DialogAgent(config)

        assert agent.is_question("What is your name?")
        assert agent.is_question("Is this a question?")
        assert not agent.is_question("This is a statement.")

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    def test_is_question_with_question_words(self, mock_provider):
        """Test detecting questions with question words."""
        config = AgentConfig(name="dialog_test", provider=ProviderType.GITHUB)
        mock_provider.return_value = Mock()
        agent = DialogAgent(config)

        assert agent.is_question("How are you")
        assert agent.is_question("Why is the sky blue")
        assert agent.is_question("Can you help me")
        assert agent.is_question("What time is it")

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    @patch("whyis_agentic.agent.InferenceAgent.generate_response")
    def test_process_non_question_post(self, mock_generate, mock_provider):
        """Test processing a non-question post."""
        config = AgentConfig(name="dialog_test", provider=ProviderType.GITHUB)
        mock_provider.return_value = Mock()
        agent = DialogAgent(config)

        post = ActivityStreamPost(id="post1", content="Hello everyone", actor="user1")

        result = agent.process_post(post)
        assert result is None
        mock_generate.assert_not_called()

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    @patch("whyis_agentic.agent.InferenceAgent.generate_response")
    @patch("whyis_agentic.agent.InferenceAgent.get_thinking_steps")
    def test_process_question_post(self, mock_thinking, mock_generate, mock_provider):
        """Test processing a question post."""
        config = AgentConfig(name="dialog_test", provider=ProviderType.GITHUB)
        mock_provider.return_value = Mock()

        mock_generate.return_value = Message(role="assistant", content="The answer is 42")
        mock_thinking.return_value = []

        agent = DialogAgent(config)

        post = ActivityStreamPost(id="post1", content="What is the answer?", actor="user1")

        reply = agent.process_post(post)

        assert reply is not None
        assert reply.in_reply_to == "post1"
        assert reply.content == "The answer is 42"
        assert reply.actor == "dialog_test"
        mock_generate.assert_called_once()

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    @patch("whyis_agentic.agent.InferenceAgent.generate_response")
    @patch("whyis_agentic.agent.InferenceAgent.get_thinking_steps")
    def test_process_post_with_callback(self, mock_thinking, mock_generate, mock_provider):
        """Test processing post with callback."""
        config = AgentConfig(name="dialog_test", provider=ProviderType.GITHUB)
        mock_provider.return_value = Mock()
        callback = Mock()

        mock_generate.return_value = Message(role="assistant", content="Answer")
        mock_thinking.return_value = []

        agent = DialogAgent(config, post_callback=callback)

        post = ActivityStreamPost(id="post1", content="What is this?", actor="user1")

        agent.process_post(post)
        callback.assert_called_once()

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    @patch("whyis_agentic.agent.InferenceAgent.generate_response")
    def test_process_post_with_error(self, mock_generate, mock_provider):
        """Test processing post that raises error."""
        config = AgentConfig(name="dialog_test", provider=ProviderType.GITHUB)
        mock_provider.return_value = Mock()

        mock_generate.side_effect = Exception("Test error")

        agent = DialogAgent(config)
        post = ActivityStreamPost(id="post1", content="What is this?", actor="user1")

        reply = agent.process_post(post)

        assert reply is not None
        assert "error" in reply.content.lower()
        assert reply.metadata.get("error") is True

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    @patch("whyis_agentic.agent.InferenceAgent.generate_response")
    @patch("whyis_agentic.agent.InferenceAgent.get_thinking_steps")
    def test_sub_conversations(self, mock_thinking, mock_generate, mock_provider):
        """Test sub-conversation recording."""
        config = AgentConfig(name="dialog_test", provider=ProviderType.GITHUB)
        mock_provider.return_value = Mock()

        mock_generate.return_value = Message(role="assistant", content="Answer")
        mock_thinking.return_value = [
            Message(role="assistant", content="Thinking step", metadata={"thinking": True})
        ]

        agent = DialogAgent(config)

        post = ActivityStreamPost(id="post1", content="What is this?", actor="user1")

        agent.process_post(post)

        subconvs = agent.get_sub_conversations("post1")
        assert len(subconvs) == 1
        assert subconvs[0].parent_post_id == "post1"
        assert len(subconvs[0].messages) == 1

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    def test_create_tool_from_activitystream(self, mock_provider):
        """Test creating a tool from ActivityStream."""
        config = AgentConfig(name="dialog_test", provider=ProviderType.GITHUB)
        mock_provider.return_value = Mock()
        agent = DialogAgent(config)

        tool = agent.create_tool_from_activitystream(
            tool_name="search_posts",
            tool_description="Search for posts",
            activity_type="Search",
            parameters={"type": "object", "properties": {"query": {"type": "string"}}},
        )

        assert tool.name == "search_posts"
        assert tool.description == "Search for posts"
        assert callable(tool.function)

        result = tool.function(query="test")
        assert result["activity_type"] == "Search"

    @patch("whyis_agentic.agent.InferenceAgent._initialize_provider")
    @patch("whyis_agentic.dialog_agent.DialogAgent.process_post")
    def test_listen_to_stream(self, mock_process, mock_provider):
        """Test listening to stream."""
        config = AgentConfig(name="dialog_test", provider=ProviderType.GITHUB)
        mock_provider.return_value = Mock()
        agent = DialogAgent(config)

        posts = [
            ActivityStreamPost(id="post1", content="Test?", actor="user1"),
            ActivityStreamPost(id="post2", content="Hello", actor="user2"),
        ]

        agent.listen_to_stream(posts)

        assert mock_process.call_count == 2
