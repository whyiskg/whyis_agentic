"""Example: Configuring the Whyis Agentic Plugin in a Whyis application."""

# This would go in your whyis.conf file or Python configuration

from whyis import autonomic

from whyis_agentic.agent import QuestionAnsweringAgent

# Site configuration
SITE_NAME = "Whyis with AI Agents"
LOD_PREFIX = "http://purl.org/whyis/local"
VOCAB_FILE = "vocab.ttl"

# Configure the agentic inference agent
INFERENCERS = {
    "SETLr": autonomic.SETLr(),
    "SETLMaker": autonomic.SETLMaker(),
    "SDDAgent": autonomic.SDDAgent(),
    # Add the question answering agent
    "QuestionAnsweringAgent": QuestionAnsweringAgent(),
}

# Environment variables to set:
# export GITHUB_TOKEN="your-github-token"
# export AGENTIC_PROVIDER="github"  # or "openai"
# export AGENTIC_MODEL="gpt-4"
# export AGENTIC_SYSTEM_PROMPT="You are a knowledge graph expert."

print("""
To use this configuration:

1. Install whyis_agentic:
   pip install -e .

2. Set environment variables:
   export GITHUB_TOKEN="your-token"
   export AGENTIC_PROVIDER="github"
   export AGENTIC_MODEL="gpt-4"

3. Add to your whyis.conf:
   from whyis_agentic.agent import QuestionAnsweringAgent

   INFERENCERS = {
       ...
       "QuestionAnsweringAgent": QuestionAnsweringAgent()
   }

4. The agent will monitor for ActivityStream Note posts with questions
   and automatically generate answers as nanopublications.
""")
