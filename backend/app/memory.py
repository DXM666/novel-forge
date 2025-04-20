class BaseMemoryStore:
    def get(self, memory_id: str) -> str:
        raise NotImplementedError()

    def add(self, memory_id: str, text: str):
        raise NotImplementedError()

class InMemoryStore(BaseMemoryStore):
    def __init__(self):
        self._data = {}

    def get(self, memory_id: str) -> str:
        return self._data.get(memory_id, "")

    def add(self, memory_id: str, text: str):
        prev = self._data.get(memory_id, "")
        self._data[memory_id] = prev + text

# 根据配置可扩展其他存储（如 Redis）
memory_store = InMemoryStore()
