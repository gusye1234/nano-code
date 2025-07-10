from openai import AsyncOpenAI
from ..core.session import Session

_global_openai_async_clients = {}


def get_openai_async_client_instance(session: Session) -> AsyncOpenAI:
    global _global_openai_async_clients
    if _global_openai_async_clients.get(session.session_id) is None:
        _global_openai_async_clients[session.session_id] = AsyncOpenAI(
            base_url=session.working_env.llm_base_url,
            api_key=session.working_env.llm_api_key,
            default_query=session.working_env.llm_default_query,
            default_headers=session.working_env.llm_default_header,
        )
    return _global_openai_async_clients[session.session_id]
