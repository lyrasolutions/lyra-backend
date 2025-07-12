from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from typing import Dict
from app.auth.routes import get_current_user
from app.db.session import get_session
from app.db.models import User, SocialMediaAccount, Platform, GeneratedContent
from app.social.oauth_service import OAuthService
from app.social.posting_service import AutoPostingService
from app.core.config import settings
from datetime import datetime, timedelta
import requests
import json

social_router = APIRouter()
oauth_service = OAuthService()
posting_service = AutoPostingService(oauth_service)

@social_router.get("/oauth/{platform}/authorize")
async def initiate_oauth(
    platform: str,
    current_user: Dict = Depends(get_current_user)
):
    """Initiate OAuth flow for social media platform"""
    
    supported_platforms = ["instagram", "facebook", "linkedin", "tiktok"]
    if platform not in supported_platforms:
        raise HTTPException(status_code=400, detail="Unsupported platform")
    
    try:
        auth_data = oauth_service.get_authorization_url(platform)
        return auth_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating OAuth for {platform}: {str(e)}")

@social_router.post("/oauth/{platform}/callback")
async def oauth_callback(
    platform: str,
    request: Request,
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Handle OAuth callback and store tokens"""
    
    body = await request.json()
    code = body.get("code")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        token_data = oauth_service.exchange_code_for_tokens(platform, code)
        
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to obtain access token")
        
        profile_data = oauth_service.get_user_profile(platform, access_token)
        
        platform_user_id = str(profile_data.get("id", ""))
        platform_username = profile_data.get("username") or profile_data.get("name", "")
        
        existing_account = session.exec(
            select(SocialMediaAccount).where(
                SocialMediaAccount.user_id == user.id,
                SocialMediaAccount.platform == Platform(platform)
            )
        ).first()
        
        if existing_account:
            existing_account.access_token = oauth_service.encrypt_token(access_token)
            if refresh_token:
                existing_account.refresh_token = oauth_service.encrypt_token(refresh_token)
            if expires_in:
                existing_account.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            existing_account.platform_user_id = platform_user_id
            existing_account.platform_username = platform_username
            existing_account.is_active = True
            existing_account.updated_at = datetime.utcnow()
            session.add(existing_account)
        else:
            new_account = SocialMediaAccount(
                user_id=user.id,
                platform=Platform(platform),
                platform_user_id=platform_user_id,
                platform_username=platform_username,
                access_token=oauth_service.encrypt_token(access_token),
                refresh_token=oauth_service.encrypt_token(refresh_token) if refresh_token else None,
                token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None,
                is_active=True
            )
            session.add(new_account)
        
        session.commit()
        
        return {
            "message": f"{platform.title()} account connected successfully",
            "platform": platform,
            "username": platform_username,
            "status": "connected"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing OAuth callback for {platform}: {str(e)}")

@social_router.post("/auto-post/{platform}")
async def auto_post_content(
    platform: str,
    request: Request,
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Auto-post approved content to connected platform"""
    
    body = await request.json()
    content_id = body.get("content_id")
    
    if not content_id:
        raise HTTPException(status_code=400, detail="Content ID is required")
    
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
    
    if not content.is_approved:
        raise HTTPException(status_code=400, detail="Content must be approved before posting")
    
    account = session.exec(
        select(SocialMediaAccount).where(
            SocialMediaAccount.user_id == user.id,
            SocialMediaAccount.platform == Platform(platform),
            SocialMediaAccount.is_active == True
        )
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail=f"No connected {platform} account found")
    
    try:
        if account.token_expires_at and account.token_expires_at <= datetime.utcnow():
            if account.refresh_token:
                token_data = oauth_service.refresh_access_token(account)
                account.access_token = oauth_service.encrypt_token(token_data["access_token"])
                if token_data.get("refresh_token"):
                    account.refresh_token = oauth_service.encrypt_token(token_data["refresh_token"])
                if token_data.get("expires_in"):
                    account.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
                session.add(account)
                session.commit()
            else:
                raise HTTPException(status_code=401, detail=f"{platform} token expired and no refresh token available")
        
        result = await posting_service.post_content(account, content)
        
        if result["success"]:
            content.is_published = True
            session.add(content)
            session.commit()
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error posting to {platform}: {str(e)}")

@social_router.get("/platforms/status")
async def get_platform_status(
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get connection status for all social media platforms"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    accounts = session.exec(
        select(SocialMediaAccount).where(
            SocialMediaAccount.user_id == user.id,
            SocialMediaAccount.is_active == True
        )
    ).all()
    
    platforms = {
        "instagram": False,
        "facebook": False,
        "linkedin": False,
        "tiktok": False
    }
    
    connected_accounts = {}
    
    for account in accounts:
        platform_name = account.platform.value
        platforms[platform_name] = True
        connected_accounts[platform_name] = {
            "username": account.platform_username,
            "connected_at": account.created_at.isoformat(),
            "expires_at": account.token_expires_at.isoformat() if account.token_expires_at else None
        }
    
    return {
        "platforms": platforms,
        "connected_accounts": connected_accounts,
        "connected_count": sum(platforms.values()),
        "total_platforms": len(platforms)
    }

@social_router.delete("/disconnect/{platform}")
async def disconnect_platform(
    platform: str,
    current_user: Dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Disconnect a social media platform"""
    
    user = session.exec(select(User).where(User.username == current_user["username"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    account = session.exec(
        select(SocialMediaAccount).where(
            SocialMediaAccount.user_id == user.id,
            SocialMediaAccount.platform == Platform(platform)
        )
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail=f"No connected {platform} account found")
    
    account.is_active = False
    session.add(account)
    session.commit()
    
    return {
        "message": f"{platform.title()} account disconnected successfully",
        "platform": platform,
        "status": "disconnected"
    }
