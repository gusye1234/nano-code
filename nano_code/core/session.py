import os
import uuid
import glob
import time
import json
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

    maximum_search_dir: int = 1000
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
        searched_dirs = 0

        for root, dirs, files in os.walk(self.__project_root):
            # Check if we've exceeded the maximum search directory limit
            if searched_dirs >= self.maximum_search_dir:
                self.log(
                    f"Exceeded maximum search directory limit of {self.maximum_search_dir}",
                    level="error",
                )
                break

            searched_dirs += 1

            # Look for .gitignore in current directory
            if ".gitignore" in files:
                ignore_files.append(os.path.join(root, ".gitignore"))

            # Sort dirs to ensure consistent traversal order
            dirs.sort()

        # Parse gitignore rules if found
        ignore_matchers = {os.path.dirname(f): parse_gitignore(f) for f in ignore_files}
        return ignore_matchers

    def ignore_path(self, path: str) -> bool:
        path = os.path.abspath(path)
        for k, v in self.__ignore_matchers.items():
            try:
                # Check if path is actually within the directory k
                # Use os.path.commonpath to safely check if k is a parent of path
                if os.path.commonpath([k, path]) == k and v(path):
                    return True
            except (ValueError, OSError):
                # os.path.commonpath can raise ValueError if paths are on different drives
                # or OSError for other path-related issues - skip this matcher
                continue
        return False

    def path_within_root(self, path: str) -> bool:
        return os.path.abspath(path).startswith(self.working_dir)

    def find_memory_paths(self) -> list[str]:
        memory_files = []
        searched_dirs = 0

        for root, dirs, files in os.walk(self.__project_root):
            # Check if we've exceeded the maximum search directory limit
            if searched_dirs >= self.maximum_search_dir:
                self.log(
                    f"Exceeded maximum search directory limit of {self.maximum_search_dir}",
                    level="error",
                )
                break

            searched_dirs += 1

            # Look for memory files in current directory
            if MEMORY_FILE in files:
                memory_files.append(os.path.join(root, MEMORY_FILE))

            # Filter out ignored subdirectories to avoid walking into them
            # (This modifies dirs in-place to affect os.walk's traversal)
            dirs[:] = [
                d for d in sorted(dirs) if not self.ignore_path(os.path.join(root, d))
            ]

        # Filter out ignored memory files
        not_ignore_memory_files = [
            m for m in memory_files if not self.ignore_path(os.path.dirname(m))
        ]
        return not_ignore_memory_files

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
        current = llm_checkpoint.usage.total_tokens
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

    def save_checkpoints(self):
        use_dir = self.get_tempdir()
        if not os.path.exists(use_dir):
            os.makedirs(use_dir)
        file_name = f"{time.strftime('%Y_%m_%d_%H_%M_%S')}-{self.session_id}.json"
        file_path = os.path.join(use_dir, file_name)
        with open(file_path, "w") as f:
            json.dump(
                {
                    "llm_checkpoints": [
                        c.to_json() for c in self.running_llm_checkpoints
                    ],
                    "tool_checkpoints": [
                        c.to_json() for c in self.running_tool_checkpoints
                    ],
                },
                f,
            )
