import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_get_styles():
    response = client.get("/api/styles/")
    assert response.status_code == 200
    data = response.json()
    assert "styles" in data
    assert isinstance(data["styles"], list)

# 如需添加风格样本和微调测试，可根据实际风格名和样本内容补充
