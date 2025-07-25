"""
小说创作流程管理系统 - 基于LangGraph实现
支持多阶段流程：大纲生成、角色设计、章节创作、内容优化等
"""
import json
import logging
from typing import Dict, Any, List, TypedDict, Optional, Literal

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from .memory import element_store, graph_store, memory_store
from .config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 定义状态类型
class NovelState(TypedDict):
    """小说创作流程状态"""
    novel_id: str  # 小说ID
    current_task: str  # 当前任务
    messages: List[Dict[str, Any]]  # 消息历史
    characters: List[Dict[str, Any]]  # 角色列表
    locations: List[Dict[str, Any]]  # 地点列表
    items: List[Dict[str, Any]]  # 物品列表
    outline: Optional[Dict[str, Any]]  # 大纲
    chapter_id: Optional[str]  # 当前章节ID
    chapter_content: Optional[str]  # 当前章节内容
    style: Optional[Dict[str, Any]]  # 写作风格
    error: Optional[str]  # 错误信息

# 获取模型
def get_llm():
    """获取语言模型"""
    if settings.mode == "api":
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=0.7
        )
    else:
        # 使用本地模型
        from langchain_ollama import OllamaLLM
        return OllamaLLM(model="qwen2.5:7b")

# 节点函数
def load_novel_context(state: NovelState) -> NovelState:
    """加载小说上下文"""
    novel_id = state["novel_id"]
    logger.info(f"加载小说 {novel_id} 的上下文")
    
    try:
        # 从数据库加载小说元素
        novel_data = element_store.get_novel_data(novel_id)
        
        return {
            **state,
            "characters": novel_data["characters"] or [],
            "locations": novel_data["locations"] or [],
            "items": novel_data["items"] or [],
            "outline": novel_data["outline"],
            "current_task": "context_loaded"
        }
    except Exception as e:
        logger.error(f"加载小说上下文失败: {e}")
        return {
            **state,
            "error": f"加载小说上下文失败: {str(e)}",
            "current_task": "error"
        }

def generate_outline(state: NovelState) -> NovelState:
    """生成小说大纲"""
    novel_id = state["novel_id"]
    characters = state["characters"]
    messages = state["messages"]
    
    logger.info(f"为小说 {novel_id} 生成大纲")
    
    try:
        llm = get_llm()
        
        # 构建角色信息
        character_info = "\n".join([
            f"- {c.get('name', '未命名')}: {c.get('role', '未知角色')}" 
            for c in characters
        ])
        
        # 构建提示
        prompt = f"""
        基于以下角色信息，生成一个小说大纲：
        
        {character_info}
        
        请提供:
        1. 故事骨架（核心冲突与主要情节）
        2. 章节脉络（至少5章）
        3. 每章关键场景
        
        以JSON格式返回，结构如下:
        {{
            "skeleton": "故事骨架描述",
            "chapters": [
                {{
                    "title": "章节标题",
                    "summary": "章节概要",
                    "scenes": [
                        {{
                            "title": "场景标题",
                            "summary": "场景描述",
                            "characters": ["角色1", "角色2"],
                            "location": "场景地点"
                        }}
                    ]
                }}
            ]
        }}
        """
        
        # 构建消息
        system_message = SystemMessage(content="你是一位专业小说策划，擅长创作引人入胜的故事大纲。")
        user_message = HumanMessage(content=prompt)
        
        # 调用模型
        response = llm.invoke([system_message, user_message])
        
        # 解析响应
        try:
            outline = json.loads(response.content)
        except json.JSONDecodeError:
            # 简单解析文本
            content = response.content
            outline = {
                "skeleton": content.split("章节脉络")[0].strip(),
                "chapters": []
            }
            # 后续可添加更复杂的解析逻辑
        
        # 保存到数据库
        element_store.save_element(
            novel_id=novel_id,
            element_type="outline",
            element_id="main",
            data=outline
        )
        
        # 更新状态
        return {
            **state,
            "outline": outline,
            "current_task": "outline_generated",
            "messages": messages + [
                {"role": "system", "content": system_message.content},
                {"role": "user", "content": user_message.content},
                {"role": "assistant", "content": response.content}
            ]
        }
    except Exception as e:
        logger.error(f"生成大纲失败: {e}")
        return {
            **state,
            "error": f"生成大纲失败: {str(e)}",
            "current_task": "error"
        }

