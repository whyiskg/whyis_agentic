"""Whyis Agentic Inference Agents."""

import json
import logging
import os
from typing import Dict, List, Optional

import flask
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
        self._tools_enabled = True

    def _resolve_entity(self, term: str, context: Optional[str] = None) -> List[Dict]:
        """
        Resolve an entity using Whyis's entity resolver plugin.

        This tool allows the AI to look up entities in the knowledge graph
        to provide more accurate and grounded answers.

        Args:
            term: The term/entity to resolve (e.g., "RDF", "Tim Berners-Lee")
            context: Optional context to help with disambiguation

        Returns:
            List of resolved entities with their URIs and labels
        """
        try:
            # Access the current Flask app context
            app = flask.current_app
            if not hasattr(app, "resolve"):
                logger.warning("Entity resolver not available in Whyis app")
                return []

            # Call Whyis's entity resolver
            results = app.resolve(term, type=None, context=context, label=True)

            # Format results for the AI
            formatted_results = []
            for result in results[:5]:  # Limit to top 5 results
                formatted_results.append(
                    {
                        "uri": str(result.get("node", "")),
                        "label": str(result.get("label", "")),
                        "types": result.get("types", "").split("||") if result.get("types") else [],
                        "score": float(result.get("score", 0)),
                    }
                )

            logger.info(f"Resolved entity '{term}': found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Error resolving entity '{term}': {e}")
            return []

    def _get_entity_resolver_tool_definition(self) -> Dict:
        """
        Get the tool definition for entity resolution.

        Returns tool specification in OpenAI function calling format.
        """
        return {
            "type": "function",
            "function": {
                "name": "resolve_entity",
                "description": (
                    "Resolve an entity or term in the knowledge graph. "
                    "Use this to look up URIs and information about people, places, "
                    "concepts, or any named entity mentioned in questions. "
                    "Returns the entity URI, label, types, and relevance score."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "term": {
                            "type": "string",
                            "description": (
                                "The term or entity name to resolve "
                                "(e.g., 'RDF', 'semantic web')"
                            ),
                        },
                        "context": {
                            "type": "string",
                            "description": "Optional context to help disambiguate the term",
                        },
                    },
                    "required": ["term"],
                },
            },
        }

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
            # Prepare messages
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": question},
            ]

            # Prepare tools if enabled
            tools = []
            if self._tools_enabled:
                tools.append(self._get_entity_resolver_tool_definition())

            thinking_steps = []
            max_iterations = 3  # Prevent infinite loops
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                # Call GitHub Copilot Chat Completions API
                response_kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                }
                if tools:
                    response_kwargs["tools"] = tools

                response = client.chat.completions.create(**response_kwargs)

                message = response.choices[0].message
                finish_reason = response.choices[0].finish_reason

                # Record usage
                thinking_steps.append(
                    {
                        "type": "inference",
                        "provider": "github_copilot",
                        "model": self.model,
                        "iteration": iteration,
                        "tokens": {
                            "prompt": response.usage.prompt_tokens,
                            "completion": response.usage.completion_tokens,
                            "total": response.usage.total_tokens,
                        },
                    }
                )

                # Check if we have a final answer
                if finish_reason == "stop" or not message.tool_calls:
                    answer = message.content or "I couldn't generate an answer."
                    return (answer, thinking_steps)

                # Handle tool calls
                if message.tool_calls:
                    # Add assistant's message with tool calls to conversation
                    messages.append(
                        {
                            "role": "assistant",
                            "content": message.content,
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {
                                        "name": tc.function.name,
                                        "arguments": tc.function.arguments,
                                    },
                                }
                                for tc in message.tool_calls
                            ],
                        }
                    )

                    # Execute each tool call
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        try:
                            function_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            function_args = {}

                        # Execute the function
                        if function_name == "resolve_entity":
                            result = self._resolve_entity(
                                term=function_args.get("term", ""),
                                context=function_args.get("context"),
                            )
                            thinking_steps.append(
                                {
                                    "type": "tool_call",
                                    "tool": "resolve_entity",
                                    "arguments": function_args,
                                    "result_count": len(result),
                                }
                            )
                        else:
                            result = {"error": f"Unknown function: {function_name}"}

                        # Add tool result to conversation
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result),
                            }
                        )

            # If we hit max iterations, return what we have
            return ("Maximum iterations reached while processing tools.", thinking_steps)

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
