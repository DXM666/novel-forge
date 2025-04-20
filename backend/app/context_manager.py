from .memory import memory_store
from .config import settings
import logging

# 假设一个最大 token 数（需要根据实际模型调整）
MAX_CONTEXT_TOKENS = 3000 # 示例值

def count_tokens(text: str) -> int:
    """粗略计算 token 数（实际应用应使用 tokenizer）"""
    return len(text.split())

def summarize_history(text: str, target_tokens: int) -> str:
    """简易历史摘要：截断或调用模型（占位）"""
    # TODO: 实现更智能的摘要，例如调用 OpenAI 或本地摘要模型
    current_tokens = count_tokens(text)
    if current_tokens <= target_tokens:
        return text
    # 简单的截断策略
    words = text.split()
    # 尝试保留结尾部分，因为结尾通常更相关
    keep_words = int(len(words) * (target_tokens / current_tokens))
    summary = "... " + " ".join(words[-keep_words:])
    logging.info(f"Summarized history from {current_tokens} to ~{count_tokens(summary)} tokens.")
    return summary

def get_context_for_generation(memory_id: str, user_prompt: str) -> str:
    """
    获取用于生成的上下文，在需要时进行摘要。
    """
    history = memory_store.get(memory_id)
    prompt_tokens = count_tokens(user_prompt)
    available_history_tokens = MAX_CONTEXT_TOKENS - prompt_tokens

    if available_history_tokens <= 0:
        # 如果用户提示本身就超长，可能需要截断提示或报错
        logging.warning("User prompt exceeds max context length.")
        # 简单处理：只使用部分提示（或者完全不给历史）
        # return user_prompt[:int(len(user_prompt) * (MAX_CONTEXT_TOKENS / prompt_tokens))]
        return user_prompt # 或者返回空历史+提示

    history_tokens = count_tokens(history)

    if history_tokens <= available_history_tokens:
        # 历史记录未超限，直接拼接
        return history + "\n" + user_prompt
    else:
        # 历史记录超限，需要摘要
        summarized_hist = summarize_history(history, available_history_tokens)
        return summarized_hist + "\n" + user_prompt
