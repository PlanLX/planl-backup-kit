# Contributing to PlanLX Backup Kit

Thank you for your interest in contributing to PlanLX Backup Kit! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

Before creating an issue, please:

1. **Search existing issues** to avoid duplicates
2. **Use the issue template** and provide all requested information
3. **Include reproduction steps** for bugs
4. **Add relevant logs** and error messages
5. **Specify your environment** (OS, Python version, etc.)

### Feature Requests

When requesting features:

1. **Describe the use case** clearly
2. **Explain the expected behavior**
3. **Consider backward compatibility**
4. **Provide examples** if possible

### Pull Requests

#### Before Submitting

1. **Fork the repository**
2. **Create a feature branch** from `main`
3. **Follow the coding standards** (see below)
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Ensure all tests pass**

#### Pull Request Guidelines

- **Use descriptive commit messages**
- **Keep PRs focused** on a single feature/fix
- **Add tests** for new functionality
- **Update documentation** if needed
- **Follow the PR template**

## 🛠️ Development Setup

### Prerequisites

- Python 3.12+
- Docker (for testing)
- Git

### Local Development

```bash
# Fork and clone
git clone https://github.com/your-username/planl-backup-kit.git
cd planl-backup-kit

# Set up development environment
cd elasticsearch
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_snapshot.py

# Run with verbose output
uv run pytest -v
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Check code style
uv run ruff check .

# Type checking
uv run mypy src/

# Run all quality checks
uv run pre-commit run --all-files
```

## 📝 Coding Standards

### Python Code Style

We use the following tools for code quality:

- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **MyPy**: Type checking
- **Pre-commit**: Git hooks

### Code Style Guidelines

1. **Follow PEP 8** with Black formatting
2. **Use type hints** for all functions
3. **Write docstrings** for public functions
4. **Use descriptive variable names**
5. **Keep functions small and focused**
6. **Handle exceptions appropriately**

### Example Code Style

```python
from typing import List, Optional
from pydantic import BaseModel


class SnapshotConfig(BaseModel):
    """Configuration for Elasticsearch snapshots."""
    
    repository_name: str
    indices: List[str]
    wait_for_completion: bool = True
    
    def validate_indices(self) -> None:
        """Validate that indices are properly formatted."""
        if not self.indices:
            raise ValueError("At least one index must be specified")


async def create_snapshot(config: SnapshotConfig) -> str:
    """Create an Elasticsearch snapshot.
    
    Args:
        config: Snapshot configuration
        
    Returns:
        Snapshot name
        
    Raises:
        ValueError: If configuration is invalid
        ConnectionError: If Elasticsearch is unreachable
    """
    config.validate_indices()
    # Implementation here
    return "snapshot_name"
```

### Documentation Standards

1. **Use clear, concise language**
2. **Include code examples**
3. **Document all public APIs**
4. **Keep documentation up to date**
5. **Use proper Markdown formatting**

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/              # Unit tests
├── integration/       # Integration tests
├── fixtures/          # Test fixtures
└── conftest.py        # Pytest configuration
```

### Writing Tests

1. **Test one thing at a time**
2. **Use descriptive test names**
3. **Arrange, Act, Assert** pattern
4. **Mock external dependencies**
5. **Test edge cases and error conditions**

### Example Test

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.core.snapshot import ElasticsearchSnapshot


@pytest.mark.asyncio
async def test_create_snapshot_success():
    """Test successful snapshot creation."""
    # Arrange
    config = SnapshotConfig(
        repository_name="test_repo",
        indices=["test_index"]
    )
    
    with patch('elasticsearch.AsyncElasticsearch') as mock_es:
        mock_client = AsyncMock()
        mock_es.return_value = mock_client
        mock_client.snapshot.create.return_value = {"accepted": True}
        
        snapshot_handler = ElasticsearchSnapshot(config)
        
        # Act
        result = await snapshot_handler.snapshot()
        
        # Assert
        assert result.startswith("snapshot_")
        mock_client.snapshot.create.assert_called_once()
```

## 📚 Documentation

### Documentation Structure

```
docs/
├── api.md              # API reference
├── configuration.md    # Configuration guide
├── deployment.md       # Deployment guide
├── troubleshooting.md  # Troubleshooting
└── examples/           # Code examples
```

### Writing Documentation

1. **Start with the user's goal**
2. **Provide step-by-step instructions**
3. **Include code examples**
4. **Explain configuration options**
5. **Add troubleshooting sections**

## 🚀 Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Changelog is updated
- [ ] Version is bumped
- [ ] Release notes are written
- [ ] Docker images are built
- [ ] GitHub release is created

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment details**
   - OS and version
   - Python version
   - Package versions

2. **Reproduction steps**
   - Clear, step-by-step instructions
   - Minimal example code

3. **Expected vs actual behavior**
   - What you expected to happen
   - What actually happened

4. **Error messages and logs**
   - Full error traceback
   - Relevant log output

## 💡 Feature Requests

When requesting features:

1. **Describe the problem** you're trying to solve
2. **Explain your use case** in detail
3. **Propose a solution** if possible
4. **Consider alternatives** you've tried
5. **Provide examples** of similar features

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: sloudy@gmail.com for private matters

## 🙏 Recognition

Contributors will be recognized in:

- **README.md** contributors section
- **GitHub contributors** page
- **Release notes** for significant contributions

Thank you for contributing to PlanLX Backup Kit! 🎉