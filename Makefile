.PHONY: check lint type test install clean

check: lint type test

lint:
	ruff check .

type:
	mypy src

test:
	pytest

install:
	pip install -e ".[dev]"

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist build
	find . -type d -name "__pycache__" -exec rm -rf {} +
