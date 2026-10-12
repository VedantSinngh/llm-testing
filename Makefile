.PHONY: install lint format type test run-api run-ui docker-up clean help

help:
	@echo "Available commands:"
	@echo "  make install    Install production and development dependencies"
	@echo "  make lint       Run Ruff linter"
	@echo "  make format     Format codebase with Ruff"
	@echo "  make type       Run mypy type checker in strict mode"
	@echo "  make test       Run pytest test suite with coverage report"
	@echo "  make run-api    Start FastAPI backend server on port 8000"
	@echo "  make run-ui     Start Streamlit dashboard"
	@echo "  make docker-up  Build and start docker containers"
	@echo "  make clean      Remove build, cache, and temporary files"

install:
	pip install -e ".[dev]"

lint:
	ruff check src tests

format:
	ruff format src tests

type:
	mypy src tests

test:
	pytest

run-api:
	uvicorn promptlab.api.main:app --reload --host 0.0.0.0 --port 8000

run-ui:
	streamlit run src/promptlab/dashboard/app.py --server.port 8501

docker-up:
	docker compose up --build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf dist build *.egg-info .coverage
