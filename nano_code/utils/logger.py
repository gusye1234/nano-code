import json
import logging
from rich.console import Console
from rich.markdown import Markdown as M


class SessionLogger:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def debug(self, session_id: str, message: str):
        self.logger.debug(json.dumps({"session_id": str(session_id)}) + " | " + message)

    def info(self, session_id: str, message: str):
        self.logger.info(json.dumps({"session_id": str(session_id)}) + " | " + message)

    def warning(self, session_id: str, message: str):
        self.logger.warning(
            json.dumps({"session_id": str(session_id)}) + " | " + message
        )

    def error(self, session_id: str, message: str):
        self.logger.error(json.dumps({"session_id": str(session_id)}) + " | " + message)


class AIConsoleLogger:

    def __init__(self, console: Console = None):
        self.console = console or Console()

    def debug(self, session_id: str, message: str):
        pass
        # self.console.print(f"💻 {message}")
        # self.console.rule()

    def info(self, session_id: str, message: str):
        self.console.print(M(message))
        self.console.rule(style="gray")

    def error(self, session_id: str, message: str):
        self.console.print(f"❌ {message}")
        self.console.rule(style="gray")
