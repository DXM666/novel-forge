from typing import Dict, Any


def intent_recognition(user_prompt: str) -> Dict[str, Any]:
    """
    识别用户意图：生成段落、对话、场景、新章节等。
    使用 NLU 模型（如 BERT）或规则匹配。
    """
    # TODO: 实现意图识别逻辑
    # 示例：简单规则匹配
    if "开始新章节" in user_prompt or user_prompt.lower().startswith("chapter"):
        intent = "start_chapter"
        chunk_type = "chapter"
    elif "场景：" in user_prompt or user_prompt.lower().startswith("scene"):
        intent = "generate_scene"
        chunk_type = "scene"
    elif '"' in user_prompt:
        intent = "generate_dialogue"
        chunk_type = "dialogue"
    else:
        intent = "generate_paragraph"
        chunk_type = "paragraph"
    return {"intent": intent, "chunk_type": chunk_type}


def outline_generator(user_prompt: str) -> Dict[str, Any]:
    """
    根据用户输入生成故事大纲。
    返回示例：{'outline': ['第一章：序幕', '第二章：冲突']}
    """
    # TODO: 用 GPT 接口实现三层大纲生成
    return {'outline': []}


def style_embedding(user_prompt: str) -> Dict[str, Any]:
    """
    从用户输入或配置中获取/生成风格向量/描述。
    可以使用预训练模型提取或匹配预设风格。
    """
    # TODO: 实现真正的风格提取或匹配逻辑
    # 示例：基于关键词的简单模拟
    if "金庸" in user_prompt:
        return {"name": "金庸", "description": "模仿金庸武侠小说风格", "vector": [0.1, 0.9, 0.2]} 
    elif "科幻" in user_prompt:
        return {"name": "硬科幻", "description": "技术细节丰富，逻辑严谨", "vector": [0.8, 0.2, 0.7]}
    else:
        return {"name": "默认", "description": "通用写作风格", "vector": [0.5, 0.5, 0.5]}


def parse_input(user_prompt: str) -> Dict[str, Any]:
    """
    综合调用意图识别、大纲生成和风格嵌入，输出统一的数据结构。
    """
    intent_data = intent_recognition(user_prompt)
    intent = intent_data.get("intent", "unknown")
    chunk_type = intent_data.get("chunk_type", "paragraph")

    outline = outline_generator(user_prompt)

    style_info = style_embedding(user_prompt) 

    parsed_data = {
        "user_prompt": user_prompt,
        "intent": intent,
        "chunk_type": chunk_type,
        "outline": outline,
        "style_vector": style_info, 
    }
    return parsed_data
