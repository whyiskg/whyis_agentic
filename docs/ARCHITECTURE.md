# Architecture Overview

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     WhyisAgenticPlugin                      │
│  (Plugin integration with Whyis framework)                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ├──> InferenceAgent (Core Agent)
                 │    ├─ AgentConfig (configuration)
                 │    ├─ Message handling
                 │    ├─ Tool management
                 │    └─ Conversation history
                 │
                 ├──> DialogAgent (ActivityStream)
                 │    ├─ Question detection
                 │    ├─ Post processing
                 │    ├─ Reply generation
                 │    └─ Sub-conversation tracking
                 │
                 └──> Providers
                      ├─ GitHubProvider (OpenAI SDK)
                      └─ [Future providers...]
```

## Class Hierarchy

### InferenceAgent
The base agent class that provides:
- Message conversation management
- Tool calling capabilities
- Provider abstraction
- Thinking/research recording

### DialogAgent
Extends `InferenceAgent` for ActivityStream interactions:
- Question detection via pattern matching
- ActivityStream post processing
- Automatic reply generation
- Sub-conversation management for transparency

### WhyisAgenticPlugin
Whyis plugin wrapper that:
- Integrates with Whyis application lifecycle
- Manages multiple agent instances
- Provides configuration interface
- Coordinates with other Whyis plugins

## Data Flow

### Question Processing Flow

```
ActivityStream Post
        ↓
DialogAgent.process_post()
        ↓
is_question() → [No] → Skip
        ↓ [Yes]
Create SubConversation
        ↓
generate_response()
        ↓
Provider.complete()
        ↓
Handle tool calls (if any)
        ↓
Record thinking steps
        ↓
Create reply post
        ↓
post_callback()
        ↓
Publish to ActivityStream
```

### Tool Execution Flow

```
generate_response()
        ↓
Provider returns tool_calls
        ↓
_handle_tool_calls()
        ↓
For each tool_call:
    ├─ Find tool definition
    ├─ Execute tool.function()
    ├─ Record as thinking (if enabled)
    └─ Collect results
        ↓
Generate final response with tool results
        ↓
Return complete answer
```

## Provider Architecture

### InferenceProvider Interface

```python
class InferenceProvider(ABC):
    @abstractmethod
    def complete(messages, tools, **kwargs) -> Message:
        """Synchronous completion"""
        
    @abstractmethod
    def stream_complete(messages, tools, **kwargs):
        """Streaming completion"""
```

### Adding New Providers

To add a new AI provider:

1. Create a new class inheriting from `InferenceProvider`
2. Implement `complete()` and `stream_complete()` methods
3. Add the provider to `ProviderType` enum
4. Update `InferenceAgent._initialize_provider()` to handle new provider

Example:

```python
class OpenAIProvider(InferenceProvider):
    def __init__(self, api_key, model):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def complete(self, messages, tools=None, **kwargs):
        # Implementation
        pass
```

## Configuration System

### AgentConfig
Pydantic model for agent configuration:
- Type validation
- Default values
- JSON schema generation
- Environment variable support

### Plugin Configuration
Dictionary-based configuration supporting:
- Multiple agents
- Provider settings
- API keys
- Backend compaction settings

## Sub-Conversations

Sub-conversations provide transparency by recording:
- Intermediate reasoning steps
- Tool execution details
- Research queries
- Decision-making process

Structure:
```python
SubConversation(
    id="unique_id",
    parent_post_id="post_being_answered",
    purpose="thinking_and_research",
    messages=[...],  # Thinking steps
    metadata={...}
)
```

## Integration Points

### With Whyis Framework
```python
# In Whyis app factory
plugin = WhyisAgenticPlugin(config)
plugin.init_app(app)
```

### With whyis_fediverse
```python
# Fediverse plugin sends posts
fediverse.on_post_received(dialog_agent.process_post)

# Dialog agent sends replies
def publish_reply(post):
    fediverse.publish(post)
    
dialog_agent.post_callback = publish_reply
```

### As Backend Compaction
```python
# Periodic check for new questions
def compaction_task():
    posts = knowledge_graph.get_recent_posts()
    for post in posts:
        if dialog_agent.is_question(post.content):
            dialog_agent.process_post(post)
```

## Extension Points

### Custom Tools
```python
tool = ToolDefinition(
    name="custom_tool",
    description="Does something",
    parameters={...},
    function=my_function
)
agent.add_tool(tool)
```

### Custom Question Detection
```python
class CustomDialogAgent(DialogAgent):
    def is_question(self, content):
        # Custom logic
        return custom_detection(content)
```

### Custom Message Processing
```python
class CustomInferenceAgent(InferenceAgent):
    def generate_response(self, message, **kwargs):
        # Pre-processing
        result = super().generate_response(message, **kwargs)
        # Post-processing
        return result
```

## Security Considerations

- API keys should be stored in environment variables
- Rate limiting should be implemented at the provider level
- Input validation on all user-provided content
- Tool execution should be sandboxed
- Sub-conversation data should be stored securely

## Performance Considerations

- Lazy provider initialization
- Connection pooling for API calls
- Caching of common queries (future)
- Async/await support (future)
- Batch processing for multiple posts (future)

## Testing Strategy

- Unit tests for core components
- Integration tests for providers
- Mock-based tests for external APIs
- Coverage target: 80%+
- Test data isolation
