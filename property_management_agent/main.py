"""Interactive CLI entry point for the property management agent."""

import anthropic

from backend.inbox_manager import InboxManager
from backend.calendar_manager import CalendarManager
from backend.listings_manager import ListingsManager
from tools import build_all_tools
from agent import Agent


def main():
    client = anthropic.Anthropic()
    inbox = InboxManager()
    calendar = CalendarManager()
    listings = ListingsManager()
    tools = build_all_tools(inbox, calendar, listings)
    agent = Agent(client, tools)

    print("Property Management Agent (ctrl-c to quit)\n")
    while True:
        try:
            user_input = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input.strip():
            continue

        try:
            response = agent.run(user_input)
            print(f"Agent: {response}\n")
        except anthropic.APITimeoutError:
            print("Agent: Request timed out. Please try again.\n")
        except anthropic.APIError as e:
            print(f"Agent: API error — {e.message}\n")


if __name__ == "__main__":
    main()
