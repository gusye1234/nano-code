import json
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown as M


def print_tool_call(console: Console, name: str, args_raw_or_dict):
    """
    统一打印工具调用信息
    
    Args:
        console: Rich控制台对象
        name: 工具名称
        args_raw_or_dict: 工具参数（字典或JSON字符串）
    """
    console.print(f"🔧 [bold blue]调用工具:[/bold blue] {name}")
    try:
        if isinstance(args_raw_or_dict, dict):
            args = args_raw_or_dict
        else:
            args = json.loads(args_raw_or_dict)
        console.print(f"📝 [bold green]参数:[/bold green] {json.dumps(args, indent=2, ensure_ascii=False)}")
    except json.JSONDecodeError:
        console.print(f"📝 [bold yellow]参数 (原始):[/bold yellow] {args_raw_or_dict}")
    console.print("─" * 50)


def print_panel(console: Console, text: str, title: str):
    """
    统一打印面板
    
    Args:
        console: Rich控制台对象
        text: 面板内容文本
        title: 面板标题
    """
    # 转义语法 防止markdown语法错误
    safe_content = text.replace('[', '\\[').replace(']', '\\]')
    console.print(Panel(M(safe_content), title=title))


def print_stage(console: Console, iteration: int, max_iterations: int):
    """
    打印执行阶段信息
    
    Args:
        console: Rich控制台对象
        iteration: 当前迭代次数
        max_iterations: 最大迭代次数
    """
    console.print(f"🔄 执行轮次 {iteration}/{max_iterations}")


def print_progress_warning(console: Console, no_progress_count: int):
    """
    打印无进展信息
    
    Args:
        console: Rich控制台对象
        no_progress_count: 无进展计数
    """
    console.print(f"⚠️ 检测到无进展，计数: {no_progress_count}/3")


def print_force_stop(console: Console):
    """
    打印强制停止信息
    
    Args:
        console: Rich控制台对象
    """
    console.print("🛑 检测到连续无进展，强制停止循环")


def print_todo_completion(console: Console):
    """
    打印TODO完成信息
    
    Args:
        console: Rich控制台对象
    """
    console.print("✅ TODO完成，无需继续执行")


def print_summary(console: Console, result_dict: dict, execution_log_length: int):
    """
    打印执行结果总结
    
    Args:
        console: Rich对象
        result_dict: 任务执行结果字典
        execution_log_length: 执行日志长度
    """
    console.print(Panel(
        f"状态: {result_dict['status']}\n"
        f"执行阶段: {result_dict.get('phase', 'unknown')}\n"
        f"使用轮次: {result_dict.get('iteration', 0)}\n"
        f"执行步骤: {execution_log_length} 个",
        title="📊 任务执行摘要",
        border_style="green" if result_dict['status'] == 'completed' else "yellow"
    ))


def print_phase_start(console: Console, phase_name: str):
    """
    打印阶段开始信息
    
    Args:
        console: Rich对象
        phase_name: 阶段名称
    """
    console.print(f"🚀 开始执行阶段: {phase_name}")


def print_phase_complete(console: Console, phase_name: str):
    """
    打印阶段完成信息
    
    Args:
        console: Rich对象
        phase_name: 阶段名称
    """
    console.print(f"✅ {phase_name} 阶段完成")


def print_agent_start(console: Console):
    """
    打印Agent开始执行信息
    
    Args:
        console: Rich对象
    """
    console.print("🚀 Agent开始执行任务...")