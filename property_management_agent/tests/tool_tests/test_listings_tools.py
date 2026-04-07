"""Tests for listings tools — verifies each tool calls the right manager method
and returns well-formed JSON."""

import json
import os

import pytest

from backend.listings_manager import ListingsManager
from tools.listings_tools import (
    CreateListingTool, UpdateListingTool, DeleteListingTool,
    SearchListingsByDescriptionTool, SearchListingsByRentRangeTool,
    ListAllListingsTool,
)

DB_PATH = "test_tool_listings.db"

SAMPLE_LISTING = {
    "description": "Spacious 2BR with balcony",
    "address": "123 Oak Street",
    "monthly_rent": 2500,
    "bedrooms": 2,
    "bathrooms": 2,
}


@pytest.fixture
def listings():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    mgr = ListingsManager(DB_PATH)
    yield mgr
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


class TestCreateListingTool:
    def test_creates_and_returns_listing(self, listings):
        tool = CreateListingTool(listings)
        result = json.loads(tool.run(SAMPLE_LISTING))

        assert result["address"] == "123 Oak Street"
        assert result["monthly_rent"] == 2500
        assert result["bedrooms"] == 2

    def test_listing_persists_in_db(self, listings):
        tool = CreateListingTool(listings)
        tool.run(SAMPLE_LISTING)

        assert len(listings.list_all_listings()) == 1

    def test_api_dict_shape(self, listings):
        tool = CreateListingTool(listings)
        api = tool.to_api_dict()
        assert api["name"] == "create_listing"
        assert "address" in api["input_schema"]["properties"]


class TestUpdateListingTool:
    def test_updates_rent(self, listings):
        listing = listings.create_listing(**SAMPLE_LISTING)

        tool = UpdateListingTool(listings)
        result = json.loads(tool.run({
            "listing_id": listing.listing_id,
            "monthly_rent": 2800,
        }))

        assert result["monthly_rent"] == 2800
        assert result["address"] == "123 Oak Street"  # unchanged

    def test_updates_description(self, listings):
        listing = listings.create_listing(**SAMPLE_LISTING)

        tool = UpdateListingTool(listings)
        result = json.loads(tool.run({
            "listing_id": listing.listing_id,
            "description": "Renovated 2BR with balcony",
        }))

        assert result["description"] == "Renovated 2BR with balcony"


class TestDeleteListingTool:
    def test_deletes_existing_listing(self, listings):
        listing = listings.create_listing(**SAMPLE_LISTING)

        tool = DeleteListingTool(listings)
        result = json.loads(tool.run({"listing_id": listing.listing_id}))

        assert result["deleted"] is True
        assert len(listings.list_all_listings()) == 0

    def test_delete_nonexistent_returns_false(self, listings):
        tool = DeleteListingTool(listings)
        result = json.loads(tool.run({"listing_id": "fake-id"}))

        assert result["deleted"] is False


class TestSearchListingsByDescriptionTool:
    def test_finds_by_partial_description(self, listings):
        listings.create_listing(**SAMPLE_LISTING)
        listings.create_listing(
            description="Cozy studio near park",
            address="456 Maple Ave",
            monthly_rent=1800,
            bedrooms=1,
            bathrooms=1,
        )

        tool = SearchListingsByDescriptionTool(listings)
        result = json.loads(tool.run({"search_term": "balcony"}))

        assert len(result) == 1
        assert result[0]["address"] == "123 Oak Street"

    def test_returns_empty_for_no_match(self, listings):
        listings.create_listing(**SAMPLE_LISTING)

        tool = SearchListingsByDescriptionTool(listings)
        result = json.loads(tool.run({"search_term": "penthouse"}))

        assert result == []


class TestSearchListingsByRentRangeTool:
    def test_filters_by_max_rent(self, listings):
        listings.create_listing(**SAMPLE_LISTING)  # 2500
        listings.create_listing(
            description="Luxury unit",
            address="789 Pine Rd",
            monthly_rent=3500,
            bedrooms=2,
            bathrooms=2,
        )

        tool = SearchListingsByRentRangeTool(listings)
        result = json.loads(tool.run({"max_rent": 3000}))

        assert len(result) == 1
        assert result[0]["monthly_rent"] == 2500

    def test_filters_by_rent_range_and_bedrooms(self, listings):
        listings.create_listing(**SAMPLE_LISTING)  # 2BR, $2500
        listings.create_listing(
            description="Studio",
            address="321 Elm St",
            monthly_rent=1800,
            bedrooms=1,
            bathrooms=1,
        )

        tool = SearchListingsByRentRangeTool(listings)
        result = json.loads(tool.run({
            "max_rent": 3000,
            "bedrooms": 2,
        }))

        assert len(result) == 1
        assert result[0]["bedrooms"] == 2

    def test_no_filters_returns_all(self, listings):
        listings.create_listing(**SAMPLE_LISTING)
        listings.create_listing(
            description="Other",
            address="456 Maple Ave",
            monthly_rent=1800,
            bedrooms=1,
            bathrooms=1,
        )

        tool = SearchListingsByRentRangeTool(listings)
        result = json.loads(tool.run({}))

        assert len(result) == 2


class TestListAllListingsTool:
    def test_returns_empty_when_no_listings(self, listings):
        tool = ListAllListingsTool(listings)
        result = json.loads(tool.run({}))

        assert result == []

    def test_returns_all_listings(self, listings):
        listings.create_listing(**SAMPLE_LISTING)
        listings.create_listing(
            description="Another",
            address="456 Maple Ave",
            monthly_rent=1800,
            bedrooms=1,
            bathrooms=1,
        )

        tool = ListAllListingsTool(listings)
        result = json.loads(tool.run({}))

        assert len(result) == 2
