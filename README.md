## Project Structure

- `nano_code/`
    - `agent/`: (Scaffolding) For different assistant agent modes. Intended for alternate agent implementations; currently contains placeholder for future expansion.
    - `agent_tool/`: Defines the extensible agent tool system. Includes the base class for tools, schema validation, tool registries, and built-in toolsets (e.g., OS and utility tools) enabling the assistant to invoke code, file ops, etc.
    - `core/`: Core session management and cost tracking. Handles persistent session state, memory storage, logging, environment variables, and usage metering.
    - `llm/`: Interfaces and utilities for various Language Model (LLM) backends. Implements async completion, OpenAI integration, and adapter logic for using different LLMs with a unified API.
    - `utils/`: Logging, file, and path utilities. Provides rich/JSON logging for assistant actions, file helpers, and path resolution across the project.
    - `__main__.py`: Main async CLI entry point. Runs the interactive assistant loop you see in the terminal.
    - `constants.py`, `env.py`: Core configuration/constants and dynamic environment controls.
- `tests/`: Test suite covering multiple code paths and behaviors.
- `pyproject.toml`: Python project metadata, entry points, and dependencies.

Each submodule is designed to be clear, extensible, and focused on a single major responsibility within the code-assistant architecture.