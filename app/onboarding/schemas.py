from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class OnboardingRequest(BaseModel):
    business_name: str
    industry_niche: str
    target_audience: str
    brand_voice: str
    content_goals: str
    preferred_platforms: List[str]
    post_frequency: str
    best_posting_times: Optional[List[str]] = None
    website_url: Optional[str] = None
    social_handles: Optional[Dict[str, str]] = None
    logo_url: Optional[str] = None

class OnboardingResponse(BaseModel):
    message: str
    profile_id: int
    user_id: int
    profile_data: Optional[Dict[str, Any]] = None
