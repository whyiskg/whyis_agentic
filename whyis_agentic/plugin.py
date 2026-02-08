"""Base Whyis plugin implementation for agentic inference."""

from typing import Any, Dict, Optional


class WhyisPlugin:
    """
    Base class for Whyis plugins.

    This is a simplified base plugin interface based on common Whyis plugin patterns.
    Plugins can be configured with settings and integrated into the Whyis framework.
    """

    def __init__(self, app: Optional[Any] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Whyis plugin.

        Args:
            app: The Whyis application instance
            config: Plugin configuration dictionary
        """
        self.app = app
        self.config = config or {}
        self._initialized = False

    def init_app(self, app: Any) -> None:
        """
        Initialize the plugin with the Whyis application.

        Args:
            app: The Whyis application instance
        """
        self.app = app
        self._initialized = True

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the plugin with settings.

        Args:
            config: Configuration dictionary
        """
        self.config.update(config)

    def is_initialized(self) -> bool:
        """Check if the plugin is initialized."""
        return self._initialized


class WhyisAgenticPlugin(WhyisPlugin):
    """
    Whyis plugin for Gen AI agentic inference.

    This plugin provides AI agent capabilities to Whyis, supporting various
    inference backends (GitHub Copilot, etc.) and integration with ActivityStreams.
    """

    def __init__(self, app: Optional[Any] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Whyis Agentic plugin.

        Args:
            app: The Whyis application instance
            config: Plugin configuration including:
                - agents: List of agent configurations
                - default_provider: Default AI provider (e.g., 'github')
                - api_keys: Dictionary of API keys for different providers
        """
        super().__init__(app, config)
        self.agents = {}
        self._setup_agents()

    def _setup_agents(self) -> None:
        """Set up configured agents from configuration."""
        agents_config = self.config.get("agents", [])
        for agent_config in agents_config:
            agent_name = agent_config.get("name")
            if agent_name:
                # Agents will be registered by the application
                self.agents[agent_name] = agent_config

    def register_agent(self, name: str, agent: Any) -> None:
        """
        Register an agent instance with the plugin.

        Args:
            name: Agent identifier
            agent: Agent instance
        """
        self.agents[name] = agent

    def get_agent(self, name: str) -> Optional[Any]:
        """
        Get a registered agent by name.

        Args:
            name: Agent identifier

        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(name)
