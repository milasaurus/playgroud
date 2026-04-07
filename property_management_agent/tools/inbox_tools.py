"""Inbox tools — send, receive, search, delete, and list email messages."""

import json
from dataclasses import asdict
from datetime import datetime

from tools.base import Tool
from backend.inbox_manager import InboxManager


# Used by process_email to record the agent's reply back to the customer.
# The e2e tests assert that a sent email appears in the inbox after the
# agent handles a request, so this must create a real DB record.
class SendEmailTool(Tool):
    def __init__(self, inbox: InboxManager):
        self.inbox = inbox
        super().__init__(
            name="send_email",
            description="Send an email to a recipient.",
            input_schema={
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body content"},
                },
                "required": ["recipient", "subject", "body"],
            },
        )

    def run(self, params: dict) -> str:
        msg = self.inbox.send_email(params["recipient"], params["subject"], params["body"])
        return json.dumps(asdict(msg))


# Records an incoming customer email into the inbox. The agent should call
# this as the first step when handling process_email, so the e2e tests can
# verify the email was logged (they check inbox.list_all_messages() after).
class ReceiveEmailTool(Tool):
    def __init__(self, inbox: InboxManager):
        self.inbox = inbox
        super().__init__(
            name="receive_email",
            description="Record an incoming email from a sender into the inbox.",
            input_schema={
                "type": "object",
                "properties": {
                    "sender": {"type": "string", "description": "Sender email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body content"},
                },
                "required": ["sender", "subject", "body"],
            },
        )

    def run(self, params: dict) -> str:
        msg = self.inbox.receive_email(params["sender"], params["subject"], params["body"])
        return json.dumps(asdict(msg))


# Flexible search across the inbox. All parameters are optional so the
# model can combine filters freely (e.g. keyword + date range, or just
# contact_email). Date strings are parsed from ISO format since that's
# what the model produces and what the DB stores.
class SearchMessagesTool(Tool):
    def __init__(self, inbox: InboxManager):
        self.inbox = inbox
        super().__init__(
            name="search_messages",
            description="Search inbox messages by contact email, direction, keyword, or date range.",
            input_schema={
                "type": "object",
                "properties": {
                    "contact_email": {"type": "string", "description": "Filter by contact email address"},
                    "is_incoming": {"type": "boolean", "description": "True for received, False for sent"},
                    "keyword": {"type": "string", "description": "Search keyword in subject or body"},
                    "start_date": {"type": "string", "description": "ISO datetime — messages on or after"},
                    "end_date": {"type": "string", "description": "ISO datetime — messages on or before"},
                },
                "required": [],
            },
        )

    def run(self, params: dict) -> str:
        messages = self.inbox.search_messages(
            contact_email=params.get("contact_email"),
            is_incoming=params.get("is_incoming"),
            keyword=params.get("keyword"),
            start_date=datetime.fromisoformat(params["start_date"]) if params.get("start_date") else None,
            end_date=datetime.fromisoformat(params["end_date"]) if params.get("end_date") else None,
        )
        return json.dumps([asdict(m) for m in messages])


# Permanent deletion — no soft-delete or trash. The model needs the
# message_id, which it can get from search_messages or list_all_messages.
class DeleteEmailTool(Tool):
    def __init__(self, inbox: InboxManager):
        self.inbox = inbox
        super().__init__(
            name="delete_email",
            description="Delete an email message by its ID.",
            input_schema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "Unique message identifier"},
                },
                "required": ["message_id"],
            },
        )

    def run(self, params: dict) -> str:
        return json.dumps({"deleted": self.inbox.delete_email(params["message_id"])})


# Returns the full inbox in one call. Useful when the model needs an
# overview or the user asks a broad question like "what emails do I have?"
# For large inboxes this could be expensive — but for this project's scope
# the dataset is small enough that pagination isn't needed.
class ListAllMessagesTool(Tool):
    def __init__(self, inbox: InboxManager):
        self.inbox = inbox
        super().__init__(
            name="list_all_messages",
            description="List all inbox messages ordered by most recent first.",
            input_schema={"type": "object", "properties": {}, "required": []},
        )

    def run(self, params: dict) -> str:
        return json.dumps([asdict(m) for m in self.inbox.list_all_messages()])
