from unittest.mock import MagicMock, patch
from claude_conversation_engine.api.messages import MessageHandler
from claude_conversation_engine.usage_tracking.tracker import UsageTracker
from claude_conversation_engine.services.send_message import run_chat, EXIT_COMMAND, IMAGE_COMMAND, IMAGE_PROMPT_GUIDANCE


def make_mock_handler(responses):
    mock_handler = MagicMock(spec=MessageHandler)
    mock_handler.send.side_effect = responses
    return mock_handler


@patch("builtins.print")
def test_quit_exits_immediately(mock_print):
    mock_handler = make_mock_handler([])
    tracker = UsageTracker()
    inputs = iter([EXIT_COMMAND])
    output = []

    run_chat(mock_handler, tracker, input_fn=lambda _: next(inputs), print_fn=output.append)

    mock_handler.send.assert_not_called()


@patch("builtins.print")
def test_single_message_then_quit(mock_print):
    expected = "Hi there!"
    mock_handler = make_mock_handler([expected])
    tracker = UsageTracker()
    inputs = iter(["Hello", EXIT_COMMAND])
    output = []

    run_chat(mock_handler, tracker, input_fn=lambda _: next(inputs), print_fn=output.append)

    mock_handler.send.assert_called_once_with("Hello", image=None)


@patch("builtins.print")
def test_multi_turn_then_quit(mock_print):
    first_expected = "Python is a language."
    second_expected = "It's used for many things."
    mock_handler = make_mock_handler([first_expected, second_expected])
    tracker = UsageTracker()
    inputs = iter(["What is Python?", "What is it used for?", EXIT_COMMAND])
    output = []

    run_chat(mock_handler, tracker, input_fn=lambda _: next(inputs), print_fn=output.append)

    assert mock_handler.send.call_count == 2


@patch("builtins.print")
def test_image_command_prompts_for_detailed_input(mock_print):
    expected = "I see a house with trees nearby."
    mock_handler = make_mock_handler([expected])
    tracker = UsageTracker()
    image_url = "https://example.com/satellite.png"
    detailed_prompt = "Analyze this satellite image for fire risk. Identify the main residence and any tree branches overhanging it."
    inputs = iter([f"{IMAGE_COMMAND} {image_url}", detailed_prompt, EXIT_COMMAND])
    output = []

    run_chat(mock_handler, tracker, input_fn=lambda _: next(inputs), print_fn=output.append)

    mock_handler.send.assert_called_once_with(detailed_prompt, image=image_url)
    assert IMAGE_PROMPT_GUIDANCE in output


@patch("builtins.print")
def test_image_command_without_url_shows_usage(mock_print):
    mock_handler = make_mock_handler([])
    tracker = UsageTracker()
    inputs = iter([IMAGE_COMMAND, EXIT_COMMAND])
    output = []

    run_chat(mock_handler, tracker, input_fn=lambda _: next(inputs), print_fn=output.append)

    mock_handler.send.assert_not_called()
    assert "Usage: /image <path or url>" in output


@patch("builtins.print")
def test_image_command_quit_during_prompt(mock_print):
    mock_handler = make_mock_handler([])
    tracker = UsageTracker()
    image_url = "https://example.com/photo.png"
    inputs = iter([f"{IMAGE_COMMAND} {image_url}", EXIT_COMMAND])
    output = []

    run_chat(mock_handler, tracker, input_fn=lambda _: next(inputs), print_fn=output.append)

    mock_handler.send.assert_not_called()


@patch("builtins.print")
def test_all_features_passed_to_handler(mock_print):
    """Verify run_chat passes image and text through to handler.send for all supported features."""
    expected = "Response."
    mock_handler = make_mock_handler([expected, expected, expected])
    tracker = UsageTracker()
    image_url = "https://example.com/property.png"
    detailed_prompt = "Assess fire risk for this property."
    inputs = iter([
        # 1. Plain text message
        "Hello",
        # 2. Image with detailed prompt
        f"{IMAGE_COMMAND} {image_url}",
        detailed_prompt,
        # 3. Follow-up plain text
        "Summarize findings",
        EXIT_COMMAND,
    ])
    output = []

    run_chat(mock_handler, tracker, input_fn=lambda _: next(inputs), print_fn=output.append)

    assert mock_handler.send.call_count == 3
    mock_handler.send.assert_any_call("Hello", image=None)
    mock_handler.send.assert_any_call(detailed_prompt, image=image_url)
    mock_handler.send.assert_any_call("Summarize findings", image=None)
