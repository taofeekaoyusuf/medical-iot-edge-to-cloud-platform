.PHONY: setup lint format test test-unit broker-up broker-down experiment build

setup:
	uv sync --locked

lint:
	uv run --locked ruff check src experiments tests
	uv run --locked ruff format --check src experiments tests

format:
	uv run --locked ruff format src experiments tests

test-unit:
	uv run --locked pytest -m "not mqtt" -q

# Full suite deliberately fails if the local broker has not been started.
test:
	uv run --locked pytest -q

broker-up:
	docker compose -f tests/compose.yaml up -d --wait

broker-down:
	docker compose -f tests/compose.yaml down

experiment:
	uv run --locked python -m experiments.mqtt_clients --clients 100

build:
	uv build
