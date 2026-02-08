"""Dialog agent for ActivityStream integration."""

import logging
import re
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from whyis_agentic.agent import AgentConfig, InferenceAgent, Message, ToolDefinition

logger = logging.getLogger(__name__)


class ActivityStreamPost(BaseModel):
    """
    Represents an ActivityStream post.

    This is a simplified ActivityStream object model focusing on posts/notes.
    """

    id: str = Field(..., description="Unique identifier for the post")
    type: str = Field(default="Note", description="ActivityStream type")
    content: str = Field(..., description="Post content")
    actor: str = Field(..., description="Actor who created the post")
    published: Optional[str] = Field(default=None, description="Publication timestamp")
    in_reply_to: Optional[str] = Field(default=None, description="ID of post being replied to")
    conversation: Optional[str] = Field(default=None, description="Conversation thread ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SubConversation(BaseModel):
    """
    Represents a sub-conversation for recording thinking/research.

    Sub-conversations are nested conversation threads that track the agent's
    reasoning process, tool usage, and research.
    """

    id: str = Field(..., description="Sub-conversation identifier")
    parent_post_id: str = Field(..., description="Parent post being responded to")
    purpose: str = Field(
        ..., description="Purpose of this sub-conversation (thinking, research, etc.)"
    )
    messages: List[Message] = Field(
        default_factory=list, description="Messages in sub-conversation"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DialogAgent(InferenceAgent):
    """
    Dialog agent that listens for questions in ActivityStream posts.

    This agent extends InferenceAgent to specifically handle ActivityStream
    interactions. It can:
    - Listen for questions in posts
    - Use available tools to answer questions
    - Reply with ActivityStream posts
    - Record thinking and research as sub-conversations
    """

    def __init__(
        self,
        config: AgentConfig,
        post_callback: Optional[Callable[[ActivityStreamPost], None]] = None,
    ):
        """
        Initialize the dialog agent.

        Args:
            config: Agent configuration
            post_callback: Callback function to handle posting replies
        """
        super().__init__(config)
        self.post_callback = post_callback
        self.sub_conversations: Dict[str, List[SubConversation]] = {}

        # Pattern to detect questions
        self.question_patterns = [
            r"\?",  # Ends with question mark
            # Question words
            r"^(what|when|where|who|why|how|can|could|would|should|is|are|do|does)",
        ]

    def is_question(self, content: str) -> bool:
        """
        Determine if a post content contains a question.

        Args:
            content: Post content to analyze

        Returns:
            True if content appears to be a question
        """
        content_lower = content.lower().strip()

        for pattern in self.question_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return True

        return False

    def process_post(self, post: ActivityStreamPost) -> Optional[ActivityStreamPost]:
        """
        Process an ActivityStream post and generate a reply if it's a question.

        Args:
            post: The ActivityStream post to process

        Returns:
            Reply post if a question was detected, None otherwise
        """
        # Check if this is a question
        if not self.is_question(post.content):
            logger.debug(f"Post {post.id} does not contain a question, skipping")
            return None

        logger.info(f"Processing question from post {post.id}: {post.content}")

        # Create a sub-conversation for thinking/research
        sub_conv = SubConversation(
            id=f"subconv_{post.id}",
            parent_post_id=post.id,
            purpose="thinking_and_research",
            metadata={"original_question": post.content},
        )

        # Generate response with thinking recorded
        try:
            response = self.generate_response(user_message=post.content, record_thinking=True)

            # Extract thinking steps for sub-conversation
            thinking_steps = self.get_thinking_steps()
            sub_conv.messages = thinking_steps

            # Store sub-conversation
            if post.id not in self.sub_conversations:
                self.sub_conversations[post.id] = []
            self.sub_conversations[post.id].append(sub_conv)

            # Create reply post
            reply_post = ActivityStreamPost(
                id=f"reply_{post.id}",
                type="Note",
                content=response.content,
                actor=self.config.name,
                in_reply_to=post.id,
                conversation=post.conversation or post.id,
                metadata={
                    "agent": self.config.name,
                    "model": self.config.model,
                    "sub_conversation_id": sub_conv.id,
                    "has_thinking": len(thinking_steps) > 0,
                },
            )

            # Post the reply if callback is set
            if self.post_callback:
                self.post_callback(reply_post)

            logger.info(f"Generated reply to post {post.id}")
            return reply_post

        except Exception as e:
            logger.error(f"Error processing post {post.id}: {e}")

            # Create error reply
            error_reply = ActivityStreamPost(
                id=f"reply_{post.id}_error",
                type="Note",
                content=f"I encountered an error while trying to answer: {str(e)}",
                actor=self.config.name,
                in_reply_to=post.id,
                conversation=post.conversation or post.id,
                metadata={"error": True},
            )

            if self.post_callback:
                self.post_callback(error_reply)

            return error_reply

    def get_sub_conversations(self, post_id: str) -> List[SubConversation]:
        """
        Get all sub-conversations for a specific post.

        Args:
            post_id: Post identifier

        Returns:
            List of sub-conversations
        """
        return self.sub_conversations.get(post_id, [])

    def get_all_sub_conversations(self) -> Dict[str, List[SubConversation]]:
        """Get all sub-conversations."""
        return self.sub_conversations.copy()

    def listen_to_stream(
        self, stream_source: Any, filter_func: Optional[Callable[[ActivityStreamPost], bool]] = None
    ):
        """
        Listen to an ActivityStream source and process incoming posts.

        Args:
            stream_source: Source of ActivityStream posts (iterable)
            filter_func: Optional filter function to select which posts to process
        """
        logger.info(f"Dialog agent {self.config.name} started listening to stream")

        try:
            for post_data in stream_source:
                # Convert to ActivityStreamPost if needed
                if isinstance(post_data, dict):
                    post = ActivityStreamPost(**post_data)
                elif isinstance(post_data, ActivityStreamPost):
                    post = post_data
                else:
                    logger.warning(f"Unknown post format: {type(post_data)}")
                    continue

                # Apply filter if provided
                if filter_func and not filter_func(post):
                    continue

                # Process the post
                self.process_post(post)

        except Exception as e:
            logger.error(f"Error in stream listening: {e}")
            raise

    def create_tool_from_activitystream(
        self,
        tool_name: str,
        tool_description: str,
        activity_type: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> ToolDefinition:
        """
        Create a tool definition that interacts with ActivityStream.

        This allows the agent to perform ActivityStream actions as tools
        (e.g., search posts, fetch user info, etc.)

        Args:
            tool_name: Name of the tool
            tool_description: Description of what the tool does
            activity_type: ActivityStream activity type
            parameters: JSON schema of parameters

        Returns:
            ToolDefinition that can be added to the agent
        """

        def tool_function(**kwargs):
            """Execute ActivityStream action."""
            # This would integrate with actual ActivityStream/Fediverse API
            logger.info(f"Executing ActivityStream tool {tool_name} with {kwargs}")
            return {"activity_type": activity_type, "parameters": kwargs, "status": "executed"}

        return ToolDefinition(
            name=tool_name,
            description=tool_description,
            parameters=parameters or {"type": "object", "properties": {}},
            function=tool_function,
        )
