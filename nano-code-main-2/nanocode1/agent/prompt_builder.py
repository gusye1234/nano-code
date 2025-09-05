from typing import List
from ..core.session import Session
from ..models.dissertation_plan import DissertationPlan
from ..prompts import SYSTEM_PROMPT
from .todo_helpers import get_todo_status


def build_user_prompt(plan: DissertationPlan) -> str:
    """
    构建user prompt
    
    Args:
        plan: 任务计划对象
        
    Returns:
        str: 格式化的用户提示词
    """
    prompt_parts = []
    
    # 总体要求部分
    if plan.experimental_requirements.overall_requirements:
        prompt_parts.extend([
            "### 总体要求",
            plan.experimental_requirements.overall_requirements,
            ""
        ])
    
    # 代码仓库分析部分
    if plan.experimental_requirements.code_repository_review:
        repo = plan.experimental_requirements.code_repository_review
        prompt_parts.extend([
            "### 代码仓库分析",
            f"- 仓库地址：{repo.url}",
            f"- 描述：{repo.description}",
            f"- 分析重点：{', '.join(repo.analysis_focus)}",
            ""
        ])
    
    # 实验任务部分
    if plan.experimental_requirements.reproduction_tasks:
        prompt_parts.append("### 需要完成的实验任务")
        for i, task in enumerate(plan.experimental_requirements.reproduction_tasks, 1):
            prompt_parts.extend([
                f"{i}. **{task.phase}**",
                f"   - 目标：{task.target}",
                f"   - 方法：{task.methodology}",
                ""
            ])
    
    # 评估要求
    if plan.experimental_requirements.critical_evaluation:
        eval_req = plan.experimental_requirements.critical_evaluation
        prompt_parts.extend([
            "### 批判性评估要求",
            f"- 失败案例研究：{eval_req.failure_case_study}",
            f"- 改进方向：{', '.join(eval_req.improvement_directions)}",
            ""
        ])
    
    # 相关资源
    if plan.urls:
        prompt_parts.append("### 相关资源")
        for url_info in plan.urls:
            prompt_parts.append(f"- {url_info.url}: {url_info.description}")
        prompt_parts.append("")

    # 外部搜索资料补充（仅当存在非空 response 时注入）
    try:
        comms = getattr(plan, "agent_communicate", None)
        if comms:
            enriched_lines: List[str] = []
            count = 0
            for comm in comms:
                resp = getattr(comm, "response", None)
                if resp and isinstance(resp, str) and resp.strip():
                    count += 1
                    # 控制长度，避免提示过长
                    resp_snippet = resp.strip()
                    if len(resp_snippet) > 3000:
                        resp_snippet = resp_snippet[:3000] + "…"
                    req_snippet = getattr(comm, "request", "")
                    if req_snippet and len(req_snippet) > 3000:
                        req_snippet = req_snippet[:3000] + "…"
                    enriched_lines.append(f"- 资料 {count}（对应需求：{req_snippet}）\n  {resp_snippet}")
                    if count >= 5:
                        break
            if enriched_lines:
                prompt_parts.append("### 外部搜索资料补充（用于提高完成质量与准确性）不允许使用没有提供的材料 只能使用提供的材料")
                prompt_parts.extend(enriched_lines)
                prompt_parts.append("")
    except Exception:
        pass
    
    return "\n".join(prompt_parts)


def format_memories(session: Session) -> str:
    """
    获取memory 暂时没有设置记录上下文记忆的文件
    
    Args:
        session: 会话对象
        
    Returns:
        str: 格式化的记忆信息文本
    """
    code_memories = session.get_memory()
    if code_memories:
        return f"Below are some working memories:\n{code_memories}"
    else:
        return ""


def build_system_prompt(session: Session, system_prompt_template: str = None) -> str:
    """
    构建system prompt
    
    Args:
        session: 会话对象
        system_prompt_template: 系统提示词模板，默认使用SYSTEM_PROMPT
        
    Returns:
        str: 格式化的系统提示词
    """
    if system_prompt_template is None:
        system_prompt_template = SYSTEM_PROMPT
        
    return system_prompt_template.format(
        working_dir=session.working_dir,
        todo_status=get_todo_status(session),
        memories=format_memories(session)
    )


def build_reminder_message(incomplete_todos: str) -> str:
    """
    构建TODO reminder
    
    Args:
        incomplete_todos: 未完成的TODO项目文本
        
    Returns:
        str: 格式化的提醒消息
    """
    return f"""Your TODO list is not yet complete. You cannot finish until all items are completed.

Incomplete items:
{incomplete_todos}

Please continue using tools to complete these remaining tasks. Use update_todo_status to mark items as completed when done."""