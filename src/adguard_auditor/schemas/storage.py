from pydantic import BaseModel, Field
from enum import Enum

class RowData(BaseModel):
    row_data: list = Field(default_factory=list)

class ModelServices(str, Enum):
    GEMINI = "gemini"
    CHATGPT = "chatgpt"
    QWEN = "qwen"