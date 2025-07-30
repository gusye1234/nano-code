import os
import asyncio
import json
from rich import console
from rich.prompt import Prompt
from rich.console import Console
from rich.markdown import Markdown as M
from rich.panel import Panel
from .core.session import Session
from .llm import llm_complete
from .agent_tool.tools import OS_TOOLS, UTIL_TOOLS, PYTHON_TOOLS
from .utils.logger import AIConsoleLogger


async def agent_loop(session: Session, CONSOLE: Console):
    # 合并所有工具注册表
    ALL_TOOLS = OS_TOOLS.merge(UTIL_TOOLS).merge(PYTHON_TOOLS)
    
    code_memories = session.get_memory()
    memories = (
        f"""Below are some working memories:
{code_memories}"""
        or ""
    )
    messages = []
    wait_user = True
    
    try:
        while True:
            if wait_user:
                try:
                    user_input = Prompt.ask("User")
                except KeyboardInterrupt:
                    CONSOLE.print("\n👋 用户中断，程序退出")
                    break
                    
                if user_input.strip() == "":
                    continue
                if user_input.strip().lower() == "exit":
                    CONSOLE.print("👋 退出程序")
                    break
                messages.append(
                    {
                        "role": "user",
                        "content": user_input,
                    }
                )
                CONSOLE.rule()
                
            r = await llm_complete(
                session,
                session.working_env.llm_main_model,
                messages,
                system_prompt=f"""You are an autonomous AI assistant designed to complete tasks using tools.
Your primary goal is to achieve the user's objective by planning and executing a series of tool calls.
Your current working directory is {session.working_dir}.

There are few rules:
- Always use absolute path.
- Line number is 1-based.
- Act autonomously. Formulate a plan and execute it without asking for my approval or for more details.
- If a step in your plan fails, analyze the error, revise the plan, and retry.
- Always examine if you have accomplished the tasks before you stop, if not, continue to try. If yes, report to me with your recap.
- Always tell me your brief plan before you call tools, but don't wait for my approval.
- The files you read before maybe updated, make sure you read the latest version before you edit them.
{memories}
""",
                tools=ALL_TOOLS.get_schemas(),
            )
            response = r.choices[0]
            if response.finish_reason == "tool_calls":
                wait_user = False
                if response.message.content is not None:
                    CONSOLE.print(Panel(M(response.message.content), title="Assistant"))
                messages.append(response.message.model_dump())
                tool_calls = [
                    t
                    for t in response.message.tool_calls
                    if ALL_TOOLS.has_tool(t.function.name)
                ]
                
                for t in tool_calls:
                    CONSOLE.print(f"🔧 [bold blue]调用工具:[/bold blue] {t.function.name}")
                    try:
                        args = json.loads(t.function.arguments)
                        CONSOLE.print(f"📝 [bold green]参数:[/bold green] {json.dumps(args, indent=2, ensure_ascii=False)}")
                    except json.JSONDecodeError:
                        CONSOLE.print(f"📝 [bold yellow]参数 (原始):[/bold yellow] {t.function.arguments}")
                    CONSOLE.print("─" * 50)
                
                tasks = [
                    ALL_TOOLS.execute(
                        session, t.function.name, json.loads(t.function.arguments)
                    )
                    for t in tool_calls
                ]
             
                results = await asyncio.gather(*tasks)
                for t, r in zip(tool_calls, results):
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": t.id,
                            "content": r.for_llm,
                        }
                    )
                continue
                
            CONSOLE.print(Panel(M(response.message.content), title="Assistant"))
            messages.append(response.message.model_dump())
            wait_user = True
    except KeyboardInterrupt:
        CONSOLE.print("\n👋 用户中断，程序退出")


async def weolcome_info():
    banner = """
🔒 ================== NANO-CODE =================== 🔒

✅ Agent在沙盒环境中启用
✅ Agent只能访问 /workspace 目录中的文件
✅ 所有操作都被限制在当前工作区内

📁 工作目录: /workspace
💡 输入 'exit' 退出，输入任务开始协作！

========================================================

"""
    return banner

async def main_loop():
    try:
        CONSOLE = Console()
        CONSOLE.print(weolcome_info())
        
        session = Session(working_dir=os.getcwd(), logger=AIConsoleLogger(CONSOLE))
        await agent_loop(session, CONSOLE)
    except KeyboardInterrupt:
        CONSOLE.print("\n👋 用户中断，程序退出")
    finally:
        session.save_checkpoints()


def main():
    asyncio.run(main_loop())


if __name__ == "__main__":
    main()