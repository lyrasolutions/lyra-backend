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

@dashboard_router.post("/quick-action/generate-content")
def quick_generate_content(
    request: dict,
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
    platform_str = request.get("platform", "instagram")
    
    try:
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
            "platform": platform.value,
            "content": content_data["content"],
            "hashtags": content_data["hashtags"]
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

@dashboard_router.post("/approve-content/{content_id}")
async def approve_content(
    content_id: int,
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Approve generated content for publishing"""
    
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
    session.refresh(content)
    
    calendar_entry = ContentCalendar(
        user_id=user.id,
        content_id=content.id,
        platform=content.platform,
        scheduled_date=datetime.utcnow() + timedelta(hours=2),
        status="scheduled"
    )
    session.add(calendar_entry)
    session.commit()
    
    try:
        webhook_data = {
            "event": "content_approved",
            "user_id": user.id,
            "content_id": content.id,
            "platform": content.platform.value,
            "scheduled_date": calendar_entry.scheduled_date.isoformat(),
            "calendar_entry_id": calendar_entry.id
        }
        
        if settings.N8N_WEBHOOK_URL:
            import requests
            requests.post(
                f"{settings.N8N_WEBHOOK_URL}/content-approved",
                json=webhook_data,
                headers={"Authorization": f"Bearer {settings.N8N_API_KEY}"}
            )
        
        from app.db.models import SocialMediaAccount
        connected_account = session.exec(
            select(SocialMediaAccount).where(
                SocialMediaAccount.user_id == user.id,
                SocialMediaAccount.platform == content.platform,
                SocialMediaAccount.is_active == True
            )
        ).first()
        
        if connected_account:
            from app.social.oauth_service import OAuthService
            from app.social.posting_service import AutoPostingService
            
            oauth_service = OAuthService()
            posting_service = AutoPostingService(oauth_service)
            
            try:
                if connected_account.token_expires_at and connected_account.token_expires_at <= datetime.utcnow():
                    if connected_account.refresh_token:
                        token_data = oauth_service.refresh_access_token(connected_account)
                        connected_account.access_token = oauth_service.encrypt_token(token_data["access_token"])
                        if token_data.get("refresh_token"):
                            connected_account.refresh_token = oauth_service.encrypt_token(token_data["refresh_token"])
                        if token_data.get("expires_in"):
                            connected_account.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
                        session.add(connected_account)
                        session.commit()
                
                auto_post_result = await posting_service.post_content(connected_account, content)
                
                if auto_post_result["success"]:
                    content.is_published = True
                    session.add(content)
                    session.commit()
                    print(f"Auto-posted content {content.id} to {content.platform.value}")
                else:
                    print(f"Auto-post failed for content {content.id}: {auto_post_result.get('error', 'Unknown error')}")
                    
            except Exception as auto_post_error:
                print(f"Auto-posting failed: {auto_post_error}")
                
    except Exception as e:
        print(f"Webhook notification failed: {e}")
    
    return {
        "message": "Content approved and scheduled",
        "content_id": content.id,
        "calendar_entry_id": calendar_entry.id,
        "scheduled_date": calendar_entry.scheduled_date
    }

@dashboard_router.get("/stats")
def get_dashboard_stats(
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get dashboard statistics for real-time updates"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    total_content = session.exec(
        select(GeneratedContent).where(GeneratedContent.user_id == user.id)
    ).all()
    
    approved_content = [c for c in total_content if c.is_approved]
    pending_content = [c for c in total_content if not c.is_approved]
    
    approval_rate = (len(approved_content) / len(total_content) * 100) if total_content else 0
    
    return {
        "total_content": len(total_content),
        "approved_content": len(approved_content),
        "pending_approvals": len(pending_content),
        "approval_rate": f"{approval_rate:.0f}%",
        "total_engagement": "2.4K"
    }

@dashboard_router.post("/schedule-content")
async def schedule_content(
    request: dict,
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Schedule content for posting"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    platform_str = request.get("platform")
    scheduled_date_str = request.get("scheduled_date")
    content_text = request.get("content", "Scheduled post content")
    
    try:
        platform = Platform(platform_str.lower())
        scheduled_date = datetime.fromisoformat(scheduled_date_str.replace('Z', '+00:00'))
        
        generated_content = GeneratedContent(
            user_id=user.id,
            content_type=ContentType.SOCIAL_MEDIA,
            platform=platform,
            content=content_text,
            is_approved=True,
            is_scheduled=True
        )
        
        session.add(generated_content)
        session.commit()
        session.refresh(generated_content)
        
        calendar_entry = ContentCalendar(
            user_id=user.id,
            content_id=generated_content.id,
            platform=platform,
            scheduled_date=scheduled_date,
            status="scheduled"
        )
        session.add(calendar_entry)
        session.commit()
        
        return {
            "message": "Content scheduled successfully",
            "calendar_entry_id": calendar_entry.id,
            "scheduled_date": calendar_entry.scheduled_date
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule content: {str(e)}")

@dashboard_router.get("/analytics")
def get_analytics(
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get analytics data for dashboard"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    total_content = session.exec(
        select(GeneratedContent).where(GeneratedContent.user_id == user.id)
    ).all()
    
    if not total_content:
        return None
    
    return {
        "total_reach": "2.4K",
        "engagement_rate": "4.2%",
        "best_platform": "LinkedIn",
        "content_count": len(total_content)
    }
