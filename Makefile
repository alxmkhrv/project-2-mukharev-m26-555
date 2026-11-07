.PHONY: install run build lint

install:
	uv sync

run:
	uv run database

build:
	uv build

lint:
	uv run ruff check .
	uv run ruff format --check .