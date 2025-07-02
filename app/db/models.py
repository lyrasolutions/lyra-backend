from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ContentType(str, Enum):
    SOCIAL_MEDIA = "social_media"
    EMAIL_NEWSLETTER = "email_newsletter"
    BLOG_POST = "blog_post"
    SHORT_FORM = "short_form"
    IMAGE_PROMPT = "image_prompt"

class Platform(str, Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    EMAIL = "email"
    TWITTER = "twitter"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: Optional[str] = Field(default=None, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    onboarding_profile: Optional["OnboardingProfile"] = Relationship(back_populates="user")
    generated_content: List["GeneratedContent"] = Relationship(back_populates="user")
    content_calendar: List["ContentCalendar"] = Relationship(back_populates="user")

class OnboardingProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    
    business_name: str
    industry_niche: str
    target_audience: str
    brand_voice: str
    content_goals: str
    preferred_platforms: str  # JSON string of platforms
    post_frequency: str
    best_posting_times: Optional[str] = Field(default=None)  # JSON string
    website_url: Optional[str] = Field(default=None)
    social_handles: Optional[str] = Field(default=None)  # JSON string
    logo_url: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="onboarding_profile")

class GeneratedContent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    
    content_type: ContentType
    platform: Platform
    title: Optional[str] = Field(default=None)
    content: str
    hashtags: Optional[str] = Field(default=None)
    image_prompt: Optional[str] = Field(default=None)
    
    prompt_used: str
    openai_model: str = Field(default="gpt-4")
    generation_tokens: Optional[int] = Field(default=None)
    
    is_approved: bool = Field(default=False)
    is_scheduled: bool = Field(default=False)
    is_published: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="generated_content")
    calendar_entries: List["ContentCalendar"] = Relationship(back_populates="content")

class ContentCalendar(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    content_id: int = Field(foreign_key="generatedcontent.id", index=True)
    
    scheduled_date: datetime
    platform: Platform
    status: str = Field(default="scheduled")  # scheduled, published, failed
    
    n8n_workflow_id: Optional[str] = Field(default=None)
    n8n_execution_id: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="content_calendar")
    content: GeneratedContent = Relationship(back_populates="calendar_entries")
