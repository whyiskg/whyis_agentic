# API Reference

## Core Classes

### InferenceAgent

The main agent class for AI inference.

#### Constructor

```python
InferenceAgent(config: AgentConfig)
```

**Parameters:**
- `config` (AgentConfig): Agent configuration

**Example:**
```python
config = AgentConfig(
    name="my_agent",
    provider=ProviderType.GITHUB,
    system_prompt="You are helpful."
)
agent = InferenceAgent(config)
```

#### Methods

##### `generate_response(user_message: str, record_thinking: bool = True) -> Message`

Generate a response to a user message.

**Parameters:**
- `user_message` (str): The user's input message
- `record_thinking` (bool): Whether to record thinking steps (default: True)

**Returns:**
- `Message`: The agent's response

**Example:**
```python
response = agent.generate_response("What is AI?")
print(response.content)
```

##### `add_message(role: str, content: str, metadata: Optional[Dict] = None)`

Add a message to conversation history.

**Parameters:**
- `role` (str): Message role ('user', 'assistant', 'system')
- `content` (str): Message content
- `metadata` (Optional[Dict]): Additional metadata

##### `add_tool(tool: ToolDefinition)`

Add a tool to the agent's capabilities.

**Parameters:**
- `tool` (ToolDefinition): Tool to add

##### `reset_conversation()`

Reset conversation history, keeping only system messages.

##### `get_conversation_history() -> List[Message]`

Get the full conversation history.

**Returns:**
- `List[Message]`: All messages in conversation

##### `get_thinking_steps() -> List[Message]`

Get only thinking/research messages.

**Returns:**
- `List[Message]`: Messages marked as thinking

---

### DialogAgent

Dialog agent for ActivityStream interactions. Extends `InferenceAgent`.

#### Constructor

```python
DialogAgent(
    config: AgentConfig,
    post_callback: Optional[Callable[[ActivityStreamPost], None]] = None
)
```

**Parameters:**
- `config` (AgentConfig): Agent configuration
- `post_callback` (Callable, optional): Callback for posting replies

#### Methods

##### `is_question(content: str) -> bool`

Determine if content is a question.

**Parameters:**
- `content` (str): Text to analyze

**Returns:**
- `bool`: True if content appears to be a question

##### `process_post(post: ActivityStreamPost) -> Optional[ActivityStreamPost]`

Process an ActivityStream post and generate reply if it's a question.

**Parameters:**
- `post` (ActivityStreamPost): Post to process

**Returns:**
- `Optional[ActivityStreamPost]`: Reply post or None

**Example:**
```python
post = ActivityStreamPost(
    id="post1",
    content="What is Whyis?",
    actor="user1"
)
reply = agent.process_post(post)
```

##### `get_sub_conversations(post_id: str) -> List[SubConversation]`

Get all sub-conversations for a post.

**Parameters:**
- `post_id` (str): Post identifier

**Returns:**
- `List[SubConversation]`: Sub-conversations

##### `listen_to_stream(stream_source, filter_func: Optional[Callable] = None)`

Listen to an ActivityStream source and process posts.

**Parameters:**
- `stream_source`: Iterable source of posts
- `filter_func` (Callable, optional): Filter for post selection

##### `create_tool_from_activitystream(...) -> ToolDefinition`

Create a tool that interacts with ActivityStream.

---

### WhyisAgenticPlugin

Whyis plugin for agentic inference.

#### Constructor

```python
WhyisAgenticPlugin(
    app: Optional[Any] = None,
    config: Optional[Dict[str, Any]] = None
)
```

**Parameters:**
- `app` (Any, optional): Whyis application instance
- `config` (Dict, optional): Plugin configuration

#### Methods

##### `init_app(app: Any)`

Initialize plugin with Whyis application.

##### `register_agent(name: str, agent: Any)`

Register an agent instance.

##### `get_agent(name: str) -> Optional[Any]`

Get a registered agent by name.

---

## Data Models

### AgentConfig

Agent configuration model.

