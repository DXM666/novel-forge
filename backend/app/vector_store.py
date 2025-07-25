"""
向量存储管理器 - 实现向量数据库的操作
支持PostgreSQL的pg_vector扩展或外部向量数据库
"""
import os
import logging
import json
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import psycopg2
from psycopg2.extras import Json, RealDictCursor

from .database.db_utils import execute_query, get_db_connection, release_db_connection
from .embeddings import get_embeddings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储管理器 - 支持PostgreSQL的pg_vector扩展"""
    
    def __init__(self):
        """初始化向量存储"""
        pass
    
    def add(self, memory_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        添加向量记忆
        
        参数:
            memory_id: 记忆ID
            text: 文本内容
            metadata: 元数据
        
        返回:
            是否成功
        """
        try:
            # 生成向量嵌入
            embedding = get_embeddings(text).tolist()
            
            # 保存到向量表
            query = """
            INSERT INTO vector_memories (memory_id, embedding)
            VALUES (%s, %s)
            RETURNING id
            """
            success, result = execute_query(query, (memory_id, embedding))
            
            return success and bool(result)
        except Exception as e:
            logger.error(f"添加向量记忆失败: {str(e)}")
            return False
    
    def search(self, project_id: str, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        语义搜索
        
        参数:
            project_id: 项目ID
            query_text: 查询文本
            limit: 返回结果数量限制
        
        返回:
            相关记忆列表
        """
        try:
            # 生成查询向量
            query_embedding = get_embeddings(query_text).tolist()
            
            # 执行向量搜索
            query = """
            SELECT 
                me.id AS memory_id,
                me.entry_type,
                me.content,
                me.metadata,
                1 - (vm.embedding <=> %s) AS similarity
            FROM 
                memory_entries me
            JOIN 
                vector_memories vm ON me.id = vm.memory_id
            WHERE 
                me.project_id = %s
            ORDER BY 
                similarity DESC
            LIMIT %s
            """
            success, result = execute_query(query, (query_embedding, project_id, limit))
            
            if not success:
                logger.error(f"向量搜索失败: {result}")
                return []
            
            return [dict(item) for item in result]
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return []
    
    def delete(self, memory_id: str) -> bool:
        """
        删除向量记忆
        
        参数:
            memory_id: 记忆ID
        
        返回:
            是否成功
        """
        try:
            query = """
            DELETE FROM vector_memories
            WHERE memory_id = %s
            """
            success, _ = execute_query(query, (memory_id,), fetch=False)
            
            return success
        except Exception as e:
            logger.error(f"删除向量记忆失败: {str(e)}")
            return False
    
    def update(self, memory_id: str, text: str) -> bool:
        """
        更新向量记忆
        
        参数:
            memory_id: 记忆ID
            text: 新文本内容
        
        返回:
            是否成功
        """
        # 先删除旧向量
        if not self.delete(memory_id):
            return False
        
        # 添加新向量
        return self.add(memory_id, text)


class ExternalVectorStore:
    """外部向量存储管理器 - 支持Pinecone、Weaviate等"""
    
    def __init__(self, provider: str = "pinecone", api_key: Optional[str] = None):
        """
        初始化外部向量存储
        
        参数:
            provider: 提供商名称（pinecone, weaviate, chroma）
            api_key: API密钥
        """
        self.provider = provider
        self.api_key = api_key or os.environ.get(f"{provider.upper()}_API_KEY")
        self.client = None
        
        # 初始化客户端
        if provider == "pinecone":
            self._init_pinecone()
        elif provider == "weaviate":
            self._init_weaviate()
        elif provider == "chroma":
            self._init_chroma()
        else:
            logger.error(f"不支持的向量存储提供商: {provider}")
    
    def _init_pinecone(self):
        """初始化Pinecone客户端"""
        try:
            import pinecone
            
            pinecone.init(api_key=self.api_key, environment=os.environ.get("PINECONE_ENV", "us-west1-gcp"))
            
            # 获取或创建索引
            index_name = os.environ.get("PINECONE_INDEX", "novel-forge")
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=index_name,
                    dimension=1536,
                    metric="cosine"
                )
            
            self.client = pinecone.Index(index_name)
            logger.info(f"Pinecone客户端初始化成功，索引: {index_name}")
        except ImportError:
            logger.error("未安装Pinecone客户端，请使用pip install pinecone-client安装")
        except Exception as e:
            logger.error(f"初始化Pinecone客户端失败: {str(e)}")
    
    def _init_weaviate(self):
        """初始化Weaviate客户端"""
        try:
            import weaviate
            
            self.client = weaviate.Client(
                url=os.environ.get("WEAVIATE_URL", "http://localhost:8080"),
                auth_client_secret=weaviate.auth.AuthApiKey(self.api_key)
            )
            
            # 检查Schema是否存在
            if not self.client.schema.contains().get("classes"):
                # 创建Schema
                schema = {
                    "classes": [
                        {
                            "class": "MemoryEntry",
                            "description": "小说创作记忆条目",
                            "properties": [
                                {
                                    "name": "memory_id",
                                    "dataType": ["string"],
                                    "description": "记忆ID"
                                },
                                {
                                    "name": "project_id",
                                    "dataType": ["string"],
                                    "description": "项目ID"
                                },
                                {
                                    "name": "entry_type",
                                    "dataType": ["string"],
                                    "description": "记忆类型"
                                },
                                {
                                    "name": "content",
                                    "dataType": ["text"],
                                    "description": "记忆内容"
                                },
                                {
                                    "name": "metadata",
                                    "dataType": ["string"],
                                    "description": "元数据JSON"
                                }
                            ]
                        }
                    ]
                }
                self.client.schema.create(schema)
            
            logger.info("Weaviate客户端初始化成功")
        except ImportError:
            logger.error("未安装Weaviate客户端，请使用pip install weaviate-client安装")
        except Exception as e:
            logger.error(f"初始化Weaviate客户端失败: {str(e)}")
    
    def _init_chroma(self):
        """初始化Chroma客户端"""
        try:
            import chromadb
            
            self.client = chromadb.Client(
                chromadb.Settings(
                    chroma_api_impl="rest",
                    chroma_server_host=os.environ.get("CHROMA_HOST", "localhost"),
                    chroma_server_http_port=int(os.environ.get("CHROMA_PORT", "8000"))
                )
            )
            
            # 获取或创建集合
            self.collection = self.client.get_or_create_collection("novel-forge")
            
            logger.info("Chroma客户端初始化成功")
        except ImportError:
            logger.error("未安装Chroma客户端，请使用pip install chromadb安装")
        except Exception as e:
            logger.error(f"初始化Chroma客户端失败: {str(e)}")
    
    def add(self, memory_id: str, text: str, project_id: str, 
           entry_type: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        添加向量记忆
        
        参数:
            memory_id: 记忆ID
            text: 文本内容
            project_id: 项目ID
            entry_type: 记忆类型
            metadata: 元数据
        
        返回:
            是否成功
        """
        try:
            # 生成向量嵌入
            embedding = get_embeddings(text).tolist()
            metadata = metadata or {}
            metadata_str = json.dumps(metadata)
            
            if self.provider == "pinecone":
                self.client.upsert(
                    vectors=[(memory_id, embedding)],
                    metadata={
                        "project_id": project_id,
                        "entry_type": entry_type,
                        "content": text,
                        "metadata": metadata_str
                    },
                    namespace=project_id
                )
            elif self.provider == "weaviate":
                self.client.data_object.create(
                    {
                        "memory_id": memory_id,
                        "project_id": project_id,
                        "entry_type": entry_type,
                        "content": text,
                        "metadata": metadata_str
                    },
                    "MemoryEntry",
                    memory_id,
                    vector=embedding
                )
            elif self.provider == "chroma":
                self.collection.upsert(
                    ids=[memory_id],
                    embeddings=[embedding],
                    metadatas=[{
                        "project_id": project_id,
                        "entry_type": entry_type,
                        "content": text,
                        "metadata": metadata_str
                    }],
                    documents=[text]
                )
            
            return True
        except Exception as e:
            logger.error(f"添加向量记忆失败: {str(e)}")
            return False
    
    def search(self, project_id: str, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        语义搜索
        
        参数:
            project_id: 项目ID
            query_text: 查询文本
            limit: 返回结果数量限制
        
        返回:
            相关记忆列表
        """
        try:
            # 生成查询向量
            query_embedding = get_embeddings(query_text).tolist()
            
            results = []
            
            if self.provider == "pinecone":
                response = self.client.query(
                    vector=query_embedding,
                    top_k=limit,
                    namespace=project_id,
                    include_metadata=True
                )
                
                for match in response['matches']:
                    metadata = match['metadata']
                    results.append({
                        "memory_id": match['id'],
                        "entry_type": metadata['entry_type'],
                        "content": metadata['content'],
                        "metadata": json.loads(metadata['metadata']),
                        "similarity": match['score']
                    })
            elif self.provider == "weaviate":
                response = self.client.query.get(
                    "MemoryEntry", 
                    ["memory_id", "project_id", "entry_type", "content", "metadata"]
                ).with_where({
                    "path": ["project_id"],
                    "operator": "Equal",
                    "valueString": project_id
                }).with_near_vector({
                    "vector": query_embedding
                }).with_limit(limit).do()
                
                for obj in response['data']['Get']['MemoryEntry']:
                    results.append({
                        "memory_id": obj['memory_id'],
                        "entry_type": obj['entry_type'],
                        "content": obj['content'],
                        "metadata": json.loads(obj['metadata']),
                        "similarity": 0.0  # Weaviate不直接返回相似度
                    })
            elif self.provider == "chroma":
                response = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    where={"project_id": project_id}
                )
                
                for i, doc_id in enumerate(response['ids'][0]):
                    metadata = response['metadatas'][0][i]
                    results.append({
                        "memory_id": doc_id,
                        "entry_type": metadata['entry_type'],
                        "content": response['documents'][0][i],
                        "metadata": json.loads(metadata['metadata']),
                        "similarity": response['distances'][0][i] if 'distances' in response else 0.0
                    })
            
            return results
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return []
    
    def delete(self, memory_id: str) -> bool:
        """
        删除向量记忆
        
        参数:
            memory_id: 记忆ID
        
        返回:
            是否成功
        """
        try:
            if self.provider == "pinecone":
                self.client.delete(ids=[memory_id])
            elif self.provider == "weaviate":
                self.client.data_object.delete(
                    memory_id,
                    "MemoryEntry"
                )
            elif self.provider == "chroma":
                self.collection.delete(ids=[memory_id])
            
            return True
        except Exception as e:
            logger.error(f"删除向量记忆失败: {str(e)}")
            return False
    
    def update(self, memory_id: str, text: str, project_id: str, 
              entry_type: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        更新向量记忆
        
        参数:
            memory_id: 记忆ID
            text: 新文本内容
            project_id: 项目ID
            entry_type: 记忆类型
            metadata: 元数据
        
        返回:
            是否成功
        """
        return self.add(memory_id, text, project_id, entry_type, metadata)


# 创建向量存储实例
vector_store = VectorStore()

# 如果环境变量指定了外部向量存储，则使用外部存储
VECTOR_STORE_PROVIDER = os.environ.get("VECTOR_STORE_PROVIDER")
if VECTOR_STORE_PROVIDER:
    vector_store = ExternalVectorStore(VECTOR_STORE_PROVIDER)
    logger.info(f"使用外部向量存储: {VECTOR_STORE_PROVIDER}")
else:
    logger.info("使用内置PostgreSQL向量存储")