def generate_chapter(state: NovelState) -> NovelState:
    """生成章节内容"""
    novel_id = state["novel_id"]
    chapter_id = state["chapter_id"]
    outline = state["outline"]
    characters = state["characters"]
    locations = state["locations"]
    style = state["style"]
    messages = state["messages"]
    
    if not chapter_id:
        return {
            **state,
            "error": "未指定章节ID",
            "current_task": "error"
        }
    
    logger.info(f"为小说 {novel_id} 生成章节 {chapter_id}")
    
    try:
        # 找到当前章节
        current_chapter = None
        chapter_index = None
        
        if outline and "chapters" in outline:
            for i, chapter in enumerate(outline["chapters"]):
                if str(i+1) == chapter_id or chapter.get("id") == chapter_id:
                    current_chapter = chapter
                    chapter_index = i
                    break
        
        if not current_chapter:
            return {
                **state,
                "error": f"找不到章节ID: {chapter_id}",
                "current_task": "error"
            }
        
        # 构建提示
        chapter_title = current_chapter.get("title", f"第{chapter_index+1}章")
        chapter_summary = current_chapter.get("summary", "")
        
        # 提取场景信息
        scenes_info = ""
        if "scenes" in current_chapter and current_chapter["scenes"]:
            for i, scene in enumerate(current_chapter["scenes"]):
                scene_title = scene.get("title", f"场景{i+1}")
                scene_summary = scene.get("summary", "")
                scene_characters = ", ".join(scene.get("characters", []))
                scene_location = scene.get("location", "")
                
                scenes_info += f"\n场景{i+1}: {scene_title}\n"
                scenes_info += f"描述: {scene_summary}\n"
                if scene_characters:
                    scenes_info += f"角色: {scene_characters}\n"
                if scene_location:
                    scenes_info += f"地点: {scene_location}\n"
        
        # 构建角色信息
        characters_info = "\n".join([
            f"- {c.get('name', '未命名')}: {c.get('role', '未知角色')}" 
            for c in characters
        ])
        
        # 构建地点信息
        locations_info = "\n".join([
            f"- {loc.get('name', '未命名')}: {loc.get('desc', '未知地点')}" 
            for loc in locations
        ])
        
        # 构建风格信息
        style_info = ""
        if style:
            style_info = f"写作风格: {style.get('name', '默认')}\n{style.get('description', '')}"
        
        # 构建提示
        prompt = f"""
        请根据以下信息生成章节内容:
        
        章节标题: {chapter_title}
        章节概要: {chapter_summary}
        
        {scenes_info}
        
        相关角色:
        {characters_info}
        
        相关地点:
        {locations_info}
        
        {style_info}
        
        请生成一个完整、连贯的章节内容，包含丰富的描写和对话。章节应当符合整体故事大纲，
        并展现出角色的性格特点。请确保场景描述生动，对话自然流畅。
        """
        
        # 构建消息
        system_message = SystemMessage(content="你是一位专业小说家，擅长创作引人入胜的故事。")
        user_message = HumanMessage(content=prompt)
        
        # 调用模型
        llm = get_llm()
        response = llm.invoke([system_message, user_message])
        
        chapter_content = response.content
        
        # 保存到数据库
        memory_id = f"{novel_id}_chapter_{chapter_id}"
        memory_store.add(memory_id, chapter_content)
        
        # 保存章节元数据
        element_store.save_element(
            novel_id=novel_id,
            element_type="chapter",
            element_id=chapter_id,
            data={
                "id": chapter_id,
                "title": chapter_title,
                "summary": chapter_summary,
                "memory_id": memory_id,
                "updated_at": "now"  # 实际应用中使用真实时间戳
            }
        )
        
        # 更新状态
        return {
            **state,
            "chapter_content": chapter_content,
            "current_task": "chapter_generated",
            "messages": messages + [
                {"role": "system", "content": system_message.content},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response.content}
            ]
        }
    except Exception as e:
        logger.error(f"生成章节失败: {e}")
        return {
            **state,
            "error": f"生成章节失败: {str(e)}",
            "current_task": "error"
        }


