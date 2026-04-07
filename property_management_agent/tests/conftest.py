"""Test configuration — patches api.py to use test database paths.

The e2e tests create managers with test_*.db paths and then call
process_email/process_query. For the agent inside api.py to read/write
the same databases, we override api's module-level DB path variables
before any tests run.
"""

import api


def pytest_configure(config):
    api.INBOX_DB = "test_inbox.db"
    api.LISTINGS_DB = "test_listings.db"
    api.CALENDAR_DB = "test_calendar.db"
