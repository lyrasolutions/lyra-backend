from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import User, OnboardingProfile, ContentCalendar, GeneratedContent
from app.dashboard.routes import get_current_user
from typing import Dict
import json

automation_router = APIRouter()

@automation_router.post("/webhook/onboarding-complete")
async def onboarding_complete_webhook(
    request: Request,
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Webhook triggered when user completes onboarding"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = session.exec(
        select(OnboardingProfile).where(OnboardingProfile.user_id == user.id)
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Onboarding profile not found")
    
    webhook_data = {
        "event": "onboarding_complete",
        "user_id": user.id,
        "username": user.username,
        "business_name": profile.business_name,
        "industry": profile.industry_niche,
        "preferred_platforms": json.loads(profile.preferred_platforms),
        "post_frequency": profile.post_frequency
    }
    
    return {
        "message": "Onboarding completion webhook processed",
        "webhook_data": webhook_data,
        "next_action": "trigger_initial_content_generation"
    }

@automation_router.post("/webhook/content-scheduled")
async def content_scheduled_webhook(
    request: Request,
    session: Session = Depends(get_session)
):
    """Webhook for when content is scheduled for posting"""
    
    body = await request.json()
    content_id = body.get("content_id")
    scheduled_date = body.get("scheduled_date")
    platform = body.get("platform")
    
    if not all([content_id, scheduled_date, platform]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    content = session.exec(
        select(GeneratedContent).where(GeneratedContent.id == content_id)
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    calendar_entry = ContentCalendar(
        user_id=content.user_id,
        content_id=content_id,
        scheduled_date=scheduled_date,
        platform=platform,
        status="scheduled"
    )
    
    session.add(calendar_entry)
    content.is_scheduled = True
    session.add(content)
    session.commit()
    
    return {
        "message": "Content scheduled successfully",
        "calendar_entry_id": calendar_entry.id
    }

@automation_router.post("/webhook/post-published")
async def post_published_webhook(
    request: Request,
    session: Session = Depends(get_session)
):
    """Webhook for when a post is successfully published"""
    
    body = await request.json()
    calendar_entry_id = body.get("calendar_entry_id")
    n8n_execution_id = body.get("execution_id")
    status = body.get("status", "published")
    
    if not calendar_entry_id:
        raise HTTPException(status_code=400, detail="Missing calendar_entry_id")
    
    calendar_entry = session.exec(
        select(ContentCalendar).where(ContentCalendar.id == calendar_entry_id)
    ).first()
    
    if not calendar_entry:
        raise HTTPException(status_code=404, detail="Calendar entry not found")
    
    calendar_entry.status = status
    calendar_entry.n8n_execution_id = n8n_execution_id
    session.add(calendar_entry)
    
    content = session.exec(
        select(GeneratedContent).where(GeneratedContent.id == calendar_entry.content_id)
    ).first()
    
    if content:
        content.is_published = (status == "published")
        session.add(content)
    
    session.commit()
    
    return {
        "message": f"Post status updated to {status}",
        "calendar_entry_id": calendar_entry_id
    }

@automation_router.get("/workflows")
def get_user_workflows(
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get user's automation workflows status"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    scheduled_posts = session.exec(
        select(ContentCalendar).where(
            ContentCalendar.user_id == user.id,
            ContentCalendar.status == "scheduled"
        )
    ).all()
    
    published_posts = session.exec(
        select(ContentCalendar).where(
            ContentCalendar.user_id == user.id,
            ContentCalendar.status == "published"
        )
    ).all()
    
    failed_posts = session.exec(
        select(ContentCalendar).where(
            ContentCalendar.user_id == user.id,
            ContentCalendar.status == "failed"
        )
    ).all()
    
    return {
        "workflows": {
            "scheduled_posts": len(scheduled_posts),
            "published_posts": len(published_posts),
            "failed_posts": len(failed_posts),
            "active_workflows": len([p for p in scheduled_posts if p.n8n_workflow_id])
        },
        "recent_executions": [
            {
                "id": entry.id,
                "content_id": entry.content_id,
                "platform": entry.platform,
                "status": entry.status,
                "scheduled_date": entry.scheduled_date,
                "n8n_workflow_id": entry.n8n_workflow_id,
                "n8n_execution_id": entry.n8n_execution_id
            }
            for entry in (scheduled_posts + published_posts + failed_posts)[-10:]
        ]
    }
