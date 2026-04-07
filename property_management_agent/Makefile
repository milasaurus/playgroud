# ── Setup ────────────────────────────────────────────────────────────────────

setup:
	uv sync

# ── Run ──────────────────────────────────────────────────────────────────────

run:
	uv run python main.py

run-seeded: seed
	uv run python main.py

seed:
	uv run python seed_data.py

api-query:
	uv run python api.py --query "$(QUERY)"

api-email:
	uv run python api.py --email "$(SENDER)" "$(SUBJECT)" "$(BODY)"

# ── Test ─────────────────────────────────────────────────────────────────────

test:
	uv run python -m pytest tests/tool_tests/ tests/test_agent.py -v

test-e2e:
	uv run python -m pytest tests/e2e.py -v

test-all:
	uv run python -m pytest tests/ -v
