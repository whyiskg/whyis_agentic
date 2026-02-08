"""Whyis Agentic - A Gen AI agentic inference plugin for Whyis."""

__version__ = "0.1.0"

from whyis_agentic.agent import InferenceAgent
from whyis_agentic.dialog_agent import DialogAgent
from whyis_agentic.plugin import WhyisAgenticPlugin

__all__ = ["InferenceAgent", "DialogAgent", "WhyisAgenticPlugin"]
