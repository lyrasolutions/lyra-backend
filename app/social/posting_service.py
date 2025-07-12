from app.social.oauth_service import OAuthService
from app.db.models import SocialMediaAccount, GeneratedContent
from typing import Dict
import requests
import json

class AutoPostingService:
    def __init__(self, oauth_service: OAuthService):
        self.oauth_service = oauth_service
    
    async def post_content(self, account: SocialMediaAccount, content: GeneratedContent) -> Dict:
        """Post content to the specified platform"""
        
        platform = account.platform.value
        
        if platform == "instagram":
            return await self.post_to_instagram(account, content)
        elif platform == "linkedin":
            return await self.post_to_linkedin(account, content)
        elif platform == "facebook":
            return await self.post_to_facebook(account, content)
        elif platform == "tiktok":
            return await self.post_to_tiktok(account, content)
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    
    async def post_to_instagram(self, account: SocialMediaAccount, content: GeneratedContent) -> Dict:
        """Post content to Instagram using Graph API"""
        
        access_token = self.oauth_service.decrypt_token(account.access_token)
        
        post_data = {
            "caption": content.content,
            "access_token": access_token
        }
        
        if content.hashtags:
            post_data["caption"] += f"\n\n{content.hashtags}"
        
        url = f"https://graph.instagram.com/{account.platform_user_id}/media"
        response = requests.post(url, data=post_data)
        
        if response.status_code == 200:
            media_data = response.json()
            
            publish_url = f"https://graph.instagram.com/{account.platform_user_id}/media_publish"
            publish_data = {
                "creation_id": media_data["id"],
                "access_token": access_token
            }
            
            publish_response = requests.post(publish_url, data=publish_data)
            
            if publish_response.status_code == 200:
                return {
                    "success": True,
                    "platform": "instagram",
                    "post_id": publish_response.json().get("id"),
                    "message": "Posted to Instagram successfully"
                }
        
        return {
            "success": False,
            "platform": "instagram",
            "error": response.text,
            "message": "Failed to post to Instagram"
        }
    
    async def post_to_linkedin(self, account: SocialMediaAccount, content: GeneratedContent) -> Dict:
        """Post content to LinkedIn using API"""
        
        access_token = self.oauth_service.decrypt_token(account.access_token)
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        post_content = content.content
        if content.hashtags:
            post_content += f"\n\n{content.hashtags}"
        
        post_data = {
            "author": f"urn:li:person:{account.platform_user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post_content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        url = "https://api.linkedin.com/v2/ugcPosts"
        response = requests.post(url, headers=headers, json=post_data)
        
        if response.status_code == 201:
            return {
                "success": True,
                "platform": "linkedin",
                "post_id": response.json().get("id"),
                "message": "Posted to LinkedIn successfully"
            }
        
        return {
            "success": False,
            "platform": "linkedin",
            "error": response.text,
            "message": "Failed to post to LinkedIn"
        }
    
    async def post_to_facebook(self, account: SocialMediaAccount, content: GeneratedContent) -> Dict:
        """Post content to Facebook using Graph API"""
        
        access_token = self.oauth_service.decrypt_token(account.access_token)
        
        post_content = content.content
        if content.hashtags:
            post_content += f"\n\n{content.hashtags}"
        
        post_data = {
            "message": post_content,
            "access_token": access_token
        }
        
        url = f"https://graph.facebook.com/{account.platform_user_id}/feed"
        response = requests.post(url, data=post_data)
        
        if response.status_code == 200:
            return {
                "success": True,
                "platform": "facebook",
                "post_id": response.json().get("id"),
                "message": "Posted to Facebook successfully"
            }
        
        return {
            "success": False,
            "platform": "facebook",
            "error": response.text,
            "message": "Failed to post to Facebook"
        }
    
    async def post_to_tiktok(self, account: SocialMediaAccount, content: GeneratedContent) -> Dict:
        """Post content to TikTok using API"""
        
        return {
            "success": False,
            "platform": "tiktok",
            "message": "TikTok posting requires video content - text-only posts not supported",
            "error": "TikTok API requires video upload for content creation"
        }
