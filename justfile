install:
    uv sync

test:
    uv run pytest

lint:
    uv run ruff check .

format:
    uv run ruff format .

digital-data-etl:
    uv run python -m tools.run

digital-data-etl-no-cache:
    uv run python -m tools.run --no-cache
