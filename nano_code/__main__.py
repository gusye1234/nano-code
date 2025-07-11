import os
import asyncio
import json
from rich.prompt import Prompt
from rich.console import Console
from rich.markdown import Markdown as M
from rich.panel import Panel
from .core.session import Session
from .llm import llm_complete
from .agent_tool.tools import OS_TOOLS
from .utils.logger import AIConsoleLogger


async def agent_loop(session: Session, CONSOLE: Console):
    code_memories = session.get_memory()
    memories = (
        f"""Below are some working memories:
{code_memories}"""
        or ""
    )
    messages = []
    wait_user = True
    while True:
        if wait_user:
            user_input = Prompt.ask("User")
            if user_input.strip() == "":
                continue
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
            system_prompt=f"""You are a helpful assistant that can help with tasks using tools.
Your current working directory is {session.working_dir}.

There are few rules:
- Always use absolute path.
- Line number is 1-based.
- When writing the code of my requirements, you can stop and ask me for more details if you need.
- Always examine if you have accomplished the tasks before you stop, if not, continue to try. If yes, report to me with your recap.
- Always tell me your brief plan before you call tools, but don't wait for my approval unless you're required to do so in some specific cases.
- When your plan failed, try to fix it by yourself instead of stopping trying.
- The files you read before maybe updated, make sure you read the latest version before you edit them.
{memories}
""",
            tools=OS_TOOLS.get_schemas(),
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
                if OS_TOOLS.has_tool(t.function.name)
            ]
            tasks = [
                OS_TOOLS.execute(
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
        wait_user = True


async def main_loop():
    try:
        CONSOLE = Console()
        session = Session(working_dir=os.getcwd(), logger=AIConsoleLogger(CONSOLE))
        await agent_loop(session, CONSOLE)
    finally:
        session.save_checkpoints()


def main():
    asyncio.run(main_loop())


if __name__ == "__main__":
    main()
