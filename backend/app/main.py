import os
import logging
import uvicorn
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel, Field

# 导入应用模块
from .ai import (
    generate_text, generate_outline, generate_chapter, 
    polish_content, continue_content, save_novel_element,
    get_novel_element, get_novel_elements_by_type, get_novel_data
)
from .memory import memory_store
from .routers import style
from app.api import knowledge_graph_api, memory_api
from .middleware.middleware import setup_middlewares
from .middleware.error_handler import APIException, NotFoundError, BadRequestError
from .database.db_utils import init_db_pool
from .embeddings import init_embedding_model
from .vector_db_init import init_vector_db, check_external_vector_db
from .cache.cache_factory import cache
from .config import settings

# 使用统一日志配置
from .utils.logging_utils import get_logger, configure_logging

# 配置日志
configure_logging(
    level=settings.log_level.value, 
    log_file=settings.log_file,
    log_format=settings.log_format
)
logger = get_logger(__name__)

# 导入配置验证模块
from .utils.config_validator import validate_config

# 导入应用状态管理模块
from .utils.app_state import get_app_state, ServiceStatus

# 导入错误处理模块
from .utils.error_handler import register_exception_handlers

# 获取应用状态实例
app_state = get_app_state()

# 在启动前验证配置
# 如果在生产环境中，可以设置 exit_on_error 为 True
is_valid = validate_config(exit_on_error=settings.strict_config_validation)
if not is_valid:
    logger.warning("配置验证失败，但应用将继续运行（非严格模式）")

