"""Tools package for the property management agent.

Each category of tools lives in its own module. All tool classes inherit from
the base Tool ABC defined in tools.base.

Adding a new tool:
    1. Subclass Tool in the appropriate category module (or create a new one).
    2. Implement run(params: dict) -> str.
    3. Register it in build_all_tools() below.
"""

from tools.base import Tool
from tools.inbox_tools import (
    SendEmailTool, ReceiveEmailTool, SearchMessagesTool,
    DeleteEmailTool, ListAllMessagesTool,
)
from tools.calendar_tools import (
    CreateEventTool, UpdateEventTool, DeleteEventTool,
    ListEventsInRangeTool, SearchEventsByNameTool,
    ListAllEventsTool, SearchEventsByGuestTool,
)
from tools.listings_tools import (
    CreateListingTool, UpdateListingTool, DeleteListingTool,
    SearchListingsByDescriptionTool, SearchListingsByRentRangeTool,
    ListAllListingsTool,
)

from backend.inbox_manager import InboxManager
from backend.calendar_manager import CalendarManager
from backend.listings_manager import ListingsManager


def build_all_tools(
    inbox: InboxManager,
    calendar: CalendarManager,
    listings: ListingsManager,
) -> list[Tool]:
    """Instantiate all tools with the given manager instances.

    Managers are injected so callers can pass different DB paths
    (e.g. test databases vs production).
    """
    return [
        # Inbox
        SendEmailTool(inbox),
        ReceiveEmailTool(inbox),
        SearchMessagesTool(inbox),
        DeleteEmailTool(inbox),
        ListAllMessagesTool(inbox),
        # Calendar
        CreateEventTool(calendar),
        UpdateEventTool(calendar),
        DeleteEventTool(calendar),
        ListEventsInRangeTool(calendar),
        SearchEventsByNameTool(calendar),
        ListAllEventsTool(calendar),
        SearchEventsByGuestTool(calendar),
        # Listings
        CreateListingTool(listings),
        UpdateListingTool(listings),
        DeleteListingTool(listings),
        SearchListingsByDescriptionTool(listings),
        SearchListingsByRentRangeTool(listings),
        ListAllListingsTool(listings),
    ]
