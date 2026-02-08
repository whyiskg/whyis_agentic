"""Whyis Agentic Inference Agents."""

import json
import logging
import os
from typing import Dict, List

import rdflib
from whyis import autonomic
from whyis.namespace import NS

logger = logging.getLogger(__name__)

# Import GitHub Copilot SDK (uses OpenAI SDK as the official client)
# GitHub Copilot Chat Completions API is accessed via the OpenAI Python SDK
# See: https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-chat-in-your-ide
try:
    from openai import OpenAI

    GITHUB_COPILOT_SDK_AVAILABLE = True
except ImportError:
    GITHUB_COPILOT_SDK_AVAILABLE = False
    logger.warning(
        "GitHub Copilot SDK (OpenAI package) not available. " "Install with: pip install openai"
    )


class QuestionAnsweringAgent(autonomic.UpdateChangeService):
    """
    Autonomic agent that answers questions in ActivityStream posts.

    This agent:
    - Monitors for ActivityStream Note posts that are questions
    - Uses GitHub Copilot Chat Completions API to generate answers
    - Records the answer as a nanopublication with provenance
    - Records thinking/reasoning steps for transparency

    GitHub Copilot Integration:
    - Uses the OpenAI Python SDK (official GitHub Copilot client)
    - Connects to GitHub's Copilot API endpoint
    - Requires GITHUB_TOKEN environment variable
    """

    activity_class = NS.agentic.answersQuestion

    def __init__(self):
        super().__init__()
        self.model = os.getenv("AGENTIC_MODEL", "gpt-4")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.system_prompt = os.getenv(
            "AGENTIC_SYSTEM_PROMPT",
            "You are a helpful AI assistant that answers questions "
            "about knowledge graphs and semantic web.",
        )
        self._copilot_client = None

    def getInputClass(self):  # noqa: N802 - Whyis convention
        """Questions are ActivityStream Note objects."""
        return NS.astr.Note

    def getOutputClass(self):  # noqa: N802 - Whyis convention
        """Output is AnsweredPost with the answer."""
        return NS.agentic.AnsweredPost

    def get_query(self):
        """
        SPARQL query to find unanswered questions.

        Looks for ActivityStream Notes that:
        - Have content ending with '?' or starting with question words
        - Don't already have an answer from this agent
        """
        return """
        PREFIX as: <https://www.w3.org/ns/activitystreams#>
        PREFIX agentic: <http://vocab.rpi.edu/whyis/agentic/>

        SELECT DISTINCT ?resource WHERE {
            ?resource a as:Note ;
                      as:content ?content .

            # Must be a question (ends with ? or starts with question word)
            FILTER (
                REGEX(?content, "\\\\?$") ||
                REGEX(?content,
                    "^(what|when|where|who|why|how|can|could|would|should|is|are|do|does)\\\\s",
                    "i")
            )

            # Not already answered
            FILTER NOT EXISTS {
                ?resource a agentic:AnsweredPost .
            }
        }
        """

    def _get_copilot_client(self):
        """
        Lazy initialization of GitHub Copilot client.

        Uses the OpenAI Python SDK which is the official client for
        GitHub Copilot Chat Completions API.
        """
        if self._copilot_client is None and GITHUB_COPILOT_SDK_AVAILABLE and self.github_token:
            # GitHub Copilot uses the OpenAI SDK with a custom endpoint
            # See: https://docs.github.com/en/copilot
            self._copilot_client = OpenAI(
                api_key=self.github_token, base_url="https://api.githubcopilot.com"
            )
        return self._copilot_client

    def _generate_answer(self, question: str) -> tuple[str, List[Dict]]:
        """
        Generate an answer using GitHub Copilot.

        Args:
            question: The question text

        Returns:
            Tuple of (answer_text, thinking_steps)
        """
        client = self._get_copilot_client()
        if not client:
            return (
                "I don't have access to GitHub Copilot to answer this question. "
                "Please set GITHUB_TOKEN environment variable.",
                [],
            )

        try:
            # Use GitHub Copilot Chat Completions API
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=0.7,
            )

            answer = response.choices[0].message.content or "I couldn't generate an answer."

            # Record thinking steps from usage
            thinking_steps = [
                {
                    "type": "inference",
                    "provider": "github_copilot",
                    "model": self.model,
                    "tokens": {
                        "prompt": response.usage.prompt_tokens,
                        "completion": response.usage.completion_tokens,
                        "total": response.usage.total_tokens,
                    },
                }
            ]

            return (answer, thinking_steps)

        except Exception as e:
            logger.error(f"Error generating answer with GitHub Copilot: {e}")
            return (f"Error generating answer: {str(e)}", [])

    def process_nanopub(self, i, o, nanopub):
        """
        Process a question post and generate an answer.

        Args:
            i: Input resource (the question post)
            o: Output resource (will become the answered post)
            nanopub: Nanopublication to record the answer
        """
        # Get the question content
        question = i.value(NS.astr.content)
        if not question:
            logger.warning(f"No content found for {i.identifier}")
            return

        question_text = str(question)
        logger.info(f"Answering question: {question_text[:100]}...")

        # Generate answer
        answer_text, thinking_steps = self._generate_answer(question_text)

        # Add answer to output
        o.add(NS.agentic.hasQuestion, rdflib.Literal(question_text))
        o.add(NS.agentic.hasAnswer, rdflib.Literal(answer_text))
        o.add(NS.RDF.type, NS.agentic.AnsweredPost)

        # Create answer as an ActivityStream Note in reply
        answer_post = nanopub.assertion.resource(rdflib.BNode())
        answer_post.add(NS.RDF.type, NS.astr.Note)
        answer_post.add(NS.astr.content, rdflib.Literal(answer_text))
        answer_post.add(NS.astr.inReplyTo, i.identifier)
        o.add(NS.astr.replies, answer_post.identifier)

        # Record thinking steps
        for idx, step in enumerate(thinking_steps):
            step_node = nanopub.provenance.resource(rdflib.BNode())
            step_node.add(NS.RDF.type, NS.agentic.ThinkingStep)
            step_node.add(NS.RDFS.label, rdflib.Literal(f"Thinking step {idx + 1}"))

            # Add step details
            for key, value in step.items():
                if isinstance(value, dict):
                    value = json.dumps(value)
                step_node.add(NS.RDFS.comment, rdflib.Literal(f"{key}: {value}"))

            o.add(NS.agentic.hasThinkingStep, step_node.identifier)

        logger.info(f"Generated answer for {i.identifier}")
