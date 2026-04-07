# Property Management Agent

An agentic tool-calling system that helps a real estate solopreneur manage their inbox, calendar, and property listings using Claude.

## Architecture

```
agent.py            — Agent class: tool-use loop with streaming + extended thinking
api.py              — Public API: process_email() and process_query() (WIP)
main.py             — Interactive CLI entry point
seed_data.py        — Populates databases with sample data for testing

tools/
  base.py           — Tool ABC (name, description, input_schema, run)
  inbox_tools.py    — Send, receive, search, delete, list emails
  calendar_tools.py — Create, update, delete, list, search events
  listings_tools.py — Create, update, delete, search, list listings

backend/
  inbox_manager.py     — SQLite CRUD for email messages
  calendar_manager.py  — SQLite CRUD for calendar events
  listings_manager.py  — SQLite CRUD for property listings

tests/
  test_agent.py              — Agent loop tests (mocked client)
  tool_tests/
    test_inbox_tools.py      — Inbox tool tests
    test_calendar_tools.py   — Calendar tool tests
    test_listings_tools.py   — Listings tool tests
  e2e.py                     — End-to-end tests (requires API key)
```

## Quick start

    make setup                 # Install dependencies via uv
    export ANTHROPIC_API_KEY=sk-ant-...
    make run-seeded            # Seed sample data + start interactive CLI

Or without sample data:

    make run                   # Start with empty/existing databases

## Commands

    make setup                 # Install dependencies
    make run                   # Start interactive CLI
    make run-seeded            # Seed databases + start interactive CLI
    make seed                  # Seed databases only
    make api-query QUERY="..." # Run a one-shot query via api.py
    make api-email SENDER="..." SUBJECT="..." BODY="..."
    make test                  # Run tool unit tests
    make test-e2e              # Run end-to-end tests
    make test-all              # Run all tests

## How it works

1. User sends a message (via CLI or `api.py`)
2. The Agent sends the message + tool definitions to Claude with extended thinking enabled
3. If Claude responds with `tool_use` blocks, the Agent executes each tool and feeds results back
4. Repeats until Claude responds with text only, or hits safety limits
5. Returns the final text response

Safety limits:
- **Depth:** 4 iterations (LLM call -> tool use cycles)
- **Tool calls:** 8 total per request

## Tech stack

- Python 3.14+, managed with uv
- Anthropic Python SDK (Claude Haiku 4.5 with extended thinking)
- SQLite for data storage
- pytest for testing
