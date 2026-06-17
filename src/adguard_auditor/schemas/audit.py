from enum import Enum

class ModelServices(str, Enum):
    GEMINI = "gemini"
    CHATGPT = "chatgpt"
    QWEN = "qwen"
    VERTEX_AI = "vertex_ai"