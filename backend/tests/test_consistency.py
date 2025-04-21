import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.pipeline.consistency import check_character_consistency, check_plot_consistency

def test_character_consistency():
    # 正常内容应返回 True
    text = "张三在北京遇到了李四。"
    assert check_character_consistency(text, novel_id="test_novel") is True

    # 明显冲突内容（如角色不存在等，实际需结合你的实现）
    text2 = "虚构角色在火星大战外星人。"
    result = check_character_consistency(text2, novel_id="test_novel")
    assert isinstance(result, bool)

def test_plot_consistency():
    text = "张三参加了北京的会议，随后前往上海。"
    assert check_plot_consistency(text, novel_id="test_novel") is True
