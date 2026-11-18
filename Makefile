.PHONY: install lint format check test

install:
	python -m pip install -r requirements.txt black ruff

lint:
	python -m ruff check .
	python -m black --check .

format:
	python -m black .
	python -m ruff check --fix .

test:
	python -m pytest

check: lint test
