"""
daytona_management - Modular Daytona Proxy System

This module provides a modular architecture for managing Daytona sandboxes
and executing nano-code tasks in a clean, maintainable way.

Components:
- config: Configuration management with security improvements
- sandbox_manager: Daytona sandbox lifecycle management  
- workspace_manager: Workspace setup and environment management
- file_transfer: File upload/download operations
- task_executor: nano-code task execution
- proxy: Main coordinator bringing all modules together
- cli: Command line interface and argument parsing

Usage:
    from daytona_management import NanoCodeProxy
    
    proxy = NanoCodeProxy()
    proxy.setup_daytona()
    proxy.start_nano_code_batch("任务描述", ["file1.py"])
"""

from .config import DaytonaConfig, LLMConfig, PathConfig
from .sandbox_manager import SandboxManager
from .workspace_manager import WorkspaceManager
from .file_transfer import FileTransfer
from .task_executor import TaskExecutor
from .proxy import NanoCodeProxy
from .cli import main

__version__ = "1.0.0"
__all__ = [
    "DaytonaConfig",
    "LLMConfig", 
    "PathConfig",
    "SandboxManager",
    "WorkspaceManager",
    "FileTransfer",
    "TaskExecutor",
    "NanoCodeProxy",
    "main"
]