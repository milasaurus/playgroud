"""Tests for calendar tools — verifies each tool calls the right manager method
and returns well-formed JSON."""

import json
import os
from datetime import datetime, timedelta

import pytest

from backend.calendar_manager import CalendarManager
from tools.calendar_tools import (
    CreateEventTool, UpdateEventTool, DeleteEventTool,
    ListEventsInRangeTool, SearchEventsByNameTool,
    ListAllEventsTool, SearchEventsByGuestTool,
)

DB_PATH = "test_tool_calendar.db"


@pytest.fixture
def calendar():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    mgr = CalendarManager(DB_PATH)
    yield mgr
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


def _tomorrow(hour=10):
    t = datetime.now() + timedelta(days=1)
    return t.replace(hour=hour, minute=0, second=0, microsecond=0)


class TestCreateEventTool:
    def test_creates_event_with_guests(self, calendar):
        tool = CreateEventTool(calendar)
        result = json.loads(tool.run({
            "name": "Showing at 123 Oak",
            "start_timestamp": _tomorrow(14).isoformat(),
            "end_timestamp": _tomorrow(15).isoformat(),
            "guests": ["tenant@example.com"],
        }))

        assert result["name"] == "Showing at 123 Oak"
        assert "tenant@example.com" in result["guests"]

    def test_creates_event_without_guests(self, calendar):
        tool = CreateEventTool(calendar)
        result = json.loads(tool.run({
            "name": "Internal sync",
            "start_timestamp": _tomorrow(9).isoformat(),
            "end_timestamp": _tomorrow(10).isoformat(),
        }))

        assert result["guests"] == []

    def test_event_persists_in_db(self, calendar):
        tool = CreateEventTool(calendar)
        tool.run({
            "name": "Persisted event",
            "start_timestamp": _tomorrow(10).isoformat(),
            "end_timestamp": _tomorrow(11).isoformat(),
        })

        assert len(calendar.list_all_events()) == 1

    def test_api_dict_shape(self, calendar):
        tool = CreateEventTool(calendar)
        api = tool.to_api_dict()
        assert api["name"] == "create_event"
        assert "start_timestamp" in api["input_schema"]["properties"]


class TestUpdateEventTool:
    def test_updates_event_name(self, calendar):
        event = calendar.create_event(
            name="Old name",
            start_timestamp=_tomorrow(10),
            end_timestamp=_tomorrow(11),
        )

        tool = UpdateEventTool(calendar)
        result = json.loads(tool.run({
            "event_id": event.event_id,
            "name": "New name",
        }))

        assert result["name"] == "New name"

    def test_updates_start_time(self, calendar):
        event = calendar.create_event(
            name="Meeting",
            start_timestamp=_tomorrow(16),
            end_timestamp=_tomorrow(17),
        )

        new_start = _tomorrow(17)
        new_end = _tomorrow(18)
        tool = UpdateEventTool(calendar)
        result = json.loads(tool.run({
            "event_id": event.event_id,
            "start_timestamp": new_start.isoformat(),
            "end_timestamp": new_end.isoformat(),
        }))

        assert datetime.fromisoformat(result["start_timestamp"]).hour == 17


class TestDeleteEventTool:
    def test_deletes_existing_event(self, calendar):
        event = calendar.create_event(
            name="Delete me",
            start_timestamp=_tomorrow(10),
            end_timestamp=_tomorrow(11),
        )

        tool = DeleteEventTool(calendar)
        result = json.loads(tool.run({"event_id": event.event_id}))

        assert result["deleted"] is True
        assert len(calendar.list_all_events()) == 0

    def test_delete_nonexistent_returns_false(self, calendar):
        tool = DeleteEventTool(calendar)
        result = json.loads(tool.run({"event_id": "fake-id"}))

        assert result["deleted"] is False


class TestListEventsInRangeTool:
    def test_finds_events_in_range(self, calendar):
        calendar.create_event("Morning", start_timestamp=_tomorrow(9), end_timestamp=_tomorrow(10))
        calendar.create_event("Afternoon", start_timestamp=_tomorrow(14), end_timestamp=_tomorrow(15))

        tool = ListEventsInRangeTool(calendar)
        result = json.loads(tool.run({
            "start_time": _tomorrow(8).isoformat(),
            "end_time": _tomorrow(11).isoformat(),
        }))

        assert len(result) == 1
        assert result[0]["name"] == "Morning"

    def test_returns_empty_for_no_matches(self, calendar):
        calendar.create_event("Late", start_timestamp=_tomorrow(20), end_timestamp=_tomorrow(21))

        tool = ListEventsInRangeTool(calendar)
        result = json.loads(tool.run({
            "start_time": _tomorrow(8).isoformat(),
            "end_time": _tomorrow(12).isoformat(),
        }))

        assert result == []


class TestSearchEventsByNameTool:
    def test_finds_by_partial_name(self, calendar):
        calendar.create_event("Showing at Oak St", start_timestamp=_tomorrow(10), end_timestamp=_tomorrow(11))
        calendar.create_event("Team standup", start_timestamp=_tomorrow(9), end_timestamp=_tomorrow(10))

        tool = SearchEventsByNameTool(calendar)
        result = json.loads(tool.run({"search_term": "Oak"}))

        assert len(result) == 1
        assert "Oak" in result[0]["name"]

    def test_returns_empty_for_no_match(self, calendar):
        calendar.create_event("Standup", start_timestamp=_tomorrow(9), end_timestamp=_tomorrow(10))

        tool = SearchEventsByNameTool(calendar)
        result = json.loads(tool.run({"search_term": "nonexistent"}))

        assert result == []


class TestListAllEventsTool:
    def test_returns_empty_when_no_events(self, calendar):
        tool = ListAllEventsTool(calendar)
        result = json.loads(tool.run({}))

        assert result == []

    def test_returns_all_events(self, calendar):
        calendar.create_event("A", start_timestamp=_tomorrow(10), end_timestamp=_tomorrow(11))
        calendar.create_event("B", start_timestamp=_tomorrow(12), end_timestamp=_tomorrow(13))

        tool = ListAllEventsTool(calendar)
        result = json.loads(tool.run({}))

        assert len(result) == 2


class TestSearchEventsByGuestTool:
    def test_finds_events_with_guest(self, calendar):
        calendar.create_event(
            "Showing", start_timestamp=_tomorrow(10), end_timestamp=_tomorrow(11),
            guests=["john@example.com"],
        )
        calendar.create_event(
            "Other", start_timestamp=_tomorrow(12), end_timestamp=_tomorrow(13),
            guests=["jane@example.com"],
        )

        tool = SearchEventsByGuestTool(calendar)
        result = json.loads(tool.run({"guest_email": "john@example.com"}))

        assert len(result) == 1
        assert result[0]["name"] == "Showing"

    def test_returns_empty_for_unknown_guest(self, calendar):
        calendar.create_event(
            "Event", start_timestamp=_tomorrow(10), end_timestamp=_tomorrow(11),
            guests=["known@example.com"],
        )

        tool = SearchEventsByGuestTool(calendar)
        result = json.loads(tool.run({"guest_email": "unknown@example.com"}))

        assert result == []
