# ── Setup ────────────────────────────────────────────────────────────────────

setup:
	uv sync

# ── Run ──────────────────────────────────────────────────────────────────────

run: seed
	uv run python main.py

seed:
	uv run python seed_data.py

# ── Test ─────────────────────────────────────────────────────────────────────

test:
	uv run python -m pytest tests/ -v

test-e2e:
	uv run python -m pytest tests/e2e.py -v
