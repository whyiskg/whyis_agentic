"""Example: Basic usage of the WhyisAgenticPlugin."""

# Example of how the plugin works with Whyis

# 1. Install the plugin in your Whyis application


# The plugin will be automatically discovered by Whyis if installed
# in the Python environment

# 2. The plugin provides:
# - vocab.ttl with RDF ontology for agentic concepts
# - QuestionAnsweringAgent autonomic agent
# - Integration with ActivityStreams

# 3. Sample RDF data that would trigger the agent:

example_question_turtle = """
@prefix as: <https://www.w3.org/ns/activitystreams#> .
@prefix dc: <http://purl.org/dc/terms/> .

<http://example.org/post1> a as:Note ;
    as:content "What is a knowledge graph?" ;
    as:published "2026-02-08T10:00:00Z" ;
    as:actor <http://example.org/user/alice> .
"""

# 4. The agent will automatically:
# - Detect this is a question (contains "What")
# - Use GitHub Copilot (or other provider) to generate an answer
# - Create a nanopublication with:
#   * The answer as an ActivityStream Note
#   * Provenance showing the AI provider used
#   * Thinking steps recording the inference process
#   * RDF linking it back to the original question

# 5. Result RDF (simplified):

example_answer_turtle = """
@prefix as: <https://www.w3.org/ns/activitystreams#> .
@prefix agentic: <http://vocab.rpi.edu/whyis/agentic/> .
@prefix prov: <http://www.w3.org/ns/prov#> .

<http://example.org/post1> a agentic:AnsweredPost ;
    agentic:hasQuestion "What is a knowledge graph?" ;
    agentic:hasAnswer "A knowledge graph is..." ;
    as:replies <http://example.org/answer1> .

<http://example.org/answer1> a as:Note ;
    as:content "A knowledge graph is..." ;
    as:inReplyTo <http://example.org/post1> .

# Provenance recorded in nanopublication
<http://example.org/activity1> a agentic:answersQuestion ;
    prov:used <http://example.org/post1> ;
    agentic:hasProvider agentic:GitHubCopilotProvider .
"""

print("Whyis Agentic Plugin integrates AI agents into the Whyis knowledge graph framework.")
print("See whyis_config_example.py for configuration details.")
