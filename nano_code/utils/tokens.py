import tiktoken
from openai.types.chat import ChatCompletionMessage

TOKENIZER = tiktoken.encoding_for_model("gpt-4")


def count_tokens(text: str) -> int:
    return len(TOKENIZER.encode(text))


def truncate_text(text: str, max_tokens: int) -> str:
    tokens = TOKENIZER.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return TOKENIZER.decode(tokens[:max_tokens]) + " ...[truncated]"


def count_message(message: dict | ChatCompletionMessage) -> int:
    return count_tokens(str(message))


def truncate_messages(messages: list[dict], max_tokens: int) -> list[dict]:
    total_tokens = 0
    saved_messages = []
    for message in messages[::-1]:
        total_tokens += count_message(message)
        if total_tokens > max_tokens:
            break
        saved_messages.append(message)
    return saved_messages[::-1]
