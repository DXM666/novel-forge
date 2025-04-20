from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from ..pipeline.style_tuner import style_tuner

router = APIRouter(
    prefix="/api/styles",
    tags=["styles"],
)


class StyleSample(BaseModel):
    """风格样本模型"""
    style_name: str
    sample_text: str
    description: Optional[str] = None


class StyleTuneRequest(BaseModel):
    """风格微调请求模型"""
    style_name: str


@router.post("/samples")
async def add_style_sample(sample: StyleSample):
    """添加风格样本"""
    success = style_tuner.add_style_sample(
        sample.style_name,
        sample.sample_text,
        sample.description
    )
    if not success:
        raise HTTPException(status_code=500, detail="添加风格样本失败")
    return {"message": "样本添加成功", "style_name": sample.style_name}


@router.post("/tune")
async def tune_style_model(request: StyleTuneRequest):
    """微调风格模型"""
    success = style_tuner.tune_style_model(request.style_name)
    if not success:
        raise HTTPException(status_code=500, detail="风格模型微调失败")
    return {"message": "风格模型微调成功", "style_name": request.style_name}


@router.get("/")
async def get_available_styles():
    """获取所有可用的风格列表"""
    styles = style_tuner.get_available_styles()
    return {"styles": styles}
