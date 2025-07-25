"""
上下文管理器单元测试
"""
import pytest
from unittest.mock import patch, MagicMock

from app.context_manager import (
    get_context_for_generation, summarize_text, 
    get_layered_context, merge_contexts
)

class TestContextManager:
    """上下文管理器测试类"""
    
    @patch('app.context_manager.memory_store')
    @patch('app.context_manager.vector_store')
    @patch('app.context_manager.get_layered_context')
    def test_get_context_for_generation(self, mock_get_layered_context, mock_vector_store, mock_memory_store):
        """测试获取生成上下文"""
        # 设置模拟
        mock_memory_id = "test_memory_id"
        mock_user_prompt = "继续写作"
        mock_context = "这是测试上下文"
        mock_get_layered_context.return_value = mock_context
        
        # 调用被测试函数
        result = get_context_for_generation(mock_memory_id, mock_user_prompt)
        
        # 验证结果
        assert result == mock_context
        mock_get_layered_context.assert_called_with(mock_memory_id, mock_user_prompt)
    
    @patch('app.context_manager.model_inference')
    def test_summarize_text(self, mock_model_inference):
        """测试文本摘要"""
        # 设置模拟
        mock_text = "这是一段较长的文本，需要进行摘要处理"
        mock_summary = "文本摘要"
        mock_model_inference.return_value = mock_summary
        
        # 调用被测试函数
        result = summarize_text(mock_text)
        
        # 验证结果
        assert result == mock_summary
        mock_model_inference.assert_called()
    
    @patch('app.context_manager.memory_store')
    @patch('app.context_manager.vector_store')
    @patch('app.context_manager.settings')
    @patch('app.context_manager.summarize_text')
    @patch('app.context_manager.tiktoken')
    def test_get_layered_context(self, mock_tiktoken, mock_summarize_text, mock_settings, mock_vector_store, mock_memory_store):
        """测试分层获取上下文"""
        # 设置模拟
        mock_memory_id = "test_memory_id"
        mock_query = "测试查询"
        mock_settings.MAX_CONTEXT_TOKENS = 1000
        
        # 模拟记忆检索
        mock_short_term_entries = [
            {"content": "短期记忆1", "metadata": {}},
            {"content": "短期记忆2", "metadata": {}}
        ]
        mock_relevant_entries = [
            {"content": "相关记忆1", "metadata": {}},
            {"content": "相关记忆2", "metadata": {}}
        ]
        mock_memory_store.get_short_term_memory.return_value = mock_short_term_entries
        mock_vector_store.search.return_value = mock_relevant_entries
        
        # 模拟token计数
        mock_encoding = MagicMock()
        mock_encoding.encode.side_effect = lambda text: [0] * len(text)  # 每个字符算一个token
        mock_tiktoken.get_encoding.return_value = mock_encoding
        
        # 模拟摘要生成
        mock_summarize_text.return_value = "记忆摘要"
        
        # 调用被测试函数
        result = get_layered_context(mock_memory_id, mock_query)
        
        # 验证结果
        assert isinstance(result, str)
        assert "记忆摘要" in result or "短期记忆" in result or "相关记忆" in result
        
        # 验证函数调用
        mock_memory_store.get_short_term_memory.assert_called_with(mock_memory_id)
        mock_vector_store.search.assert_called_with(mock_query, limit=5)
    
    def test_merge_contexts(self):
        """测试合并上下文"""
        # 设置测试数据
        short_term = "这是短期记忆内容"
        relevant = "这是相关记忆内容"
        summaries = "这是摘要内容"
        user_prompt = "用户提示"
        
        # 调用被测试函数
        result = merge_contexts(short_term, relevant, summaries, user_prompt)
        
        # 验证结果
        assert short_term in result
        assert relevant in result
        assert summaries in result
        assert user_prompt in result
