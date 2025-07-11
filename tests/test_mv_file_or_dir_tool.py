import os
import shutil
import asyncio
import pytest
from unittest.mock import Mock
from nano_code.agent_tool.os_tool.mv_file_or_dir import MoveFileOrDirTool
from nano_code.agent_tool.base import AgentToolReturn

def make_mock_session(working_dir):
    session = Mock()
    session.working_dir = working_dir
    session.path_within_root.side_effect = lambda ap: ap.startswith(working_dir)
    return session

def test_mv_file_success(tmp_path):
    src_file = tmp_path / "source.txt"
    dst_file = tmp_path / "dest.txt"
    src_file.write_text("move me!")
    session = make_mock_session(str(tmp_path))
    args = {"from_path": str(src_file), "to_path": str(dst_file)}
    tool = MoveFileOrDirTool.init()
    result = asyncio.run(tool._execute(session, args))
    assert isinstance(result, AgentToolReturn)
    assert "successfully" in result.for_llm
    assert not src_file.exists() and dst_file.exists()
    assert dst_file.read_text() == "move me!"

def test_mv_missing_source(tmp_path):
    src_file = tmp_path / "404.txt"
    dst_file = tmp_path / "dest.txt"
    session = make_mock_session(str(tmp_path))
    args = {"from_path": str(src_file), "to_path": str(dst_file)}
    tool = MoveFileOrDirTool.init()
    result = asyncio.run(tool._execute(session, args))
    assert "does not exist" in result.for_llm or "does not exist" in result.for_human

def test_mv_destination_exists(tmp_path):
    src_file = tmp_path / "source.txt"
    dst_file = tmp_path / "dest.txt"
    src_file.write_text("original")
    dst_file.write_text("should block")
    session = make_mock_session(str(tmp_path))
    args = {"from_path": str(src_file), "to_path": str(dst_file)}
    tool = MoveFileOrDirTool.init()
    result = asyncio.run(tool._execute(session, args))
    assert "already exists" in result.for_llm or "already exists" in result.for_human

def test_mv_directory_success(tmp_path):
    src_dir = tmp_path / "mydir"
    src_dir.mkdir()
    (src_dir / "afile.txt").write_text("dir content")
    dst_dir = tmp_path / "targetdir"
    session = make_mock_session(str(tmp_path))
    args = {"from_path": str(src_dir), "to_path": str(dst_dir)}
    tool = MoveFileOrDirTool.init()
    result = asyncio.run(tool._execute(session, args))
    assert isinstance(result, AgentToolReturn)
    assert "successfully" in result.for_llm
    assert not src_dir.exists() and dst_dir.exists()
    assert (dst_dir / "afile.txt").read_text() == "dir content"
