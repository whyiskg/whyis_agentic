# whyis_agentic

A Whyis plugin that provides Gen AI agentic inference capabilities for answering questions in ActivityStream posts with transparent reasoning trails.

## Overview

`whyis_agentic` is a backend compaction plugin for the [Whyis](https://github.com/tetherless-world/whyis) knowledge graph framework. It enables AI agents to automatically answer questions posted to ActivityStreams with full provenance tracking and transparent reasoning.

## Features

- **Autonomic Agent**: `QuestionAnsweringAgent` extends Whyis's `UpdateChangeService` to monitor and answer questions
- **ActivityStream Integration**: Works with ActivityStream Note posts from the `whyis_fediverse` plugin
- **GitHub Copilot SDK**: Uses GitHub Copilot Chat Completions API (via OpenAI Python SDK)
- **SPARQL Query Tool**: AI can query the knowledge graph with SPARQL, with introspection and entity resolution
- **Entity Resolution Tool**: AI can resolve entities in the knowledge graph using Whyis's entity resolver
- **Provenance Tracking**: Full RDF provenance via nanopublications
- **Transparent Reasoning**: Records thinking steps and tool usage
- **RDF Vocabulary**: Complete ontology in `vocab.ttl`

## Installation

```bash
# Install the plugin
pip install -e .

# Install with GitHub Copilot support (uses OpenAI SDK as official client)
pip install -e ".[github]"
```

## Configuration

### In your Whyis application `whyis.conf`:

```python
from whyis import autonomic
from whyis_agentic.agent import QuestionAnsweringAgent

# Add to your INFERENCERS
INFERENCERS = {
    "SETLr": autonomic.SETLr(),
    "SETLMaker": autonomic.SETLMaker(),
    "SDDAgent": autonomic.SDDAgent(),
    "QuestionAnsweringAgent": QuestionAnsweringAgent()
}
```

### Environment Variables:

```bash
# Required: GitHub token for Copilot API access
export GITHUB_TOKEN="your-github-token"

# Optional: Configure the agent
export AGENTIC_MODEL="gpt-4"      # default: gpt-4
export AGENTIC_SYSTEM_PROMPT="You are a helpful assistant..."
```

## How It Works

1. **Monitor**: The agent monitors for ActivityStream `as:Note` posts that contain questions
2. **Detect**: Questions are identified by:
   - Ending with `?`
   - Starting with question words (what, when, where, who, why, how, etc.)
3. **Query & Resolve**: The AI can use tools to gather information:
   - Query the knowledge graph with SPARQL
   - Resolve entities to URIs
   - Introspect graph structure
4. **Generate**: Uses GitHub Copilot Chat Completions API to generate an answer
5. **Record**: Creates a nanopublication with:
   - The answer as an `as:Note` in reply to the question
   - RDF type `agentic:AnsweredPost`
   - Provenance showing the activity and AI provider
   - Thinking steps and tool usage for transparency
6. **Publish**: Publishes to the knowledge graph for whyis_fediverse to display

## RDF Vocabulary

The plugin defines an RDF vocabulary in `vocab.ttl`:

- `agentic:AgenticAgent` - An AI agent
- `agentic:QuestionPost` - An ActivityStream post containing a question
- `agentic:AnsweredPost` - A question that has been answered
- `agentic:ThinkingStep` - A step in the reasoning process
- `agentic:answersQuestion` - Activity of answering a question
- And more...

## SPARQL Query Tool

The agent includes a SPARQL query tool that allows the AI to query `app.db` (the full knowledge graph) directly. Features include:

- **Direct SPARQL Queries**: Execute SELECT, ASK, CONSTRUCT queries on the full graph
- **Graph Introspection**: Automatically discover graph structure (classes, properties) when needed
- **Entity Resolution Integration**: Suggests using entity resolver for better query construction
- **Result Formatting**: Returns structured results with metadata

**Capabilities:**

1. **Query Execution**: Run any valid SPARQL query with namespace prefixes
2. **Pre-Query Introspection**: Get top classes and properties to understand graph schema
3. **Smart Grounding**: Combine with entity resolver to build accurate queries

**Example interaction:**

```
Question: "How many people are in the knowledge graph?"

AI thinks: Let me introspect the graph first to find the right class
Tool call: query_knowledge_graph(query="SELECT ?type (COUNT(?s) as ?count) WHERE { ?s a ?type } GROUP BY ?type LIMIT 10", introspect=true)
Tool result: {top_classes: [{"type": "foaf:Person", "count": 42}, ...], results: [...]}

AI thinks: Now I can query for people specifically
Tool call: query_knowledge_graph(query="SELECT (COUNT(?person) as ?count) WHERE { ?person a foaf:Person }")
Tool result: {count: 42}

Answer: "There are 42 people in the knowledge graph."
```

**Query Guidelines:**
- Standard SPARQL prefixes (rdf, rdfs, owl, dc, foaf, skos) are available
- Results limited to 100 rows for performance
- Use introspection when schema is unknown
- Combine with entity resolver for entity-specific queries

## Entity Resolution Tool

The agent includes an entity resolution tool that allows the AI to look up entities in the Whyis knowledge graph. When answering questions, the AI can:

- Resolve entity names to URIs (e.g., "Tim Berners-Lee" → `http://dbpedia.org/resource/Tim_Berners-Lee`)
- Disambiguate terms using context
- Get entity types and metadata
- Ground answers in the actual knowledge graph data

**Example interaction:**

```
Question: "Who created RDF?"
AI thinks: Let me resolve "RDF" to see what's in the knowledge graph
Tool call: resolve_entity(term="RDF", context="creator")
Tool result: [{uri: "http://www.w3.org/1999/02/22-rdf-syntax-ns#", label: "RDF", types: ["Standard"]}]
AI uses the URI to provide grounded answer
```

The tool uses Whyis's built-in `EntityResolverListener` plugin system, which can be configured with different backends (SPARQL, Fuseki, Neptune, etc.).

## Example

### Input (ActivityStream post):

```turtle
@prefix as: <https://www.w3.org/ns/activitystreams#> .

<http://example.org/post1> a as:Note ;
    as:content "What is a knowledge graph?" ;
    as:actor <http://example.org/user/alice> .
```

### Output (Nanopublication with answer):

```turtle
@prefix agentic: <http://vocab.rpi.edu/whyis/agentic/> .
@prefix as: <https://www.w3.org/ns/activitystreams#> .

<http://example.org/post1> a agentic:AnsweredPost ;
    agentic:hasQuestion "What is a knowledge graph?" ;
    agentic:hasAnswer "A knowledge graph is a semantic network..." ;
    as:replies <http://example.org/answer1> .

<http://example.org/answer1> a as:Note ;
    as:content "A knowledge graph is a semantic network..." ;
    as:inReplyTo <http://example.org/post1> .
```

## Integration with whyis_fediverse

This plugin is designed to work with [whyis_fediverse](https://github.com/whyiskg/whyis_fediverse):

1. whyis_fediverse displays ActivityStream posts and discussions
2. Users post questions as ActivityStream Notes
3. whyis_agentic agents detect and answer questions
4. Answers appear as replies in the whyis_fediverse UI

## Architecture

### Plugin Structure (following Whyis conventions)

```
whyis_agentic/
├── __init__.py           # Package exports
├── plugin.py             # WhyisAgenticPlugin (extends whyis.plugin.Plugin)
├── agent.py              # QuestionAnsweringAgent (extends autonomic.UpdateChangeService)
└── vocab.ttl             # RDF vocabulary definitions
```

### Autonomic Agent Pattern

The `QuestionAnsweringAgent` follows Whyis's autonomic agent pattern:

- Extends `autonomic.UpdateChangeService`
- Defines input class: `as:Note`
- Defines output class: `agentic:AnsweredPost`
- SPARQL query to find unanswered questions
- `process_nanopub()` method to generate answers
- Automatic provenance and activity tracking

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black whyis_agentic tests

# Lint code
ruff check whyis_agentic tests
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=whyis_agentic
```

## Examples

See the `examples/` directory:

- `whyis_config_example.py` - How to configure in Whyis
- `basic_usage.py` - Understanding the plugin workflow

## Requirements

- Python >= 3.8
- Whyis knowledge graph framework
- OpenAI SDK (for GitHub Copilot support)
- rdflib
- flask-pluginengine

## License

Apache License 2.0

## Contributing

See `CONTRIBUTING.md` for guidelines.

## Repository

https://github.com/whyiskg/whyis_agentic
