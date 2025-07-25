"""
记忆系统演示脚本 - 展示如何使用小说创作记忆系统
"""
import os
import sys
import logging
import json
from datetime import datetime
from pprint import pprint

# 添加父目录到路径，以便导入应用模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.memory_system import memory_system
from app.vector_store import get_embedding, vector_store
from app.database.db_utils import create_project, get_project

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_demo_project():
    """创建示例项目"""
    print("创建示例小说项目...")
    success, project_id = create_project(
        title="星际旅程",
        description="一部关于星际探索和人类命运的科幻小说",
        author_id="user_001"
    )
    
    if not success:
        print(f"创建项目失败: {project_id}")
        return None
    
    print(f"项目创建成功，ID: {project_id}")
    return project_id


def add_demo_characters(project_id):
    """添加示例角色"""
    print("\n添加角色...")
    
    # 添加主角
    memory_system.add_character(
        project_id=project_id,
        character_id="li_hang",
        name="李航",
        role="protagonist",
        description="34岁的航天工程师，性格沉稳冷静，有着敏锐的观察力和过人的解决问题能力。在一次任务中接收到来自深空的神秘信号后，决定踏上星际旅程。",
        attributes={
            "age": 34,
            "occupation": "航天工程师",
            "skills": ["工程学", "宇航技术", "编程", "物理学"],
            "personality": ["沉稳", "冷静", "理性", "勇敢"]
        }
    )
    
    # 添加配角
    memory_system.add_character(
        project_id=project_id,
        character_id="zhang_mei",
        name="张梅",
        role="supporting",
        description="29岁的天体物理学家，李航的搭档。性格活泼开朗，思维敏捷，是团队的灵魂人物。对宇宙充满好奇，渴望探索未知。",
        attributes={
            "age": 29,
            "occupation": "天体物理学家",
            "skills": ["天体物理", "数据分析", "外星语言学"],
            "personality": ["活泼", "好奇", "聪明", "幽默"]
        }
    )
    
    # 添加反派
    memory_system.add_character(
        project_id=project_id,
        character_id="commander_zhao",
        name="赵司令",
        role="antagonist",
        description="星环联邦的军事领袖，50多岁，野心勃勃，认为人类应该通过武力征服宇宙。想要获取李航发现的外星技术用于军事目的。",
        attributes={
            "age": 53,
            "occupation": "军事领袖",
            "skills": ["战略", "领导", "政治", "武器技术"],
            "personality": ["野心勃勃", "专制", "冷酷", "聪明"]
        }
    )
    
    print("角色添加完成")


def add_demo_locations(project_id):
    """添加示例地点"""
    print("\n添加地点...")
    
    # 添加地球基地
    memory_system.add_location(
        project_id=project_id,
        location_id="earth_base",
        name="地球太空中心",
        description="位于中国海南的大型太空发射基地，拥有最先进的航天技术和研究设施。李航和张梅的工作基地。",
        attributes={
            "type": "space_center",
            "location": "中国海南",
            "facilities": ["发射台", "研究实验室", "训练中心", "指挥控制室"]
        }
    )
    
    # 添加太空站
    memory_system.add_location(
        project_id=project_id,
        location_id="orbital_station",
        name="轨道空间站",
        description="环绕地球运行的国际空间站，是李航接收到神秘信号的地方。配备了先进的通信设备和天文观测仪器。",
        attributes={
            "type": "space_station",
            "location": "地球轨道",
            "facilities": ["观测室", "通信中心", "生活舱", "科研实验室"]
        }
    )
    
    # 添加外星遗迹
    memory_system.add_location(
        project_id=project_id,
        location_id="alien_ruins",
        name="泰坦星遗迹",
        description="位于土星卫星泰坦上的神秘外星文明遗迹，蕴含着高等文明的科技和知识。是李航和张梅探索的主要目标。",
        attributes={
            "type": "alien_structure",
            "location": "土星卫星泰坦",
            "features": ["古代建筑", "能量核心", "数据库", "传送装置"]
        }
    )
    
    print("地点添加完成")


def add_demo_rules(project_id):
    """添加示例世界规则"""
    print("\n添加世界规则...")
    
    # 添加星际旅行规则
    memory_system.add_rule(
        project_id=project_id,
        rule_id="space_travel",
        name="星际旅行技术",
        description="在故事世界中，人类已经掌握了曲速引擎技术，可以进行星际旅行，但仍受到能源限制，最远只能到达土星系统。更远的旅行需要依靠外星技术。"
    )
    
    # 添加星环联邦规则
    memory_system.add_rule(
        project_id=project_id,
        rule_id="stellar_federation",
        name="星环联邦政治",
        description="星环联邦是地球上最强大的政治军事联盟，控制着大部分太空资源和技术。联邦内部分为民用科研部门和军事部门，两者经常有冲突。"
    )
    
    # 添加外星文明规则
    memory_system.add_rule(
        project_id=project_id,
        rule_id="alien_civilization",
        name="先驱者文明",
        description="一个已经消失的高等外星文明，在太阳系各处留下了遗迹和技术。他们似乎在预警某种宇宙威胁，并为人类留下了应对的方法。"
    )
    
    print("世界规则添加完成")


