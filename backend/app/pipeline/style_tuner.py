from typing import Dict, Any, List, Optional
import datetime
import os
import json
import logging
from pathlib import Path

# 风格样本存储路径
STYLE_SAMPLES_DIR = Path("./data/style_samples")
STYLE_MODELS_DIR = Path("./data/style_models")

# 确保目录存在
STYLE_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
STYLE_MODELS_DIR.mkdir(parents=True, exist_ok=True)


class StyleTuner:
    """风格微调器：处理用户上传的样本文本，并基于样本微调风格模型"""
    
    def __init__(self):
        self.styles_metadata = {}
        self._load_styles_metadata()
    
    def _load_styles_metadata(self):
        """加载已有的风格元数据"""
        metadata_path = STYLE_SAMPLES_DIR / "metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    self.styles_metadata = json.load(f)
            except Exception as e:
                logging.error(f"加载风格元数据失败: {e}")
                self.styles_metadata = {}
    
    def _save_styles_metadata(self):
        """保存风格元数据"""
        metadata_path = STYLE_SAMPLES_DIR / "metadata.json"
        try:
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.styles_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存风格元数据失败: {e}")
    
    def add_style_sample(self, style_name: str, sample_text: str, description: Optional[str] = None) -> bool:
        """
        添加风格样本
        
        Args:
            style_name: 风格名称
            sample_text: 样本文本
            description: 风格描述（可选）
            
        Returns:
            bool: 是否成功添加
        """
        # 规范化风格名称
        style_name = style_name.strip().lower()
        
        # 创建风格目录
        style_dir = STYLE_SAMPLES_DIR / style_name
        style_dir.mkdir(exist_ok=True)
        
        # 生成样本文件名
        sample_count = len(list(style_dir.glob("sample_*.txt")))
        sample_path = style_dir / f"sample_{sample_count + 1}.txt"
        
        # 保存样本文本
        try:
            with open(sample_path, "w", encoding="utf-8") as f:
                f.write(sample_text)
        except Exception as e:
            logging.error(f"保存样本文本失败: {e}")
            return False
        
        # 更新元数据
        if style_name not in self.styles_metadata:
            self.styles_metadata[style_name] = {
                "name": style_name,
                "description": description or f"{style_name}风格",
                "sample_count": 1,
                "tuned_model": None,
                "created_at": str(datetime.datetime.now()),
                "updated_at": str(datetime.datetime.now())
            }
        else:
            self.styles_metadata[style_name]["sample_count"] += 1
            self.styles_metadata[style_name]["updated_at"] = str(datetime.datetime.now())
            if description:
                self.styles_metadata[style_name]["description"] = description
        
        self._save_styles_metadata()
        return True
    
    def tune_style_model(self, style_name: str) -> bool:
        """
        基于样本微调风格模型
        
        Args:
            style_name: 风格名称
            
        Returns:
            bool: 是否成功微调
        """
        # 规范化风格名称
        style_name = style_name.strip().lower()
        
        # 检查风格是否存在
        if style_name not in self.styles_metadata:
            logging.error(f"风格 {style_name} 不存在")
            return False
        
        # 检查样本数量
        style_dir = STYLE_SAMPLES_DIR / style_name
        samples = list(style_dir.glob("sample_*.txt"))
        if len(samples) < 1:
            logging.error(f"风格 {style_name} 样本数量不足")
            return False
        
        # TODO: 实现实际的微调逻辑
        # 这里是占位代码，实际应用中应该调用相应的模型微调API
        logging.info(f"开始微调风格模型: {style_name}")
        
        # 模拟微调过程
        import time
        time.sleep(2)  # 模拟耗时操作
        
        # 更新元数据
        model_path = STYLE_MODELS_DIR / f"{style_name}_model.bin"
        self.styles_metadata[style_name]["tuned_model"] = str(model_path)
        self.styles_metadata[style_name]["updated_at"] = str(datetime.datetime.now())
        self._save_styles_metadata()
        
        # 创建一个假的模型文件
        with open(model_path, "w") as f:
            f.write("模拟的模型文件")
        
        logging.info(f"风格模型微调完成: {style_name}")
        return True
    
    def get_available_styles(self) -> List[Dict[str, Any]]:
        """获取所有可用的风格列表"""
        return [
            {
                "name": name,
                "description": info["description"],
                "sample_count": info["sample_count"],
                "has_model": info["tuned_model"] is not None
            }
            for name, info in self.styles_metadata.items()
        ]
    
    def get_style_embedding(self, style_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定风格的嵌入向量
        
        Args:
            style_name: 风格名称
            
        Returns:
            Optional[Dict[str, Any]]: 风格嵌入信息，包含名称、描述和向量
        """
        # 规范化风格名称
        style_name = style_name.strip().lower()
        
        # 检查风格是否存在
        if style_name not in self.styles_metadata:
            return None
        
        info = self.styles_metadata[style_name]
        
        # 检查是否有微调模型
        if not info["tuned_model"]:
            return None
        
        # TODO: 实际应用中应该加载模型并提取嵌入向量
        # 这里返回模拟的嵌入向量
        return {
            "name": style_name,
            "description": info["description"],
            "vector": [0.1, 0.2, 0.3],  # 模拟向量
            "is_custom": True
        }


# 全局实例
style_tuner = StyleTuner()