**Fields:**
- `name` (str): Agent name
- `provider` (ProviderType): AI provider ('github')
- `model` (str): Model identifier (default: 'gpt-4')
- `system_prompt` (str): System prompt (default: 'You are a helpful AI assistant.')
- `tools` (List[ToolDefinition]): Available tools (default: [])
- `temperature` (float): Sampling temperature 0-2 (default: 0.7)
- `max_tokens` (Optional[int]): Maximum response tokens
- `api_key` (Optional[str]): Provider API key
- `api_base` (Optional[str]): Custom API endpoint

**Example:**
```python
config = AgentConfig(
    name="qa_bot",
    provider=ProviderType.GITHUB,
    model="gpt-4",
    system_prompt="You are a QA bot.",
    temperature=0.5,
    max_tokens=500
)
```

### Message

A message in conversation.

**Fields:**
- `role` (str): Message role ('system', 'user', 'assistant')
- `content` (str): Message content
- `metadata` (Dict[str, Any]): Additional metadata (default: {})

**Example:**
```python
msg = Message(
    role="user",
    content="Hello!",
    metadata={"timestamp": "2024-01-01"}
)
```

### ToolDefinition

Definition of a tool.

**Fields:**
- `name` (str): Tool name
- `description` (str): What the tool does
- `parameters` (Dict[str, Any]): JSON schema of parameters (default: {})
- `function` (Optional[Callable]): Callable function

**Example:**
```python
def add(a: int, b: int) -> int:
    return a + b

tool = ToolDefinition(
    name="add",
    description="Add two numbers",
    parameters={
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "integer"}
        },
        "required": ["a", "b"]
    },
    function=add
)
```

### ActivityStreamPost

ActivityStream post representation.

**Fields:**
- `id` (str): Unique identifier
- `type` (str): ActivityStream type (default: 'Note')
- `content` (str): Post content
- `actor` (str): Actor who created the post
- `published` (Optional[str]): Publication timestamp
- `in_reply_to` (Optional[str]): ID of post being replied to
- `conversation` (Optional[str]): Conversation thread ID
- `metadata` (Dict[str, Any]): Additional metadata (default: {})

### SubConversation

Sub-conversation for thinking/research.

**Fields:**
- `id` (str): Sub-conversation identifier
- `parent_post_id` (str): Parent post being responded to
- `purpose` (str): Purpose (e.g., 'thinking_and_research')
- `messages` (List[Message]): Messages in sub-conversation (default: [])
- `metadata` (Dict[str, Any]): Additional metadata (default: {})

---

## Providers

### InferenceProvider

Abstract base class for AI providers.

#### Methods

##### `complete(messages: List[Message], tools: Optional[List[ToolDefinition]] = None, **kwargs) -> Message`

Generate a completion.

##### `stream_complete(messages: List[Message], tools: Optional[List[ToolDefinition]] = None, **kwargs)`

Stream completions (generator).

### GitHubProvider

GitHub Copilot provider using OpenAI SDK.

#### Constructor

```python
GitHubProvider(
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: str = "gpt-4"
)
```

**Parameters:**
- `api_key` (str, optional): GitHub token (defaults to GITHUB_TOKEN env var)
- `api_base` (str, optional): API base URL
- `model` (str): Model identifier

---

## Enums

### ProviderType

```python
class ProviderType(str, Enum):
    GITHUB = "github"
    # Future providers...
```

---

## Exceptions

The library uses standard Python exceptions:

- `ValueError`: Invalid configuration or parameters
- `ImportError`: Missing dependencies (e.g., OpenAI SDK)
- Standard exceptions from underlying providers

---

## Type Hints

All functions and methods include type hints for better IDE support and type checking.

Example:
```python
from typing import List, Optional
from whyis_agentic.agent import Message

def process_messages(messages: List[Message]) -> Optional[str]:
    if not messages:
        return None
    return messages[-1].content
```

---

## Configuration Format

### JSON Configuration

```json
{
  "agents": [
    {
      "name": "agent_name",
      "provider": "github",
      "model": "gpt-4",
      "system_prompt": "...",
      "temperature": 0.7
    }
  ]
}
```

### YAML Configuration

```yaml
agents:
  - name: agent_name
    provider: github
    model: gpt-4
    system_prompt: "..."
    temperature: 0.7
```

### Python Configuration

```python
config = {
    "agents": [
        {
            "name": "agent_name",
            "provider": "github",
            "model": "gpt-4",
            "system_prompt": "...",
            "temperature": 0.7
        }
    ]
}
```
