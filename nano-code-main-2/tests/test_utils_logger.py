import logging
import types
from unittest.mock import Mock
import pytest
from nano_code.utils.logger import SessionLogger, AIConsoleLogger


def test_session_logger_methods():
    mock_logger = Mock()
    slog = SessionLogger(mock_logger)
    slog.debug("1", "a dbg")
    slog.info("2", "msg info")
    slog.warning("3", "warn issue")
    slog.error("4", "errzzz")
    # Ensure each logging method is called once
    assert mock_logger.debug.called
    assert mock_logger.info.called
    assert mock_logger.warning.called
    assert mock_logger.error.called

def test_aiconsole_logger_info_and_error():
    mock_console = Mock()
    clog = AIConsoleLogger(mock_console)
    clog.info("s", "see me?")
    clog.error("s", "errhf")
    # Should call print() and rule()
    assert mock_console.print.call_count >= 1
    assert mock_console.rule.call_count >= 1

# No test for debug as method stubbed (pass)
