.PHONY: install playground run test

install:
	uv sync --link-mode=copy

playground:
	uv run adk web app --host 127.0.0.1 --port 18081 --reload_agents

run:
	uv run uvicorn app.agent_runtime_app:app --host 127.0.0.1 --port 8080

test:
	uv run pytest
