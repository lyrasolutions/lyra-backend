from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import User, OnboardingProfile, GeneratedContent, ContentType, Platform
from app.dashboard.routes import get_current_user
from app.ai.service import AIContentService
from app.ai.schemas import ContentGenerationRequest, ContentGenerationResponse, WeeklyContentResponse
from typing import Dict, List

ai_router = APIRouter()
ai_service = AIContentService()

@ai_router.post("/generate-content", response_model=ContentGenerationResponse)
def generate_content(
    request: ContentGenerationRequest,
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Generate AI content based on user's onboarding profile"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = session.exec(
        select(OnboardingProfile).where(OnboardingProfile.user_id == user.id)
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Please complete onboarding first")
    
    try:
        content_data = ai_service.generate_content(
            profile=profile,
            content_type=request.content_type,
            platform=request.platform,
            custom_prompt=request.custom_prompt
        )
        
        generated_content = GeneratedContent(
            user_id=user.id,
            content_type=request.content_type,
            platform=request.platform,
            title=request.title,
            content=content_data["content"],
            hashtags=content_data["hashtags"],
            image_prompt=content_data.get("image_prompt"),
            prompt_used=content_data["prompt_used"],
            openai_model=content_data["model"],
            generation_tokens=content_data["tokens_used"]
        )
        
        session.add(generated_content)
        session.commit()
        session.refresh(generated_content)
        
        return ContentGenerationResponse(
            content_id=generated_content.id,
            content=content_data["content"],
            hashtags=content_data["hashtags"],
            platform=request.platform,
            content_type=request.content_type,
            tokens_used=content_data["tokens_used"],
            message="Content generated successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")

@ai_router.post("/generate-weekly-content", response_model=WeeklyContentResponse)
def generate_weekly_content(
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Generate a week's worth of content based on user's posting frequency"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = session.exec(
        select(OnboardingProfile).where(OnboardingProfile.user_id == user.id)
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Please complete onboarding first")
    
    try:
        content_items = ai_service.generate_weekly_content(profile)
        
        saved_content = []
        for item in content_items:
            generated_content = GeneratedContent(
                user_id=user.id,
                content_type=item["content_type"],
                platform=item["platform"],
                content=item["content"],
                hashtags=item["hashtags"],
                prompt_used=item["prompt_used"],
                openai_model=item["model"],
                generation_tokens=item["tokens_used"]
            )
            session.add(generated_content)
            saved_content.append(generated_content)
        
        session.commit()
        
        for content in saved_content:
            session.refresh(content)
        
        return WeeklyContentResponse(
            message=f"Generated {len(saved_content)} pieces of content for the week",
            content_count=len(saved_content),
            content_ids=[content.id for content in saved_content]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate weekly content: {str(e)}")

@ai_router.get("/content/{content_id}")
def get_generated_content(
    content_id: int,
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a specific piece of generated content"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    content = session.exec(
        select(GeneratedContent).where(
            GeneratedContent.id == content_id,
            GeneratedContent.user_id == user.id
        )
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return {
        "id": content.id,
        "content_type": content.content_type,
        "platform": content.platform,
        "title": content.title,
        "content": content.content,
        "hashtags": content.hashtags,
        "image_prompt": content.image_prompt,
        "is_approved": content.is_approved,
        "is_scheduled": content.is_scheduled,
        "is_published": content.is_published,
        "created_at": content.created_at
    }
