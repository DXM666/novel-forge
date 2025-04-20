import logging
from typing import List, Dict, Any
from .parser import parse_input
from .generator import paragraph_generator, dialogue_generator, scene_generator
from .consistency import check_character_consistency, check_plot_consistency, update_knowledge_graph
from .postprocessing import polish_text, style_transfer_text, diversity_augmentation, analyze_emotion_curve
from .parallel_inference import parallel_generate, split_into_chunks


def run_pipeline(user_prompt: str, full_context: str) -> str:
    """
    主流程：
    1. 解析用户输入（主题、大纲、风格等）
    2. 生成内容（段落、对话、场景）
    3. 一致性检查和后处理
    """
    # 解析输入
    data = parse_input(user_prompt)
    intent = data.get("intent", "unknown")
    chunk_type = data.get("chunk_type", "paragraph")

    logging.info(f"处理请求 - 意图: {intent}, 块类型: {chunk_type}")
    
    # 根据块类型决定是否使用并行生成
    if chunk_type == "chapter":
        # 章节级别的生成，尝试并行处理
        return run_parallel_pipeline(data, user_prompt, full_context)
    else:
        # 普通生成流程
        return run_sequential_pipeline(data, user_prompt, full_context)


def run_sequential_pipeline(data: Dict[str, Any], user_prompt: str, full_context: str) -> str:
    """
    顺序执行生成流程
    """
    # 生成各部分文本
    text_blocks = []
    para = paragraph_generator(data, full_context)
    if para:
        text_blocks.append(para)
    dialog = dialogue_generator(data, full_context)
    if dialog:
        text_blocks.append(dialog)
    scene = scene_generator(data, full_context)
    if scene:
        text_blocks.append(scene)
    # 合并输出
    raw_text = "\n\n".join(text_blocks)
    return apply_postprocessing(raw_text, data)


def run_parallel_pipeline(data: Dict[str, Any], user_prompt: str, full_context: str) -> str:
    """
    并行执行生成流程
    """
    # 将输入拆分为多个块
    data_list, context_list = split_into_chunks(user_prompt, full_context)
    
    # 并行生成段落
    logging.info(f"启动并行生成，共 {len(data_list)} 个块")
    para_results = parallel_generate(paragraph_generator, data_list, context_list)
    
    # 合并结果
    raw_text = "\n\n".join([r for r in para_results if r])
    
    # 应用后处理
    return apply_postprocessing(raw_text, data)


def apply_postprocessing(raw_text: str, data: Dict[str, Any]) -> str:
    """
    应用一致性检查和后处理
    """
    # 获取小说ID（如果有）
    novel_id = data.get("novel_id", "default")
    
    # 一致性校验
    if not check_character_consistency(raw_text, novel_id):
        # TODO: 角色一致性校验失败处理
        logging.warning("角色一致性校验失败，可能需要人工干预")
        pass
    if not check_plot_consistency(raw_text, novel_id):
        # TODO: 情节一致性校验失败处理
        logging.warning("情节一致性校验失败，可能需要人工干预")
        pass
    
    # 后处理：润色、风格迁移、多样性增强
    processed = polish_text(raw_text)
    processed = style_transfer_text(processed, data.get("style_vector"))
    processed = diversity_augmentation(processed)
    
    # 情感曲线分析，可用于前端可视化或进一步处理
    emotion_curve = analyze_emotion_curve(processed)
    # TODO: 将 emotion_curve 返回或保存，当前仅执行分析
    
    # 更新知识图谱
    update_knowledge_graph(processed, novel_id)
    
    return processed
