# powerplant coding challenge

[![CI](https://github.com/SBillion/powerplant-coding-challenge/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/SBillion/powerplant-coding-challenge/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/SBillion/powerplant-coding-challenge/branch/master/graph/badge.svg)](https://codecov.io/gh/SBillion/powerplant-coding-challenge)
![Python](https://img.shields.io/badge/python-3.14%2B-blue)
![Lint](https://img.shields.io/badge/code%20style-ruff-46a2f1)
![Types](https://img.shields.io/badge/type%20checked-mypy-2f72b6)

Welcome to te powerplant coding challenge. To get more information about the challenge please read the [CHALLENGE.md](./CHALLENGE.md) file

## About the algorith to calculate the powerplants plan

Calculate optimal production plan using merit-order algorithm.

Steps:

    1. Calculate cost per MWh for each powerplant
    2. Adjust wind turbine capacity based on wind percentage
    3. Sort powerplants by cost (cheapest first)
    4. Allocate power to meet load, respecting min/max constraints
    5. Return power output for each plant

## How to Build and Run

### Prerequisites
- **Option 1**: Python 3.14 or higher + [uv](https://docs.astral.sh/uv/)
- **Option 2**: Docker + Docker Compose

### Option 1: Local Installation with uv

1. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install the required dependencies:
```bash
uv sync
```

3. Launch the API server on port 8888:
```bash
uv run python main.py
```

### Option 2: Docker

#### Production mode
```bash
# Using Docker
docker build --target production -t powerplant-api:prod .
docker run -p 8888:8888 powerplant-api:prod

# Or using Docker Compose
docker-compose up powerplant-api
```

#### Development mode (with hot-reload)
```bash
# Using Docker with volume mounts
docker build --target development -t powerplant-api:dev .
docker run -p 8888:8888 \
  -v $(pwd)/app:/app/app \
  -v $(pwd)/main.py:/app/main.py \
  powerplant-api:dev

# Or using Docker Compose (recommended)
docker-compose up powerplant-api-dev
```

### API Access

The API will be available at `http://localhost:8888`

### Documentation

The interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8888/docs` - Interactive API testing interface
- **ReDoc**: `http://localhost:8888/redoc` - Alternative documentation view

### Using the API

1. Open `http://localhost:8888/docs` in your browser
2. Click on the `POST /productionplan` endpoint
3. Click "Try it out"
4. Use the example payload or modify it
5. Click "Execute" to see the response


### Lint and type-check
[Ruff](https://docs.astral.sh/ruff/) if used for formatting

[Mypy](https://mypy.readthedocs.io/en/stable/config_file.html) is used for type checking
```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app main.py
```

With docker-compose
```bash
docker-compose run powerplant-api-dev uv run ruff check .
docker-compose run powerplant-api-dev uv run ruff format --check .
docker-compose run powerplant-api-dev uv run mypy app main.py

```

### Run tests and coverage
```bash
uv run pytest
```

With docker-compose 
```bash
docker-compose run powerplant-api-dev uv run pytest
```

Then you can this the report
```bash
open htmlcov/index.html  # view HTML coverage report
```

### Pre-commit hooks
[pre-commit](`https://pre-commit.com/`) is used to add git hook scripts. For every new hook that you add in `.pre-commit-config.yml`, please launch the following commands
```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files --show-diff-on-failure
```

With docker-compose 
```bash
docker-compose run powerplant-api-dev uv run pre-commit install --hook-type pre-commit --hook-type pre-push
docker-compose run powerplant-api-dev uv run pre-commit run --all-files --show-diff-on-failure
```

### CI
GitHub Actions runs tests, ruff, mypy, and uploads HTML coverage on each push/PR.
