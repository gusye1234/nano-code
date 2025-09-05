from ..core.session import Session


def get_todo_status(session: Session) -> str:
    """
    获取TODO状态文本
    
    Args:
        session: 会话对象，包含todo_list
        
    Returns:
        str: 格式化的TODO状态文本
    """
    if not hasattr(session, 'todo_list') or not session.todo_list:
        return "TODO Status: No TODO list created yet. Create one at the start!"
    
    total = len(session.todo_list)
    completed = sum(1 for item in session.todo_list if item.status == "completed")
    completion_rate = (completed / total) * 100 if total > 0 else 0
    
    status_lines = [f"TODO Progress: {completed}/{total} completed ({completion_rate:.0f}%)"]
    
    for item in session.todo_list:
        status_icon = "✅" if item.status == "completed" else "🔄" if item.status == "in_progress" else "⏳"
        status_lines.append(f"{status_icon} [{item.id}] {item.description}")
    
    return "\n".join(status_lines)


def is_complete(session: Session) -> bool:
    """
    检查TODO是否全部完成
    
    Args:
        session: 会话对象，包含todo_list
        
    Returns:
        bool: 如果所有TODO都完成则返回True，否则返回False
    """
    if not hasattr(session, 'todo_list') or not session.todo_list:
        return True  # 没有TODO列表视为完成
    
    return all(item.status == "completed" for item in session.todo_list)


def get_incomplete_lines(session: Session) -> str:
    """
    获取未完成TODO项目的描述
    
    Args:
        session: 会话对象，包含todo_list
        
    Returns:
        str: 格式化的未完成TODO项目文本
    """
    if not hasattr(session, 'todo_list') or not session.todo_list:
        return "No TODO items"
    
    incomplete = [item for item in session.todo_list if item.status != "completed"]
    if not incomplete:
        return "All TODO items completed"
    
    lines = []
    for item in incomplete:
        status_icon = "🔄" if item.status == "in_progress" else "⏳"
        lines.append(f"{status_icon} [{item.id}] {item.description}")
    
    return "\n".join(lines)


def get_completion_stats(session: Session) -> dict:
    """
    获取TODO完成统计信息
    
    辅助函数，提供详细的完成状态统计
    
    Args:
        session: 会话对象，包含todo_list
        
    Returns:
        dict: 包含完成统计的字典
    """
    if not hasattr(session, 'todo_list') or not session.todo_list:
        return {
            "total": 0,
            "completed": 0,
            "in_progress": 0,
            "pending": 0,
            "completion_rate": 100.0
        }
    
    total = len(session.todo_list)
    completed = sum(1 for item in session.todo_list if item.status == "completed")
    in_progress = sum(1 for item in session.todo_list if item.status == "in_progress")
    pending = sum(1 for item in session.todo_list if item.status == "pending")
    completion_rate = (completed / total) * 100 if total > 0 else 0
    
    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "pending": pending,
        "completion_rate": completion_rate
    }