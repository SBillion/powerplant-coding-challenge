# powerplant-coding-challenge

[![CI](https://github.com/SBillion/powerplant-coding-challenge/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/SBillion/powerplant-coding-challenge/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/SBillion/powerplant-coding-challenge/branch/master/graph/badge.svg)](https://codecov.io/gh/SBillion/powerplant-coding-challenge)
![Python](https://img.shields.io/badge/python-3.14%2B-blue)
![Lint](https://img.shields.io/badge/code%20style-ruff-46a2f1)
![Types](https://img.shields.io/badge/type%20checked-mypy-2f72b6)

## How to Build and Run

### Prerequisites
- Python 3.14 or higher
- [uv](https://docs.astral.sh/uv/) (fast Python package installer)

### Installation

1. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install the required dependencies:
Sync from pyproject.toml:
```bash
uv sync
```

### Running the API

Launch the API server on port 8888:
```bash
uv run python main.py
```

The API will be available at `http://localhost:8888`

### Documentation

The documentation is available in
- Swagger at `http://localhost:8888/docs`
- ReDoc at `http://localhost:8888/redoc`

### Lint and type-check
[Ruff](https://docs.astral.sh/ruff/) if used for formatting
[Mypy](https://mypy.readthedocs.io/en/stable/config_file.html) is used for type checking
```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app main.py
```

### Run tests and coverage
```bash
uv run pytest
open htmlcov/index.html  # view HTML coverage report
```

### Pre-commit hooks
[pre-commit](`https://pre-commit.com/`) is used to add git hook scripts. For every new hook that you add in `.pre-commit-config.yml`, please launch the following commands
```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files --show-diff-on-failure
```

### CI
GitHub Actions runs tests, ruff, mypy, and uploads HTML coverage on each push/PR.
