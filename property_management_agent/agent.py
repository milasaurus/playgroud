"""
Property management agent — runs a tool-use loop with multi-turn conversation.

The Agent holds conversation history across calls to `run()`, so each new
user message can reference prior context.
"""

import anthropic

from tools import Tool
from system_prompt import SYSTEM_PROMPT


MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 16_000
MAX_ITERATIONS = 4
# Cap total tool calls per run() to prevent runaway loops on overly complex
# requests. Each iteration can invoke multiple tools in parallel, so this
# limit is independent of MAX_ITERATIONS.
MAX_TOOL_CALLS = 8
# Timeout per API request in seconds. Prevents hung requests from blocking
# the agent indefinitely. Haiku responses typically complete in 5-15s.
API_TIMEOUT = 60

# Budget tokens for the model's internal reasoning. Extended thinking lets
# the model plan multi-step tool sequences before acting, which significantly
# improves tool-selection accuracy on complex requests (e.g. "search listings,
# then schedule a viewing, then email the customer"). We cap it to keep
# latency and cost reasonable for a Haiku-class model.
THINKING_BUDGET = 5_000

class Agent:
    """Agentic loop with persistent conversation history.

    Args:
        client: Anthropic API client.
        tools: List of Tool instances the agent can invoke.
    """

    def __init__(
        self,
        client: anthropic.Anthropic,
        tools: list[Tool],
    ):
        self.client = client
        self.tools = tools
        self.messages: list[dict] = []

        # Cache the API-formatted tool dicts. These are sent with every API
        # request but never change during the agent's lifetime, so we build
        # the list once here instead of re-deriving it on every call to run().
        # This avoids repeated iteration and allocation in the hot loop, and
        # makes it easy to add cache_control markup in one place.
        self._tool_defs_cache = [t.to_api_dict() for t in self.tools]

    def run(self, user_message: str) -> str:
        """Append a user message and run the tool-use loop until Claude responds with text."""
        self.messages.append({"role": "user", "content": user_message})
        tool_call_count = 0

        for _ in range(MAX_ITERATIONS):
            response = self._run_inference()

            # Strip thinking blocks before appending to self.messages.
            # Thinking blocks are ephemeral — the API rejects them if they
            # appear in subsequent requests. Since self.messages is sent back
            # on every call to _run_inference(), we must filter them out.
            content_for_history = [
                block for block in response.content
                if block.type != "thinking"
            ]
            self.messages.append({"role": "assistant", "content": content_for_history})

            if response.stop_reason != "tool_use":
                return self._extract_text(response)

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_call_count += 1
                    if tool_call_count > MAX_TOOL_CALLS:
                        return self._extract_text(response)
                    result = self._execute_tool(block.id, block.name, block.input)
                    tool_results.append(result)

            self.messages.append({"role": "user", "content": tool_results})

        return self._extract_text(response)

    def _run_inference(self) -> anthropic.types.Message:
        """Stream a response from Claude with extended thinking enabled.

        Streaming gives us the final message in a single pass while allowing
        future callers (e.g. a chat UI) to display tokens as they arrive.
        For now we consume the stream silently and return the completed message.
        """
        # Mark the system prompt and last tool definition as ephemeral for
        # prompt caching. The API caches content up to the last cache_control
        # breakpoint, so on subsequent requests within the same session the
        # system prompt and tool schemas are served from cache rather than
        # re-processed — reducing latency and input token costs.
        system_with_cache = [{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }]

        tool_defs = self._tool_defs_cache
        if tool_defs:
            tool_defs[-1]["cache_control"] = {"type": "ephemeral"}

        with self.client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_with_cache,
            tools=tool_defs,
            messages=self.messages,
            # Extended thinking with ephemeral cache_control. Thinking blocks
            # are never cached or persisted — they exist only for the current
            # request. This keeps cost down while letting the model reason
            # through which tools to call and in what order.
            thinking={
                "type": "enabled",
                "budget_tokens": THINKING_BUDGET,
            },
            timeout=API_TIMEOUT,
        ) as stream:
            return stream.get_final_message()

    def _execute_tool(self, tool_id: str, name: str, input: dict) -> dict:
        """Look up a tool by name, run it, and return a tool_result dict."""
        tool = next((t for t in self.tools if t.name == name), None)
        if tool is None:
            return {
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": f"tool '{name}' not found",
                "is_error": True,
            }

        try:
            result = tool.run(input)
            return {"type": "tool_result", "tool_use_id": tool_id, "content": result}
        except Exception as e:
            return {
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": str(e),
                "is_error": True,
            }

    def _extract_text(self, response: anthropic.types.Message) -> str:
        """Pull the text content from a Claude response."""
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""
