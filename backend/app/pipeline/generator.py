from typing import Dict, Any
import logging
from app.config import settings
from app.model_infer import model_inference
from openai import OpenAI


def call_openai_api(prompt: str, context: str) -> str:
    try:
        # 兼容 openai>=1.0.0 新版 API，显式传递 api_key
        client = OpenAI(base_url='https://ms-fc-b1d7c8af-1a6d.api-inference.modelscope.cn/v1', 
                        api_key=settings.openai_api_key)
        messages = [
            {"role": "system", "content": "你是一个中文小说写作助手，请根据上下文和风格要求生成高质量中文小说内容。"},
            {"role": "user", "content": f"【背景/上下文】\n{context}\n【写作要求】\n{prompt}"}
        ]
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.85,
            max_tokens=512,
            top_p=0.95,
            frequency_penalty=0.2,
            presence_penalty=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI API 调用失败: {e}")
        return f"[错误] OpenAI API 调用失败: {e}"


def paragraph_generator(data: Dict[str, Any], context: str) -> str:
    """
    核心段落生成器：根据历史上下文、用户输入、风格向量等生成段落。
    根据 settings.mode 自动切换推理方式。
    """
    prompt = data.get("prompt") or data.get("raw") or "请生成一段符合设定的小说正文。"
    return model_inference(prompt, context)


def dialogue_generator(data: Dict[str, Any], context: str) -> str:
    """
    对话生成器：专注于人物对话。
    根据 settings.mode 自动切换推理方式。
    """
    prompt = data.get("prompt") or data.get("raw") or "请生成一段符合设定的人物对话。"
    return model_inference(prompt, context)


def scene_generator(data: Dict[str, Any], context: str) -> str:
    """
    场景描述生成器：环境描写、动作细节等。
    根据 settings.mode 自动切换推理方式。
    """
    prompt = data.get("prompt") or data.get("raw") or "请生成一段环境或动作描写。"
    return model_inference(prompt, context)
