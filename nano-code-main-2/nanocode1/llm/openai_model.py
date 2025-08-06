import asyncio
from openai.types.chat import ChatCompletion
from .clients import get_openai_async_client_instance
from ..core.session import Session
from ..core.cost import LLMCheckpoint, LLMUsage


async def openai_complete(
    session: Session,
    model: str,
    messages: list[dict] = [],
    system_prompt: str = None,
    tools: list[dict] = [],
    **kwargs,
) -> ChatCompletion:

    openai_async_client = get_openai_async_client_instance(session)
    if system_prompt:
        messages.insert(0, {"role": "system", "content": system_prompt})

    # UTF-8错误检查和清理
    try:
        from ..utils.utf8_debugger import debug_utf8_error_simple, clean_utf8_data
        
        # 检查并报告UTF-8错误
        debug_utf8_error_simple(messages, "API_messages")
        if system_prompt:
            debug_utf8_error_simple(system_prompt, "system_prompt")
        if tools:
            debug_utf8_error_simple(tools, "tools")
        
        # 清理UTF-8问题
        messages = clean_utf8_data(messages)
        if system_prompt:
            system_prompt = clean_utf8_data(system_prompt)
        if tools:
            tools = clean_utf8_data(tools)
            
    except Exception as e:
        print(f"UTF-8处理出错: {e}")
        pass  # 调试失败不影响主流程
    
    _start = asyncio.get_event_loop().time()
    response: ChatCompletion = await openai_async_client.chat.completions.create(
        model=model,
        messages=messages,
        timeout=120,
        tools=tools,
        **kwargs,
    )
    _finish = asyncio.get_event_loop().time()

    session.update_llm_checkpoint(
        LLMCheckpoint(
            messages=messages,
            response={"openai": response.choices[0].model_dump()},
            finish_response_time=_finish - _start,
            usage=LLMUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            ),
        )
    )
    return response
