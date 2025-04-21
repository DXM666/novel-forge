import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.context_manager import get_context_for_generation, MAX_CONTEXT_TOKENS
from app.memory import memory_store

def test_context_concat_and_truncate():
    memory_id = "test_ctx"
    long_history = "历史内容。" * 1000
    user_prompt = "用户新输入。"
    memory_store._data[memory_id] = long_history
    context = get_context_for_generation(memory_id, user_prompt)
    # 结果应该以 user_prompt 结尾
    assert context.endswith(user_prompt)
    # 长度不超过最大 token 限制
    assert len(context) <= MAX_CONTEXT_TOKENS * 10  # 近似判断