def polish_content(state: NovelState) -> NovelState:
    """优化内容（提升语言质量、风格转换等）"""
    novel_id = state["novel_id"]
    chapter_id = state["chapter_id"]
    chapter_content = state["chapter_content"]
    style = state["style"]
    messages = state["messages"]
    
    if not chapter_content:
        return {
            **state,
            "error": "没有可优化的内容",
            "current_task": "error"
        }
    
    logger.info(f"优化小说 {novel_id} 章节 {chapter_id} 的内容")
    
    try:
        # 构建风格信息
        style_info = ""
        if style:
            style_info = f"目标风格: {style.get('name', '默认')}\n{style.get('description', '')}"
        
        # 构建提示
        prompt = f"""
        请优化以下小说内容，提升语言质量，使表达更加生动、优美：
        
        {style_info}
        
        原始内容:
        {chapter_content}
        
        请保持原有情节和对话不变，仅优化语言表达、描写和节奏。使文本更加引人入胜，
        更符合专业小说的写作水准。请返回完整优化后的内容。
        """
        
        # 构建消息
        system_message = SystemMessage(content="你是一位专业文学编辑，擅长优化文本质量，提升语言表达的生动性和美感。")
        user_message = HumanMessage(content=prompt)
        
        # 调用模型
        llm = get_llm()
        response = llm.invoke([system_message, user_message])
        
        polished_content = response.content
        
        # 保存到数据库
        memory_id = f"{novel_id}_chapter_{chapter_id}"
        memory_store.add(memory_id, "\n\n【优化版本】\n" + polished_content)
        
        # 更新状态
        return {
            **state,
            "chapter_content": polished_content,
            "current_task": "content_polished",
            "messages": messages + [
                {"role": "system", "content": system_message.content},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response.content}
            ]
        }
    except Exception as e:
        logger.error(f"优化内容失败: {e}")
        return {
            **state,
            "error": f"优化内容失败: {str(e)}",
            "current_task": "error"
        }


def continue_writing(state: NovelState) -> NovelState:
    """续写当前章节内容"""
    novel_id = state["novel_id"]
    chapter_id = state["chapter_id"]
    chapter_content = state["chapter_content"]
    outline = state["outline"]
    characters = state["characters"]
    messages = state["messages"]
    
    if not chapter_content:
        return {
            **state,
            "error": "没有可续写的内容",
            "current_task": "error"
        }
    
    logger.info(f"续写小说 {novel_id} 章节 {chapter_id} 的内容")
    
    try:
        # 找到当前章节
        current_chapter = None
        if outline and "chapters" in outline:
            for i, chapter in enumerate(outline["chapters"]):
                if str(i+1) == chapter_id or chapter.get("id") == chapter_id:
                    current_chapter = chapter
                    break
        
        chapter_summary = ""
        if current_chapter:
            chapter_summary = current_chapter.get("summary", "")
        
        # 构建角色信息
        characters_info = "\n".join([
            f"- {c.get('name', '未命名')}: {c.get('role', '未知角色')}" 
            for c in characters
        ])
        
        # 构建提示
        prompt = f"""
        请基于以下已有内容，续写小说章节：
        
        章节概要: {chapter_summary}
        
        相关角色:
        {characters_info}
        
        已有内容:
        {chapter_content}
        
        请自然地续写后续内容，保持风格一致性，延续已有情节发展。续写内容应当是现有内容的
        自然延伸，不要重复已有内容，直接从断点处继续。请确保人物性格和行为一致。
        """
        
        # 构建消息
        system_message = SystemMessage(content="你是一位专业小说家，擅长创作引人入胜的故事。")
        user_message = HumanMessage(content=prompt)
        
        # 调用模型
        llm = get_llm()
        response = llm.invoke([system_message, user_message])
        
        continuation = response.content
        
        # 合并内容
        new_content = chapter_content + "\n\n" + continuation
        
        # 保存到数据库
        memory_id = f"{novel_id}_chapter_{chapter_id}"
        memory_store.add(memory_id, "\n\n【续写内容】\n" + continuation)
        
        # 更新状态
        return {
            **state,
            "chapter_content": new_content,
            "current_task": "content_continued",
            "messages": messages + [
                {"role": "system", "content": system_message.content},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response.content}
            ]
        }
    except Exception as e:
        logger.error(f"续写内容失败: {e}")
        return {
            **state,
            "error": f"续写内容失败: {str(e)}",
            "current_task": "error"
        }


# 路由函数
def router(state: NovelState) -> Literal["load_novel_context", "generate_outline", "generate_chapter", "polish_content", "continue_writing", "error", "END"]:
    """根据当前状态路由到下一个节点"""
    task = state.get("current_task", "")
    error = state.get("error")
    
    # 如果有错误，直接结束
    if error:
        return "error"
    
    # 根据当前任务路由
    if task == "start":
        return "load_novel_context"
    elif task == "context_loaded":
        if not state.get("outline"):
            return "generate_outline"
        elif state.get("chapter_id"):
            return "generate_chapter"
        else:
            return END
    elif task == "outline_generated":
        if state.get("chapter_id"):
            return "generate_chapter"
        else:
            return END
    elif task == "chapter_generated":
        if state.get("polish_requested"):
            return "polish_content"
        elif state.get("continue_requested"):
            return "continue_writing"
        else:
            return END
    elif task == "content_polished" or task == "content_continued":
        return END
    
    # 默认结束
    return END


