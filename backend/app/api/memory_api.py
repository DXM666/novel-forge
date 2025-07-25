"""
记忆系统API - 提供记忆系统功能的REST接口
"""
import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..memory_system import memory_system
from ..vector_store import vector_store

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/api/memory",
    tags=["memory"],
    responses={404: {"description": "未找到"}}
)


# 请求/响应模型
class ProjectRequest(BaseModel):
    title: str
    description: str
    author_id: str


class ProjectResponse(BaseModel):
    success: bool
    project_id: Optional[str] = None
    error: Optional[str] = None


class MemoryRequest(BaseModel):
    project_id: str
    content: str
    entry_type: str
    metadata: Optional[Dict[str, Any]] = None
    add_to_short_term: Optional[bool] = True


class MemoryResponse(BaseModel):
    success: bool
    memory_id: Optional[str] = None
    error: Optional[str] = None


class CharacterRequest(BaseModel):
    project_id: str
    character_id: str
    name: str
    role: str
    description: str
    attributes: Optional[Dict[str, Any]] = None


class LocationRequest(BaseModel):
    project_id: str
    location_id: str
    name: str
    description: str
    attributes: Optional[Dict[str, Any]] = None


class RuleRequest(BaseModel):
    project_id: str
    rule_id: str
    name: str
    description: str
    attributes: Optional[Dict[str, Any]] = None


class EventRequest(BaseModel):
    project_id: str
    event_id: str
    title: str
    description: str
    characters: List[str]
    location: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None


class ChapterSummaryRequest(BaseModel):
    project_id: str
    chapter_number: int
    title: str
    summary: str


class SearchRequest(BaseModel):
    project_id: str
    query: str
    limit: Optional[int] = 5


class ElementResponse(BaseModel):
    success: bool
    element_id: Optional[str] = None
    error: Optional[str] = None


class ContextRequest(BaseModel):
    project_id: str
    query: str
    include_short_term: Optional[bool] = True
    include_long_term: Optional[bool] = True
    include_knowledge_graph: Optional[bool] = True


class ContextResponse(BaseModel):
    success: bool
    context: Optional[str] = None
    error: Optional[str] = None


class SearchResponse(BaseModel):
    success: bool
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


# API端点
@router.post("/project", response_model=ProjectResponse)
async def create_project(request: ProjectRequest):
    """创建新项目"""
    try:
        from ..database.db_utils import create_project
        
        success, result = create_project(
            title=request.title,
            description=request.description,
            author_id=request.author_id
        )
        
        if success:
            return ProjectResponse(success=True, project_id=result)
        else:
            return ProjectResponse(success=False, error=result)
    except Exception as e:
        logger.error(f"创建项目失败: {str(e)}")
        return ProjectResponse(success=False, error=str(e))


@router.post("/memory", response_model=MemoryResponse)
async def add_memory(request: MemoryRequest):
    """添加记忆"""
    try:
        memory_id = memory_system.add_memory(
            project_id=request.project_id,
            content=request.content,
            entry_type=request.entry_type,
            metadata=request.metadata,
            add_to_short_term=request.add_to_short_term
        )
        
        if memory_id:
            return MemoryResponse(success=True, memory_id=memory_id)
        else:
            return MemoryResponse(success=False, error="添加记忆失败")
    except Exception as e:
        logger.error(f"添加记忆失败: {str(e)}")
        return MemoryResponse(success=False, error=str(e))


@router.post("/character", response_model=ElementResponse)
async def add_character(request: CharacterRequest):
    """添加角色"""
    try:
        success = memory_system.add_character(
            project_id=request.project_id,
            character_id=request.character_id,
            name=request.name,
            role=request.role,
            description=request.description,
            attributes=request.attributes
        )
        
        if success:
            return ElementResponse(success=True, element_id=request.character_id)
        else:
            return ElementResponse(success=False, error="添加角色失败")
    except Exception as e:
        logger.error(f"添加角色失败: {str(e)}")
        return ElementResponse(success=False, error=str(e))


@router.post("/location", response_model=ElementResponse)
async def add_location(request: LocationRequest):
    """添加地点"""
    try:
        success = memory_system.add_location(
            project_id=request.project_id,
            location_id=request.location_id,
            name=request.name,
            description=request.description,
            attributes=request.attributes
        )
        
        if success:
            return ElementResponse(success=True, element_id=request.location_id)
        else:
            return ElementResponse(success=False, error="添加地点失败")
    except Exception as e:
        logger.error(f"添加地点失败: {str(e)}")
        return ElementResponse(success=False, error=str(e))


