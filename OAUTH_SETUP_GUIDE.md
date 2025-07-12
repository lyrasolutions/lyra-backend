# OAuth Setup Guide for Lyra Social Media Integration

This guide walks you through setting up OAuth applications for each social media platform to enable auto-posting functionality.

## Prerequisites

- Admin access to each social media platform
- Business accounts for Instagram and TikTok
- Company page for LinkedIn
- Facebook Page for Facebook posting

## 1. Instagram (via Facebook Developer)

### Step 1: Create Facebook App
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click "Create App" → "Business" → "Next"
3. Enter app name: "Lyra Content Manager"
4. Enter contact email and select app purpose

### Step 2: Add Instagram Basic Display
1. In your app dashboard, click "Add Product"
2. Find "Instagram Basic Display" and click "Set Up"
3. Go to Instagram Basic Display → Basic Display
4. Click "Create New App"
5. Add OAuth Redirect URI: `https://lyra-enhanced-dashboard.pages.dev/oauth/callback`

### Step 3: Get Credentials
```env
INSTAGRAM_CLIENT_ID=your_instagram_app_id
INSTAGRAM_CLIENT_SECRET=your_instagram_app_secret
```

## 2. Facebook Pages API

### Step 1: Use Same Facebook App
1. In your Facebook app dashboard, click "Add Product"
2. Find "Facebook Login" and click "Set Up"
3. Go to Facebook Login → Settings
4. Add OAuth Redirect URI: `https://lyra-enhanced-dashboard.pages.dev/oauth/callback`

### Step 2: Configure Permissions
Required permissions:
- `pages_manage_posts`
- `pages_read_engagement`
- `pages_show_list`

### Step 3: Get Credentials
```env
FACEBOOK_CLIENT_ID=your_facebook_app_id
FACEBOOK_CLIENT_SECRET=your_facebook_app_secret
```

## 3. LinkedIn API

### Step 1: Create LinkedIn App
1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Click "Create App"
3. Fill in app details:
   - App name: "Lyra Content Manager"
   - LinkedIn Page: Select your company page
   - App logo: Upload Lyra logo

### Step 2: Configure OAuth
1. Go to "Auth" tab
2. Add OAuth 2.0 redirect URL: `https://lyra-enhanced-dashboard.pages.dev/oauth/callback`
3. Request access to "Share on LinkedIn" product

### Step 3: Get Credentials
```env
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
```

## 4. TikTok for Business

### Step 1: Create TikTok Developer Account
1. Go to [TikTok Developers](https://developers.tiktok.com/)
2. Sign up with your TikTok Business account
3. Complete verification process

### Step 2: Create App
1. Go to "Manage Apps" → "Create an App"
2. Fill in app details:
   - App name: "Lyra Content Manager"
   - Category: "Social Media Management"
3. Add redirect URI: `https://lyra-enhanced-dashboard.pages.dev/oauth/callback`

### Step 3: Request Permissions
Required scopes:
- `user.info.basic`
- `video.publish`

### Step 4: Get Credentials
```env
TIKTOK_CLIENT_ID=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
```

## 5. Generate Encryption Key

Generate a secure encryption key for token storage:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add to your environment:
```env
ENCRYPTION_KEY=your_generated_encryption_key
```

## 6. Environment Configuration

Create a `.env` file in your backend root with all the credentials:

```env
# Copy from .env.example and fill in your values
INSTAGRAM_CLIENT_ID=your_instagram_client_id
INSTAGRAM_CLIENT_SECRET=your_instagram_client_secret
FACEBOOK_CLIENT_ID=your_facebook_client_id
FACEBOOK_CLIENT_SECRET=your_facebook_client_secret
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
TIKTOK_CLIENT_ID=your_tiktok_client_id
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
ENCRYPTION_KEY=your_encryption_key
OAUTH_REDIRECT_URI=https://lyra-enhanced-dashboard.pages.dev/oauth/callback
```

## 7. Testing OAuth Flows

### Test Instagram Connection
1. Login to Lyra dashboard
2. Go to Settings → Social Media
3. Click "Connect Instagram"
4. Authorize the app
5. Verify connection in dashboard

### Test Auto-Posting
1. Generate content via AI
2. Approve content for Instagram
3. Verify auto-posting occurs
4. Check Instagram account for posted content

## 8. Production Considerations

### Rate Limits
- Instagram: 200 requests per hour per user
- Facebook: 200 requests per hour per user  
- LinkedIn: 500 requests per day per member
- TikTok: 1000 requests per day per app

### Token Refresh
- Instagram: Tokens expire in 60 days
- Facebook: Tokens expire in 60 days
- LinkedIn: Tokens expire in 60 days
- TikTok: Tokens expire in 24 hours

### Error Handling
- Implement retry logic for failed posts
- Handle token expiration gracefully
- Log all API interactions for debugging

## 9. Troubleshooting

### Common Issues

**"Invalid redirect URI"**
- Ensure redirect URI matches exactly in app settings
- Check for trailing slashes or protocol mismatches

**"Insufficient permissions"**
- Verify all required scopes are requested
- Check if app is approved for production use

**"Token expired"**
- Implement automatic token refresh
- Handle refresh token expiration

**"Rate limit exceeded"**
- Implement exponential backoff
- Queue posts for later retry

### Debug Mode
Enable debug logging in production:
```env
DEBUG_OAUTH=true
```

## Support

For additional help:
- Instagram/Facebook: [Facebook Developer Support](https://developers.facebook.com/support/)
- LinkedIn: [LinkedIn Developer Support](https://www.linkedin.com/help/linkedin/answer/a1342443)
- TikTok: [TikTok Developer Support](https://developers.tiktok.com/support/)
