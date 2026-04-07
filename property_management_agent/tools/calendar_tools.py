"""Calendar tools — create, update, delete, list, and search events."""

import json
from dataclasses import asdict
from datetime import datetime

from tools.base import Tool
from backend.calendar_manager import CalendarManager


# Used when a customer requests a viewing or the owner schedules a meeting.
# Guests is optional — the model includes the customer's email when
# scheduling on their behalf, which the e2e tests assert against.
class CreateEventTool(Tool):
    def __init__(self, calendar: CalendarManager):
        self.calendar = calendar
        super().__init__(
            name="create_event",
            description="Create a new calendar event.",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Event name/title"},
                    "start_timestamp": {"type": "string", "description": "ISO datetime for event start"},
                    "end_timestamp": {"type": "string", "description": "ISO datetime for event end"},
                    "guests": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of guest email addresses",
                    },
                },
                "required": ["name", "start_timestamp", "end_timestamp"],
            },
        )

    def run(self, params: dict) -> str:
        event = self.calendar.create_event(
            name=params["name"],
            start_timestamp=datetime.fromisoformat(params["start_timestamp"]),
            end_timestamp=datetime.fromisoformat(params["end_timestamp"]),
            guests=params.get("guests"),
        )
        return json.dumps(asdict(event))


# Partial update — only fields the model provides are changed. This lets
# the model reschedule an event (change start/end) without needing to
# re-specify the name or guest list. The model first needs the event_id,
# typically obtained from list_all_events or list_events_in_range.
class UpdateEventTool(Tool):
    def __init__(self, calendar: CalendarManager):
        self.calendar = calendar
        super().__init__(
            name="update_event",
            description="Update an existing calendar event. Only provided fields are changed.",
            input_schema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "Unique event identifier"},
                    "name": {"type": "string", "description": "New event name"},
                    "start_timestamp": {"type": "string", "description": "New ISO datetime for start"},
                    "end_timestamp": {"type": "string", "description": "New ISO datetime for end"},
                    "guests": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New guest list",
                    },
                },
                "required": ["event_id"],
            },
        )

    def run(self, params: dict) -> str:
        event = self.calendar.update_event(
            event_id=params["event_id"],
            name=params.get("name"),
            start_timestamp=datetime.fromisoformat(params["start_timestamp"]) if params.get("start_timestamp") else None,
            end_timestamp=datetime.fromisoformat(params["end_timestamp"]) if params.get("end_timestamp") else None,
            guests=params.get("guests"),
        )
        return json.dumps(asdict(event))


# Permanent deletion. Used when a customer cancels a showing — the e2e
# tests verify the event is fully removed from calendar.list_all_events().
# The model typically finds the event_id by searching by guest email or
# listing events in a date range first.
class DeleteEventTool(Tool):
    def __init__(self, calendar: CalendarManager):
        self.calendar = calendar
        super().__init__(
            name="delete_event",
            description="Delete a calendar event by its ID.",
            input_schema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "Unique event identifier"},
                },
                "required": ["event_id"],
            },
        )

    def run(self, params: dict) -> str:
        return json.dumps({"deleted": self.calendar.delete_event(params["event_id"])})


# Primary tool for schedule queries like "what's my schedule for tomorrow?"
# The model computes the start/end of the day and passes ISO strings.
# Returns all events that overlap with the range, not just those that
# start within it — matches CalendarManager.list_events_in_range behavior.
class ListEventsInRangeTool(Tool):
    def __init__(self, calendar: CalendarManager):
        self.calendar = calendar
        super().__init__(
            name="list_events_in_range",
            description="List all calendar events within a time range.",
            input_schema={
                "type": "object",
                "properties": {
                    "start_time": {"type": "string", "description": "ISO datetime for range start"},
                    "end_time": {"type": "string", "description": "ISO datetime for range end"},
                },
                "required": ["start_time", "end_time"],
            },
        )

    def run(self, params: dict) -> str:
        events = self.calendar.list_events_in_range(
            start_time=datetime.fromisoformat(params["start_time"]),
            end_time=datetime.fromisoformat(params["end_time"]),
        )
        return json.dumps([asdict(e) for e in events])


# Case-insensitive substring match on event names. Useful when the user
# references an event by name rather than by time (e.g. "the Oak Street
# showing"). Falls back to the DB's LIKE operator.
class SearchEventsByNameTool(Tool):
    def __init__(self, calendar: CalendarManager):
        self.calendar = calendar
        super().__init__(
            name="search_events_by_name",
            description="Search calendar events by name.",
            input_schema={
                "type": "object",
                "properties": {
                    "search_term": {"type": "string", "description": "Text to search for in event names"},
                },
                "required": ["search_term"],
            },
        )

    def run(self, params: dict) -> str:
        return json.dumps([asdict(e) for e in self.calendar.search_by_name(params["search_term"])])


# Returns every event on the calendar. Same caveat as ListAllMessagesTool —
# fine for the project's small dataset, but would need pagination at scale.
class ListAllEventsTool(Tool):
    def __init__(self, calendar: CalendarManager):
        self.calendar = calendar
        super().__init__(
            name="list_all_events",
            description="List all calendar events ordered by start time.",
            input_schema={"type": "object", "properties": {}, "required": []},
        )

    def run(self, params: dict) -> str:
        return json.dumps([asdict(e) for e in self.calendar.list_all_events()])


# Finds events where a specific email appears in the guest list. Critical
# for the "cancel my showing" flow — the model uses the sender's email to
# find their upcoming event, then deletes it.
class SearchEventsByGuestTool(Tool):
    def __init__(self, calendar: CalendarManager):
        self.calendar = calendar
        super().__init__(
            name="search_events_by_guest",
            description="Search calendar events that include a specific guest email.",
            input_schema={
                "type": "object",
                "properties": {
                    "guest_email": {"type": "string", "description": "Guest email address to search for"},
                },
                "required": ["guest_email"],
            },
        )

    def run(self, params: dict) -> str:
        return json.dumps([asdict(e) for e in self.calendar.search_by_guest(params["guest_email"])])
