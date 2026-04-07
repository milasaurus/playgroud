"""
Main API module for the property management system.
Provides email processing and query handling functionality.
"""

import argparse
import logging

import anthropic

from agent import Agent
from backend.inbox_manager import InboxManager
from backend.calendar_manager import CalendarManager
from backend.listings_manager import ListingsManager
from tools import build_all_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default DB paths — override these before calling process_email/process_query
# to point at different databases (e.g. test databases).
INBOX_DB = "inbox.db"
LISTINGS_DB = "listings.db"
CALENDAR_DB = "calendar.db"


def _make_agent() -> Agent:
    """Create a fresh Agent with managers pointing at the configured DB paths."""
    client = anthropic.Anthropic()
    inbox = InboxManager(INBOX_DB)
    calendar = CalendarManager(CALENDAR_DB)
    listings = ListingsManager(LISTINGS_DB)
    tools = build_all_tools(inbox, calendar, listings)
    return Agent(client, tools)


def process_email(subject: str, body: str, sender: str) -> str:
    """
    Process incoming emails to handle property-related requests.
    If response to this email cannot be given with the tools available,
    return <NEEDS MANUAL RESPONSE>.

    Args:
        subject: Email subject line
        body: Email body content
        sender: Email address of the sender

    Returns:
        Response message
    """
    agent = _make_agent()

    # Format the email as a user message. The system prompt instructs the
    # agent to call receive_email first to record it, then handle the request.
    message = (
        f"New email from {sender}:\n"
        f"Subject: {subject}\n"
        f"Body: {body}"
    )

    try:
        return agent.run(message)
    except Exception as e:
        logger.error(f"Agent error processing email: {e}")
        return "<NEEDS MANUAL RESPONSE>"


def process_query(query: str) -> str:
    """
    Process natural language queries about inbox, listings and calendar.
    If response to this question cannot be given with the tools available,
    return <NEEDS MANUAL RESPONSE>.

    Args:
        query: Natural language query string

    Returns:
        Response to the query
    """
    agent = _make_agent()

    try:
        return agent.run(query)
    except Exception as e:
        logger.error(f"Agent error processing query: {e}")
        return "<NEEDS MANUAL RESPONSE>"


def main():
    """CLI interface for testing API methods."""
    parser = argparse.ArgumentParser(
        description="Property Management System API"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--query",
        type=str,
        help="Process a natural language query"
    )
    group.add_argument(
        "--email",
        nargs=3,
        metavar=("SENDER", "SUBJECT", "BODY"),
        help="Process an email (requires sender, subject, and body)"
    )

    args = parser.parse_args()

    if args.query:
        logger.info(f"Processing query: {args.query}")
        result = process_query(args.query)
        print(f"Result: {result}")
    elif args.email:
        sender, subject, body = args.email
        logger.info(f"Processing email from: {sender}")
        result = process_email(subject, body, sender)
        print(f"Result: {result}")


if __name__ == "__main__":
    main()
