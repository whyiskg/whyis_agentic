# Quick Start Guide

Get started with whyis_agentic in 5 minutes!

## Installation

```bash
# Clone the repository
git clone https://github.com/whyiskg/whyis_agentic.git
cd whyis_agentic

# Install with GitHub Copilot support
pip install -e ".[github]"

# Or for development
pip install -e ".[dev]"
```

## Set Up API Key

```bash
# Set your GitHub token
export GITHUB_TOKEN="your-github-token-here"
```

## Your First Agent

Create a file `my_first_agent.py`:

```python
from whyis_agentic.agent import InferenceAgent, AgentConfig, ProviderType

# Configure your agent
config = AgentConfig(
    name="my_assistant",
    provider=ProviderType.GITHUB,
    model="gpt-4",
    system_prompt="You are a helpful programming assistant."
)

# Create the agent
agent = InferenceAgent(config)

# Ask a question
response = agent.generate_response("What is a Python decorator?")
print(f"Agent: {response.content}")
```

Run it:
```bash
python my_first_agent.py
```

## Your First Dialog Agent

Create a file `dialog_bot.py`:

```python
from whyis_agentic.dialog_agent import DialogAgent, ActivityStreamPost
from whyis_agentic.agent import AgentConfig, ProviderType

# Configure dialog agent
config = AgentConfig(
    name="dialog_bot",
    provider=ProviderType.GITHUB,
    system_prompt="You are a helpful bot in discussions."
)

# Callback to handle replies
def post_reply(reply: ActivityStreamPost):
    print(f"\n[REPLY TO {reply.in_reply_to}]")
    print(f"Content: {reply.content}")

# Create agent
agent = DialogAgent(config, post_callback=post_reply)

# Simulate an incoming question
post = ActivityStreamPost(
    id="post1",
    content="What is a knowledge graph?",
    actor="alice"
)

# Process it
reply = agent.process_post(post)
```

Run it:
```bash
python dialog_bot.py
```

## Adding Custom Tools

```python
from whyis_agentic.agent import ToolDefinition

# Define a tool
def get_weather(city: str) -> str:
    """Get weather for a city (mock)."""
    return f"The weather in {city} is sunny!"

weather_tool = ToolDefinition(
    name="get_weather",
    description="Get current weather for a city",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name"
            }
        },
        "required": ["city"]
    },
    function=get_weather
)

# Add to agent
agent.add_tool(weather_tool)

# Now the agent can use this tool!
response = agent.generate_response("What's the weather in Paris?")
```

## Using with Whyis

```python
from whyis_agentic.plugin import WhyisAgenticPlugin

# Configure plugin
config = {
    "agents": [
        {
            "name": "qa_agent",
            "provider": "github",
            "model": "gpt-4",
            "system_prompt": "You are a Whyis expert."
        }
    ]
}

# Create plugin
plugin = WhyisAgenticPlugin(config=config)

# In your Whyis app
# plugin.init_app(app)
```

## Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=whyis_agentic

# Specific test file
pytest tests/test_agent.py
```

## Common Patterns

### Multi-turn Conversation

```python
agent = InferenceAgent(config)

# First question
agent.generate_response("My name is Bob")

# Follow-up (agent remembers context)
response = agent.generate_response("What's my name?")
# Returns: "Your name is Bob"
```

### Thinking Recording

```python
# Enable thinking recording
response = agent.generate_response(
    "Complex question?",
    record_thinking=True
)

# View thinking steps
thinking = agent.get_thinking_steps()
for step in thinking:
    print(f"Thought: {step.content}")
```

### Stream Processing

```python
def my_stream():
    """Your ActivityStream source."""
    while True:
        post = fetch_next_post()
        yield post

# Agent listens and auto-replies to questions
agent.listen_to_stream(my_stream())
```

## Configuration Files

Create `config.yaml`:

```yaml
agents:
  - name: main_agent
    provider: github
    model: gpt-4
    system_prompt: "You are helpful"
    temperature: 0.7

api_keys:
  github: "${GITHUB_TOKEN}"
```

Load it:

```python
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)

plugin = WhyisAgenticPlugin(config=config)
```

## Next Steps

- Read the [Architecture Guide](docs/ARCHITECTURE.md)
- Check the [API Reference](docs/API_REFERENCE.md)
- Explore [Examples](examples/)
- Star the repo! ⭐

## Troubleshooting

### "Module not found" error

```bash
# Make sure you installed the package
pip install -e .
```

### "API key not found" error

```bash
# Set your GitHub token
export GITHUB_TOKEN="your-token"
```

### Import errors

```bash
# Install OpenAI SDK
pip install openai
```

## Get Help

- Issues: https://github.com/whyiskg/whyis_agentic/issues
- Examples: Check `examples/` directory
- Tests: Check `tests/` for usage patterns

Happy coding! 🚀
