"""Example: Basic usage of the InferenceAgent with GitHub Copilot."""

import os
from whyis_agentic.agent import InferenceAgent, AgentConfig, ProviderType, ToolDefinition


def example_basic_agent():
    """Basic example of creating and using an inference agent."""
    
    # Configure the agent
    config = AgentConfig(
        name="example_agent",
        provider=ProviderType.GITHUB,
        model="gpt-4",
        system_prompt="You are a helpful assistant that answers questions about Python programming.",
        temperature=0.7,
        api_key=os.getenv("GITHUB_TOKEN")  # Use your GitHub token
    )
    
    # Create the agent
    agent = InferenceAgent(config)
    
    # Generate a response
    print("User: What is a Python decorator?")
    response = agent.generate_response("What is a Python decorator?")
    print(f"Agent: {response.content}")
    print()
    
    # Continue the conversation
    print("User: Can you show me an example?")
    response = agent.generate_response("Can you show me an example?")
    print(f"Agent: {response.content}")


def example_agent_with_tools():
    """Example of using an agent with custom tools."""
    
    # Define a custom tool
    def calculate_sum(a: int, b: int) -> int:
        """Calculate the sum of two numbers."""
        return a + b
    
    tool = ToolDefinition(
        name="calculate_sum",
        description="Calculate the sum of two integers",
        parameters={
            "type": "object",
            "properties": {
                "a": {"type": "integer", "description": "First number"},
                "b": {"type": "integer", "description": "Second number"}
            },
            "required": ["a", "b"]
        },
        function=calculate_sum
    )
    
    # Configure agent with tool
    config = AgentConfig(
        name="math_agent",
        provider=ProviderType.GITHUB,
        system_prompt="You are a math assistant. Use the available tools to help with calculations.",
        tools=[tool],
        api_key=os.getenv("GITHUB_TOKEN")
    )
    
    agent = InferenceAgent(config)
    
    print("User: What is 15 + 27?")
    response = agent.generate_response("What is 15 + 27?")
    print(f"Agent: {response.content}")


def example_conversation_management():
    """Example of managing conversation history."""
    
    config = AgentConfig(
        name="history_agent",
        provider=ProviderType.GITHUB,
        api_key=os.getenv("GITHUB_TOKEN")
    )
    
    agent = InferenceAgent(config)
    
    # Have a conversation
    agent.generate_response("My name is Alice")
    agent.generate_response("What is my name?")
    
    # View conversation history
    print("Conversation history:")
    for msg in agent.get_conversation_history():
        print(f"{msg.role}: {msg.content[:50]}...")
    print()
    
    # Reset conversation
    agent.reset_conversation()
    print("After reset:")
    for msg in agent.get_conversation_history():
        print(f"{msg.role}: {msg.content[:50]}...")


if __name__ == "__main__":
    print("=" * 60)
    print("Example 1: Basic Agent")
    print("=" * 60)
    # example_basic_agent()
    print("\nNote: Uncomment examples and set GITHUB_TOKEN to run")
    
    print("\n" + "=" * 60)
    print("Example 2: Agent with Tools")
    print("=" * 60)
    # example_agent_with_tools()
    print("\nNote: Uncomment examples and set GITHUB_TOKEN to run")
    
    print("\n" + "=" * 60)
    print("Example 3: Conversation Management")
    print("=" * 60)
    # example_conversation_management()
    print("\nNote: Uncomment examples and set GITHUB_TOKEN to run")
