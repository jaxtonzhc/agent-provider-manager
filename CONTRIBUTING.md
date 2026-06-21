# Contributing to apm

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/jaxtonzhc/apm.git
cd apm

# Install in development mode
pip install -e ".[dev]"

# Run tests
make test

# Run linter
make lint
```

## Project Structure

```
src/apm/
├── __init__.py          # Version
├── __main__.py          # python -m apm entry
├── cli.py               # CLI argument parsing and dispatch
├── config.py            # Path constants
├── detect.py            # Agent detection
├── providers.py         # Provider CRUD
├── sync.py              # Sync engine
└── agents/
    ├── base.py          # Abstract adapter + helpers
    ├── claude_code.py   # Claude Code adapter
    ├── codex.py         # Codex adapter
    ├── hermes.py        # Hermes adapter
    ├── openclaw.py      # OpenClaw adapter
    ├── zcode.py         # ZCode adapter
    ├── workbuddy.py     # WorkBuddy adapter
    └── registry.py      # Adapter registry
```

## Adding a New Agent

1. Create `src/apm/agents/your_agent.py`
2. Implement `AgentAdapter` from `base.py`
3. Register it in `registry.py`
4. Add detection path in `config.py`
5. Add tests in `tests/agents/test_your_agent.py`

## Code Style

- Python 3.10+ with type hints
- `ruff` for linting and formatting
- Keep it simple — zero external dependencies preferred

## Commit Messages

Use conventional commits:

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `test:` tests
- `refactor:` code refactoring
- `chore:` maintenance

## Pull Requests

1. Fork the repo
2. Create a feature branch
3. Add tests for new functionality
4. Ensure `make check` passes
5. Submit a PR with a clear description
