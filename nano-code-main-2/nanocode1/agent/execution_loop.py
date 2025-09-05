"""自主执行循环模块

该模块负责把原 _autonomous_execution_loop 单独托管，依赖所有上述模块。
所有逻辑都是从原 non_interactive_agent.py 中提取的执行循环逻辑。
"""

import asyncio
import json
from typing import List, Dict, Any
from pathlib import Path
from ..core.session import Session
from ..llm import llm_complete
from . import tracing
from . import todo_helpers
from . import prompt_builder
from . import artifacts
from . import content_analyzer


class ExecutionHelpers:
    """
    执行循环辅助工具容器
    
    封装所有执行循环需要的辅助函数引用，避免参数传递过多
    """
    
    def __init__(self, session: Session, console):
        self.session = session
        self.console = console
    
    # TODO相关辅助方法
    def is_todo_complete(self) -> bool:
        return todo_helpers.is_complete(self.session)
    
    def get_incomplete_todos(self) -> str:
        return todo_helpers.get_incomplete_lines(self.session)
    
    # 提示词构建辅助方法
    def build_system_prompt(self, system_prompt_template: str) -> str:
        return prompt_builder.build_system_prompt(self.session, system_prompt_template)
    
    def build_reminder_message(self, incomplete_todos: str) -> str:
        return prompt_builder.build_reminder_message(incomplete_todos)
    
    # format_memories 已移除，现在由 prompt_builder.build_system_prompt 统一处理
    
    # 跟踪输出辅助方法
    def print_stage(self, iteration: int, max_iterations: int):
        tracing.print_stage(self.console, iteration, max_iterations)
    
    def print_progress_warning(self, no_progress_count: int):
        tracing.print_progress_warning(self.console, no_progress_count)
    
    def print_force_stop(self):
        tracing.print_force_stop(self.console)
    
    def print_todo_completion(self):
        tracing.print_todo_completion(self.console)
    
    def print_panel(self, text: str, title: str):
        tracing.print_panel(self.console, text, title)
    
    def print_tool_call(self, name: str, args_raw_or_dict):
        tracing.print_tool_call(self.console, name, args_raw_or_dict)
    
    # 内容分析辅助方法
    async def analyze_generated_content(self, file_path: str, content: str, system_prompt: str = None) -> str:
        return await content_analyzer.analyze_generated_content(self.session, file_path, content, system_prompt)


async def run_loop(
    session: Session,
    all_tools,
    messages: List[dict],
    system_prompt: str,
    console,
    max_iterations: int = 80
) -> Dict[str, Any]:
    """
    执行循环
    
    Args:
        session: 会话对象
        all_tools: 工具集合
        messages: 消息历史
        system_prompt: 系统提示词
        console: 控制台对象
        max_iterations: 最大迭代次数
        
    Returns:
        Dict[str, Any]: 任务执行结果，包含状态、最终消息、迭代次数和执行日志
    """
    iteration = 0
    last_assistant_message = ""
    no_progress_count = 0  # 无进展计数器
    execution_log = []
    
    # 创建辅助工具容器
    helpers = ExecutionHelpers(session, console)
    
    
    while iteration < max_iterations:
        iteration += 1
        helpers.print_stage(iteration, max_iterations)
        
        # 调用LLM - 使用统一的系统提示词构建
        formatted_system_prompt = prompt_builder.build_system_prompt(session, system_prompt)
        response = await llm_complete(
            session,
            session.working_env.llm_main_model,
            messages,
            system_prompt=formatted_system_prompt,
            tools=all_tools.get_schemas(),
        )
        
        choice = response.choices[0]
        
        if choice.finish_reason != "tool_calls":
            # 更新最后的助手消息
            current_message = choice.message.content or ""
            
            # 检查是否有进展（消息内容是否发生变化）
            if current_message == last_assistant_message:
                no_progress_count += 1
                helpers.print_progress_warning(no_progress_count)
            else:
                no_progress_count = 0
                last_assistant_message = current_message
            
            # 无进展停止条件检查
            if no_progress_count >= 3:
                helpers.print_force_stop()
                return {
                    "status": "stopped_no_progress",
                    "final_message": f"任务因无进展而停止。最后消息: {current_message}",
                    "iteration": iteration,
                    "execution_log": execution_log
                }
            
            # 检查TODO完成状态 - 只在非工具调用分支进行完成判断
            todo_complete = helpers.is_todo_complete()
            
            if todo_complete:
                # 任务完成：TODO全部完成 + LLM给出非工具调用回复
                return {
                    "status": "completed",
                    "final_message": current_message,
                    "iteration": iteration,
                    "execution_log": execution_log
                }
            else:
                # TODO未完成，继续执行
                incomplete_items = helpers.get_incomplete_todos()
                
                # 向消息历史添加提醒
                reminder = helpers.build_reminder_message(incomplete_items)
                
                messages.append({"role": "assistant", "content": current_message})
                messages.append({"role": "user", "content": reminder})
                continue
        
        # 显示AI的思考过程
        if choice.message.content:
            helpers.print_panel(choice.message.content, "Assistant")
        
        # 添加助手消息
        messages.append(choice.message.model_dump())
        
        # 执行工具调用
        tool_calls = [
            t for t in choice.message.tool_calls
            if all_tools.has_tool(t.function.name)
        ]
        
        # 工具调用信息
        for t in tool_calls:
            helpers.print_tool_call(t.function.name, t.function.arguments)
        
        # 批量执行工具
        tasks = [
            all_tools.execute(
                session, t.function.name, json.loads(t.function.arguments)
            )
            for t in tool_calls
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 添加工具结果到消息历史并分析生成的内容
        for t, r in zip(tool_calls, results):
            messages.append({
                "role": "tool",
                "tool_call_id": t.id,
                "content": r.for_llm,
            })
            
            # 创建基础执行日志
            log_entry = {
                "iteration": iteration,
                "tool": t.function.name,
                "args": json.loads(t.function.arguments),
                "result": r.for_human
            }
            
            # 如果是artifact创建工具，请求LLM对生成内容进行分析
            if artifacts.is_artifact_tool(t.function.name):
                args = log_entry.get("args", {})
                file_path = args.get("file_path", "")
                content = args.get("content", "")
                
                if file_path and content:
                    file_extension = Path(file_path).suffix.lower()
                    # 只为需要深度分析的文件类型生成LLM分析
                    if artifacts.should_analyze_for_tool(t.function.name, file_extension):
                        if file_extension in ['.py', '.csv', '.xlsx']:
                            analysis = await helpers.analyze_generated_content(file_path, content)
                            log_entry["llm_analysis"] = analysis
                        elif file_extension in ['.png', '.jpg', '.jpeg', '.svg']:
                            # PNG文件使用文件路径进行分析（不需要content）
                            analysis = await helpers.analyze_generated_content(file_path, "")
                            log_entry["llm_analysis"] = analysis
            
            execution_log.append(log_entry)
    
    # 循环正常结束（达到最大迭代次数）
    final_message = f"任务因达到最大迭代次数({max_iterations})而停止。最后消息: {last_assistant_message}"
    
    return {
        "status": "stopped_max_iterations", 
        "final_message": final_message,
        "iteration": iteration,
        "execution_log": execution_log
    }