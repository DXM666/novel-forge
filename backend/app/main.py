import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .ai import generate_text
from .memory import memory_store

# 创建 FastAPI 应用
app = FastAPI(title="NovelForge API")

# 跨域设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求/响应模型
class GenerateRequest(BaseModel):
    memory_id: str
    prompt: str

class GenerateResponse(BaseModel):
    text: str

class MemoryRequest(BaseModel):
    memory_id: str
    text: str

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

if __name__ == "__main__":
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
