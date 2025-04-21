from langchain_ollama import OllamaLLM

model = OllamaLLM(model="qwen2.5:7b")
print(model.invoke("Come up with 10 names for a song about parrots"))