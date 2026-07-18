from enum import Enum

class ModelServices(str, Enum):
    GEMINI = "gemini"
    CHATGPT = "chatgpt"
    DEEPSEEK = "deepseek"
    VERTEX_AI = "vertex_ai"
    UNSLOTH = "unsloth"