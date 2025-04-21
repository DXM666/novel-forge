"""
知识图谱模块：管理角色、地点、事件和世界观规则，确保生成内容的一致性
"""
from typing import Dict, List, Any, Optional, Set, Tuple
import json
import os
import logging
from pathlib import Path
import datetime

# 知识图谱存储路径
KNOWLEDGE_GRAPH_DIR = Path("./data/knowledge_graph")
KNOWLEDGE_GRAPH_DIR.mkdir(parents=True, exist_ok=True)


class Entity:
    """实体基类（角色、地点、物品等）"""
    
    def __init__(self, entity_id: str, name: str, entity_type: str, attributes: Dict[str, Any] = None):
        self.id = entity_id
        self.name = name
        self.type = entity_type
        self.attributes = attributes or {}
        self.relations = []  # 与其他实体的关系
        self.mentions = []  # 在文本中的提及
        self.created_at = datetime.datetime.now()
        self.updated_at = self.created_at
    
    def add_attribute(self, key: str, value: Any) -> None:
        """添加属性"""
        self.attributes[key] = value
        self.updated_at = datetime.datetime.now()
    
    def add_relation(self, relation_type: str, target_id: str, attributes: Dict[str, Any] = None) -> None:
        """添加关系"""
        self.relations.append({
            "type": relation_type,
            "target_id": target_id,
            "attributes": attributes or {},
            "created_at": datetime.datetime.now()
        })
        self.updated_at = datetime.datetime.now()
    
    def add_mention(self, text_id: str, position: int, context: str) -> None:
        """添加文本提及"""
        self.mentions.append({
            "text_id": text_id,
            "position": position,
            "context": context,
            "created_at": datetime.datetime.now()
        })
        self.updated_at = datetime.datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，递归将所有 datetime 字段转为字符串"""
        def convert(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            if isinstance(obj, list):
                return [convert(item) for item in obj]
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            return obj

        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "attributes": convert(self.attributes),
            "relations": convert(self.relations),
            "mentions": convert(self.mentions),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """从字典创建实体"""
        entity = cls(data["id"], data["name"], data["type"], data["attributes"])
        entity.relations = data["relations"]
        entity.mentions = data["mentions"]
        entity.created_at = datetime.datetime.fromisoformat(data["created_at"])
        entity.updated_at = datetime.datetime.fromisoformat(data["updated_at"])
        return entity


class Character(Entity):
    """角色实体"""
    
    def __init__(self, entity_id: str, name: str, attributes: Dict[str, Any] = None):
        super().__init__(entity_id, name, "character", attributes)


class Location(Entity):
    """地点实体"""
    
    def __init__(self, entity_id: str, name: str, attributes: Dict[str, Any] = None):
        super().__init__(entity_id, name, "location", attributes)


class Item(Entity):
    """物品实体"""
    
    def __init__(self, entity_id: str, name: str, attributes: Dict[str, Any] = None):
        super().__init__(entity_id, name, "item", attributes)


class Event(Entity):
    """事件实体"""
    
    def __init__(self, entity_id: str, name: str, attributes: Dict[str, Any] = None):
        super().__init__(entity_id, name, "event", attributes)
        if "time" not in self.attributes:
            self.attributes["time"] = None
        if "participants" not in self.attributes:
            self.attributes["participants"] = []


class Rule(Entity):
    """世界规则实体"""
    
    def __init__(self, entity_id: str, name: str, attributes: Dict[str, Any] = None):
        super().__init__(entity_id, name, "rule", attributes)
        if "description" not in self.attributes:
            self.attributes["description"] = ""


class KnowledgeGraph:
    """知识图谱管理器"""

    def to_cytoscape(self):
        """
        导出 Cytoscape.js 兼容的 JSON 格式
        {"elements": [ {"data": {...}}, ... ]}
        """
        elements = []
        # 导出实体节点
        for entity in self.entities.values():
            elements.append({
                "data": {
                    "id": entity.id,
                    "label": entity.name,
                    "type": entity.type,
                    **(entity.attributes or {})
                }
            })
        # 导出关系边
        for entity in self.entities.values():
            for rel in getattr(entity, "relations", []):
                elements.append({
                    "data": {
                        "source": entity.id,
                        "target": rel["target_id"],
                        "label": rel["type"],
                        **(rel.get("attributes") or {})
                    }
                })
        return {"elements": elements}
    
    def __init__(self, novel_id: str):
        self.novel_id = novel_id
        self.entities: Dict[str, Entity] = {}
        self.entity_index: Dict[str, Set[str]] = {
            "character": set(),
            "location": set(),
            "item": set(),
            "event": set(),
            "rule": set()
        }
        self.name_to_id: Dict[str, str] = {}
        self._load_graph()
    
    def _get_graph_path(self) -> Path:
        """获取知识图谱文件路径"""
        return KNOWLEDGE_GRAPH_DIR / f"{self.novel_id}.json"
    
    def _load_graph(self) -> None:
        """加载知识图谱"""
        graph_path = self._get_graph_path()
        if not graph_path.exists():
            return
        
        try:
            with open(graph_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 加载实体
            for entity_data in data.get("entities", []):
                entity_type = entity_data["type"]
                entity_id = entity_data["id"]
                
                if entity_type == "character":
                    entity = Character.from_dict(entity_data)
                elif entity_type == "location":
                    entity = Location.from_dict(entity_data)
                elif entity_type == "item":
                    entity = Item.from_dict(entity_data)
                elif entity_type == "event":
                    entity = Event.from_dict(entity_data)
                elif entity_type == "rule":
                    entity = Rule.from_dict(entity_data)
                else:
                    entity = Entity.from_dict(entity_data)
                
                self.entities[entity_id] = entity
                self.entity_index[entity_type].add(entity_id)
                self.name_to_id[entity.name] = entity_id
        
        except Exception as e:
            logging.error(f"加载知识图谱失败: {e}")
    
    def save_graph(self) -> None:
        """保存知识图谱"""
        graph_path = self._get_graph_path()
        
        try:
            data = {
                "novel_id": self.novel_id,
                "entities": [entity.to_dict() for entity in self.entities.values()],
                "updated_at": datetime.datetime.now().isoformat()
            }
            
            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logging.error(f"保存知识图谱失败: {e}")
    
    def add_entity(self, entity: Entity) -> None:
        """添加实体"""
        self.entities[entity.id] = entity
        self.entity_index[entity.type].add(entity.id)
        self.name_to_id[entity.name] = entity.id
        self.save_graph()
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """获取实体"""
        return self.entities.get(entity_id)
    
    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """通过名称获取实体"""
        entity_id = self.name_to_id.get(name)
        if entity_id:
            return self.get_entity(entity_id)
        return None
    
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """获取指定类型的所有实体"""
        entity_ids = self.entity_index.get(entity_type, set())
        return [self.entities[entity_id] for entity_id in entity_ids if entity_id in self.entities]
    
    def add_character(self, name: str, attributes: Dict[str, Any] = None) -> Character:
        """添加角色"""
        entity_id = f"character_{len(self.entity_index['character']) + 1}"
        character = Character(entity_id, name, attributes)
        self.add_entity(character)
        return character
    
    def add_location(self, name: str, attributes: Dict[str, Any] = None) -> Location:
        """添加地点"""
        entity_id = f"location_{len(self.entity_index['location']) + 1}"
        location = Location(entity_id, name, attributes)
        self.add_entity(location)
        return location
    
    def add_item(self, name: str, attributes: Dict[str, Any] = None) -> Item:
        """添加物品"""
        entity_id = f"item_{len(self.entity_index['item']) + 1}"
        item = Item(entity_id, name, attributes)
        self.add_entity(item)
        return item
    
    def add_event(self, name: str, attributes: Dict[str, Any] = None) -> Event:
        """添加事件"""
        entity_id = f"event_{len(self.entity_index['event']) + 1}"
        event = Event(entity_id, name, attributes)
        self.add_entity(event)
        return event
    
    def add_rule(self, name: str, description: str, attributes: Dict[str, Any] = None) -> Rule:
        """添加世界规则"""
        entity_id = f"rule_{len(self.entity_index['rule']) + 1}"
        if attributes is None:
            attributes = {}
        attributes["description"] = description
        rule = Rule(entity_id, name, attributes)
        self.add_entity(rule)
        return rule
    
    def add_relation(self, source_id: str, relation_type: str, target_id: str, attributes: Dict[str, Any] = None) -> bool:
        """添加关系"""
        source = self.get_entity(source_id)
        target = self.get_entity(target_id)
        
        if not source or not target:
            return False
        
        source.add_relation(relation_type, target_id, attributes)
        self.save_graph()
        return True
    
    def extract_entities_from_text(self, text: str, text_id: str = None) -> List[Tuple[Entity, int, str]]:
        """从文本中提取实体（简单实现）"""
        if text_id is None:
            text_id = f"text_{datetime.datetime.now().timestamp()}"
        
        results = []
        
        # 简单的名称匹配（实际应用中应使用 NER 模型）
        for name, entity_id in self.name_to_id.items():
            if name in text:
                entity = self.get_entity(entity_id)
                position = text.find(name)
                context = text[max(0, position - 20):min(len(text), position + len(name) + 20)]
                
                # 添加提及
                entity.add_mention(text_id, position, context)
                
                results.append((entity, position, context))
        
        self.save_graph()
        return results
    
    def check_consistency(self, text: str) -> List[Dict[str, Any]]:
        """检查文本与知识图谱的一致性"""
        # 提取实体
        entities = self.extract_entities_from_text(text)
        
        # 检查一致性问题
        issues = []
        
        # TODO: 实现更复杂的一致性检查逻辑
        # 例如：检查角色行为是否符合其属性、事件时间线是否合理等
        
        return issues


# 全局知识图谱管理器
_knowledge_graphs: Dict[str, KnowledgeGraph] = {}

def get_knowledge_graph(novel_id: str) -> KnowledgeGraph:
    """获取知识图谱"""
    if novel_id not in _knowledge_graphs:
        _knowledge_graphs[novel_id] = KnowledgeGraph(novel_id)
    return _knowledge_graphs[novel_id]
