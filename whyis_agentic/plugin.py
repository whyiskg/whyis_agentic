"""Whyis Agentic Plugin - Gen AI inference for knowledge graphs."""

import logging

import rdflib
from flask_pluginengine import PluginBlueprint
from whyis.plugin import Plugin

logger = logging.getLogger(__name__)

plugin_blueprint = PluginBlueprint("agentic", __name__)


class WhyisAgenticPlugin(Plugin):
    """
    Whyis plugin for Gen AI agentic inference.

    This plugin provides AI agent capabilities to Whyis, enabling agents
    to answer questions in ActivityStream posts using various AI providers
    (GitHub Copilot, etc.) with transparent reasoning trails.
    """

    def create_blueprint(self):
        """Create the plugin blueprint for web routes."""
        return plugin_blueprint

    def init(self):
        """Initialize the plugin with Whyis."""
        # Register the agentic namespace
        self.app.NS.agentic = rdflib.Namespace("http://vocab.rpi.edu/whyis/agentic/")
        logger.info("Whyis Agentic Plugin initialized")
