from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Dict, List, Optional
from sqlmodel import Session, select
from app.core.config import settings
from app.db.session import get_session
from app.db.models import User, OnboardingProfile, GeneratedContent, ContentCalendar, ContentType, Platform
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

@dashboard_router.get("/widgets")
def get_dashboard_widgets(
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get enhanced dashboard widgets with real-time stats"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    total_content = session.exec(
        select(GeneratedContent).where(GeneratedContent.user_id == user.id)
    ).all()
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_content = [c for c in total_content if c.created_at >= week_ago]
    
    upcoming_posts = session.exec(
        select(ContentCalendar).where(
            ContentCalendar.user_id == user.id,
            ContentCalendar.status == "scheduled",
            ContentCalendar.scheduled_date >= datetime.utcnow()
        ).order_by(ContentCalendar.scheduled_date).limit(5)
    ).all()
    
    approval_rate = (len([c for c in total_content if c.is_approved]) / len(total_content) * 100) if total_content else 0
    
    return {
        "widgets": {
            "content_stats": {
                "total_generated": len(total_content),
                "this_week": len(recent_content),
                "approved": len([c for c in total_content if c.is_approved]),
                "published": len([c for c in total_content if c.is_published]),
                "approval_rate": round(approval_rate, 1)
            },
            "upcoming_posts": [
                {
                    "id": post.id,
                    "content_id": post.content_id,
                    "platform": post.platform,
                    "scheduled_date": post.scheduled_date,
                    "days_until": (post.scheduled_date - datetime.utcnow()).days,
                    "hours_until": round((post.scheduled_date - datetime.utcnow()).total_seconds() / 3600, 1)
                }
                for post in upcoming_posts
            ],
            "quick_stats": {
                "pending_approval": len([c for c in total_content if not c.is_approved]),
                "scheduled_today": len([p for p in upcoming_posts if p.scheduled_date.date() == datetime.utcnow().date()]),
                "platforms_active": len(set([c.platform for c in total_content]))
            }
        }
    }

@dashboard_router.get("/calendar-ticker")
def get_calendar_ticker(
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session),
    days_ahead: int = 7
):
    """Get calendar ticker showing upcoming posts with countdown"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    end_date = datetime.utcnow() + timedelta(days=days_ahead)
    
    upcoming_posts = session.exec(
        select(ContentCalendar).where(
            ContentCalendar.user_id == user.id,
            ContentCalendar.status == "scheduled",
            ContentCalendar.scheduled_date >= datetime.utcnow(),
            ContentCalendar.scheduled_date <= end_date
        ).order_by(ContentCalendar.scheduled_date)
    ).all()
    
    ticker_items = []
    for post in upcoming_posts:
        time_until = post.scheduled_date - datetime.utcnow()
        
        content = session.exec(
            select(GeneratedContent).where(GeneratedContent.id == post.content_id)
        ).first()
        
        ticker_items.append({
            "id": post.id,
            "content_preview": content.content[:100] + "..." if content and len(content.content) > 100 else content.content if content else "",
            "platform": post.platform,
            "scheduled_date": post.scheduled_date,
            "countdown": {
                "days": time_until.days,
                "hours": time_until.seconds // 3600,
                "minutes": (time_until.seconds % 3600) // 60,
                "total_minutes": int(time_until.total_seconds() / 60)
            }
        })
    
    return {
        "ticker_items": ticker_items,
        "next_post": ticker_items[0] if ticker_items else None,
        "total_upcoming": len(ticker_items)
    }

@dashboard_router.post("/quick-actions/generate-content")
def quick_generate_content(
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Quick action to generate content based on user's preferences"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = session.exec(
        select(OnboardingProfile).where(OnboardingProfile.user_id == user.id)
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Please complete onboarding first")
    
    import json
    from app.ai.service import AIContentService
    
    ai_service = AIContentService()
    preferred_platforms = json.loads(profile.preferred_platforms)
    
    try:
        platform_str = preferred_platforms[0] if preferred_platforms else "instagram"
        platform = Platform(platform_str.lower())
        
        content_data = ai_service.generate_content(
            profile=profile,
            content_type=ContentType.SOCIAL_MEDIA,
            platform=platform
        )
        
        generated_content = GeneratedContent(
            user_id=user.id,
            content_type=ContentType.SOCIAL_MEDIA,
            platform=platform,
            content=content_data["content"],
            hashtags=content_data["hashtags"],
            prompt_used=content_data["prompt_used"],
            openai_model=content_data["model"],
            generation_tokens=content_data["tokens_used"]
        )
        
        session.add(generated_content)
        session.commit()
        session.refresh(generated_content)
        
        return {
            "message": "Content generated successfully",
            "content_id": generated_content.id,
            "platform": platform,
            "content_preview": content_data["content"][:100] + "..."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")

@dashboard_router.get("/quick-actions/pending-approvals")
def get_pending_approvals(
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get content pending approval for quick action"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    pending_content = session.exec(
        select(GeneratedContent).where(
            GeneratedContent.user_id == user.id,
            GeneratedContent.is_approved == False
        ).order_by(GeneratedContent.created_at.desc()).limit(5)
    ).all()
    
    return {
        "pending_approvals": [
            {
                "id": content.id,
                "content_type": content.content_type,
                "platform": content.platform,
                "content_preview": content.content[:100] + "..." if len(content.content) > 100 else content.content,
                "created_at": content.created_at
            }
            for content in pending_content
        ],
        "total_pending": len(pending_content)
    }