# 创建图
def create_novel_graph():
    """创建小说创作流程图"""
    # 构建图
    builder = StateGraph(NovelState)
    
    # 添加节点
    builder.add_node("load_novel_context", load_novel_context)
    builder.add_node("generate_outline", generate_outline)
    builder.add_node("generate_chapter", generate_chapter)
    builder.add_node("polish_content", polish_content)
    builder.add_node("continue_writing", continue_writing)
    builder.add_node("error", lambda x: x)  # 错误节点仅返回当前状态
    
    # 添加条件边
    builder.add_conditional_edges(
        "load_novel_context",
        router,
        {
            "generate_outline": "generate_outline",
            "generate_chapter": "generate_chapter",
            END: END,
            "error": "error"
        }
    )
    
    builder.add_conditional_edges(
        "generate_outline",
        router,
        {
            "generate_chapter": "generate_chapter",
            END: END,
            "error": "error"
        }
    )
    
    builder.add_conditional_edges(
        "generate_chapter",
        router,
        {
            "polish_content": "polish_content",
            "continue_writing": "continue_writing",
            END: END,
            "error": "error"
        }
    )
    
    builder.add_conditional_edges(
        "polish_content",
        router,
        {
            END: END,
            "error": "error"
        }
    )
    
    builder.add_conditional_edges(
        "continue_writing",
        router,
        {
            END: END,
            "error": "error"
        }
    )
    
    builder.add_edge("error", END)
    
    # 设置入口点
    builder.set_entry_point("load_novel_context")
    
    # 编译图
    return builder.compile()


# 创建小说创作图
novel_graph = create_novel_graph()


# 运行小说创作流程
def run_novel_flow(novel_id: str, task_type: str, **kwargs) -> Dict[str, Any]:
    """
    运行小说创作流程
    
    参数:
        novel_id: 小说ID
        task_type: 任务类型，如 'outline', 'chapter', 'polish', 'continue'
        **kwargs: 其他参数，如 chapter_id, style 等
    
    返回:
        流程运行结果
    """
    # 尝试恢复状态
    thread_id = f"{novel_id}_{task_type}"
    if task_type == "chapter" and "chapter_id" in kwargs:
        thread_id = f"{novel_id}_chapter_{kwargs['chapter_id']}"
    
    saved_state = graph_store.load_state(thread_id)
    
    # 初始状态
    initial_state = {
        "novel_id": novel_id,
        "current_task": "start",
        "messages": [],
        "characters": [],
        "locations": [],
        "items": [],
        "outline": None,
        "chapter_id": None,
        "chapter_content": None,
        "style": None,
        "error": None
    }
    
    # 根据任务类型设置状态
    if task_type == "outline":
        initial_state["current_task"] = "context_loaded"
    elif task_type == "chapter" and "chapter_id" in kwargs:
        initial_state["chapter_id"] = kwargs["chapter_id"]
        initial_state["current_task"] = "context_loaded"
    elif task_type == "polish" and "chapter_id" in kwargs and "content" in kwargs:
        initial_state["chapter_id"] = kwargs["chapter_id"]
        initial_state["chapter_content"] = kwargs["content"]
        initial_state["polish_requested"] = True
        initial_state["current_task"] = "chapter_generated"
    elif task_type == "continue" and "chapter_id" in kwargs and "content" in kwargs:
        initial_state["chapter_id"] = kwargs["chapter_id"]
        initial_state["chapter_content"] = kwargs["content"]
        initial_state["continue_requested"] = True
        initial_state["current_task"] = "chapter_generated"
    
    # 如果有风格参数
    if "style" in kwargs:
        initial_state["style"] = kwargs["style"]
    
    # 如果有保存的状态，合并状态
    if saved_state:
        # 仅合并非任务相关的状态
        for key in ["characters", "locations", "items", "outline", "messages"]:
            if key in saved_state and saved_state[key]:
                initial_state[key] = saved_state[key]
    
    # 运行图
    try:
        result = novel_graph.invoke(initial_state)
        
        # 保存状态
        graph_store.save_state(thread_id, result)
        
        return {
            "success": True,
            "novel_id": novel_id,
            "task_type": task_type,
            "result": {
                "outline": result.get("outline"),
                "chapter_content": result.get("chapter_content"),
                "error": result.get("error"),
                "current_task": result.get("current_task")
            }
        }
    except Exception as e:
        logger.error(f"运行小说流程失败: {e}")
        return {
            "success": False,
            "novel_id": novel_id,
            "task_type": task_type,
            "error": str(e)
        }
