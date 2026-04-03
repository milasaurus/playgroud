chat:
	source venv/bin/activate && python -m core_services.claude_conversation_engine.services.send_message

prompt:
	source venv/bin/activate && python -m core_services.prompt_eval.services.evaluation

test:
	source venv/bin/activate && python -m pytest core_services/ -v

test-chat:
	source venv/bin/activate && python -m pytest core_services/claude_conversation_engine/tests/ -v

test-eval:
	source venv/bin/activate && python -m pytest core_services/prompt_eval/tests/ -v

setup:
	python3 -m venv venv && source venv/bin/activate && pip install anthropic python-dotenv pytest
