"""
数据库工具模块单元测试
"""
import pytest
from unittest.mock import patch, MagicMock, call

from app.database.db_utils import (
    init_db_pool, get_connection, execute_query, 
    execute_transaction, DBConnection
)

class TestDBUtils:
    """数据库工具测试类"""
    
    @patch('app.database.db_utils.create_engine')
    @patch('app.database.db_utils.logging')
    def test_init_db_pool_success(self, mock_logging, mock_create_engine):
        """测试成功初始化数据库连接池"""
        # 设置模拟返回值
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        # 调用被测试函数
        result = init_db_pool()
        
        # 验证结果
        assert result is True
        mock_logging.info.assert_called_with("数据库连接池初始化成功")
    
    @patch('app.database.db_utils.create_engine')
    @patch('app.database.db_utils.logging')
    def test_init_db_pool_failure(self, mock_logging, mock_create_engine):
        """测试初始化数据库连接池失败"""
        # 设置模拟抛出异常
        mock_create_engine.side_effect = Exception("连接失败")
        
        # 调用被测试函数
        result = init_db_pool()
        
        # 验证结果
        assert result is False
        mock_logging.error.assert_called()
    
    @patch('app.database.db_utils.engine')
    def test_get_connection(self, mock_engine):
        """测试获取数据库连接"""
        # 设置模拟连接
        mock_conn = MagicMock()
        mock_engine.connect.return_value = mock_conn
        
        # 使用上下文管理器
        with get_connection() as conn:
            # 验证结果
            assert conn == mock_conn
            # 验证连接被获取
            mock_engine.connect.assert_called_once()
        
        # 验证连接被关闭
        mock_conn.close.assert_called_once()
    
    @patch('app.database.db_utils.engine')
    @patch('app.database.db_utils.text')
    def test_execute_query(self, mock_text, mock_engine):
        """测试执行查询"""
        # 设置模拟
        mock_conn = MagicMock()
        mock_engine.connect.return_value = mock_conn
        mock_result = MagicMock()
        mock_conn.execute.return_value = mock_result
        mock_text.return_value = "SELECT 1"
        
        # 准备参数
        sql = "SELECT * FROM test WHERE id = :id"
        params = {"id": 1}
        
        # 调用被测试函数
        result = execute_query(sql, params)
        
        # 验证结果
        assert result == mock_result
        mock_text.assert_called_with(sql)
        mock_conn.execute.assert_called_with("SELECT 1", params)
        mock_conn.close.assert_called_once()
    
    @patch('app.database.db_utils.engine')
    @patch('app.database.db_utils.text')
    def test_execute_transaction_success(self, mock_text, mock_engine):
        """测试成功执行事务"""
        # 设置模拟
        mock_conn = MagicMock()
        mock_engine.connect.return_value = mock_conn
        mock_trans = MagicMock()
        mock_conn.begin.return_value = mock_trans
        
        # 准备参数
        sqls = [
            ("INSERT INTO test VALUES (:id, :name)", {"id": 1, "name": "测试1"}),
            ("INSERT INTO test VALUES (:id, :name)", {"id": 2, "name": "测试2"})
        ]
        
        # 调用被测试函数
        result = execute_transaction(sqls)
        
        # 验证结果
        assert result is True
        # 验证事务开始
        mock_conn.begin.assert_called_once()
        # 验证SQL执行
        assert mock_conn.execute.call_count == 2
        # 验证事务提交
        mock_trans.commit.assert_called_once()
        # 验证连接关闭
        mock_conn.close.assert_called_once()
    
    @patch('app.database.db_utils.engine')
    @patch('app.database.db_utils.text')
    @patch('app.database.db_utils.logging')
    def test_execute_transaction_failure(self, mock_logging, mock_text, mock_engine):
        """测试执行事务失败"""
        # 设置模拟
        mock_conn = MagicMock()
        mock_engine.connect.return_value = mock_conn
        mock_trans = MagicMock()
        mock_conn.begin.return_value = mock_trans
        mock_conn.execute.side_effect = Exception("执行失败")
        
        # 准备参数
        sqls = [
            ("INSERT INTO test VALUES (:id, :name)", {"id": 1, "name": "测试1"})
        ]
        
        # 调用被测试函数
        result = execute_transaction(sqls)
        
        # 验证结果
        assert result is False
        # 验证事务回滚
        mock_trans.rollback.assert_called_once()
        # 验证错误日志
        mock_logging.error.assert_called()
        # 验证连接关闭
        mock_conn.close.assert_called_once()
    
    @patch('app.database.db_utils.engine')
    def test_db_connection_context_manager(self, mock_engine):
        """测试DBConnection上下文管理器"""
        # 设置模拟
        mock_conn = MagicMock()
        mock_engine.connect.return_value = mock_conn
        
        # 使用上下文管理器
        with DBConnection() as conn:
            # 验证结果
            assert conn == mock_conn
            # 验证连接被获取
            mock_engine.connect.assert_called_once()
        
        # 验证连接被关闭
        mock_conn.close.assert_called_once()
    
    @patch('app.database.db_utils.engine')
    def test_db_connection_exception(self, mock_engine):
        """测试DBConnection异常处理"""
        # 设置模拟
        mock_conn = MagicMock()
        mock_engine.connect.return_value = mock_conn
        
        # 使用上下文管理器并抛出异常
        try:
            with DBConnection() as conn:
                raise RuntimeError("测试异常")
        except RuntimeError:
            pass
        
        # 验证连接被关闭
        mock_conn.close.assert_called_once()
