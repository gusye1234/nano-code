import pytest
import sys
import types
import asyncio

# Dynamically import AddTasksTool and todos global for direct reference
module_path = "nano_code.agent_tool.util_tool.add_tasks"
add_tasks_module = __import__(module_path, fromlist=["AddTasksTool", "todos"])
AddTasksTool = getattr(add_tasks_module, "AddTasksTool")
todos = getattr(add_tasks_module, "todos")

class DummySession:
    def path_within_root(self, _):
        return True
    @property
    def working_dir(self):
        return "/"

def run_async(func, *args, **kwargs):
    return asyncio.get_event_loop().run_until_complete(func(*args, **kwargs))

@pytest.fixture(autouse=True)
def clear_todos():
    todos.clear()
    yield
    todos.clear()

def test_add_single_task():
    tool = AddTasksTool.init()
    session = DummySession()
    md = "- [ ] Buy milk"
    result = run_async(tool._execute, session, {"markdown": md})
    assert "Added 1 tasks" in result.for_human
    assert todos == ["Buy milk"]

def test_add_multiple_tasks():
    tool = AddTasksTool.init()
    session = DummySession()
    md = """
- [ ] Buy milk
- [ ] Walk the dog
- [ ] Write code
"""
    result = run_async(tool._execute, session, {"markdown": md})
    assert len(todos) == 3
    assert todos == ["Buy milk", "Walk the dog", "Write code"]

def test_ignore_invalid_lines():
    tool = AddTasksTool.init()
    session = DummySession()
    md = """
[ ] Not a valid item
- [x] Completed task
- [] Almost there
- [ ] Valid task
This is just a sentence.
    """
    result = run_async(tool._execute, session, {"markdown": md})
    assert len(todos) == 1
    assert todos[0] == "Valid task"


def test_empty_and_duplicate_lines():
    tool = AddTasksTool.init()
    session = DummySession()
    md = """

- [ ] Task A
- [ ] Task A
- [ ] Task B


- [ ] Task B
"""
    run_async(tool._execute, session, {"markdown": md})
    # Duplicates are allowed; this tests parsing robustness not deduplication
    assert todos == ["Task A", "Task A", "Task B", "Task B"]


def test_no_valid_tasks():
    tool = AddTasksTool.init()
    session = DummySession()
    md = "- [x] Done\nJust a line\n- []*\n"
    result = run_async(tool._execute, session, {"markdown": md})
    assert todos == []
    assert "Added 0 tasks" in result.for_llm
