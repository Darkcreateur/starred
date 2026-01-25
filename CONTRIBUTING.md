# Contributing to Starred

Thank you for your interest in contributing! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Git
- A GitHub account
- API key for at least one LLM provider (Anthropic, OpenAI, or Gemini)

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/amirhmoradi/starred.git
cd starred

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev,all]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_categorizer.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/
```

## 📝 Pull Request Process

1. **Fork** the repository
2. **Create a branch** for your feature: `git checkout -b feature/amazing-feature`
3. **Make your changes** with clear, descriptive commits
4. **Add tests** for new functionality
5. **Ensure all tests pass** and code is formatted
6. **Update documentation** as needed
7. **Submit a pull request** with a clear description

### Commit Messages

Follow conventional commits:

```
feat: add support for Ollama provider
fix: handle rate limiting in GitHub API
docs: update README with new examples
chore: update dependencies
```

## 🎯 Areas for Contribution

### Good First Issues

- Improve error messages
- Add more examples to documentation
- Fix typos and documentation errors
- Add tests for existing code

### Feature Ideas

- **New LLM Providers**: Ollama, Claude local, Llama
- **Export Formats**: Obsidian, Notion, Raindrop.io
- **Web UI**: Simple interface for managing categories
- **Browser Extension**: Easier cookie management
- **Better Categorization**: Use embeddings, semantic search

### Code Improvements

- Increase test coverage
- Add type hints where missing
- Improve error handling
- Performance optimizations

## 🏗️ Architecture

```
starred/
├── src/
│   ├── __init__.py      # Package exports
│   ├── cli.py           # CLI interface
│   ├── models.py        # Data models
│   ├── github.py        # GitHub API client
│   ├── categorizer.py   # AI categorization
│   ├── exporter.py      # Markdown export
│   ├── sync.py          # GitHub lists sync
│   └── llm/             # LLM providers
│       ├── base.py      # Abstract base
│       ├── anthropic.py # Claude
│       ├── openai.py    # GPT
│       ├── gemini.py    # Gemini
│       └── factory.py   # Provider factory
├── tests/
├── .github/workflows/   # GitHub Actions
└── examples/            # Example files
```

### Adding a New LLM Provider

1. Create `src/llm/newprovider.py`:

```python
from .base import BaseLLMProvider, LLMResponse

class NewProvider(BaseLLMProvider):
    name = "newprovider"
    default_model = "model-name"
    
    def complete(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        # Implementation
        pass
    
    def complete_json(self, prompt: str, max_tokens: int = 4096) -> dict:
        # Implementation
        pass
```

2. Register in `src/llm/factory.py`
3. Add to `pyproject.toml` optional dependencies
4. Update documentation

## 📋 Code Style

- Use type hints for all function signatures
- Write docstrings for public functions
- Keep functions focused and small
- Handle errors gracefully with helpful messages

## 🐛 Reporting Issues

When reporting issues, please include:

- Python version (`python --version`)
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Relevant error messages or logs

## 💬 Questions?

- Open a GitHub Discussion for questions
- Check existing issues before creating new ones
- Join the conversation in pull requests

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.
