"""
嵌入模块单元测试
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from app.embeddings import (
    init_embedding_model, get_embeddings, 
    get_text_chunks, calculate_similarity
)

class TestEmbeddings:
    """嵌入模块测试类"""
    
    @patch('app.embeddings.logging')
    def test_init_embedding_model(self, mock_logging):
        """测试初始化嵌入模型"""
        with patch('app.embeddings.embedding_model', None):
            # 调用被测试函数
            init_embedding_model()
            
            # 验证日志
            mock_logging.info.assert_called()
    
    @patch('app.embeddings.embedding_model')
    def test_get_embeddings(self, mock_embedding_model):
        """测试获取文本嵌入向量"""
        # 设置模拟
        mock_embedding = np.array([0.1, 0.2, 0.3])
        mock_embedding_model.encode.return_value = mock_embedding
        
        # 准备参数
        text = "测试文本"
        
        # 调用被测试函数
        result = get_embeddings(text)
        
        # 验证结果
        assert np.array_equal(result, mock_embedding)
        mock_embedding_model.encode.assert_called_with([text])
    
    @patch('app.embeddings.embedding_model')
    def test_get_embeddings_list(self, mock_embedding_model):
        """测试获取多个文本的嵌入向量"""
        # 设置模拟
        mock_embeddings = np.array([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ])
        mock_embedding_model.encode.return_value = mock_embeddings
        
        # 准备参数
        texts = ["测试文本1", "测试文本2"]
        
        # 调用被测试函数
        result = get_embeddings(texts)
        
        # 验证结果
        assert np.array_equal(result, mock_embeddings)
        mock_embedding_model.encode.assert_called_with(texts)
    
    def test_get_text_chunks(self):
        """测试文本分块"""
        # 准备参数
        text = "这是一段测试文本，我们需要将它分成多个块。这是第二句话。这是第三句话，比较长一些。"
        max_length = 10
        
        # 调用被测试函数
        chunks = get_text_chunks(text, max_length)
        
        # 验证结果
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        # 验证每个块的长度不超过最大长度
        for chunk in chunks:
            assert len(chunk) <= max_length
    
    def test_calculate_similarity(self):
        """测试计算相似度"""
        # 准备参数
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([0, 1, 0])
        vec3 = np.array([1, 1, 0]) / np.sqrt(2)  # 归一化
        
        # 调用被测试函数并验证结果
        # 垂直向量相似度为0
        assert calculate_similarity(vec1, vec2) == 0
        # 相同向量相似度为1
        assert calculate_similarity(vec1, vec1) == 1
        # 45度角向量相似度为0.7071（√2/2）
        assert round(calculate_similarity(vec1, vec3), 4) == 0.7071
