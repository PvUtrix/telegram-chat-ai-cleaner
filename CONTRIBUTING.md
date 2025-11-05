# Contributing

Thanks for your interest in contributing!

## Development Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Style & Tooling

- Format: `black` and `isort`
- Lint: `ruff`
- Types: `mypy`
- Tests: `pytest`

We provide a pre-commit config to run these automatically.

## Running Tests

```bash
pytest -q
```

## Pull Requests

- Create a feature branch
- Include tests for new behavior
- Update docs as needed
- Ensure CI passes

## Security & Privacy

- Do not include real chat data in PRs. Use synthetic/redacted examples.
- Never add `.env` files or anything under `data/`.
