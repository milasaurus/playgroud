from client import client
from claude_conversation_engine.api.history import HistoryHandler
from claude_conversation_engine.api.messages import MessageHandler
from claude_conversation_engine.usage_tracking.tracker import UsageTracker

EXIT_COMMAND = "quit"
IMAGE_COMMAND = "/image"

IMAGE_PROMPT_GUIDANCE = """You attached an image. For best results, write a detailed prompt:
  - Describe what you want Claude to analyze or extract
  - Be specific about the output format you expect
  - Consider providing context (e.g. "This is a satellite image of a residential property")
  - For counting or detection tasks, specify exactly what to look for

Prompt: """


def run_chat(handler, tracker, input_fn=input, print_fn=print):
    print_fn(f"(Type '{IMAGE_COMMAND} <path or url>' to attach an image, '{EXIT_COMMAND}' to exit)")
    while True:
        user_input = input_fn("\nYou: ")
        if user_input == EXIT_COMMAND:
            print_fn(tracker.report())
            break

        image = None
        if user_input.startswith(IMAGE_COMMAND):
            image_source = user_input[len(IMAGE_COMMAND):].strip()
            if not image_source:
                print_fn("Usage: /image <path or url>")
                continue
            image = image_source
            print_fn(IMAGE_PROMPT_GUIDANCE)
            user_input = input_fn("")
            if user_input == EXIT_COMMAND:
                print_fn(tracker.report())
                break

        print("\nClaude: ", end="", flush=True)
        handler.send(user_input, image=image)
        print_fn(f"(Type '{IMAGE_COMMAND} <path or url>' to attach an image, '{EXIT_COMMAND}' to exit)")


if __name__ == "__main__":
    history = HistoryHandler()
    tracker = UsageTracker()
    handler = MessageHandler(client, history, tracker)
    run_chat(handler, tracker)
