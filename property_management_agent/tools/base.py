"""Base Tool class for the property management agent.

All tools inherit from this ABC. It enforces a consistent interface so the
Agent can look up tools by name, serialize them for the API, and execute
them — all without knowing the concrete type.
"""

from abc import ABC, abstractmethod


class Tool(ABC):
    """Base class for all agent tools.

    Subclasses set name, description, and input_schema in their __init__,
    then implement run() to perform the actual work.
    """

    def __init__(self, name: str, description: str, input_schema: dict):
        self.name = name
        self.description = description
        self.input_schema = input_schema

    def to_api_dict(self) -> dict:
        """Return the dict the Anthropic API expects for tool definitions."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    @abstractmethod
    def run(self, params: dict) -> str:
        """Execute the tool and return a JSON string result."""
