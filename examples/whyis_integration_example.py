"""Example: Integrating with Whyis as a plugin."""

from whyis_agentic.plugin import WhyisAgenticPlugin
from whyis_agentic.dialog_agent import DialogAgent, ActivityStreamPost
from whyis_agentic.agent import AgentConfig, ProviderType


def example_whyis_plugin_integration():
    """
    Example of integrating the agentic plugin with a Whyis application.
    
    Note: This is a conceptual example. Actual integration would depend on
    the specific Whyis application structure and whyis_fediverse plugin.
    """
    
    # Configure the plugin
    plugin_config = {
        "agents": [
            {
                "name": "question_answerer",
                "provider": "github",
                "model": "gpt-4",
                "system_prompt": "You are a helpful assistant in the Whyis knowledge graph."
            }
        ],
        "default_provider": "github",
        "api_keys": {
            "github": "your-github-token-here"
        }
    }
    
    # Create and initialize plugin
    # In a real Whyis app, this would be done in the app factory
    plugin = WhyisAgenticPlugin(config=plugin_config)
    
    # Simulate Whyis app initialization
    # app = create_whyis_app()
    # plugin.init_app(app)
    
    print("Plugin initialized with agents:")
    for name in plugin.agents.keys():
        print(f"  - {name}")
    
    return plugin


def example_whyis_fediverse_integration():
    """
    Example of integrating with whyis_fediverse plugin.
    
    This shows how the dialog agent would work with ActivityStream posts
    from the Fediverse.
    """
    
    # Create a dialog agent
    config = AgentConfig(
        name="fediverse_bot",
        provider=ProviderType.GITHUB,
        system_prompt="You are a bot that helps answer questions in the Fediverse.",
    )
    
    def publish_to_fediverse(post: ActivityStreamPost):
        """
        Callback to publish to Fediverse.
        
        In a real implementation, this would use whyis_fediverse plugin
        to publish the post to ActivityPub servers.
        """
        print(f"Publishing to Fediverse:")
        print(f"  Actor: {post.actor}")
        print(f"  Content: {post.content}")
        print(f"  In Reply To: {post.in_reply_to}")
        # Real implementation:
        # fediverse_plugin.publish(post)
    
    agent = DialogAgent(config, post_callback=publish_to_fediverse)
    
    # Simulate receiving a post from Fediverse
    incoming_post = ActivityStreamPost(
        id="https://mastodon.social/users/alice/statuses/123",
        content="@fediverse_bot What is a knowledge graph?",
        actor="https://mastodon.social/users/alice",
        conversation="https://mastodon.social/conversations/456"
    )
    
    print("\nReceived post from Fediverse:")
    print(f"  From: {incoming_post.actor}")
    print(f"  Content: {incoming_post.content}")
    print()
    
    # Process and reply
    # agent.process_post(incoming_post)
    print("Note: Uncomment agent.process_post() and set GITHUB_TOKEN to test")


def example_backend_compaction_integration():
    """
    Example showing how this works as a backend compaction plugin.
    
    Backend compaction in Whyis refers to background processing that
    enriches the knowledge graph with inferred or computed data.
    """
    
    print("Backend Compaction Integration Example")
    print("=" * 60)
    print()
    print("This plugin acts as a backend compaction agent that:")
    print("1. Monitors ActivityStream posts in the knowledge graph")
    print("2. Identifies questions that need answering")
    print("3. Uses AI tools to generate informed responses")
    print("4. Publishes answers back to the ActivityStream")
    print("5. Records thinking/research as sub-conversations for transparency")
    print()
    
    # Example configuration for backend compaction
    compaction_config = {
        "enabled": True,
        "check_interval": 60,  # Check for new posts every 60 seconds
        "agents": [
            {
                "name": "qa_agent",
                "provider": "github",
                "system_prompt": "You are an expert on knowledge graphs and semantic web.",
                "tools": [
                    # Tools would be configured here
                    # e.g., SPARQL query tools, knowledge graph traversal, etc.
                ]
            }
        ]
    }
    
    print("Example Configuration:")
    import json
    print(json.dumps(compaction_config, indent=2))
    print()
    print("The agent would run in the background, monitoring the graph")
    print("and automatically responding to questions as they appear.")


def example_with_knowledge_graph_tools():
    """
    Example of agent with Whyis knowledge graph tools.
    
    This shows how the agent could use SPARQL queries and other
    knowledge graph operations as tools.
    """
    from whyis_agentic.agent import ToolDefinition
    
    # Define a SPARQL query tool (conceptual)
    def sparql_query(query: str) -> str:
        """Execute a SPARQL query on the knowledge graph."""
        # Real implementation would use Whyis's SPARQL endpoint
        # return whyis_app.knowledge_graph.query(query)
        return "Query results would go here"
    
    sparql_tool = ToolDefinition(
        name="sparql_query",
        description="Execute a SPARQL query on the Whyis knowledge graph",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SPARQL query string"
                }
            },
            "required": ["query"]
        },
        function=sparql_query
    )
    
    # Configure agent with KG tools
    config = AgentConfig(
        name="kg_agent",
        provider=ProviderType.GITHUB,
        system_prompt="You are an expert that can query the knowledge graph to answer questions.",
        tools=[sparql_tool]
    )
    
    print("Knowledge Graph Agent Configuration:")
    print(f"  Name: {config.name}")
    print(f"  Tools: {[t.name for t in config.tools]}")
    print()
    print("This agent can use SPARQL queries to answer questions")
    print("by directly accessing the knowledge graph.")


if __name__ == "__main__":
    print("Whyis Plugin Integration Examples")
    print("=" * 80)
    print()
    
    print("Example 1: Basic Plugin Integration")
    print("-" * 80)
    example_whyis_plugin_integration()
    print()
    
    print("\nExample 2: Fediverse Integration")
    print("-" * 80)
    example_whyis_fediverse_integration()
    print()
    
    print("\nExample 3: Backend Compaction")
    print("-" * 80)
    example_backend_compaction_integration()
    print()
    
    print("\nExample 4: Knowledge Graph Tools")
    print("-" * 80)
    example_with_knowledge_graph_tools()
