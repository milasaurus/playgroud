"""Tests for inbox tools — verifies each tool calls the right manager method
and returns well-formed JSON."""

import json
import os
import pytest

from backend.inbox_manager import InboxManager
from tools.inbox_tools import (
    SendEmailTool, ReceiveEmailTool, SearchMessagesTool,
    DeleteEmailTool, ListAllMessagesTool,
)

DB_PATH = "test_tool_inbox.db"


@pytest.fixture
def inbox():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    mgr = InboxManager(DB_PATH)
    yield mgr
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


class TestSendEmailTool:
    def test_sends_and_returns_message(self, inbox):
        tool = SendEmailTool(inbox)
        result = json.loads(tool.run({
            "recipient": "tenant@example.com",
            "subject": "Lease renewal",
            "body": "Your lease is up for renewal.",
        }))

        assert result["contact_email"] == "tenant@example.com"
        assert result["subject"] == "Lease renewal"
        assert result["is_incoming"] is False

    def test_message_persists_in_db(self, inbox):
        tool = SendEmailTool(inbox)
        tool.run({
            "recipient": "tenant@example.com",
            "subject": "Test",
            "body": "Body",
        })

        assert len(inbox.list_all_messages()) == 1

    def test_api_dict_shape(self, inbox):
        tool = SendEmailTool(inbox)
        api = tool.to_api_dict()
        assert api["name"] == "send_email"
        assert "recipient" in api["input_schema"]["properties"]


class TestReceiveEmailTool:
    def test_receives_and_returns_message(self, inbox):
        tool = ReceiveEmailTool(inbox)
        result = json.loads(tool.run({
            "sender": "customer@example.com",
            "subject": "Inquiry",
            "body": "Do you have any 2BR apartments?",
        }))

        assert result["contact_email"] == "customer@example.com"
        assert result["is_incoming"] is True

    def test_message_persists_in_db(self, inbox):
        tool = ReceiveEmailTool(inbox)
        tool.run({
            "sender": "customer@example.com",
            "subject": "Inquiry",
            "body": "Body",
        })

        messages = inbox.get_inbox()
        assert len(messages) == 1
        assert messages[0].contact_email == "customer@example.com"


class TestSearchMessagesTool:
    def test_search_by_keyword(self, inbox):
        inbox.receive_email("a@test.com", "Hello", "I need a 2BR apartment")
        inbox.receive_email("b@test.com", "Question", "What is the rent?")

        tool = SearchMessagesTool(inbox)
        result = json.loads(tool.run({"keyword": "2BR"}))

        assert len(result) == 1
        assert result[0]["contact_email"] == "a@test.com"

    def test_search_by_contact(self, inbox):
        inbox.receive_email("a@test.com", "First", "Body 1")
        inbox.receive_email("b@test.com", "Second", "Body 2")

        tool = SearchMessagesTool(inbox)
        result = json.loads(tool.run({"contact_email": "b@test.com"}))

        assert len(result) == 1
        assert result[0]["subject"] == "Second"

    def test_search_no_filters_returns_all(self, inbox):
        inbox.receive_email("a@test.com", "First", "Body")
        inbox.send_email("b@test.com", "Second", "Body")

        tool = SearchMessagesTool(inbox)
        result = json.loads(tool.run({}))

        assert len(result) == 2


class TestDeleteEmailTool:
    def test_deletes_existing_message(self, inbox):
        msg = inbox.receive_email("a@test.com", "Delete me", "Body")

        tool = DeleteEmailTool(inbox)
        result = json.loads(tool.run({"message_id": msg.message_id}))

        assert result["deleted"] is True
        assert len(inbox.list_all_messages()) == 0

    def test_delete_nonexistent_returns_false(self, inbox):
        tool = DeleteEmailTool(inbox)
        result = json.loads(tool.run({"message_id": "fake-id"}))

        assert result["deleted"] is False


class TestListAllMessagesTool:
    def test_returns_empty_list_when_no_messages(self, inbox):
        tool = ListAllMessagesTool(inbox)
        result = json.loads(tool.run({}))

        assert result == []

    def test_returns_all_messages(self, inbox):
        inbox.receive_email("a@test.com", "First", "Body")
        inbox.send_email("b@test.com", "Second", "Body")

        tool = ListAllMessagesTool(inbox)
        result = json.loads(tool.run({}))

        assert len(result) == 2
