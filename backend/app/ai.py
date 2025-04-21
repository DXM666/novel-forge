from .config import settings
from .memory import memory_store

from .context_manager import get_context_for_generation

# 如果使用 OpenAI API
try:
    import openai
    openai.api_key = settings.openai_api_key
except ImportError:
    openai = None

from .config import settings
from .memory import memory_store
from .context_manager import get_context_for_generation
from app.model_infer import model_inference

def generate_text(memory_id: str, user_prompt: str) -> str:
    """
    生成文本：先存储输入，再获取上下文，然后调用统一推理接口。
    """
    memory_store.add(memory_id, user_prompt)
    full_context = get_context_for_generation(memory_id, user_prompt)
    result = model_inference(user_prompt, full_context)
    memory_store.add(memory_id, result)
    return result
