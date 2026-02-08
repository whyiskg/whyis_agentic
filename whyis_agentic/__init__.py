"""Whyis Agentic - Gen AI inference plugin for Whyis."""

__version__ = "0.1.0"

from whyis_agentic.agent import QuestionAnsweringAgent
from whyis_agentic.plugin import WhyisAgenticPlugin

__all__ = ["WhyisAgenticPlugin", "QuestionAnsweringAgent"]
