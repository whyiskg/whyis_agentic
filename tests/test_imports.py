"""Tests for basic package structure."""

import sys
from unittest.mock import MagicMock

# Mock Whyis and related dependencies before any imports
sys.modules["whyis"] = MagicMock()
sys.modules["whyis.plugin"] = MagicMock()
sys.modules["whyis.autonomic"] = MagicMock()
sys.modules["whyis.namespace"] = MagicMock()
sys.modules["flask_pluginengine"] = MagicMock()
sys.modules["flask"] = MagicMock()
sys.modules["rdflib"] = MagicMock()


class TestPackageStructure:
    """Test package structure and basic functionality."""

    def test_package_has_version(self):
        """Test that package has version."""
        import whyis_agentic

        assert hasattr(whyis_agentic, "__version__")
        assert whyis_agentic.__version__ == "0.1.0"

    def test_vocab_file_exists(self):
        """Test that vocab.ttl exists."""
        import os

        vocab_path = os.path.join(os.path.dirname(__file__), "../whyis_agentic/vocab.ttl")
        assert os.path.exists(vocab_path)

    def test_vocab_content(self):
        """Test that vocab.ttl has expected content."""
        import os

        vocab_path = os.path.join(os.path.dirname(__file__), "../whyis_agentic/vocab.ttl")
        with open(vocab_path) as f:
            content = f.read()
            assert "agentic:AgenticAgent" in content
            assert "agentic:QuestionPost" in content
            assert "agentic:AnsweredPost" in content
