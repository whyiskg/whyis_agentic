# Contributing to whyis_agentic

Thank you for your interest in contributing to whyis_agentic!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/whyiskg/whyis_agentic.git
cd whyis_agentic
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

3. Set up pre-commit hooks (optional):
```bash
pip install pre-commit
pre-commit install
```

## Development Workflow

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes

3. Run tests:
```bash
pytest
```

4. Format code:
```bash
black whyis_agentic tests examples
```

5. Lint code:
```bash
ruff check whyis_agentic tests examples
```

6. Run tests with coverage:
```bash
pytest --cov=whyis_agentic --cov-report=html
```

7. Commit your changes:
```bash
git add .
git commit -m "Description of your changes"
```

8. Push and create a pull request

## Code Style

- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use type hints for all functions
- Write docstrings for public APIs
- Keep functions focused and small

## Testing Guidelines

- Write tests for new features
- Maintain or improve coverage (target: 80%+)
- Use mocks for external APIs
- Test both success and error cases
- Name tests descriptively: `test_<what>_<when>_<expected>`

Example:
```python
def test_generate_response_with_invalid_input_raises_error(self):
    """Test that invalid input raises appropriate error."""
    # Test implementation
```

## Adding a New Provider

1. Create a new file in `whyis_agentic/providers/`
2. Implement `InferenceProvider` interface
3. Add to `ProviderType` enum
4. Update `InferenceAgent._initialize_provider()`
5. Add tests
6. Update documentation

Example:
```python
# whyis_agentic/providers/custom.py
from whyis_agentic.agent import InferenceProvider, Message

class CustomProvider(InferenceProvider):
    def complete(self, messages, tools=None, **kwargs):
        # Implementation
        pass
    
    def stream_complete(self, messages, tools=None, **kwargs):
        # Implementation
        pass
```

## Documentation

- Update README.md for user-facing changes
- Update API_REFERENCE.md for API changes
- Add examples for new features
- Update ARCHITECTURE.md for design changes

## Pull Request Process

1. Ensure all tests pass
2. Update documentation
3. Add entry to CHANGELOG.md (if exists)
4. Request review from maintainers
5. Address review feedback
6. Squash commits if requested

## Reporting Issues

When reporting issues, include:
- Python version
- Package version
- Minimal reproduction code
- Expected vs actual behavior
- Error messages and tracebacks

## Feature Requests

For feature requests:
- Describe the use case
- Explain why it's valuable
- Suggest implementation approach (optional)
- Consider contributing it yourself!

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## Questions?

- Open an issue for questions
- Check existing issues first
- Be patient and respectful

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

Thank you for contributing! 🎉