@router.post("/rule", response_model=ElementResponse)
async def add_rule(request: RuleRequest):
    """添加世界规则"""
    try:
        success = memory_system.add_rule(
            project_id=request.project_id,
            rule_id=request.rule_id,
            name=request.name,
            description=request.description,
            attributes=request.attributes
        )
        
        if success:
            return ElementResponse(success=True, element_id=request.rule_id)
        else:
            return ElementResponse(success=False, error="添加世界规则失败")
    except Exception as e:
        logger.error(f"添加世界规则失败: {str(e)}")
        return ElementResponse(success=False, error=str(e))


@router.post("/event", response_model=ElementResponse)
async def add_event(request: EventRequest):
    """添加事件"""
    try:
        success = memory_system.add_event(
            project_id=request.project_id,
            event_id=request.event_id,
            title=request.title,
            description=request.description,
            characters=request.characters,
            location=request.location,
            attributes=request.attributes
        )
        
        if success:
            return ElementResponse(success=True, element_id=request.event_id)
        else:
            return ElementResponse(success=False, error="添加事件失败")
    except Exception as e:
        logger.error(f"添加事件失败: {str(e)}")
        return ElementResponse(success=False, error=str(e))


@router.post("/chapter-summary", response_model=MemoryResponse)
async def add_chapter_summary(request: ChapterSummaryRequest):
    """添加章节摘要"""
    try:
        memory_id = memory_system.add_chapter_summary(
            project_id=request.project_id,
            chapter_number=request.chapter_number,
            title=request.title,
            summary=request.summary
        )
        
        if memory_id:
            return MemoryResponse(success=True, memory_id=memory_id)
        else:
            return MemoryResponse(success=False, error="添加章节摘要失败")
    except Exception as e:
        logger.error(f"添加章节摘要失败: {str(e)}")
        return MemoryResponse(success=False, error=str(e))


@router.post("/search", response_model=SearchResponse)
async def search_memories(request: SearchRequest):
    """搜索记忆"""
    try:
        results = memory_system.long_term.search(
            project_id=request.project_id,
            query=request.query,
            limit=request.limit
        )
        
        return SearchResponse(success=True, results=results)
    except Exception as e:
        logger.error(f"搜索记忆失败: {str(e)}")
        return SearchResponse(success=False, error=str(e))


@router.post("/context", response_model=ContextResponse)
async def get_generation_context(request: ContextRequest):
    """获取生成上下文"""
    try:
        context = memory_system.get_context_for_generation(
            project_id=request.project_id,
            query=request.query,
            include_short_term=request.include_short_term,
            include_long_term=request.include_long_term,
            include_knowledge_graph=request.include_knowledge_graph
        )
        
        return ContextResponse(success=True, context=context)
    except Exception as e:
        logger.error(f"获取生成上下文失败: {str(e)}")
        return ContextResponse(success=False, error=str(e))


@router.get("/short-term/{project_id}", response_model=Dict[str, Any])
async def get_short_term_memories(project_id: str, limit: Optional[int] = None):
    """获取短期记忆"""
    try:
        memories = memory_system.short_term.get(project_id, limit)
        return {"success": True, "memories": memories}
    except Exception as e:
        logger.error(f"获取短期记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/long-term/{project_id}", response_model=Dict[str, Any])
async def get_long_term_memories(project_id: str, entry_type: Optional[str] = None, limit: int = 100):
    """获取长期记忆"""
    try:
        memories = memory_system.long_term.get(project_id, entry_type, limit)
        return {"success": True, "memories": memories}
    except Exception as e:
        logger.error(f"获取长期记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-graph/{project_id}/nodes/{node_type}", response_model=Dict[str, Any])
async def get_knowledge_graph_nodes(project_id: str, node_type: str):
    """获取知识图谱节点"""
    try:
        nodes = memory_system.knowledge_graph.get_nodes_by_type(project_id, node_type)
        return {"success": True, "nodes": nodes}
    except Exception as e:
        logger.error(f"获取知识图谱节点失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-graph/{project_id}/relationships", response_model=Dict[str, Any])
async def get_knowledge_graph_relationships(
    project_id: str, 
    node_type: Optional[str] = None, 
    node_id: Optional[str] = None
):
    """获取知识图谱关系"""
    try:
        relationships = memory_system.knowledge_graph.get_relationships(project_id, node_type, node_id)
        return {"success": True, "relationships": relationships}
    except Exception as e:
        logger.error(f"获取知识图谱关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
