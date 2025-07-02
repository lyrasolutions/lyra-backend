from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import User, OnboardingProfile
from app.dashboard.routes import get_current_user
from app.onboarding.schemas import OnboardingRequest, OnboardingResponse
from typing import Dict
import json

onboarding_router = APIRouter()

@onboarding_router.post("/submit", response_model=OnboardingResponse)
def submit_onboarding(
    onboarding_data: OnboardingRequest,
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Submit onboarding form data and tie it to the authenticated user"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_profile = session.exec(
        select(OnboardingProfile).where(OnboardingProfile.user_id == user.id)
    ).first()
    
    if existing_profile:
        existing_profile.business_name = onboarding_data.business_name
        existing_profile.industry_niche = onboarding_data.industry_niche
        existing_profile.target_audience = onboarding_data.target_audience
        existing_profile.brand_voice = onboarding_data.brand_voice
        existing_profile.content_goals = onboarding_data.content_goals
        existing_profile.preferred_platforms = json.dumps(onboarding_data.preferred_platforms)
        existing_profile.post_frequency = onboarding_data.post_frequency
        existing_profile.best_posting_times = json.dumps(onboarding_data.best_posting_times) if onboarding_data.best_posting_times else None
        existing_profile.website_url = onboarding_data.website_url
        existing_profile.social_handles = json.dumps(onboarding_data.social_handles) if onboarding_data.social_handles else None
        existing_profile.logo_url = onboarding_data.logo_url
        
        session.add(existing_profile)
        profile = existing_profile
    else:
        profile = OnboardingProfile(
            user_id=user.id,
            business_name=onboarding_data.business_name,
            industry_niche=onboarding_data.industry_niche,
            target_audience=onboarding_data.target_audience,
            brand_voice=onboarding_data.brand_voice,
            content_goals=onboarding_data.content_goals,
            preferred_platforms=json.dumps(onboarding_data.preferred_platforms),
            post_frequency=onboarding_data.post_frequency,
            best_posting_times=json.dumps(onboarding_data.best_posting_times) if onboarding_data.best_posting_times else None,
            website_url=onboarding_data.website_url,
            social_handles=json.dumps(onboarding_data.social_handles) if onboarding_data.social_handles else None,
            logo_url=onboarding_data.logo_url
        )
        session.add(profile)
    
    session.commit()
    session.refresh(profile)
    
    return OnboardingResponse(
        message="Onboarding profile saved successfully",
        profile_id=profile.id,
        user_id=user.id
    )

@onboarding_router.get("/profile", response_model=OnboardingResponse)
def get_onboarding_profile(
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get the user's onboarding profile"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = session.exec(
        select(OnboardingProfile).where(OnboardingProfile.user_id == user.id)
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Onboarding profile not found")
    
    return OnboardingResponse(
        message="Onboarding profile retrieved successfully",
        profile_id=profile.id,
        user_id=user.id,
        profile_data={
            "business_name": profile.business_name,
            "industry_niche": profile.industry_niche,
            "target_audience": profile.target_audience,
            "brand_voice": profile.brand_voice,
            "content_goals": profile.content_goals,
            "preferred_platforms": json.loads(profile.preferred_platforms),
            "post_frequency": profile.post_frequency,
            "best_posting_times": json.loads(profile.best_posting_times) if profile.best_posting_times else None,
            "website_url": profile.website_url,
            "social_handles": json.loads(profile.social_handles) if profile.social_handles else None,
            "logo_url": profile.logo_url
        }
    )
