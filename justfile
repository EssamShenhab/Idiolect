install:
    uv sync

test:
    uv run pytest

lint:
    uv run ruff check .

format:
    uv run ruff format .

zenml-demo:
    uv run python -m tools.run --run-zenml-demo --config-filename zenml_demo.yaml

zenml-demo-no-cache:
    uv run python -m tools.run --run-zenml-demo --config-filename zenml_demo.yaml --no-cache
