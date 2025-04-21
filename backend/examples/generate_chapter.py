"""
示例脚本：生成一个小说章节并展示各个功能模块的作用
"""
import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

from app.ai import generate_text
from app.memory import memory_store
from app.pipeline.knowledge_graph import get_knowledge_graph
from app.pipeline.style_tuner import style_tuner
# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')



def setup_knowledge_graph():
    """设置示例知识图谱"""
    novel_id = "example_novel"
    kg = get_knowledge_graph(novel_id)
    
    # 添加角色
    hero = kg.add_character("李剑", {"性格": "勇敢正直", "年龄": 25, "职业": "侠客"})
    villain = kg.add_character("黑煞", {"性格": "阴险狡诈", "年龄": 40, "职业": "邪派掌门"})
    mentor = kg.add_character("白眉道人", {"性格": "智慧沉稳", "年龄": 70, "职业": "道士"})
    
    # 添加地点
    mountain = kg.add_location("青云山", {"气候": "常年云雾缭绕", "特点": "道家圣地"})
    city = kg.add_location("东海城", {"规模": "繁华大城", "特点": "商贾云集"})
    
    # 添加物品
    sword = kg.add_item("青锋剑", {"材质": "寒铁", "特性": "锋利无比"})
    
    # 添加事件
    kg.add_event("拜师学艺", {"时间": "十年前", "参与者": ["李剑", "白眉道人"], "地点": "青云山"})
    kg.add_event("邪派入侵", {"时间": "三天前", "参与者": ["黑煞"], "地点": "东海城"})
    
    # 添加关系
    kg.add_relation(hero.id, "徒弟", mentor.id)
    kg.add_relation(hero.id, "敌人", villain.id)
    kg.add_relation(hero.id, "拥有", sword.id)
    
    # 添加世界规则
    kg.add_rule("武功境界", "分为入门、小成、大成、宗师四个境界")
    kg.add_rule("内力运行", "内力沿任督二脉运行，可以增强武功威力")
    
    # 保存知识图谱
    kg.save_graph()
    logging.info(f"知识图谱设置完成，共有 {len(kg.entities)} 个实体")
    
    return novel_id

def setup_style():
    """设置示例风格"""
    # 添加金庸风格样本
    sample_text = """
    李剑手持青锋，剑光如电，剑气纵横。那黑煞虽然武功高强，但面对李剑的青锋剑法，也不禁心惊胆战。
    "哼，小子，你以为凭借一把宝剑就能胜过我吗？"黑煞冷笑道。
    李剑不答，手中青锋却是越发凌厉，剑招如行云流水，绵绵不绝。
    """
    style_tuner.add_style_sample("金庸", sample_text, "金庸武侠风格，讲究气势磅礴、行云流水")
    
    # 微调风格模型
    style_tuner.tune_style_model("金庸")
    
    logging.info("风格设置完成")

def main():
    """主函数"""
    # 设置知识图谱
    novel_id = setup_knowledge_graph()
    
    # 设置风格
    setup_style()
    
    # 创建记忆ID
    memory_id = f"{novel_id}_chapter1"
    
    # 添加一些背景信息到记忆
    memory_store.add(memory_id, "李剑是青云山白眉道人的弟子，习得一身武艺。")
    memory_store.add(memory_id, "黑煞率领邪派弟子攻入东海城，杀害了城主。")
    memory_store.add(memory_id, "李剑奉师命下山，前往东海城调查此事。")
    
    # 生成章节开头
    prompt = "chapter 第一章 东海风云\n李剑来到东海城，发现城中百姓惶恐不安。请用金庸风格续写。"
    print(f"[调试] generate_text 输入 prompt: {prompt}")
    result = generate_text(memory_id, prompt)
    print(f"[调试] generate_text 返回: {result}")
    print("\n===== 生成的章节开头 =====")
    print(result if result else "[警告] 未生成任何内容！")
    
    # 生成对话
    prompt = "李剑在城中遇到一位老者，询问黑煞的下落。"
    print(f"[调试] generate_text 输入 prompt: {prompt}")
    result = generate_text(memory_id, prompt)
    print(f"[调试] generate_text 返回: {result}")
    print("\n===== 生成的对话 =====")
    print(result if result else "[警告] 未生成任何内容！")
    
    # 生成场景描写
    prompt = "scene 夜晚，李剑独自来到城东的一座破庙，据说这里是黑煞的藏身之处。"
    print(f"[调试] generate_text 输入 prompt: {prompt}")
    result = generate_text(memory_id, prompt)
    print(f"[调试] generate_text 返回: {result}")
    print("\n===== 生成的场景 =====")
    print(result if result else "[警告] 未生成任何内容！")
    
    # 生成战斗场景
    prompt = "李剑在破庙中遇到了黑煞，两人展开激烈打斗。"
    print(f"[调试] generate_text 输入 prompt: {prompt}")
    result = generate_text(memory_id, prompt)
    print(f"[调试] generate_text 返回: {result}")
    print("\n===== 生成的战斗场景 =====")
    print(result if result else "[警告] 未生成任何内容！")
    
    # 打印记忆内容
    print("\n===== 完整记忆内容 =====")
    print(memory_store.get(memory_id))

if __name__ == "__main__":
    main()
