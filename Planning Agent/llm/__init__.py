import traceback
from openai.types.chat import ChatCompletion
from .openai_model import openai_complete
from ..core.session import Session
from ..core.cost import LLMCheckpointFailed
from ..utils.tokens import truncate_messages


async def llm_complete(
    session: Session,
    model: str,
    messages: list[dict] = [],
    system_prompt: str = None,
    llm_style: str = "openai",
    tools: list[dict] = [],
    **kwargs,
) -> ChatCompletion | None:
    messages = truncate_messages(messages, session.maximum_token_window_size)
    if llm_style == "openai":
        try:
            return await openai_complete(
                session,
                model,
                messages,
                system_prompt,
                tools,
                **kwargs,
            )
        except Exception as e:
            session.log(
                f"LLM {model} failed: {e}, {traceback.format_exc()}",
                level="error",
            )
            session.running_llm_checkpoints.append(
                LLMCheckpointFailed(messages=messages, error=e)
            )
        return None
    raise ValueError(f"LLM API style {llm_style} not supported")
