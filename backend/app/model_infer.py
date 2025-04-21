from app.config import settings

# 本地模型调用（使用 langchain-ollama，仅供内部调用）
def local_model_inference(prompt: str) -> str:
    try:
        from langchain_ollama import OllamaLLM
        model = OllamaLLM(model="qwen2.5:7b")  # 可根据实际模型名称和配置调整
        return model.invoke(prompt)
    except Exception as e:
        return f"[本地模型调用失败: {e}]"


def model_inference(prompt: str, context: str) -> str:
    """
    统一AI推理入口，根据 settings.mode 调用云端API或本地模型。
    """
    if settings.mode == "api":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
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
            return f"[OpenAI API 调用失败: {e}]"
    elif settings.mode == "local":
        return local_model_inference(context + "\n" + prompt)
    else:
        return f"[不支持的AI模式: {settings.mode}]"