# 创建 FastAPI 应用
app = FastAPI(
    title="NovelForge API",
    description="小说创作辅助AI API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# 初始化数据库
db_initialized = init_db_pool()
if not db_initialized:
    logger.error("数据库初始化失败！")

# 导入API路由
from .api import api_router

# 注册 API 路由
app.include_router(api_router, prefix="/api/v1")

# 注册已有路由器
try:
    from .routes import style, knowledge_graph_api
    
    # 集成路由器
    app.include_router(style.router)
    app.include_router(knowledge_graph_api.router)
    logger.info("已注册所有路由器")
except ImportError as e:
    logger.warning(f"导入路由器时出错: {e}")

# 注册错误处理器
register_exception_handlers(app)
try:
    from .routes import memory_api
    app.include_router(memory_api.router)
except ImportError as e:
    logger.warning(f"导入memory_api路由器时出错: {e}")

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的事件"""
    logger.info("应用启动中...")
    
    # 设置应用状态
    app_state.status = ServiceStatus.STARTING
    
    # 记录关键配置信息
    logger.info(f"环境: {settings.env}")
    logger.info(f"使用的AI模型: {settings.model_provider} - {settings.get_model_name()}")
    logger.info(f"使用的缓存类型: {settings.cache_type}")
    logger.info(f"使用的向量存储: {settings.vector_store_provider}")
    
    # 初始化数据库连接池
    logger.info("初始化数据库连接池...")
    db_initialized = init_db_pool()
    if not db_initialized:
        logger.error("数据库连接池初始化失败")
        app_state.set_component_status("database", ServiceStatus.UNAVAILABLE, "数据库连接池初始化失败")
    else:
        app_state.set_component_status("database", ServiceStatus.RUNNING, "数据库连接池初始化成功")
    
    # 初始化向量数据库
    logger.info("初始化向量数据库...")
    from .vector_db_init import init_vector_db
    vector_db_initialized = init_vector_db()
    if not vector_db_initialized:
        logger.error("向量数据库初始化失败")
        app_state.set_component_status("vector_store", ServiceStatus.UNAVAILABLE, "向量数据库初始化失败")
    else:
        app_state.set_component_status("vector_store", ServiceStatus.RUNNING, "向量数据库初始化成功")
        
    # 初始化缓存
    from .cache.cache_factory import init_cache
    cache_initialized = init_cache()
    if not cache_initialized:
        logger.warning("缓存初始化失败，将使用内存缓存替代")
        app_state.set_component_status("cache", ServiceStatus.DEGRADED, "使用内存缓存替代")
    else:
        app_state.set_component_status("cache", ServiceStatus.RUNNING, f"缓存初始化成功，使用{settings.cache_type}")
    
    # 所有组件检查完成，应用开始运行
    app_state.status = ServiceStatus.RUNNING
    logger.info("应用已成功启动！")
    
    # 检查缓存状态
    logger.info("检查缓存状态...")
    cache_type = cache.get_type()
    cache_available = cache.health_check()
    logger.info(f"缓存类型: {cache_type}, 状态: {'可用' if cache_available else '不可用'}")
    
    logger.info("应用初始化完成")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行的事件"""
    logger.info("应用关闭中...")
    app_state.status = ServiceStatus.STOPPING
    
    # 关闭数据库连接
    try:
        from .database.db_utils import close_db_pool
        close_db_pool()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {e}")
    
    # 关闭缓存
    try:
        if hasattr(cache, 'close'):
            cache.close()
            logger.info("缓存连接已关闭")
    except Exception as e:
        logger.error(f"关闭缓存连接时出错: {e}")
    
    logger.info("应用已安全关闭")

# 请求/响应模型
class GenerateRequest(BaseModel):
    memory_id: str
    prompt: str

class GenerateResponse(BaseModel):
    text: str

class MemoryRequest(BaseModel):
    memory_id: str
    text: str

# 小说元素模型
class Character(BaseModel):
    name: str
    role: str
    desc: Optional[str] = None

class Location(BaseModel):
    name: str
    desc: str

class Item(BaseModel):
    name: str
    desc: str

class Scene(BaseModel):
    title: str
    summary: str
    characters: List[str] = Field(default_factory=list)
    location: Optional[str] = None

class Chapter(BaseModel):
    title: str
    summary: str
    scenes: List[Scene] = Field(default_factory=list)

class Outline(BaseModel):
    skeleton: str
    chapters: List[Chapter] = Field(default_factory=list)

class Style(BaseModel):
    name: str
    description: Optional[str] = None
    sample: Optional[str] = None

# 小说生成请求/响应模型
class OutlineRequest(BaseModel):
    novel_id: str
    style: Optional[Style] = None

class OutlineResponse(BaseModel):
    success: bool
    novel_id: str
    outline: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ChapterRequest(BaseModel):
    novel_id: str
    chapter_id: str
    style: Optional[Style] = None

class ChapterResponse(BaseModel):
    success: bool
    novel_id: str
    chapter_id: str
    content: Optional[str] = None
    error: Optional[str] = None

class ContentRequest(BaseModel):
    novel_id: str
    chapter_id: str
    content: str
    style: Optional[Style] = None

class ElementRequest(BaseModel):
    novel_id: str
    element_type: str  # character, location, item, etc.
    element_id: str
    data: Dict[str, Any]

class ElementResponse(BaseModel):
    success: bool
    novel_id: str
    element_type: str
    element_id: str
    error: Optional[str] = None

@app.post("/generate", response_model=GenerateResponse)
async def generate_endpoint(req: GenerateRequest):
    """
    调用 AI 生成文本，并追加到指定 memory_id。
    """
    try:
        result = generate_text(req.memory_id, req.prompt)
        return GenerateResponse(text=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory", status_code=204)
async def save_memory(req: MemoryRequest):
    """
    将文本追加到 memory store。
    """
    memory_store.add(req.memory_id, req.text)
    return

@app.get("/memory/{memory_id}", response_model=MemoryRequest)
async def get_memory(memory_id: str):
    """
    获取指定 memory_id 的存储内容。
    """
    text = memory_store.get(memory_id)
    return MemoryRequest(memory_id=memory_id, text=text)


# 小说大纲生成接口
@app.post("/api/outline/generate", response_model=OutlineResponse)
async def generate_outline_endpoint(req: OutlineRequest):
    """
    生成小说大纲。
    """
    try:
        result = generate_outline(req.novel_id, req.style.dict() if req.style else None)
        return OutlineResponse(
            success=result.get("success", False),
            novel_id=req.novel_id,
            outline=result.get("result", {}).get("outline"),
            error=result.get("error") or result.get("result", {}).get("error")
        )
    except Exception as e:
        return OutlineResponse(success=False, novel_id=req.novel_id, error=str(e))


# 章节生成接口
@app.post("/api/chapter/generate", response_model=ChapterResponse)
async def generate_chapter_endpoint(req: ChapterRequest):
    """
    生成章节内容。
    """
    try:
        result = generate_chapter(req.novel_id, req.chapter_id, req.style.dict() if req.style else None)
        return ChapterResponse(
            success=result.get("success", False),
            novel_id=req.novel_id,
            chapter_id=req.chapter_id,
            content=result.get("result", {}).get("chapter_content"),
            error=result.get("error") or result.get("result", {}).get("error")
        )
    except Exception as e:
        return ChapterResponse(success=False, novel_id=req.novel_id, chapter_id=req.chapter_id, error=str(e))


# 内容优化接口
@app.post("/api/chapter/polish", response_model=ChapterResponse)
async def polish_chapter_endpoint(req: ContentRequest):
    """
    优化章节内容。
    """
    try:
        result = polish_content(req.novel_id, req.chapter_id, req.content, req.style.dict() if req.style else None)
        return ChapterResponse(
            success=result.get("success", False),
            novel_id=req.novel_id,
            chapter_id=req.chapter_id,
            content=result.get("result", {}).get("chapter_content"),
            error=result.get("error") or result.get("result", {}).get("error")
        )
    except Exception as e:
        return ChapterResponse(success=False, novel_id=req.novel_id, chapter_id=req.chapter_id, error=str(e))


# 续写接口
@app.post("/api/chapter/continue", response_model=ChapterResponse)
async def continue_chapter_endpoint(req: ContentRequest):
    """
    续写章节内容。
    """
    try:
        result = continue_content(req.novel_id, req.chapter_id, req.content)
        return ChapterResponse(
            success=result.get("success", False),
            novel_id=req.novel_id,
            chapter_id=req.chapter_id,
            content=result.get("result", {}).get("chapter_content"),
            error=result.get("error") or result.get("result", {}).get("error")
        )
    except Exception as e:
        return ChapterResponse(success=False, novel_id=req.novel_id, chapter_id=req.chapter_id, error=str(e))


# 小说元素管理接口
@app.post("/api/novel/element", response_model=ElementResponse)
async def save_element_endpoint(req: ElementRequest):
    """
    保存小说元素（角色、地点、物品等）。
    """
    try:
        success = save_novel_element(req.novel_id, req.element_type, req.element_id, req.data)
        return ElementResponse(
            success=success,
            novel_id=req.novel_id,
            element_type=req.element_type,
            element_id=req.element_id
        )
    except Exception as e:
        return ElementResponse(
            success=False,
            novel_id=req.novel_id,
            element_type=req.element_type,
            element_id=req.element_id,
            error=str(e)
        )


@app.get("/api/novel/element/{novel_id}/{element_type}/{element_id}")
async def get_element_endpoint(novel_id: str, element_type: str, element_id: str):
    """
    获取小说元素。
    """
    try:
        element = get_novel_element(novel_id, element_type, element_id)
        if not element:
            raise HTTPException(status_code=404, detail=f"元素不存在: {element_type}/{element_id}")
        return element
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/novel/elements/{novel_id}/{element_type}")
async def get_elements_by_type_endpoint(novel_id: str, element_type: str):
    """
    获取指定类型的所有小说元素。
    """
    try:
        elements = get_novel_elements_by_type(novel_id, element_type)
        return {"elements": elements}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/novel/data/{novel_id}")
async def get_novel_data_endpoint(novel_id: str):
    """
    获取小说的所有数据。
    """
    try:
        data = get_novel_data(novel_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
