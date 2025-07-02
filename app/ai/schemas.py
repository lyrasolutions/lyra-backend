from pydantic import BaseModel
from typing import Optional, List
from app.db.models import ContentType, Platform

class ContentGenerationRequest(BaseModel):
    content_type: ContentType
    platform: Platform
    title: Optional[str] = None
    custom_prompt: Optional[str] = None

class ContentGenerationResponse(BaseModel):
    content_id: int
    content: str
    hashtags: Optional[str] = None
    platform: Platform
    content_type: ContentType
    tokens_used: int
    message: str

class WeeklyContentResponse(BaseModel):
    message: str
    content_count: int
    content_ids: List[int]
