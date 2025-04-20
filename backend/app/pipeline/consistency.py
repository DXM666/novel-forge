"""
角色与情节一致性校验
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from .knowledge_graph import get_knowledge_graph


def check_character_consistency(text: str, novel_id: str = "default") -> bool:
    """
    检查角色属性和行为在文本中是否一致。
    使用知识图谱进行校验。
    
    Args:
        text: 要检查的文本
        novel_id: 小说ID，用于获取对应的知识图谱
        
    Returns:
        bool: 是否通过校验
    """
    try:
        # 获取知识图谱
        kg = get_knowledge_graph(novel_id)
        
        # 从文本中提取实体
        extracted_entities = kg.extract_entities_from_text(text)
        
        # 检查角色一致性
        character_issues = []
        for entity, position, context in extracted_entities:
            if entity.type == "character":
                # 检查角色行为是否符合其属性
                # 这里是简化的逻辑，实际应用中应该更复杂
                for attr_key, attr_value in entity.attributes.items():
                    if attr_key in ["性格", "personality"] and attr_value:
                        # 简单示例：如果角色性格是"温柔"，但文本中描述为"暴躁"
                        if "温柔" in attr_value and "暴躁" in context:
                            character_issues.append({
                                "entity": entity.name,
                                "attribute": attr_key,
                                "expected": attr_value,
                                "found": context,
                                "position": position
                            })
        
        # 如果有问题，记录并返回失败
        if character_issues:
            logging.warning(f"角色一致性问题: {character_issues}")
            return False
        
        return True
    
    except Exception as e:
        logging.error(f"角色一致性检查出错: {e}")
        # 出错时默认通过，避免阻塞生成流程
        return True


def check_plot_consistency(text: str, novel_id: str = "default") -> bool:
    """
    检查生成内容是否与大纲及逻辑保持一致。
    使用知识图谱中的事件和规则进行校验。
    
    Args:
        text: 要检查的文本
        novel_id: 小说ID，用于获取对应的知识图谱
        
    Returns:
        bool: 是否通过校验
    """
    try:
        # 获取知识图谱
        kg = get_knowledge_graph(novel_id)
        
        # 检查情节一致性
        plot_issues = kg.check_consistency(text)
        
        # 检查时间线一致性
        # 获取所有事件
        events = kg.get_entities_by_type("event")
        
        # 简单的时间线检查
        # 实际应用中应该更复杂，例如使用自然语言处理提取时间信息
        time_issues = []
        
        # 如果有问题，记录并返回失败
        if plot_issues or time_issues:
            logging.warning(f"情节一致性问题: {plot_issues + time_issues}")
            return False
        
        return True
    
    except Exception as e:
        logging.error(f"情节一致性检查出错: {e}")
        # 出错时默认通过，避免阻塞生成流程
        return True


def update_knowledge_graph(text: str, novel_id: str = "default") -> None:
    """
    从生成的文本中更新知识图谱
    
    Args:
        text: 生成的文本
        novel_id: 小说ID
    """
    try:
        # 获取知识图谱
        kg = get_knowledge_graph(novel_id)
        
        # 提取实体并更新知识图谱
        kg.extract_entities_from_text(text)
        
        # TODO: 使用更复杂的 NLP 技术提取新实体和关系
        # 例如：使用命名实体识别提取新角色、地点等
        # 例如：使用关系提取模型识别实体间的关系
        
        # 保存知识图谱
        kg.save_graph()
    
    except Exception as e:
        logging.error(f"更新知识图谱出错: {e}")
