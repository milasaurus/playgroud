import base64
import mimetypes
import os
import urllib.request

from anthropic import Anthropic
from claude_conversation_engine.api.history import HistoryHandler, USER_ROLE, ASSISTANT_ROLE
from claude_conversation_engine.usage_tracking.tracker import UsageTracker


DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOKENS = 4000
DEFAULT_THINKING_BUDGET = 1024
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024

DEFAULT_SYSTEM_PROMPT = """Give the user guidance on how to solve their problem.
Do not provide the answer directly.
Instead, ask questions and provide hints that help the user
arrive at the solution on their own."""


class ImageHelper:
    """Handles image validation and conversion to base64 content blocks."""

    @staticmethod
    def load_from_file(path):
        """Read a local image file and return (base64_data, media_type)."""
        with open(path, "rb") as f:
            image_bytes = f.read()
        media_type = mimetypes.guess_type(path)[0] or "image/png"
        return base64.standard_b64encode(image_bytes).decode("utf-8"), media_type

    @staticmethod
    def fetch_from_url(url):
        """Download an image URL and return (base64_data, media_type)."""
        with urllib.request.urlopen(url) as response:
            image_bytes = response.read()
            content_type = response.headers.get("Content-Type")
        if not content_type:
            content_type = mimetypes.guess_type(url)[0] or "image/png"
        return base64.standard_b64encode(image_bytes).decode("utf-8"), content_type

    @staticmethod
    def build_content_block(image):
        """Build a base64 image content block from a file path, URL, or raw data dict."""
        if isinstance(image, str):
            if os.path.isfile(image):
                data, media_type = ImageHelper.load_from_file(image)
            else:
                data, media_type = ImageHelper.fetch_from_url(image)
        else:
            data, media_type = image["data"], image["media_type"]

        decoded_size = len(data) * 3 // 4
        if decoded_size > MAX_IMAGE_SIZE_BYTES:
            raise ValueError(
                f"Image exceeds maximum size of {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB"
            )
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": data,
            },
        }


class MessageHandler:
    """Wraps the Anthropic messages API for multi-turn conversations."""

    def __init__(
        self,
        client: Anthropic,
        history: HistoryHandler,
        tracker: UsageTracker,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        thinking: bool = False,
        thinking_budget: int = DEFAULT_THINKING_BUDGET,
    ):
        self.client = client
        self.history = history
        self.tracker = tracker
        self.system_prompt = system_prompt
        self.model = model
        self.max_tokens = max_tokens
        self.thinking = thinking
        self.thinking_budget = thinking_budget

    def send(self, content: str, system_prompt: str = None, image=None) -> str:
        if image is not None:
            user_content = [
                ImageHelper.build_content_block(image),
                {"type": "text", "text": content},
            ]
        else:
            user_content = content

        self.history.add(USER_ROLE, user_content)

        response_text = ""

        api_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system_prompt if system_prompt is not None else self.system_prompt,
            "messages": self.history.get_messages(),
        }

        if self.thinking:
            api_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.thinking_budget,
            }
            print("[Thinking...]", end=" ", flush=True)

        with self.client.messages.stream(**api_params) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                response_text += text

            final_message = stream.get_final_message()

        print()
        self.tracker.record(
            final_message.usage.input_tokens,
            final_message.usage.output_tokens,
        )

        if self.thinking:
            content_blocks = [
                block.model_dump() for block in final_message.content
            ]
            self.history.add(ASSISTANT_ROLE, content_blocks)
        else:
            self.history.add(ASSISTANT_ROLE, response_text)

        return response_text