def add_demo_events(project_id):
    """添加示例事件"""
    print("\n添加事件...")
    
    # 添加事件1：接收信号
    memory_system.add_event(
        project_id=project_id,
        event_id="receive_signal",
        title="接收神秘信号",
        description="李航在轨道空间站值班时，接收到来自土星方向的神秘信号，信号中包含了泰坦星表面的坐标和一些无法解读的数据。",
        characters=["li_hang"],
        location="orbital_station",
        attributes={
            "chapter": 1,
            "importance": "high",
            "consequences": ["引发探索", "引起军方注意"]
        }
    )
    
    # 添加事件2：组建探索队
    memory_system.add_event(
        project_id=project_id,
        event_id="form_team",
        title="组建探索队",
        description="李航和张梅说服太空中心领导，组建一支探索队前往泰坦星调查神秘信号的来源。赵司令派遣军方人员加入，暗中监视。",
        characters=["li_hang", "zhang_mei", "commander_zhao"],
        location="earth_base",
        attributes={
            "chapter": 2,
            "importance": "medium",
            "consequences": ["团队冲突", "资源支持"]
        }
    )
    
    # 添加事件3：发现遗迹
    memory_system.add_event(
        project_id=project_id,
        event_id="discover_ruins",
        title="发现泰坦星遗迹",
        description="探索队抵达泰坦星，在信号指示的坐标处发现了掩埋在冰层下的巨大外星建筑群。建筑内部有仍在运行的能量系统和数据库。",
        characters=["li_hang", "zhang_mei"],
        location="alien_ruins",
        attributes={
            "chapter": 5,
            "importance": "high",
            "consequences": ["科技发现", "文明线索"]
        }
    )
    
    print("事件添加完成")


def add_chapter_summaries(project_id):
    """添加章节摘要"""
    print("\n添加章节摘要...")
    
    # 第一章摘要
    memory_system.add_chapter_summary(
        project_id=project_id,
        chapter_number=1,
        title="神秘信号",
        summary="李航在轨道空间站执行例行任务时，接收到一段来自土星方向的神秘信号。信号分析显示，它指向泰坦星表面的特定坐标。李航将这一发现报告给地球基地，引起了科研部门和军方的关注。"
    )
    
    # 第二章摘要
    memory_system.add_chapter_summary(
        project_id=project_id,
        chapter_number=2,
        title="组建探索队",
        summary="李航和同事张梅提出前往泰坦星探索的计划。经过激烈讨论，太空中心决定批准这一计划，但军方代表赵司令坚持派遣军事人员共同前往。团队成员之间的紧张关系初现端倪。"
    )
    
    # 第三章摘要
    memory_system.add_chapter_summary(
        project_id=project_id,
        chapter_number=3,
        title="启程",
        summary="探索队完成准备工作，搭乘'远征号'飞船启程前往土星系统。旅途中，李航和张梅尝试进一步解析神秘信号，发现其中可能包含某种警告。与此同时，军方成员似乎有自己的秘密议程。"
    )
    
    print("章节摘要添加完成")


def demonstrate_memory_search(project_id):
    """演示记忆搜索功能"""
    print("\n演示记忆搜索功能...")
    
    # 搜索与李航相关的记忆
    print("\n搜索与'李航'相关的记忆:")
    results = memory_system.long_term.search(project_id, "李航的背景和特点是什么")
    for i, result in enumerate(results):
        print(f"\n结果 {i+1} (相似度: {result.get('similarity', 0):.4f}):")
        print(f"类型: {result['entry_type']}")
        print(f"内容: {result['content'][:200]}...")
    
    # 搜索与外星遗迹相关的记忆
    print("\n搜索与'外星遗迹'相关的记忆:")
    results = memory_system.long_term.search(project_id, "外星遗迹有什么特点和重要发现")
    for i, result in enumerate(results):
        print(f"\n结果 {i+1} (相似度: {result.get('similarity', 0):.4f}):")
        print(f"类型: {result['entry_type']}")
        print(f"内容: {result['content'][:200]}...")
    
    # 搜索与故事情节相关的记忆
    print("\n搜索与'故事情节'相关的记忆:")
    results = memory_system.long_term.search(project_id, "主要角色之间有什么冲突")
    for i, result in enumerate(results):
        print(f"\n结果 {i+1} (相似度: {result.get('similarity', 0):.4f}):")
        print(f"类型: {result['entry_type']}")
        print(f"内容: {result['content'][:200]}...")


def demonstrate_context_generation(project_id):
    """演示上下文生成功能"""
    print("\n演示上下文生成功能...")
    
    # 添加一些短期记忆
    memory_system.short_term.add(
        project_id=project_id,
        content="李航和张梅正在研究遗迹中发现的能量核心",
        entry_type="scene"
    )
    
    memory_system.short_term.add(
        project_id=project_id,
        content="能量核心似乎可以产生一种未知的空间扭曲效应",
        entry_type="observation"
    )
    
    memory_system.short_term.add(
        project_id=project_id,
        content="军方成员秘密向赵司令报告了这一发现",
        entry_type="event"
    )
    
    # 生成用于AI推理的上下文
    print("\n为查询'李航应该如何处理能量核心'生成上下文:")
    context = memory_system.get_context_for_generation(
        project_id=project_id,
        query="李航应该如何处理能量核心"
    )
    
    print("\n生成的上下文:")
    print(context)


def main():
    """主函数"""
    print("=== 小说创作记忆系统演示 ===\n")
    
    # 创建示例项目
    project_id = create_demo_project()
    if not project_id:
        return
    
    # 添加示例数据
    add_demo_characters(project_id)
    add_demo_locations(project_id)
    add_demo_rules(project_id)
    add_demo_events(project_id)
    add_chapter_summaries(project_id)
    
    # 演示功能
    demonstrate_memory_search(project_id)
    demonstrate_context_generation(project_id)
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    main()
