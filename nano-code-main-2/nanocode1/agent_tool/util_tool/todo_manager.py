import json
import uuid
from typing import List, Dict, Any
from pathlib import Path
from ..base import AgentToolDefine, AgentToolReturn


class TodoItem:
    def __init__(self, id: str, description: str, required_tools: List[str], 
                 success_criteria: str, status: str = "pending"):
        self.id = id
        self.description = description
        self.required_tools = required_tools
        self.success_criteria = success_criteria
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "required_tools": self.required_tools,
            "success_criteria": self.success_criteria,
            "status": self.status
        }


class CreateTodoList(AgentToolDefine):
    @classmethod
    def init(cls) -> "CreateTodoList":
        return cls(
            name="create_todo_list",
            description="创建任务执行的TODO清单",
            parameters_schema={
                "type": "object",
                "properties": {
                    "todo_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "required_tools": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "success_criteria": {"type": "string"}
                            },
                            "required": ["description", "required_tools", "success_criteria"]
                        }
                    }
                },
                "required": ["todo_items"]
            }
        )
    
    async def _execute(self, session, arguments: dict) -> AgentToolReturn:
        try:
            todo_items_data = arguments.get("todo_items", [])
            
            todo_items = []
            for item_data in todo_items_data:
                todo_item = TodoItem(
                    id=str(uuid.uuid4())[:8],
                    description=item_data["description"],
                    required_tools=item_data["required_tools"],
                    success_criteria=item_data["success_criteria"]
                )
                todo_items.append(todo_item)
            
            session.todo_list = todo_items
            
            todo_file = Path(session.working_dir) / "agent_todo_list.json"
            with open(todo_file, 'w', encoding='utf-8') as f:
                json.dump([item.to_dict() for item in todo_items], f, 
                         ensure_ascii=False, indent=2)
            
            return AgentToolReturn(
                for_llm=f"Created TODO list with {len(todo_items)} items",
                for_human=f"✅ 创建了 {len(todo_items)} 项TODO清单"
            )
        except Exception as e:
            return AgentToolReturn(
                for_llm=f"Error creating TODO list: {str(e)}",
                for_human=f"❌ 创建TODO清单失败"
            )


class UpdateTodoStatus(AgentToolDefine):
    @classmethod
    def init(cls) -> "UpdateTodoStatus":
        return cls(
            name="update_todo_status",
            description="更新TODO项目状态",
            parameters_schema={
                "type": "object",
                "properties": {
                    "item_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]}
                },
                "required": ["item_id", "status"]
            }
        )
    
    async def _execute(self, session, arguments: dict) -> AgentToolReturn:
        try:
            item_id = arguments.get("item_id")
            new_status = arguments.get("status")
            
            if not hasattr(session, 'todo_list') or not session.todo_list:
                return AgentToolReturn(
                    for_llm="No TODO list found",
                    for_human="❌ 未找到TODO清单"
                )
            
            for item in session.todo_list:
                if item.id == item_id:
                    item.status = new_status
                    
                    # 保存更新
                    todo_file = Path(session.working_dir) / "agent_todo_list.json"
                    with open(todo_file, 'w', encoding='utf-8') as f:
                        json.dump([item.to_dict() for item in session.todo_list], f, 
                                 ensure_ascii=False, indent=2)
                    
                    return AgentToolReturn(
                        for_llm=f"Updated TODO item {item_id} to {new_status}",
                        for_human=f"✅ 更新项目 {item_id} 为 {new_status}"
                    )
            
            return AgentToolReturn(
                for_llm=f"TODO item {item_id} not found",
                for_human=f"❌ 未找到项目 {item_id}"
            )
        except Exception as e:
            return AgentToolReturn(
                for_llm=f"Error updating TODO: {str(e)}",
                for_human=f"❌ 更新失败"
            )


class GetTodoStatus(AgentToolDefine):
    @classmethod
    def init(cls) -> "GetTodoStatus":
        return cls(
            name="get_todo_status",
            description="获取TODO清单状态",
            parameters_schema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    
    async def _execute(self, session, arguments: dict) -> AgentToolReturn:
        try:
            if not hasattr(session, 'todo_list') or not session.todo_list:
                return AgentToolReturn(
                    for_llm="No TODO list exists",
                    for_human="❌ 无TODO清单"
                )
            
            total = len(session.todo_list)
            completed = sum(1 for item in session.todo_list if item.status == "completed")
            completion_rate = (completed / total) * 100 if total > 0 else 0
            
            status_lines = [f"TODO进度: {completed}/{total} ({completion_rate:.0f}%)"]
            for item in session.todo_list:
                status_icon = "✅" if item.status == "completed" else "🔄" if item.status == "in_progress" else "⏳"
                status_lines.append(f"{status_icon} [{item.id}] {item.description}")
            
            return AgentToolReturn(
                for_llm=f"TODO Status: {completed}/{total} completed ({completion_rate:.1f}%)",
                for_human="\n".join(status_lines)
            )
        except Exception as e:
            return AgentToolReturn(
                for_llm=f"Error getting status: {str(e)}",
                for_human="❌ 获取状态失败"
            )


TODO_TOOLS = [CreateTodoList, UpdateTodoStatus, GetTodoStatus]