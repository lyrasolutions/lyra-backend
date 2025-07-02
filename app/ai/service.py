import openai
from app.core.config import settings
from app.db.models import OnboardingProfile, GeneratedContent, ContentType, Platform
from typing import Dict, List, Optional
import json

class AIContentService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
    
    def generate_content_prompt(self, profile: OnboardingProfile, content_type: ContentType, platform: Platform) -> str:
        """Generate a structured prompt based on user's onboarding data"""
        
        preferred_platforms = json.loads(profile.preferred_platforms)
        platform_specific = ""
        
        if platform == Platform.INSTAGRAM:
            platform_specific = "Include relevant hashtags and make it visually engaging. Keep captions under 2200 characters."
        elif platform == Platform.TIKTOK:
            platform_specific = "Make it trendy, engaging, and suitable for short-form video content. Include trending hashtags."
        elif platform == Platform.LINKEDIN:
            platform_specific = "Keep it professional and business-focused. Include industry-relevant insights."
        elif platform == Platform.FACEBOOK:
            platform_specific = "Make it conversational and community-focused. Encourage engagement."
        elif platform == Platform.EMAIL:
            platform_specific = "Create a compelling subject line and engaging email content."
        
        content_type_instruction = ""
        if content_type == ContentType.SOCIAL_MEDIA:
            content_type_instruction = "Create engaging social media content"
        elif content_type == ContentType.EMAIL_NEWSLETTER:
            content_type_instruction = "Write a newsletter section"
        elif content_type == ContentType.BLOG_POST:
            content_type_instruction = "Create a blog post outline and introduction"
        elif content_type == ContentType.SHORT_FORM:
            content_type_instruction = "Create short-form content suitable for TikTok or Reels"
        elif content_type == ContentType.IMAGE_PROMPT:
            content_type_instruction = "Create a detailed image generation prompt"
        
        prompt = f"""
        Act as a social media marketer for a {profile.industry_niche} business called "{profile.business_name}" 
        targeting {profile.target_audience} with a {profile.brand_voice} brand voice.
        
        {content_type_instruction} to help achieve this goal: {profile.content_goals}.
        
        Platform: {platform.value}
        {platform_specific}
        
        Business context:
        - Industry: {profile.industry_niche}
        - Target audience: {profile.target_audience}
        - Brand voice: {profile.brand_voice}
        - Goals: {profile.content_goals}
        
        Create content that is authentic, engaging, and aligned with the brand voice.
        """
        
        return prompt.strip()
    
    def generate_content(
        self, 
        profile: OnboardingProfile, 
        content_type: ContentType, 
        platform: Platform,
        custom_prompt: Optional[str] = None
    ) -> Dict:
        """Generate content using OpenAI API"""
        
        try:
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self.generate_content_prompt(profile, content_type, platform)
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert social media marketer and content creator."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            hashtags = ""
            if content_type == ContentType.SOCIAL_MEDIA and "#" in content:
                hashtags = " ".join([word for word in content.split() if word.startswith("#")])
            
            return {
                "content": content,
                "hashtags": hashtags,
                "tokens_used": tokens_used,
                "prompt_used": prompt,
                "model": "gpt-4"
            }
            
        except Exception as e:
            raise Exception(f"Failed to generate content: {str(e)}")
    
    def generate_weekly_content(self, profile: OnboardingProfile) -> List[Dict]:
        """Generate a week's worth of content based on user's posting frequency"""
        
        preferred_platforms = json.loads(profile.preferred_platforms)
        content_items = []
        
        frequency_map = {
            "daily": 7,
            "3x/week": 3,
            "weekly": 1,
            "2x/week": 2
        }
        
        posts_per_week = frequency_map.get(profile.post_frequency.lower(), 3)
        
        for i in range(posts_per_week):
            for platform_str in preferred_platforms:
                try:
                    platform = Platform(platform_str.lower())
                    content_type = ContentType.SOCIAL_MEDIA
                    
                    content_data = self.generate_content(profile, content_type, platform)
                    content_items.append({
                        "platform": platform,
                        "content_type": content_type,
                        "day": i + 1,
                        **content_data
                    })
                except ValueError:
                    continue
        
        return content_items
