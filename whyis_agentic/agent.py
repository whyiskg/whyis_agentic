"""Whyis Agentic Inference Agents."""

import json
import logging
import os
from typing import Dict, List

import rdflib
from whyis import autonomic
from whyis.namespace import NS

logger = logging.getLogger(__name__)

# Import AI provider
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI SDK not available. Install with: pip install openai")


class QuestionAnsweringAgent(autonomic.UpdateChangeService):
    """
    Autonomic agent that answers questions in ActivityStream posts.

    This agent:
    - Monitors for ActivityStream Note posts that are questions
    - Uses AI (GitHub Copilot or other providers) to generate answers
    - Records the answer as a nanopublication with provenance
    - Records thinking/reasoning steps for transparency
    """

    activity_class = NS.agentic.answersQuestion

    def __init__(self):
        super().__init__()
        self.provider = os.getenv("AGENTIC_PROVIDER", "github")
        self.model = os.getenv("AGENTIC_MODEL", "gpt-4")
        self.api_key = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")
        self.system_prompt = os.getenv(
            "AGENTIC_SYSTEM_PROMPT",
            "You are a helpful AI assistant that answers questions "
            "about knowledge graphs and semantic web.",
        )
        self._client = None

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

    def _get_client(self):
        """Lazy initialization of AI client."""
        if self._client is None and OPENAI_AVAILABLE and self.api_key:
            if self.provider == "github":
                self._client = OpenAI(
                    api_key=self.api_key, base_url="https://api.githubcopilot.com"
                )
            else:
                self._client = OpenAI(api_key=self.api_key)
        return self._client

    def _generate_answer(self, question: str) -> tuple[str, List[Dict]]:
        """
        Generate an answer using the AI provider.

        Args:
            question: The question text

        Returns:
            Tuple of (answer_text, thinking_steps)
        """
        client = self._get_client()
        if not client:
            return ("I don't have access to an AI provider to answer this question.", [])

        try:
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
                    "provider": self.provider,
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
            logger.error(f"Error generating answer: {e}")
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
