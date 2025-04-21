from fastapi import APIRouter
from app.pipeline.knowledge_graph import get_knowledge_graph

router = APIRouter()

@router.get("/api/knowledge-graph/{novel_id}")
def get_knowledge_graph_cytoscape(novel_id: str):
    kg = get_knowledge_graph(novel_id)
    return kg.to_cytoscape()
