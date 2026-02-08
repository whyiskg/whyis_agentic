"""Example: Using DialogAgent for ActivityStream interactions."""

import os
from whyis_agentic.dialog_agent import DialogAgent, ActivityStreamPost
from whyis_agentic.agent import AgentConfig, ProviderType, ToolDefinition


def post_callback(post: ActivityStreamPost):
    """Callback function to handle posting replies."""
    print(f"\n[POSTING REPLY]")
    print(f"  ID: {post.id}")
    print(f"  In Reply To: {post.in_reply_to}")
    print(f"  Content: {post.content}")
    print(f"  Actor: {post.actor}")
    if post.metadata.get("sub_conversation_id"):
        print(f"  Sub-conversation: {post.metadata['sub_conversation_id']}")
    print()


def example_basic_dialog_agent():
    """Example of a basic dialog agent processing ActivityStream posts."""
    
    # Configure the dialog agent
    config = AgentConfig(
        name="dialog_bot",
        provider=ProviderType.GITHUB,
        system_prompt="You are a helpful bot that answers questions in ActivityStream discussions.",
        api_key=os.getenv("GITHUB_TOKEN")
    )
    
    # Create dialog agent with callback
    agent = DialogAgent(config, post_callback=post_callback)
    
    # Simulate incoming posts
    posts = [
        ActivityStreamPost(
            id="post1",
            content="Hello everyone!",
            actor="alice"
        ),
        ActivityStreamPost(
            id="post2",
            content="What is the capital of France?",
            actor="bob"
        ),
        ActivityStreamPost(
            id="post3",
            content="How does photosynthesis work?",
            actor="charlie",
            conversation="conv1"
        ),
    ]
    
    print("Processing incoming posts...\n")
    for post in posts:
        print(f"[INCOMING POST] {post.actor}: {post.content}")
        result = agent.process_post(post)
        if result:
            print(f"✓ Generated reply")
        else:
            print(f"✗ Not a question, skipped")
    
    # View sub-conversations
    print("\n" + "=" * 60)
    print("Sub-conversations (thinking/research):")
    print("=" * 60)
    for post_id, subconvs in agent.get_all_sub_conversations().items():
        for subconv in subconvs:
            print(f"\nPost {subconv.parent_post_id}:")
            print(f"  Purpose: {subconv.purpose}")
            print(f"  Thinking steps: {len(subconv.messages)}")


def example_dialog_agent_with_tools():
    """Example of dialog agent with custom tools."""
    
    # Define a knowledge base search tool
    def search_knowledge_base(query: str) -> str:
        """Search the knowledge base."""
        # Simulate a knowledge base
        kb = {
            "whyis": "Whyis is a knowledge graph framework for building semantic web applications.",
            "fediverse": "The Fediverse is a collection of federated social networking services.",
            "activitypub": "ActivityPub is a decentralized social networking protocol."
        }
        return kb.get(query.lower(), "No information found.")
    
    tool = ToolDefinition(
        name="search_kb",
        description="Search the knowledge base for information",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        },
        function=search_knowledge_base
    )
    
    # Configure agent with tool
    config = AgentConfig(
        name="kb_bot",
        provider=ProviderType.GITHUB,
        system_prompt="You are a knowledgeable bot. Use the search_kb tool to look up information.",
        tools=[tool],
        api_key=os.getenv("GITHUB_TOKEN")
    )
    
    agent = DialogAgent(config, post_callback=post_callback)
    
    # Process a question that should trigger tool use
    post = ActivityStreamPost(
        id="post_kb1",
        content="What is Whyis?",
        actor="user1"
    )
    
    print("[INCOMING POST] What is Whyis?")
    agent.process_post(post)


def example_stream_listener():
    """Example of agent listening to a stream."""
    
    config = AgentConfig(
        name="stream_bot",
        provider=ProviderType.GITHUB,
        system_prompt="You are a helpful assistant in the stream.",
        api_key=os.getenv("GITHUB_TOKEN")
    )
    
    agent = DialogAgent(config, post_callback=post_callback)
    
    # Simulate a stream of posts
    def mock_stream():
        """Generator that simulates a stream of posts."""
        posts = [
            {"id": "s1", "content": "Anyone here?", "actor": "user1"},
            {"id": "s2", "content": "What time is it?", "actor": "user2"},
            {"id": "s3", "content": "Thanks everyone!", "actor": "user3"},
        ]
        for post in posts:
            yield post
    
    # Optional filter to only process certain posts
    def filter_mentions(post: ActivityStreamPost) -> bool:
        """Only process posts that mention the bot."""
        return "@stream_bot" in post.content or agent.is_question(post.content)
    
    print("Listening to stream...\n")
    agent.listen_to_stream(mock_stream(), filter_func=filter_mentions)


def example_activitystream_tools():
    """Example of creating ActivityStream-specific tools."""
    
    config = AgentConfig(
        name="as_bot",
        provider=ProviderType.GITHUB,
        api_key=os.getenv("GITHUB_TOKEN")
    )
    
    agent = DialogAgent(config)
    
    # Create ActivityStream tools
    search_tool = agent.create_tool_from_activitystream(
        tool_name="search_posts",
        tool_description="Search for posts in the stream",
        activity_type="Search",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"}
            }
        }
    )
    
    agent.add_tool(search_tool)
    
    print(f"Added tool: {search_tool.name}")
    print(f"Description: {search_tool.description}")
    
    # Test the tool
    result = search_tool.function(query="test", limit=10)
    print(f"Tool result: {result}")


if __name__ == "__main__":
    print("=" * 60)
    print("Dialog Agent Examples")
    print("=" * 60)
    print("\nNote: Set GITHUB_TOKEN environment variable to run these examples")
    print("Uncomment the example calls below to test\n")
    
    # Uncomment to run examples:
    # example_basic_dialog_agent()
    # example_dialog_agent_with_tools()
    # example_stream_listener()
    # example_activitystream_tools()
