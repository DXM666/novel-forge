"""上下文管理模块 - 实现高级上下文窗口管理和递归摘要

提供以下功能：
1. 递归摘要算法 - 将长文本压缩成摘要，保留关键信息
2. 分层上下文管理 - 管理不同层级的上下文（章节、场景、段落）
3. 动态窗口调整 - 根据模型容量和输入长度动态调整上下文窗口
4. 关键信息提取 - 识别和保留文本中的关键信息
"""

import logging
import re
import math
from typing import List, Dict, Any, Optional, Tuple, Union

from .memory import memory_store
from .config import settings
from .cache.cache_factory import cache
from .model_infer import model_inference

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 上下文窗口配置
CONTEXT_CONFIG = {
    "max_tokens": int(os.environ.get("MAX_CONTEXT_TOKENS", "4000")),  # 最大上下文窗口大小
    "summary_ratio": 0.3,  # 摘要压缩比例（摘要长度/原文长度）
    "min_chunk_size": 500,  # 最小分块大小（token）
    "max_chunk_size": 1000,  # 最大分块大小（token）
    "overlap": 100,  # 分块重叠大小（token）
    "key_info_ratio": 0.2,  # 关键信息保留比例
    "recency_bias": 0.7,  # 最近内容的权重（0-1）
}


def count_tokens(text: str) -> int:
    """
    计算文本的token数量
    
    参数:
        text: 输入文本
    
    返回:
        token数量
    """
    try:
        # 尝试使用tiktoken库进行精确计算
        import tiktoken
        encoder = tiktoken.get_encoding("cl100k_base")  # 使用OpenAI的编码器
        return len(encoder.encode(text))
    except ImportError:
        # 如果没有tiktoken，使用简单的估算方法
        # 英文约为每4个字符1个token，中文约为每1.5个字符1个token
        chinese_char_count = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_char_count = len(text) - chinese_char_count
        
        # 估算token数
        return math.ceil(chinese_char_count / 1.5 + other_char_count / 4)


def split_text_into_chunks(text: str, max_chunk_size: int, overlap: int) -> List[str]:
    """
    将文本分割成重叠的块
    
    参数:
        text: 输入文本
        max_chunk_size: 每个块的最大token数
        overlap: 块之间的重叠token数
    
    返回:
        文本块列表
    """
    if not text:
        return []
    
    # 按段落分割文本
    paragraphs = re.split(r'\n+', text)
    chunks = []
    current_chunk = ""
    current_chunk_tokens = 0
    
    for para in paragraphs:
        para_tokens = count_tokens(para)
        
        # 如果段落本身超过最大块大小，需要进一步分割
        if para_tokens > max_chunk_size:
            # 先添加当前块（如果有）
            if current_chunk:
                chunks.append(current_chunk)
                # 保留重叠部分作为新块的开始
                if len(chunks) > 0 and overlap > 0:
                    # 获取上一个块的最后部分作为重叠
                    words = current_chunk.split()
                    overlap_words = min(len(words), overlap)
                    current_chunk = " ".join(words[-overlap_words:])
                    current_chunk_tokens = count_tokens(current_chunk)
                else:
                    current_chunk = ""
                    current_chunk_tokens = 0
            
            # 分割大段落
            sentences = re.split(r'(?<=[.!?。！？]\s)', para)
            for sentence in sentences:
                sentence_tokens = count_tokens(sentence)
                
                if current_chunk_tokens + sentence_tokens <= max_chunk_size:
                    current_chunk += (" " if current_chunk else "") + sentence
                    current_chunk_tokens += sentence_tokens
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence
                    current_chunk_tokens = sentence_tokens
        else:
            # 正常段落处理
            if current_chunk_tokens + para_tokens <= max_chunk_size:
                current_chunk += ("\n" if current_chunk else "") + para
                current_chunk_tokens += para_tokens
            else:
                chunks.append(current_chunk)
                # 保留重叠部分作为新块的开始
                if len(chunks) > 0 and overlap > 0:
                    # 获取上一个块的最后部分作为重叠
                    words = current_chunk.split()
                    overlap_words = min(len(words), overlap)
                    current_chunk = " ".join(words[-overlap_words:]) + "\n" + para
                    current_chunk_tokens = count_tokens(current_chunk)
                else:
                    current_chunk = para
                    current_chunk_tokens = para_tokens
    
    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def summarize_chunk(chunk: str, target_tokens: int) -> str:
    """
    对文本块进行摘要
    
    参数:
        chunk: 文本块
        target_tokens: 目标token数
    
    返回:
        摘要文本
    """
    # 检查是否需要摘要
    chunk_tokens = count_tokens(chunk)
    if chunk_tokens <= target_tokens:
        return chunk
    
    # 缓存键
    cache_key = f"summary:{hash(chunk)}:{target_tokens}"
    
    # 尝试从缓存获取
    cached_summary = cache.get(cache_key)
    if cached_summary:
        return cached_summary
    
    # 构建摘要提示
    prompt = f"""
    请对以下文本进行摘要，保留关键信息，控制在{target_tokens}个token以内：
    
    {chunk}
    
    摘要：
    """
    
    try:
        # 调用模型生成摘要
        summary = model_inference(prompt, "")
        
        # 如果摘要仍然太长，进行截断
        summary_tokens = count_tokens(summary)
        if summary_tokens > target_tokens:
            # 按句子截断
            sentences = re.split(r'(?<=[.!?。！？]\s)', summary)
            truncated_summary = ""
            truncated_tokens = 0
            
            for sentence in sentences:
                sentence_tokens = count_tokens(sentence)
                if truncated_tokens + sentence_tokens <= target_tokens:
                    truncated_summary += sentence
                    truncated_tokens += sentence_tokens
                else:
                    break
            
            summary = truncated_summary
        
        # 缓存摘要
        cache.set(cache_key, summary, expire=3600)  # 缓存1小时
        
        return summary
    except Exception as e:
        logger.error(f"摘要生成失败: {str(e)}")
        
        # 回退到简单截断
        words = chunk.split()
        keep_ratio = target_tokens / chunk_tokens
        keep_words = max(1, int(len(words) * keep_ratio))
        simple_summary = "..." + " ".join(words[-keep_words:])
        
        return simple_summary


