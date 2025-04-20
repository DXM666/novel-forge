from .config import settings
from .memory import memory_store
from .pipeline.workflow import run_pipeline
from .context_manager import get_context_for_generation

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
    # 先存储用户输入到记忆
    memory_store.add(memory_id, user_prompt)
    # 1. 获取包含历史和当前提示的完整上下文
    full_context = get_context_for_generation(memory_id, user_prompt)
    # 2. 使用 pipeline 生成文本，传入用户提示和完整上下文
    # 注意：run_pipeline 签名需要更新
    result = run_pipeline(user_prompt, full_context)
    # 将 AI 生成的内容也存储
    memory_store.add(memory_id, result)
    return result
