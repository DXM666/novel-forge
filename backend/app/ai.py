import os
from typing import Optional
from config import settings
from memory import memory_store

# 如果使用 OpenAI API
try:
    import openai
    openai.api_key = settings.openai_api_key
except ImportError:
    openai = None

# 本地模型调用占位
def local_model_inference(prompt: str) -> str:
    # TODO: 使用 llama-cpp-python 或其他库进行本地推理
    return "[local model stub response for prompt: {}]".format(prompt[:50])


def generate_text(memory_id: str, user_prompt: str) -> str:
    # 获取历史上下文
    history = memory_store.get(memory_id)
    full_prompt = history + "\n" + user_prompt

    if settings.use_openai and openai:
        response = openai.ChatCompletion.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for novel writing."},
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.7,
        )
        text = response.choices[0].message.content
    else:
        # 本地模型推理
        text = local_model_inference(full_prompt)

    # 存储到记忆
    memory_store.add(memory_id, text)
    return text
