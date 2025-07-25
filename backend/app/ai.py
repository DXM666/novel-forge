from typing import Dict, Any, List, Optional
import logging

from .memory import memory_store, element_store
from .context_manager import get_context_for_generation
from .model_infer import model_inference
from .novel_flow import run_novel_flow

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_text(memory_id: str, user_prompt: str) -> str:
    """
    生成文本：先存储输入，再获取上下文，然后调用统一推理接口。
    """
    memory_store.add(memory_id, user_prompt)
    full_context = get_context_for_generation(memory_id, user_prompt)
    result = model_inference(user_prompt, full_context)
    memory_store.add(memory_id, result)
    return result


def generate_outline(novel_id: str, style: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    生成小说大纲
    
    参数:
        novel_id: 小说ID
        style: 可选的风格信息
    
    返回:
        生成结果，包含大纲信息
    """
    kwargs = {}
    if style:
        kwargs["style"] = style
    
    return run_novel_flow(novel_id, "outline", **kwargs)


def generate_chapter(novel_id: str, chapter_id: str, style: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    生成章节内容
    
    参数:
        novel_id: 小说ID
        chapter_id: 章节ID
        style: 可选的风格信息
    
    返回:
        生成结果，包含章节内容
    """
    kwargs = {"chapter_id": chapter_id}
    if style:
        kwargs["style"] = style
    
    return run_novel_flow(novel_id, "chapter", **kwargs)


def polish_content(novel_id: str, chapter_id: str, content: str, style: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    优化章节内容
    
    参数:
        novel_id: 小说ID
        chapter_id: 章节ID
        content: 当前内容
        style: 可选的风格信息
    
    返回:
        生成结果，包含优化后的内容
    """
    kwargs = {"chapter_id": chapter_id, "content": content}
    if style:
        kwargs["style"] = style
    
    return run_novel_flow(novel_id, "polish", **kwargs)


def continue_content(novel_id: str, chapter_id: str, content: str) -> Dict[str, Any]:
    """
    续写章节内容
    
    参数:
        novel_id: 小说ID
        chapter_id: 章节ID
        content: 当前内容
    
    返回:
        生成结果，包含续写后的内容
    """
    kwargs = {"chapter_id": chapter_id, "content": content}
    
    return run_novel_flow(novel_id, "continue", **kwargs)


def save_novel_element(novel_id: str, element_type: str, element_id: str, data: Dict[str, Any]) -> bool:
    """
    保存小说元素（角色、地点、物品等）
    
    参数:
        novel_id: 小说ID
        element_type: 元素类型（character, location, item等）
        element_id: 元素ID
        data: 元素数据
    
    返回:
        是否保存成功
    """
    return element_store.save_element(novel_id, element_type, element_id, data)


def get_novel_element(novel_id: str, element_type: str, element_id: str) -> Optional[Dict[str, Any]]:
    """
    获取小说元素
    
    参数:
        novel_id: 小说ID
        element_type: 元素类型
        element_id: 元素ID
    
    返回:
        元素数据，如果不存在则返回None
    """
    return element_store.get_element(novel_id, element_type, element_id)


def get_novel_elements_by_type(novel_id: str, element_type: str) -> List[Dict[str, Any]]:
    """
    获取指定类型的所有小说元素
    
    参数:
        novel_id: 小说ID
        element_type: 元素类型
    
    返回:
        元素列表
    """
    return element_store.get_elements_by_type(novel_id, element_type)


def get_novel_data(novel_id: str) -> Dict[str, Any]:
    """
    获取小说的所有数据
    
    参数:
        novel_id: 小说ID
    
    返回:
        小说数据，包含角色、地点、物品、大纲、章节等
    """
    return element_store.get_novel_data(novel_id)
