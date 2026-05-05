from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=500)

class RAGSource(BaseModel):
    pmid: str
    title: str
    relevance_score: float
    year: Optional[int] = None

class ChatResponse(BaseModel):
    message_id: str
    role: str = "assistant"
    content: str
    sources: List[RAGSource]
    session_grounded: bool
    created_at: datetime

class ChatMessageItem(BaseModel):
    id: str
    role: str
    content: str
    sources: Optional[List[dict]] = None
    created_at: datetime

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[ChatMessageItem]
