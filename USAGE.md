# Usage Guide

## Installation

```bash
pip install -e .

# With AI provider support
pip install -e ".[github]"
```

## Configuration

### 1. Environment Variables

```bash
# Required: API key for your provider
export GITHUB_TOKEN="your-github-token"

# Optional: Configure the agent
export AGENTIC_PROVIDER="github"  # default
export AGENTIC_MODEL="gpt-4"      # default
export AGENTIC_SYSTEM_PROMPT="Custom prompt..."
```

### 2. Whyis Configuration

In your Whyis application's `whyis.conf`:

```python
from whyis import autonomic
from whyis_agentic.agent import QuestionAnsweringAgent

SITE_NAME = "My Whyis Site"
LOD_PREFIX = 'http://purl.org/whyis/local'
VOCAB_FILE = "vocab.ttl"

# Add the agentic agent to your inferencers
INFERENCERS = {
    "SETLr": autonomic.SETLr(),
    "SETLMaker": autonomic.SETLMaker(),
    "SDDAgent": autonomic.SDDAgent(),
    "QuestionAnsweringAgent": QuestionAnsweringAgent()
}
```

### 3. Plugin Installation

The plugin will be automatically discovered by Whyis through Python's package system.

## How It Works

### 1. Question Detection

The agent monitors the knowledge graph for ActivityStream `as:Note` posts that:
- End with `?`
- Start with question words (what, when, where, who, why, how, can, could, etc.)
- Haven't been answered yet (no `agentic:AnsweredPost` type)

### 2. Answer Generation

When a question is detected:
1. Extracts the question content from `as:content`
2. Sends to AI provider (GitHub Copilot by default)
3. Receives answer
4. Creates a nanopublication with:
   - Answer as an `as:Note` in reply
   - RDF type `agentic:AnsweredPost`
   - Provenance showing the activity
   - Thinking steps for transparency

### 3. RDF Output

The answer is stored as RDF in the knowledge graph:

```turtle
@prefix agentic: <http://vocab.rpi.edu/whyis/agentic/> .
@prefix as: <https://www.w3.org/ns/activitystreams#> .
@prefix prov: <http://www.w3.org/ns/prov#> .

<http://example.org/post1> a agentic:AnsweredPost ;
    agentic:hasQuestion "What is RDF?" ;
    agentic:hasAnswer "RDF is..." ;
    as:replies <http://example.org/answer1> .

<http://example.org/answer1> a as:Note ;
    as:content "RDF is..." ;
    as:inReplyTo <http://example.org/post1> .
```

## Integration with whyis_fediverse

1. Install both plugins in your Whyis application
2. Users post questions via whyis_fediverse UI
3. QuestionAnsweringAgent detects and answers
4. Answers appear in whyis_fediverse discussion threads

## Customization

### Custom System Prompt

```bash
export AGENTIC_SYSTEM_PROMPT="You are an expert in semantic web technologies and knowledge graphs. Provide detailed, accurate answers with examples."
```

### Different AI Model

```bash
export AGENTIC_MODEL="gpt-3.5-turbo"  # For faster/cheaper responses
```

### Custom Agent Subclass

```python
from whyis_agentic.agent import QuestionAnsweringAgent

class MyCustomAgent(QuestionAnsweringAgent):
    def get_query(self):
        # Override to detect different types of questions
        return '''
        SELECT DISTINCT ?resource WHERE {
            ?resource a as:Note ;
                      as:content ?content .
            FILTER (REGEX(?content, "custom pattern"))
        }
        '''
    
    def process_nanopub(self, i, o, nanopub):
        # Add custom processing
        super().process_nanopub(i, o, nanopub)
        # Additional custom logic here
```

## Troubleshooting

### Agent Not Answering

1. Check logs for errors:
   ```bash
   tail -f /var/log/whyis/whyis.log
   ```

2. Verify API key is set:
   ```bash
   echo $GITHUB_TOKEN
   ```

3. Check SPARQL query is finding questions:
   ```sparql
   PREFIX as: <https://www.w3.org/ns/activitystreams#>
   
   SELECT * WHERE {
       ?post a as:Note ;
             as:content ?content .
       FILTER (REGEX(?content, "\\?$"))
   }
   ```

### API Rate Limits

If hitting rate limits:
1. Use a different model (gpt-3.5-turbo)
2. Add caching logic in custom agent
3. Implement rate limiting in process_nanopub()

### Wrong Answers

1. Adjust system prompt for better context
2. Add tools/functions for knowledge graph queries
3. Pre-filter questions by topic

## Development

### Testing Locally

```python
from whyis_agentic.agent import QuestionAnsweringAgent

agent = QuestionAnsweringAgent()

# Check the SPARQL query
print(agent.get_query())

# Test answer generation
answer, steps = agent._generate_answer("What is RDF?")
print(answer)
print(steps)
```

### Adding Tools

```python
def search_knowledge_graph(query: str) -> str:
    """Search the knowledge graph."""
    # SPARQL query implementation
    return results

# Add to agent (requires modifying agent to support tool parameter)
```

## Best Practices

1. **Set specific system prompts** for your domain
2. **Monitor token usage** via thinking steps metadata
3. **Review answers** before deploying to production
4. **Rate limit** API calls if needed
5. **Cache common answers** for efficiency
6. **Log all interactions** for debugging
