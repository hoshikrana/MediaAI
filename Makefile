.PHONY: lint format test test-all clean verify run-dev

lint:
	ruff check backend/
	black --check backend/
	mypy backend/core/

format:
	ruff check --fix backend/
	black backend/

test:
	pytest -m "unit" --tb=short

test-all:
	pytest --tb=short

clean:
	del /s /q __pycache__ .pytest_cache .ruff_cache

verify:
	python verify_env.py

run-dev:
	uvicorn backend.main:app --reload --port 8000
