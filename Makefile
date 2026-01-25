.PHONY: help install test docs clean build publish

help:
	@echo "R5 Framework - Makefile"
	@echo "======================"
	@echo ""
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make dev         - Install dev dependencies"
	@echo "  make docs-deps   - Install documentation dependencies"
	@echo "  make test        - Run tests"
	@echo "  make test-cov    - Run tests with coverage"
	@echo "  make docs        - Build documentation"
	@echo "  make docs-serve  - Serve documentation locally"
	@echo "  make lint        - Run linters"
	@echo "  make format      - Format code"
	@echo "  make clean       - Clean build artifacts"
	@echo "  make build       - Build package"
	@echo "  make examples    - Run example scripts"
	@echo ""

install:
	@echo "Installing dependencies..."
	uv sync

dev:
	@echo "Installing dev dependencies..."
	uv sync --group dev

docs-deps:
	@echo "Installing documentation dependencies..."
	uv sync --group docs

test:
	@echo "Running tests..."
	uv run pytest

test-cov:
	@echo "Running tests with coverage..."
	uv run pytest --cov=R5 --cov-report=html --cov-report=term

test-watch:
	@echo "Running tests in watch mode..."
	uv run pytest-watch

docs:
	@echo "Building documentation..."
	uv run mkdocs build

docs-serve:
	@echo "Serving documentation at http://127.0.0.1:8000"
	uv run mkdocs serve

docs-deploy:
	@echo "Deploying documentation to GitHub Pages..."
	uv run mkdocs gh-deploy

lint:
	@echo "Running linters..."
	uv run ruff check R5/
	uv run mypy R5/

format:
	@echo "Formatting code..."
	uv run ruff format R5/
	uv run ruff check --fix R5/

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf site/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	@echo "Building package..."
	uv build

publish: build
	@echo "Publishing to PyPI..."
	uv publish

examples:
	@echo "Running examples..."
	@echo "\n=== IoC Example ==="
	uv run python examples.py
	@echo "\n=== HTTP Example ==="
	uv run python example_http.py
	@echo "\n=== Background Example ==="
	uv run python example_background.py

check: lint test
	@echo "All checks passed!"

all: install dev docs-deps test docs
	@echo "Setup complete!"
