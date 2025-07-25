"""
小说创作记忆系统 - 实现短期记忆、长期记忆和知识图谱功能
基于PostgreSQL + 向量数据库设计
"""
import os
import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from .memory import memory_store, element_store, graph_store
from .database.db_utils import (
    execute_query, get_db_connection, release_db_connection,
    save_memory_entry, get_memory_entries, save_vector_memory,
    search_related_memories, save_novel_element, get_novel_element,
    get_novel_elements_by_type, save_version_history, get_version_history
)
from .embeddings import get_embedding

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 使用统一的嵌入函数，减少代码冗余
from .embeddings import get_embeddings as get_embedding_vector

def get_embedding(text: str) -> List[float]:
    """
    获取文本的向量嵌入表示
    
    参数:
        text: 输入文本
    
    返回:
        向量嵌入（向量维度由模型决定）
    """
    try:
        # 调用统一的嵌入函数
        return get_embedding_vector(text).tolist()
    except Exception as e:
        logger.warning(f"获取嵌入向量失败: {str(e)}，使用随机向量作为替代")
        # 备用方法：使用随机向量（仅用于测试）
        return np.random.randn(1536).tolist()


class ShortTermMemory:
    """短期记忆系统 - 模拟模型当前上下文窗口内的临时记忆"""
    
    def __init__(self, window_size: int = 10):
        """
        初始化短期记忆
        
        参数:
            window_size: 滑动窗口大小，保留最近的N个记忆条目
        """
        self.window_size = window_size
        self.memory_buffer = {}  # 项目ID -> 记忆列表
    
    def add(self, project_id: str, content: str, entry_type: str = "input", 
           metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        添加记忆条目到短期记忆
        
        参数:
            project_id: 项目ID
            content: 记忆内容
            entry_type: 记忆类型
            metadata: 元数据
        
        返回:
            记忆ID
        """
        # 初始化项目缓冲区（如果不存在）
        if project_id not in self.memory_buffer:
            self.memory_buffer[project_id] = []
        
        # 创建记忆条目
        memory_item = {
            "id": f"mem_{int(time.time() * 1000)}",
            "content": content,
            "entry_type": entry_type,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # 添加到缓冲区
        self.memory_buffer[project_id].append(memory_item)
        
        # 如果超出窗口大小，移除最旧的条目
        if len(self.memory_buffer[project_id]) > self.window_size:
            self.memory_buffer[project_id].pop(0)
        
        return memory_item["id"]
    
    def get(self, project_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        获取短期记忆
        
        参数:
            project_id: 项目ID
            limit: 限制返回的条目数量
        
        返回:
            记忆条目列表
        """
        if project_id not in self.memory_buffer:
            return []
        
        memories = self.memory_buffer[project_id]
        if limit:
            return memories[-limit:]
        return memories
    
    def clear(self, project_id: str) -> None:
        """
        清空短期记忆
        
        参数:
            project_id: 项目ID
        """
        if project_id in self.memory_buffer:
            self.memory_buffer[project_id] = []
    
    def get_formatted_context(self, project_id: str, limit: int = None) -> str:
        """
        获取格式化的上下文，用于注入到Prompt中
        
        参数:
            project_id: 项目ID
            limit: 限制返回的条目数量
        
        返回:
            格式化的上下文字符串
        """
        memories = self.get(project_id, limit)
        if not memories:
            return ""
        
        formatted = "=== 最近的上下文 ===\n"
        for memory in memories:
            formatted += f"- {memory['entry_type']}: {memory['content']}\n"
        return formatted


class LongTermMemory:
    """长期记忆系统 - 保存整个小说项目的关键信息"""
    
    def __init__(self):
        """初始化长期记忆系统"""
        pass
    
    def add(self, project_id: str, content: str, entry_type: str, 
           metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        添加记忆条目到长期记忆
        
        参数:
            project_id: 项目ID
            content: 记忆内容
            entry_type: 记忆类型（summary, event, character_state, plot_point, worldbuilding）
            metadata: 元数据
        
        返回:
            记忆ID
        """
        # 保存到数据库
        success, memory_id = save_memory_entry(project_id, entry_type, content, metadata)
        
        if not success:
            logger.error(f"保存记忆条目失败: {memory_id}")
            return ""
        
        # 生成向量嵌入并保存
        try:
            embedding = get_embedding(content)
            save_vector_memory(memory_id, embedding)
        except Exception as e:
            logger.error(f"保存向量记忆失败: {str(e)}")
        
        # 保存版本历史
        version_data = {
            "content": content,
            "entry_type": entry_type,
            "metadata": metadata or {}
        }
        save_version_history(project_id, "memory", memory_id, version_data)
        
        return memory_id
    
    def get(self, project_id: str, entry_type: Optional[str] = None, 
           limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取长期记忆条目
        
        参数:
            project_id: 项目ID
            entry_type: 可选的条目类型过滤
            limit: 返回结果数量限制
        
        返回:
            记忆条目列表
        """
        success, memories = get_memory_entries(project_id, entry_type, limit)
        if not success:
            logger.error(f"获取记忆条目失败: {memories}")
            return []
        
        return memories
    
    def search(self, project_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        语义搜索相关记忆
        
        参数:
            project_id: 项目ID
            query: 查询文本
            limit: 返回结果数量限制
        
        返回:
            相关记忆列表
        """
        try:
            # 生成查询向量
            query_embedding = get_embedding(query)
            
            # 搜索相关记忆
            success, results = search_related_memories(project_id, query_embedding, limit)
            
            if not success:
                logger.error(f"搜索相关记忆失败: {results}")
                return []
            
            return results
        except Exception as e:
            logger.error(f"语义搜索失败: {str(e)}")
            return []
    
    def get_formatted_context(self, project_id: str, query: str, limit: int = 5) -> str:
        """
        获取格式化的相关记忆上下文，用于注入到Prompt中
        
        参数:
            project_id: 项目ID
            query: 查询文本
            limit: 返回结果数量限制
        
        返回:
            格式化的上下文字符串
        """
        memories = self.search(project_id, query, limit)
        if not memories:
            return ""
        
        formatted = "=== 相关记忆 ===\n"
        for memory in memories:
            formatted += f"- {memory['entry_type']}: {memory['content']}\n"
        return formatted


class KnowledgeGraph:
    """知识图谱系统 - 构建结构化的记忆网络"""
    
    def __init__(self):
        """初始化知识图谱系统"""
        pass
    
    def add_node(self, project_id: str, node_type: str, node_id: str, 
                properties: Dict[str, Any]) -> bool:
        """
        添加节点
        
        参数:
            project_id: 项目ID
            node_type: 节点类型（Character, Event, Location, Rule）
            node_id: 节点ID
            properties: 节点属性
        
        返回:
            是否成功
        """
        data = {
            "type": node_type,
            "properties": properties
        }
        success, _ = save_novel_element(project_id, node_type.lower(), node_id, data)
        return success
    
    def add_relationship(self, project_id: str, from_node: Tuple[str, str], 
                        to_node: Tuple[str, str], rel_type: str, 
                        properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        添加关系
        
        参数:
            project_id: 项目ID
            from_node: (节点类型, 节点ID)
            to_node: (节点类型, 节点ID)
            rel_type: 关系类型（如WITNESSED, HAS_RULE）
            properties: 关系属性
        
        返回:
            是否成功
        """
        # 获取当前图状态
        success, graph_data = graph_store.load_state(project_id)
        
        if not success or not graph_data:
            # 初始化图数据
            graph_data = {
                "nodes": {},
                "relationships": []
            }
        
        # 创建关系ID
        from_type, from_id = from_node
        to_type, to_id = to_node
        rel_id = f"{from_type.lower()}_{from_id}__{rel_type}__{to_type.lower()}_{to_id}"
        
        # 添加关系
        relationship = {
            "id": rel_id,
            "from_node": {"type": from_type, "id": from_id},
            "to_node": {"type": to_type, "id": to_id},
            "type": rel_type,
            "properties": properties or {}
        }
        
        # 检查是否已存在相同关系
        for rel in graph_data.get("relationships", []):
            if rel["id"] == rel_id:
                # 更新现有关系
                rel["properties"] = properties or {}
                break
        else:
            # 添加新关系
            if "relationships" not in graph_data:
                graph_data["relationships"] = []
            graph_data["relationships"].append(relationship)
        
        # 保存图状态
        return graph_store.save_state(project_id, graph_data)
    
    def get_node(self, project_id: str, node_type: str, node_id: str) -> Optional[Dict[str, Any]]:
        """
        获取节点
        
        参数:
            project_id: 项目ID
            node_type: 节点类型
            node_id: 节点ID
        
        返回:
            节点数据或None
        """
        success, node = get_novel_element(project_id, node_type.lower(), node_id)
        if not success:
            return None
        return node
    
    def get_nodes_by_type(self, project_id: str, node_type: str) -> List[Dict[str, Any]]:
        """
        获取指定类型的所有节点
        
        参数:
            project_id: 项目ID
            node_type: 节点类型
        
        返回:
            节点列表
        """
        success, nodes = get_novel_elements_by_type(project_id, node_type.lower())
        if not success:
            return []
        return nodes
    
    def get_relationships(self, project_id: str, node_type: Optional[str] = None, 
                         node_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取关系
        
        参数:
            project_id: 项目ID
            node_type: 可选的节点类型过滤
            node_id: 可选的节点ID过滤
        
        返回:
            关系列表
        """
        # 获取当前图状态
        success, graph_data = graph_store.load_state(project_id)
        
        if not success or not graph_data or "relationships" not in graph_data:
            return []
        
        relationships = graph_data["relationships"]
        
        # 应用过滤
        if node_type and node_id:
            filtered = []
            for rel in relationships:
                from_node = rel["from_node"]
                to_node = rel["to_node"]
                if (from_node["type"] == node_type and from_node["id"] == node_id) or \
                   (to_node["type"] == node_type and to_node["id"] == node_id):
                    filtered.append(rel)
            return filtered
        elif node_type:
            filtered = []
            for rel in relationships:
                from_node = rel["from_node"]
                to_node = rel["to_node"]
                if from_node["type"] == node_type or to_node["type"] == node_type:
                    filtered.append(rel)
            return filtered
        
        return relationships
    
    def get_formatted_context(self, project_id: str, node_type: Optional[str] = None, 
                             node_id: Optional[str] = None) -> str:
        """
        获取格式化的知识图谱上下文，用于注入到Prompt中
        
        参数:
            project_id: 项目ID
            node_type: 可选的节点类型过滤
            node_id: 可选的节点ID过滤
        
        返回:
            格式化的上下文字符串
        """
        relationships = self.get_relationships(project_id, node_type, node_id)
        if not relationships:
            return ""
        
        formatted = "=== 知识图谱关系 ===\n"
        for rel in relationships:
            from_node = rel["from_node"]
            to_node = rel["to_node"]
            rel_type = rel["type"]
            formatted += f"- ({from_node['type']}:{from_node['id']}) -[{rel_type}]-> ({to_node['type']}:{to_node['id']})\n"
        return formatted


class MemorySystem:
    """完整的记忆系统 - 集成短期记忆、长期记忆和知识图谱"""
    
    def __init__(self):
        """初始化记忆系统"""
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
        self.knowledge_graph = KnowledgeGraph()
    
    def add_memory(self, project_id: str, content: str, entry_type: str,
                  metadata: Optional[Dict[str, Any]] = None, 
                  add_to_short_term: bool = True) -> str:
        """
        添加记忆
        
        参数:
            project_id: 项目ID
            content: 记忆内容
            entry_type: 记忆类型
            metadata: 元数据
            add_to_short_term: 是否同时添加到短期记忆
        
        返回:
            记忆ID
        """
        # 添加到长期记忆
        memory_id = self.long_term.add(project_id, content, entry_type, metadata)
        
        # 可选添加到短期记忆
        if add_to_short_term:
            self.short_term.add(project_id, content, entry_type, metadata)
        
        return memory_id
    
    def add_character(self, project_id: str, character_id: str, name: str, 
                     role: str, description: str, attributes: Dict[str, Any] = None) -> bool:
        """
        添加角色
        
        参数:
            project_id: 项目ID
            character_id: 角色ID
            name: 角色名称
            role: 角色角色（如protagonist, antagonist）
            description: 角色描述
            attributes: 其他属性
        
        返回:
            是否成功
        """
        properties = {
            "name": name,
            "role": role,
            "description": description,
            **(attributes or {})
        }
        
        # 添加到知识图谱
        success = self.knowledge_graph.add_node(project_id, "Character", character_id, properties)
        
        # 添加到长期记忆
        if success:
            metadata = {"character_id": character_id, "name": name, "role": role}
            self.long_term.add(project_id, description, "character_state", metadata)
        
        return success
    
    def add_location(self, project_id: str, location_id: str, name: str, 
                    description: str, attributes: Dict[str, Any] = None) -> bool:
        """
        添加地点
        
        参数:
            project_id: 项目ID
            location_id: 地点ID
            name: 地点名称
            description: 地点描述
            attributes: 其他属性
        
        返回:
            是否成功
        """
        properties = {
            "name": name,
            "description": description,
            **(attributes or {})
        }
        
        # 添加到知识图谱
        success = self.knowledge_graph.add_node(project_id, "Location", location_id, properties)
        
        # 添加到长期记忆
        if success:
            metadata = {"location_id": location_id, "name": name}
            self.long_term.add(project_id, description, "worldbuilding", metadata)
        
        return success
    
    def add_event(self, project_id: str, event_id: str, title: str, description: str,
                 characters: List[str], location: Optional[str] = None,
                 attributes: Dict[str, Any] = None) -> bool:
        """
        添加事件
        
        参数:
            project_id: 项目ID
            event_id: 事件ID
            title: 事件标题
            description: 事件描述
            characters: 相关角色ID列表
            location: 可选的地点ID
            attributes: 其他属性
        
        返回:
            是否成功
        """
        properties = {
            "title": title,
            "description": description,
            "characters": characters,
            "location": location,
            **(attributes or {})
        }
        
        # 添加到知识图谱
        success = self.knowledge_graph.add_node(project_id, "Event", event_id, properties)
        
        # 添加关系
        if success:
            # 角色与事件的关系
            for character_id in characters:
                self.knowledge_graph.add_relationship(
                    project_id,
                    ("Character", character_id),
                    ("Event", event_id),
                    "PARTICIPATED_IN"
                )
            
            # 地点与事件的关系
            if location:
                self.knowledge_graph.add_relationship(
                    project_id,
                    ("Event", event_id),
                    ("Location", location),
                    "OCCURRED_AT"
                )
            
            # 添加到长期记忆
            metadata = {
                "event_id": event_id,
                "title": title,
                "characters": characters,
                "location": location
            }
            self.long_term.add(project_id, description, "plot_point", metadata)
        
        return success
    
    def add_rule(self, project_id: str, rule_id: str, name: str, 
                description: str, attributes: Dict[str, Any] = None) -> bool:
        """
        添加世界规则
        
        参数:
            project_id: 项目ID
            rule_id: 规则ID
            name: 规则名称
            description: 规则描述
            attributes: 其他属性
        
        返回:
            是否成功
        """
        properties = {
            "name": name,
            "description": description,
            **(attributes or {})
        }
        
        # 添加到知识图谱
        success = self.knowledge_graph.add_node(project_id, "Rule", rule_id, properties)
        
        # 添加到长期记忆
        if success:
            metadata = {"rule_id": rule_id, "name": name}
            self.long_term.add(project_id, description, "worldbuilding", metadata)
        
        return success
    
    def add_chapter_summary(self, project_id: str, chapter_number: int, 
                           title: str, summary: str) -> str:
        """
        添加章节摘要
        
        参数:
            project_id: 项目ID
            chapter_number: 章节编号
            title: 章节标题
            summary: 章节摘要
        
        返回:
            记忆ID
        """
        metadata = {
            "chapter_number": chapter_number,
            "title": title
        }
        
        return self.add_memory(project_id, summary, "summary", metadata)
    
    def get_context_for_generation(self, project_id: str, query: str, 
                                 include_short_term: bool = True,
                                 include_long_term: bool = True,
                                 include_knowledge_graph: bool = True) -> str:
        """
        获取用于生成的上下文
        
        参数:
            project_id: 项目ID
            query: 查询文本
            include_short_term: 是否包含短期记忆
            include_long_term: 是否包含长期记忆
            include_knowledge_graph: 是否包含知识图谱
        
        返回:
            格式化的上下文字符串
        """
        context_parts = []
        
        # 添加短期记忆
        if include_short_term:
            short_term_context = self.short_term.get_formatted_context(project_id)
            if short_term_context:
                context_parts.append(short_term_context)
        
        # 添加长期记忆
        if include_long_term:
            long_term_context = self.long_term.get_formatted_context(project_id, query)
            if long_term_context:
                context_parts.append(long_term_context)
        
        # 添加知识图谱
        if include_knowledge_graph:
            # 从查询中提取可能的节点类型和ID（简单实现）
            node_type = None
            node_id = None
            
            # 如果查询中包含角色名，尝试获取相关角色的关系
            characters = self.knowledge_graph.get_nodes_by_type(project_id, "Character")
            for character in characters:
                if character["data"]["properties"]["name"].lower() in query.lower():
                    node_type = "Character"
                    node_id = character["element_id"]
                    break
            
            graph_context = self.knowledge_graph.get_formatted_context(project_id, node_type, node_id)
            if graph_context:
                context_parts.append(graph_context)
        
        return "\n\n".join(context_parts)


# 创建记忆系统实例
memory_system = MemorySystem()
