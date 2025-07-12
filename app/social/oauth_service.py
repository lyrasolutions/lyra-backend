from authlib.integrations.requests_client import OAuth2Session
from cryptography.fernet import Fernet
from app.core.config import settings
from app.db.models import SocialMediaAccount, Platform
from typing import Dict, Optional
import base64
import requests
from datetime import datetime, timedelta

class OAuthService:
    def __init__(self):
        if settings.ENCRYPTION_KEY:
            self.encryption_key = settings.ENCRYPTION_KEY.encode()
        else:
            self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    def get_authorization_url(self, platform: str) -> Dict[str, str]:
        """Generate OAuth authorization URL for platform"""
        
        if platform == "instagram":
            client_id = settings.INSTAGRAM_CLIENT_ID
            redirect_uri = settings.OAUTH_REDIRECT_URI
            scope = "user_profile,user_media"
            auth_url = f"https://api.instagram.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&response_type=code"
            
        elif platform == "facebook":
            client_id = settings.FACEBOOK_CLIENT_ID
            redirect_uri = settings.OAUTH_REDIRECT_URI
            scope = "pages_manage_posts,pages_read_engagement"
            auth_url = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&response_type=code"
            
        elif platform == "linkedin":
            client_id = settings.LINKEDIN_CLIENT_ID
            redirect_uri = settings.OAUTH_REDIRECT_URI
            scope = "w_member_social"
            auth_url = f"https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}"
            
        elif platform == "tiktok":
            client_id = settings.TIKTOK_CLIENT_ID
            redirect_uri = settings.OAUTH_REDIRECT_URI
            scope = "user.info.basic,video.publish"
            auth_url = f"https://www.tiktok.com/auth/authorize/?client_key={client_id}&response_type=code&scope={scope}&redirect_uri={redirect_uri}"
            
        else:
            raise ValueError(f"Unsupported platform: {platform}")
            
        return {
            "authorization_url": auth_url,
            "platform": platform
        }
    
    def exchange_code_for_tokens(self, platform: str, code: str) -> Dict:
        """Exchange authorization code for access tokens"""
        
        if platform == "instagram":
            token_url = "https://api.instagram.com/oauth/access_token"
            data = {
                "client_id": settings.INSTAGRAM_CLIENT_ID,
                "client_secret": settings.INSTAGRAM_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": settings.OAUTH_REDIRECT_URI,
                "code": code
            }
            
        elif platform == "facebook":
            token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
            data = {
                "client_id": settings.FACEBOOK_CLIENT_ID,
                "client_secret": settings.FACEBOOK_CLIENT_SECRET,
                "redirect_uri": settings.OAUTH_REDIRECT_URI,
                "code": code
            }
            
        elif platform == "linkedin":
            token_url = "https://www.linkedin.com/oauth/v2/accessToken"
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.OAUTH_REDIRECT_URI,
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET
            }
            
        elif platform == "tiktok":
            token_url = "https://open-api.tiktok.com/oauth/access_token/"
            data = {
                "client_key": settings.TIKTOK_CLIENT_ID,
                "client_secret": settings.TIKTOK_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code"
            }
            
        else:
            raise ValueError(f"Unsupported platform: {platform}")
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def refresh_access_token(self, account: SocialMediaAccount) -> Dict:
        """Refresh expired access token"""
        
        if not account.refresh_token:
            raise ValueError("No refresh token available")
        
        refresh_token = self.decrypt_token(account.refresh_token)
        platform = account.platform.value
        
        if platform == "instagram":
            token_url = "https://graph.instagram.com/refresh_access_token"
            data = {
                "grant_type": "ig_refresh_token",
                "access_token": self.decrypt_token(account.access_token)
            }
            
        elif platform == "facebook":
            token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
            data = {
                "grant_type": "fb_exchange_token",
                "client_id": settings.FACEBOOK_CLIENT_ID,
                "client_secret": settings.FACEBOOK_CLIENT_SECRET,
                "fb_exchange_token": self.decrypt_token(account.access_token)
            }
            
        elif platform == "linkedin":
            token_url = "https://www.linkedin.com/oauth/v2/accessToken"
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET
            }
            
        elif platform == "tiktok":
            token_url = "https://open-api.tiktok.com/oauth/refresh_token/"
            data = {
                "client_key": settings.TIKTOK_CLIENT_ID,
                "client_secret": settings.TIKTOK_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            
        else:
            raise ValueError(f"Unsupported platform: {platform}")
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt token for database storage"""
        return self.cipher.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token from database"""
        return self.cipher.decrypt(encrypted_token.encode()).decode()
    
    def get_user_profile(self, platform: str, access_token: str) -> Dict:
        """Get user profile information from platform"""
        
        if platform == "instagram":
            url = f"https://graph.instagram.com/me?fields=id,username&access_token={access_token}"
            
        elif platform == "facebook":
            url = f"https://graph.facebook.com/me?access_token={access_token}"
            
        elif platform == "linkedin":
            headers = {"Authorization": f"Bearer {access_token}"}
            url = "https://api.linkedin.com/v2/people/~"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
            
        elif platform == "tiktok":
            url = f"https://open-api.tiktok.com/user/info/?access_token={access_token}"
            
        else:
            raise ValueError(f"Unsupported platform: {platform}")
        
        if platform != "linkedin":
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
