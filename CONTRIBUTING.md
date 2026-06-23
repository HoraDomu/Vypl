# Contributing to Vypl

## Setup

```bash
git clone https://github.com/HoraDomu/Vypl
cd Vypl
pip install -e ".[watch,clipboard,jedi]"
pip install pytest pytest-cov ruff
```

## Running tests

```bash
pytest tests/
```

With coverage:

```bash
pytest tests/ --cov=vypl --cov-report=term-missing
```

## Linting

```bash
ruff check .
ruff check --fix .   # auto-fix where possible
```

## Pre-commit (optional)

Install [pre-commit](https://pre-commit.com) then:

```bash
pre-commit install
```

This runs ruff on every commit automatically.

## Submitting a pull request

1. Fork the repo and create a branch from `main`.
2. Make your change. Add or update tests if the change affects behaviour.
3. Run `pytest tests/` and `ruff check .` — both must pass.
4. Open a PR against `main`. Fill in the template.

## What to work on

Open issues are tracked on [GitHub](https://github.com/HoraDomu/Vypl/issues).
Good starting points are labelled `good first issue`.
