"""
向量嵌入模块 - 提供统一的文本嵌入功能
"""
import os
import logging
import numpy as np
from typing import List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局嵌入模型
EMBEDDING_MODEL = None

def init_embedding_model():
    """初始化嵌入模型"""
    global EMBEDDING_MODEL
    
    # 尝试加载本地模型
    try:
        from sentence_transformers import SentenceTransformer
        EMBEDDING_MODEL = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        logger.info("成功加载本地Embedding模型")
        return True
    except Exception as e:
        logger.warning(f"加载本地Embedding模型失败: {str(e)}，将尝试使用OpenAI API")
        
    # 尝试使用OpenAI API
    try:
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            logger.info("将使用OpenAI API进行文本嵌入")
            return True
    except Exception as e:
        logger.warning(f"配置OpenAI API失败: {str(e)}")
    
    logger.warning("无法初始化任何嵌入模型，将使用随机向量（仅用于测试）")
    return False

def get_embedding(text: str, model: Optional[str] = None) -> List[float]:
    """
    获取文本的向量嵌入表示
    
    参数:
        text: 输入文本
        model: 可选的模型名称
    
    返回:
        向量嵌入（1536维浮点数列表）
    """
    global EMBEDDING_MODEL
    
    # 如果模型未初始化，尝试初始化
    if EMBEDDING_MODEL is None and not init_embedding_model():
        # 使用随机向量作为后备方案
        logger.warning("使用随机向量作为嵌入，仅用于测试")
        return np.random.randn(1536).tolist()
    
    # 使用本地模型
    if EMBEDDING_MODEL:
        try:
            embedding = EMBEDDING_MODEL.encode(text)
            # 确保维度一致（如果本地模型维度不是1536，进行填充或截断）
            if len(embedding) < 1536:
                padding = np.zeros(1536 - len(embedding))
                embedding = np.concatenate([embedding, padding])
            elif len(embedding) > 1536:
                embedding = embedding[:1536]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"本地模型嵌入失败: {str(e)}")
    
    # 使用OpenAI API
    try:
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            client = OpenAI(api_key=api_key)
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
    except Exception as e:
        logger.error(f"OpenAI API嵌入失败: {str(e)}")
    
    # 所有方法都失败，返回随机向量
    logger.warning("所有嵌入方法都失败，使用随机向量")
    return np.random.randn(1536).tolist()

# 初始化嵌入模型
init_embedding_model()
