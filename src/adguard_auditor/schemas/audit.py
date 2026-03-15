from enum import Enum

class ModelServices(str, Enum):
    GEMINI = "gemini"
    CHATGPT = "chatgpt"
    QWEN = "qwen"