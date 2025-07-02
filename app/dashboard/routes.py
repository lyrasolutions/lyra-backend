from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Dict, List, Optional
from sqlmodel import Session, select
from app.core.config import settings
from app.db.session import get_session
from app.db.models import User, OnboardingProfile, GeneratedContent, ContentCalendar
from datetime import datetime, timedelta

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
dashboard_router = APIRouter()

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return {"username": payload.get("sub")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")

@dashboard_router.get("/")
def read_dashboard(
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get dashboard overview with user stats"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    total_content = session.exec(
        select(GeneratedContent).where(GeneratedContent.user_id == user.id)
    ).all()
    
    scheduled_content = session.exec(
        select(ContentCalendar).where(
            ContentCalendar.user_id == user.id,
            ContentCalendar.status == "scheduled"
        )
    ).all()
    
    onboarding_complete = session.exec(
        select(OnboardingProfile).where(OnboardingProfile.user_id == user.id)
    ).first() is not None
    
    return {
        "message": f"Welcome to your dashboard, {user.username}!",
        "user_id": user.id,
        "onboarding_complete": onboarding_complete,
        "stats": {
            "total_content_generated": len(total_content),
            "scheduled_posts": len(scheduled_content),
            "approved_content": len([c for c in total_content if c.is_approved]),
            "published_content": len([c for c in total_content if c.is_published])
        }
    }

@dashboard_router.get("/content")
def get_user_content(
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session),
    limit: int = 20,
    offset: int = 0
):
    """Get user's generated content with pagination"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    content = session.exec(
        select(GeneratedContent)
        .where(GeneratedContent.user_id == user.id)
        .order_by(GeneratedContent.created_at)
        .offset(offset)
        .limit(limit)
    ).all()
    
    return {
        "content": [
            {
                "id": c.id,
                "content_type": c.content_type,
                "platform": c.platform,
                "title": c.title,
                "content": c.content,
                "hashtags": c.hashtags,
                "is_approved": c.is_approved,
                "is_scheduled": c.is_scheduled,
                "is_published": c.is_published,
                "created_at": c.created_at
            }
            for c in content
        ],
        "total": len(content),
        "limit": limit,
        "offset": offset
    }

@dashboard_router.put("/content/{content_id}/approve")
def approve_content(
    content_id: int,
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Approve a piece of generated content"""
    
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
    
    content.is_approved = True
    session.add(content)
    session.commit()
    
    return {"message": "Content approved successfully"}

@dashboard_router.get("/calendar")
def get_content_calendar(
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get content calendar for date range"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    query = select(ContentCalendar).where(ContentCalendar.user_id == user.id)
    
    if start_date:
        start = datetime.fromisoformat(start_date)
        query = query.where(ContentCalendar.scheduled_date >= start)
    
    if end_date:
        end = datetime.fromisoformat(end_date)
        query = query.where(ContentCalendar.scheduled_date <= end)
    
    calendar_entries = session.exec(query.order_by(ContentCalendar.scheduled_date)).all()
    
    return {
        "calendar_entries": [
            {
                "id": entry.id,
                "content_id": entry.content_id,
                "scheduled_date": entry.scheduled_date,
                "platform": entry.platform,
                "status": entry.status,
                "n8n_workflow_id": entry.n8n_workflow_id
            }
            for entry in calendar_entries
        ]
    }
