import os
import uuid
from hashlib import sha256
from logging import Logger
from dataclasses import dataclass, field
from gitignore_parser import parse_gitignore
from typing import Literal
from ..constants import NANO_CODE_TEMP_DIR, MEMORY_FILE
from ..utils.paths import upward_git_root
from ..utils.logger import SessionLogger, AIConsoleLogger
from ..env import Env
from .cost import (
    LLMCheckpoint,
    LLMCheckpointFailed,
    ToolCheckpoint,
    ToolCheckpointFailed,
)


def ascii_progress_bar(current, maximum, bar_width=20):
    filled = int(bar_width * min(current, maximum) / maximum)
    bar = f"{'█'*filled}"
    return bar


@dataclass
class Session:
    working_dir: str

    debug_mode: bool = False
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    maximum_search_dir: int = 200
    maximum_token_window_size: int = 32000
    working_env: Env = field(default_factory=lambda: Env.from_home())
    logger: SessionLogger = None

    running_llm_checkpoints: list[LLMCheckpoint | LLMCheckpointFailed] = field(
        default_factory=lambda: []
    )
    running_tool_checkpoints: list[ToolCheckpoint | ToolCheckpointFailed] = field(
        default_factory=lambda: []
    )

    def __post_init__(self):
        self.working_dir = os.path.abspath(self.working_dir)
        if not os.path.exists(self.working_dir):
            raise ValueError(f"Working directory {self.working_dir} does not exist")
        if os.getcwd() != self.working_dir:
            self.log(
                f"Current working directory {os.getcwd()}, changing to {self.working_dir}",
            )
            os.chdir(self.working_dir)

        self.__project_root = upward_git_root(self.working_dir) or self.working_dir
        self.__ignore_matchers = self.find_ignore_matchers()

        self.log(f"Session Environment: {self.working_env}")
        self.log(f"Git project root: {self.__project_root}")
        self.log(f"Found {len(self.__ignore_matchers)} ignore matchers")

    def get_tempdir(self) -> str:
        return os.path.join(
            NANO_CODE_TEMP_DIR, sha256(self.__project_root.encode()).hexdigest()
        )

    def cleanup_checkpoint(self):
        try:
            os.rmdir(self.get_tempdir())
        except Exception:
            pass

    def find_ignore_matchers(self) -> list:
        ignore_files = []
        # Find .gitignore file in the working directory
        for root, dirs, files in os.walk(self.__project_root):
            if ".gitignore" in files:
                ignore_files.append(os.path.join(root, ".gitignore"))

        # Parse gitignore rules if found
        ignore_matchers = {os.path.dirname(f): parse_gitignore(f) for f in ignore_files}
        return ignore_matchers

    def ignore_path(self, path: str) -> bool:
        path = os.path.abspath(path)
        for k, v in self.__ignore_matchers.items():
            if path.startswith(k) and v(path):
                return True
        return False

    def path_within_root(self, path: str) -> bool:
        return os.path.abspath(path).startswith(self.working_dir)

    def find_memory_paths(self) -> list[str]:
        __search_dir = 0
        memory_contents = []
        for root, dirs, files in os.walk(self.__project_root):
            if self.ignore_path(root):
                self.log(f"Ignoring {root}", level="debug")
                continue
            if MEMORY_FILE in files:
                memory_contents.append(os.path.join(root, MEMORY_FILE))

            __search_dir += 1
            if __search_dir > self.maximum_search_dir:
                break

        return memory_contents

    def get_memory(self) -> list[str]:
        memory = []
        memory_paths = self.find_memory_paths()
        for path in memory_paths:
            try:
                with open(path, "r") as f:
                    memory.append(f.read())
            except Exception as e:
                self.log(
                    f"Error reading memory file {path}: {e}",
                    level="error",
                )
        self.log(f"Found {len(memory_paths)} memory files")
        return memory

    def update_llm_checkpoint(
        self, llm_checkpoint: LLMCheckpoint | LLMCheckpointFailed
    ):
        self.running_llm_checkpoints.append(llm_checkpoint)
        current = llm_checkpoint.response.usage.total_tokens
        maximum = self.maximum_token_window_size
        bar = ascii_progress_bar(current, maximum)
        msg = f"{current}/{maximum} tokens {bar}"
        self.log(msg)

    def update_tool_checkpoint(
        self, tool_checkpoint: ToolCheckpoint | ToolCheckpointFailed
    ):
        self.running_tool_checkpoints.append(tool_checkpoint)

    def log(self, message: str, level: Literal["info", "debug", "error"] = "info"):
        if self.logger is None:
            return
        if level == "info":
            self.logger.info(self.session_id, message)
        elif level == "debug":
            self.logger.debug(self.session_id, message)
        elif level == "error":
            self.logger.error(self.session_id, message)
