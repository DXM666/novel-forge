import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app.pipeline.knowledge_graph import KnowledgeGraph, Entity
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def create_sample_kg(novel_id="test_novel"):
    kg = KnowledgeGraph(novel_id)
    # 添加角色
    kg.add_entity(Entity("c1", "张三", "character"))
    kg.add_entity(Entity("c2", "李四", "character"))
    # 添加地点
    kg.add_entity(Entity("l1", "北京", "location"))
    # 添加关系
    kg.add_relation("c1", "朋友", "c2")
    kg.add_relation("c1", "去过", "l1")
    return kg

def test_to_cytoscape():
    kg = create_sample_kg()
    data = kg.to_cytoscape()
    assert "elements" in data
    node_ids = [e["data"]["id"] for e in data["elements"] if "id" in e["data"]]
    assert "c1" in node_ids and "c2" in node_ids and "l1" in node_ids
    edge_labels = [e["data"]["label"] for e in data["elements"] if "source" in e["data"]]
    assert "朋友" in edge_labels and "去过" in edge_labels

def test_api_knowledge_graph():
    # 这里假设 test_novel 已经有数据，或 KnowledgeGraph 支持自动创建
    response = client.get("/api/knowledge-graph/test_novel")
    assert response.status_code == 200
    data = response.json()
    assert "elements" in data
