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
