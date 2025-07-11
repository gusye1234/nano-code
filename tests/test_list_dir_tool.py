import pytest
import tempfile
import os
import stat
from pathlib import Path
from unittest import mock

from nano_code.agent_tool.os_tool.list_dir import ListDirTool
from nano_code.core.session import Session


def build_session(tmp_path):
    sess = Session(working_dir=str(tmp_path))
    sess.working_dir = str(tmp_path)
    return sess


def run_tool(session, **kwargs):
    tool = ListDirTool.init()
    import asyncio

    return asyncio.get_event_loop().run_until_complete(tool._execute(session, kwargs))


def test_list_normal(tmp_path):
    (tmp_path / "d1").mkdir()
    (tmp_path / "f1.txt").write_text("abc")
    (tmp_path / "f2.txt").write_text("def")
    session = build_session(tmp_path)
    result = run_tool(session, absolute_path=str(tmp_path), show_hidden=False)
    assert "d1" in result.for_llm or "d1" in result.for_human
    assert "f1.txt" in result.for_llm or "f1.txt" in result.for_human
    assert "f2.txt" in result.for_llm or "f2.txt" in result.for_human


def test_list_empty(tmp_path):
    session = build_session(tmp_path)
    result = run_tool(session, absolute_path=str(tmp_path))
    assert "Directory is empty." in result.for_llm


def test_show_hidden(tmp_path):
    (tmp_path / ".hidden").write_text("hidden")
    (tmp_path / "visible").write_text("v")
    session = build_session(tmp_path)
    # Hidden off
    result = run_tool(session, absolute_path=str(tmp_path), show_hidden=False)
    assert ".hidden" not in result.for_llm
    # Hidden on
    result = run_tool(session, absolute_path=str(tmp_path), show_hidden=True)
    assert ".hidden" in result.for_llm


def test_path_does_not_exist(tmp_path):
    session = build_session(tmp_path)
    bad = str(tmp_path / "notfound")
    result = run_tool(session, absolute_path=bad)
    assert "does not exist" in result.for_llm.lower()


def test_path_not_a_directory(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("foo")
    session = build_session(tmp_path)
    result = run_tool(session, absolute_path=str(file))
    assert "not a directory" in result.for_llm.lower()


def test_permission_denied(monkeypatch, tmp_path):
    (tmp_path / "subdir").mkdir()
    session = build_session(tmp_path)
    with mock.patch("os.listdir", side_effect=PermissionError):
        result = run_tool(session, absolute_path=str(tmp_path))
        assert "permission denied" in result.for_llm.lower()


def test_path_not_within_root(tmp_path):
    session = build_session(tmp_path)
    result = run_tool(session, absolute_path="/")
    assert "not within the working directory" in result.for_llm.lower()
