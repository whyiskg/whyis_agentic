# whyis_agentic

An agentic framework plugin for Whyis that provides Gen AI inference capabilities with support for ActivityStream interactions.

## Overview

`whyis_agentic` is a Whyis plugin that enables AI-powered agents to interact with knowledge graphs and ActivityStream posts. It supports multiple AI providers (currently GitHub Copilot with the OpenAI SDK) and can be extended to other providers.

### Key Features

- **Configurable AI Agents**: Create agents with custom prompts and tools
- **GitHub Copilot SDK Support**: Uses OpenAI SDK for GitHub Copilot integration
- **Extensible Provider Architecture**: Easy to add new AI providers
- **ActivityStream Dialog Agent**: Automatically responds to questions in ActivityStream posts
- **Sub-Conversations**: Records thinking and research steps transparently
- **Tool Support**: Agents can use custom tools for enhanced capabilities
- **Whyis Plugin Integration**: Seamlessly integrates with Whyis framework

## Installation

```bash
# Basic installation
pip install -e .

# With GitHub Copilot support
pip install -e ".[github]"

# Development installation
pip install -e ".[dev]"
```

## Quick Start

### Basic Inference Agent

```python
from whyis_agentic.agent import InferenceAgent, AgentConfig, ProviderType

# Configure the agent
config = AgentConfig(
    name="my_agent",
    provider=ProviderType.GITHUB,
    model="gpt-4",
    system_prompt="You are a helpful assistant.",
    api_key="your-github-token"
)

# Create and use the agent
agent = InferenceAgent(config)
response = agent.generate_response("What is a knowledge graph?")
print(response.content)
```

### Dialog Agent for ActivityStreams

```python
from whyis_agentic.dialog_agent import DialogAgent, ActivityStreamPost
from whyis_agentic.agent import AgentConfig, ProviderType

# Configure dialog agent
config = AgentConfig(
    name="dialog_bot",
    provider=ProviderType.GITHUB,
    system_prompt="You answer questions in discussions.",
    api_key="your-github-token"
)

# Create agent with callback for posting replies
def post_reply(post: ActivityStreamPost):
    print(f"Reply to {post.in_reply_to}: {post.content}")

agent = DialogAgent(config, post_callback=post_reply)

# Process incoming posts
post = ActivityStreamPost(
    id="post1",
    content="What is Whyis?",
    actor="user1"
)

reply = agent.process_post(post)
```

### Adding Custom Tools

```python
from whyis_agentic.agent import ToolDefinition

def search_database(query: str) -> str:
    """Search the database."""
    return f"Results for: {query}"

tool = ToolDefinition(
    name="search_db",
    description="Search the database",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"]
    },
    function=search_database
)

agent.add_tool(tool)
```

## Architecture

### Components

1. **InferenceAgent**: Core agent class with AI provider integration
2. **DialogAgent**: Extends InferenceAgent for ActivityStream interactions
3. **WhyisAgenticPlugin**: Whyis plugin wrapper for easy integration
4. **Providers**: AI provider implementations (GitHub, extensible to others)
5. **Models**: Pydantic models for messages, tools, and configuration

### Provider Architecture

The plugin uses an abstract `InferenceProvider` interface, making it easy to add new AI providers:

```python
from whyis_agentic.agent import InferenceProvider, Message

class CustomProvider(InferenceProvider):
    def complete(self, messages, tools=None, **kwargs):
        # Implement your provider logic
        pass
    
    def stream_complete(self, messages, tools=None, **kwargs):
        # Implement streaming logic
        pass
```

### Sub-Conversations

Dialog agents automatically record "thinking" and research as sub-conversations:

```python
# Generate response with thinking recorded
response = agent.generate_response("Complex question?", record_thinking=True)

# Retrieve thinking steps
thinking_steps = agent.get_thinking_steps()

# Get sub-conversations for a specific post
sub_convs = agent.get_sub_conversations("post_id")
```

## Whyis Integration

### As a Backend Compaction Plugin

This plugin is designed to work as a backend compaction agent in Whyis:

```python
from whyis_agentic.plugin import WhyisAgenticPlugin

# Configure plugin
config = {
    "agents": [
        {
            "name": "qa_agent",
            "provider": "github",
            "model": "gpt-4",
            "system_prompt": "You are an expert on knowledge graphs."
        }
    ],
    "api_keys": {
        "github": "your-token"
    }
}

# Initialize plugin
plugin = WhyisAgenticPlugin(config=config)
plugin.init_app(whyis_app)
```

### Integration with whyis_fediverse

The dialog agent works seamlessly with the whyis_fediverse plugin:

1. Monitor ActivityStream posts from Fediverse
2. Identify questions using pattern matching
3. Generate informed responses using AI and tools
4. Publish replies back to ActivityPub
5. Record thinking as sub-conversations

## Configuration

### Agent Configuration

```python
AgentConfig(
    name="agent_name",              # Agent identifier
    provider=ProviderType.GITHUB,   # AI provider
    model="gpt-4",                  # Model identifier
    system_prompt="...",            # System prompt
    tools=[...],                    # Available tools
    temperature=0.7,                # Sampling temperature (0-2)
    max_tokens=None,                # Max response tokens
    api_key="...",                  # Provider API key
    api_base="..."                  # Custom API endpoint
)
```

### Plugin Configuration

```python
{
    "agents": [
        {
            "name": "agent1",
            "provider": "github",
            "model": "gpt-4",
            "system_prompt": "..."
        }
    ],
    "default_provider": "github",
    "api_keys": {
        "github": "your-github-token"
    }
}
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=whyis_agentic --cov-report=html
```

### Code Style

```bash
# Format code
black whyis_agentic tests

# Lint code
ruff whyis_agentic tests

# Type checking
mypy whyis_agentic
```

## Examples

See the `examples/` directory for detailed examples:

- `basic_agent_example.py`: Basic inference agent usage
- `dialog_agent_example.py`: ActivityStream dialog agent
- `whyis_integration_example.py`: Whyis plugin integration

## Environment Variables

- `GITHUB_TOKEN`: GitHub API token for GitHub Copilot provider

## License

Apache License 2.0 - See LICENSE file for details

## Contributing

Contributions are welcome! Please ensure:

1. Tests pass: `pytest`
2. Code is formatted: `black .`
3. Code is linted: `ruff .`
4. Documentation is updated

## Support

For issues and questions:
- GitHub Issues: https://github.com/whyiskg/whyis_agentic/issues
- Documentation: See `docs/` directory

## Roadmap

- [ ] Add more AI providers (OpenAI, Anthropic, etc.)
- [ ] Enhanced tool calling with function chaining
- [ ] SPARQL query tools for Whyis integration
- [ ] Streaming response support in dialog agent
- [ ] Rate limiting and quotas
- [ ] Agent conversation persistence
- [ ] Multi-agent coordination