def recursive_summarize(text: str, target_tokens: int, max_recursion: int = 3) -> str:
    """
    递归摘要算法
    
    参数:
        text: 输入文本
        target_tokens: 目标token数
        max_recursion: 最大递归层数
    
    返回:
        摘要文本
    """
    text_tokens = count_tokens(text)
    
    # 基本情况：文本已经足够短或达到最大递归层数
    if text_tokens <= target_tokens or max_recursion <= 0:
        return summarize_chunk(text, target_tokens)
    
    # 分割文本
    max_chunk_size = CONTEXT_CONFIG["max_chunk_size"]
    overlap = CONTEXT_CONFIG["overlap"]
    chunks = split_text_into_chunks(text, max_chunk_size, overlap)
    
    # 计算每个块的目标token数
    chunk_target_tokens = int(target_tokens / len(chunks) * 0.9)  # 预留10%用于连接
    
    # 对每个块进行摘要
    summaries = []
    for i, chunk in enumerate(chunks):
        # 对最后一个块给予更多的token配额（因为通常包含更重要的信息）
        if i == len(chunks) - 1:
            chunk_target = int(chunk_target_tokens * 1.5)  # 给最后一块50%的额外空间
        else:
            chunk_target = chunk_target_tokens
        
        # 递归摘要
        chunk_summary = recursive_summarize(chunk, chunk_target, max_recursion - 1)
        summaries.append(chunk_summary)
    
    # 合并摘要
    combined_summary = "\n\n".join(summaries)
    
    # 检查合并后的摘要是否仍然过长
    combined_tokens = count_tokens(combined_summary)
    if combined_tokens > target_tokens:
        # 需要进一步摘要
        return summarize_chunk(combined_summary, target_tokens)
    
    return combined_summary


def extract_key_information(text: str) -> str:
    """
    从文本中提取关键信息（人物、地点、事件等）
    
    参数:
        text: 输入文本
    
    返回:
        关键信息文本
    """
    # 缓存键
    cache_key = f"key_info:{hash(text)}"
    
    # 尝试从缓存获取
    cached_info = cache.get(cache_key)
    if cached_info:
        return cached_info
    
    # 构建提取提示
    prompt = """
    请从以下文本中提取关键信息，包括：
    1. 主要人物及其行为
    2. 重要地点
    3. 关键事件
    4. 重要对话
    5. 情节转折点
    
    以简洁的要点形式列出：
    
    {text}
    
    关键信息：
    """.format(text=text)
    
    try:
        # 调用模型提取关键信息
        key_info = model_inference(prompt, "")
        
        # 缓存结果
        cache.set(cache_key, key_info, expire=3600)  # 缓存1小时
        
        return key_info
    except Exception as e:
        logger.error(f"关键信息提取失败: {str(e)}")
        return ""  # 失败时返回空字符串


