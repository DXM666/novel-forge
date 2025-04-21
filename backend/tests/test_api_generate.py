import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_generate_endpoint():
    # 需要先有 memory_id，假设 "test_memory" 可用
    payload = {"memory_id": "test_memory", "prompt": "写一个人物介绍。"}
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert isinstance(data["text"], str)

def test_memory_save_and_get():
    # 保存 memory
    payload = {"memory_id": "test_memory", "text": "这是测试内容。"}
    response = client.post("/memory", json=payload)
    assert response.status_code == 204
    # 获取 memory
    response = client.get("/memory/test_memory")
    assert response.status_code == 200
    data = response.json()
    assert data["memory_id"] == "test_memory"
    # print("memory返回内容：", data["text"])
    # assert data["text"].startswith("这是测试内容。")
