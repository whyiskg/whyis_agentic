"""Tests for the WhyisAgenticPlugin."""

from whyis_agentic.plugin import WhyisAgenticPlugin, WhyisPlugin


class TestWhyisPlugin:
    """Tests for the base WhyisPlugin class."""

    def test_plugin_initialization(self):
        """Test basic plugin initialization."""
        plugin = WhyisPlugin()
        assert plugin.app is None
        assert plugin.config == {}
        assert not plugin.is_initialized()

    def test_plugin_with_config(self):
        """Test plugin initialization with config."""
        config = {"key": "value"}
        plugin = WhyisPlugin(config=config)
        assert plugin.config == config

    def test_plugin_init_app(self):
        """Test plugin app initialization."""
        plugin = WhyisPlugin()
        app = object()
        plugin.init_app(app)
        assert plugin.app is app
        assert plugin.is_initialized()

    def test_plugin_configure(self):
        """Test plugin configuration."""
        plugin = WhyisPlugin(config={"a": 1})
        plugin.configure({"b": 2})
        assert plugin.config == {"a": 1, "b": 2}


class TestWhyisAgenticPlugin:
    """Tests for the WhyisAgenticPlugin class."""

    def test_agentic_plugin_initialization(self):
        """Test agentic plugin initialization."""
        plugin = WhyisAgenticPlugin()
        assert plugin.agents == {}
        assert not plugin.is_initialized()

    def test_agentic_plugin_with_agents_config(self):
        """Test plugin with agents configuration."""
        config = {
            "agents": [
                {"name": "agent1", "provider": "github"},
                {"name": "agent2", "provider": "github"},
            ]
        }
        plugin = WhyisAgenticPlugin(config=config)
        assert "agent1" in plugin.agents
        assert "agent2" in plugin.agents

    def test_register_agent(self):
        """Test registering an agent."""
        plugin = WhyisAgenticPlugin()
        agent = object()
        plugin.register_agent("test_agent", agent)
        assert plugin.get_agent("test_agent") is agent

    def test_get_nonexistent_agent(self):
        """Test getting a non-existent agent."""
        plugin = WhyisAgenticPlugin()
        assert plugin.get_agent("nonexistent") is None