def get_context_for_generation(memory_id: str, user_prompt: str, include_key_info: bool = True) -> str:
    """
    获取用于生成的上下文，使用递归摘要算法处理长文本
    
    参数:
        memory_id: 记忆ID
        user_prompt: 用户提示
        include_key_info: 是否包含关键信息提取
    
    返回:
        处理后的上下文
    """
    # 获取历史记忆
    history = memory_store.get(memory_id)
    if not history:
        return user_prompt
    
    # 计算token数
    prompt_tokens = count_tokens(user_prompt)
    max_tokens = CONTEXT_CONFIG["max_tokens"]
    available_history_tokens = max_tokens - prompt_tokens - 100  # 预留100个token的缓冲
    
    # 检查是否有足够空间
    if available_history_tokens <= 0:
        logger.warning(f"用户提示过长 ({prompt_tokens} tokens)，无法包含历史记忆")
        return user_prompt
    
    # 计算历史记忆的token数
    history_tokens = count_tokens(history)
    
    # 如果历史记忆足够短，直接使用
    if history_tokens <= available_history_tokens:
        return history + "\n\n" + user_prompt
    
    # 分配token预算
    key_info_tokens = 0
    if include_key_info:
        key_info_tokens = int(available_history_tokens * CONTEXT_CONFIG["key_info_ratio"])
        summary_tokens = available_history_tokens - key_info_tokens
    else:
        summary_tokens = available_history_tokens
    
    # 生成摘要
    logger.info(f"生成历史记忆摘要 (目标: {summary_tokens} tokens)")
    summary = recursive_summarize(history, summary_tokens)
    
    # 提取关键信息（如果需要）
    if include_key_info and key_info_tokens > 0:
        logger.info(f"提取关键信息 (目标: {key_info_tokens} tokens)")
        key_info = extract_key_information(history)
        
        # 如果关键信息过长，进行截断
        key_info_actual_tokens = count_tokens(key_info)
        if key_info_actual_tokens > key_info_tokens:
            key_info = summarize_chunk(key_info, key_info_tokens)
        
        # 组合上下文
        context = f"""【历史摘要】
{summary}

【关键信息】
{key_info}

【当前输入】
{user_prompt}"""
    else:
        # 不包含关键信息
        context = f"""【历史摘要】
{summary}

【当前输入】
{user_prompt}"""
    
    return context


def get_layered_context(project_id: str, chapter_id: Optional[str] = None, 
                      scene_id: Optional[str] = None, query: Optional[str] = None) -> str:
    """
    获取分层上下文，包括项目、章节和场景级别的信息
    
    参数:
        project_id: 项目ID
        chapter_id: 章节ID（可选）
        scene_id: 场景ID（可选）
        query: 查询文本（可选），用于检索相关记忆
    
    返回:
        分层上下文
    """
    from .memory_system import memory_system
    
    # 获取项目级上下文
    project_context = memory_system.get_context_for_generation(
        project_id=project_id,
        query=query or "项目概述",
        include_short_term=True,
        include_long_term=True,
        include_knowledge_graph=True
    )
    
    # 如果指定了章节，获取章节级上下文
    chapter_context = ""
    if chapter_id:
        # 从数据库获取章节信息
        from .database.db_utils import get_chapter
        success, chapter_data = get_chapter(project_id, chapter_id)
        
        if success and chapter_data:
            chapter_context = f"""【当前章节】
标题: {chapter_data.get('title', '未命名章节')}
摘要: {chapter_data.get('summary', '无摘要')}
"""
    
    # 如果指定了场景，获取场景级上下文
    scene_context = ""
    if scene_id:
        # TODO: 实现场景信息获取
        pass
    
    # 组合上下文
    combined_context = ""
    if project_context:
        combined_context += f"【项目上下文】\n{project_context}\n\n"
    if chapter_context:
        combined_context += f"{chapter_context}\n"
    if scene_context:
        combined_context += f"{scene_context}\n"
    
    return combined_context
