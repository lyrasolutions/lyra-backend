# 🚀 Lyra MVP Launch Guide - Start Right Now

## ⚡ Quick Start (30 minutes to live MVP)

### Step 1: Set Up OpenAI API Key (5 minutes)
```bash
# Get your OpenAI API key from https://platform.openai.com/api-keys
export OPENAI_API_KEY="sk-your-actual-openai-key-here"

# For local development, add to your .env file (DO NOT commit this file)
echo "OPENAI_API_KEY=sk-your-actual-openai-key-here" >> .env

# For production deployment, set as environment variable:
# Railway: railway variables set OPENAI_API_KEY=sk-your-key-here
# Fly.io: fly secrets set OPENAI_API_KEY=sk-your-key-here
# Cloudflare: wrangler secret put OPENAI_API_KEY
```

### Step 2: Deploy Backend to Production (10 minutes)

**Option A - Railway (Recommended):**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables in Railway dashboard
railway variables set OPENAI_API_KEY=sk-your-key-here
railway variables set SECRET_KEY=your-super-secret-key-here
```

**Option B - Fly.io:**
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly secrets set OPENAI_API_KEY=sk-your-key-here
fly secrets set SECRET_KEY=your-super-secret-key-here
fly deploy
```

### Step 3: Update Frontend API Endpoints (10 minutes)

In your frontend at https://lyra-ui.pages.dev/, update the JavaScript to point to your deployed backend:

```javascript
// Replace with your deployed backend URL
const API_BASE = 'https://your-app-name.railway.app'; // or .fly.dev

// User Registration
async function registerUser(userData) {
    const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
    });
    return response.json();
}

// User Login
async function loginUser(credentials) {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        body: formData
    });
    return response.json();
}

// Submit Onboarding Data
async function submitOnboarding(onboardingData, token) {
    const response = await fetch(`${API_BASE}/onboarding/submit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(onboardingData)
    });
    return response.json();
}

// Generate AI Content
async function generateContent(contentRequest, token) {
    const response = await fetch(`${API_BASE}/ai/generate-content`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(contentRequest)
    });
    return response.json();
}
```

### Step 4: Test Complete MVP Flow (5 minutes)

1. **Visit your deployed backend**: `https://your-app-name.railway.app/docs`
2. **Test the flow**:
   - Register a new user
   - Login to get auth token
   - Submit onboarding data
   - Generate AI content
   - View dashboard

## 🎯 MVP Feature Checklist

### ✅ Core Features (Already Implemented)
- [x] **User Authentication** - Registration, login, JWT tokens
- [x] **Onboarding Wizard** - 10-field business profile collection
- [x] **AI Content Generation** - OpenAI GPT-4 integration with personalized prompts
- [x] **Content Dashboard** - View, approve, edit generated content
- [x] **Content Calendar** - Schedule and track posts
- [x] **n8n Integration** - Webhook endpoints for automation

### 🚀 MVP User Journey
1. **User visits** https://app.lyra.solutions/
2. **Registers account** with email/password
3. **Completes onboarding** (business info, target audience, brand voice)
4. **Generates AI content** based on their profile
5. **Reviews and approves** content in dashboard
6. **Schedules posts** for optimal times
7. **Receives automated** content via n8n workflows

## 💰 Revenue-Ready Features

### Immediate Monetization Options:
- **Freemium Model**: 5 free content pieces, then $29/month
- **Usage-Based**: $0.10 per AI-generated content piece
- **Subscription Tiers**: 
  - Basic: $19/month (50 pieces)
  - Pro: $49/month (200 pieces + scheduling)
  - Enterprise: $99/month (unlimited + automation)

### Payment Integration (Next Step):
```bash
# Add Stripe integration
pip install stripe
```

## 🔧 Production Checklist

### Security & Performance:
- [x] CORS configured for your domains
- [x] JWT authentication with secure tokens
- [x] Environment variables for secrets
- [x] Health check endpoints for monitoring
- [ ] Rate limiting (add if needed)
- [ ] Database backups (set up with hosting provider)

### Monitoring & Analytics:
- [x] Health check endpoint: `/health`
- [ ] User analytics (add Google Analytics)
- [ ] Error tracking (add Sentry)
- [ ] Performance monitoring

## 🎨 Frontend Integration Examples

### Complete Onboarding Form Handler:
```javascript
async function handleOnboardingSubmit(formData) {
    try {
        const token = localStorage.getItem('authToken');
        
        const onboardingData = {
            business_name: formData.businessName,
            industry_niche: formData.industry,
            target_audience: formData.targetAudience,
            brand_voice: formData.brandVoice,
            content_goals: formData.contentGoals,
            preferred_platforms: formData.platforms, // Array of strings
            post_frequency: formData.frequency,
            best_posting_times: formData.postingTimes, // Optional array
            website_url: formData.website, // Optional
            social_handles: formData.socialHandles, // Optional object
            logo_url: formData.logoUrl // Optional
        };
        
        const response = await submitOnboarding(onboardingData, token);
        
        if (response.message === "Onboarding completed successfully") {
            // Redirect to dashboard
            window.location.href = '/dashboard';
        }
    } catch (error) {
        console.error('Onboarding failed:', error);
    }
}
```

### AI Content Generation:
```javascript
async function generateWeeklyContent() {
    try {
        const token = localStorage.getItem('authToken');
        
        const response = await fetch(`${API_BASE}/ai/generate-weekly-content`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const result = await response.json();
        console.log(`Generated ${result.content_count} pieces of content!`);
        
        // Refresh dashboard to show new content
        loadDashboard();
    } catch (error) {
        console.error('Content generation failed:', error);
    }
}
```

## 🚀 Launch Day Checklist

### Pre-Launch (Day -1):
- [ ] Deploy backend to production
- [ ] Update frontend API endpoints
- [ ] Test complete user flow end-to-end
- [ ] Set up domain and SSL certificates
- [ ] Configure monitoring and error tracking

### Launch Day:
- [ ] Announce on social media
- [ ] Send to beta user list
- [ ] Monitor for errors and performance
- [ ] Collect user feedback
- [ ] Track key metrics (signups, content generated, retention)

### Post-Launch (Week 1):
- [ ] Analyze user behavior and drop-off points
- [ ] Implement payment processing
- [ ] Add user onboarding improvements
- [ ] Scale infrastructure based on usage

## 📊 Success Metrics for MVP

### Week 1 Goals:
- 50+ user registrations
- 80% onboarding completion rate
- 200+ pieces of AI content generated
- 5+ paying customers (if payment is implemented)

### Month 1 Goals:
- 500+ users
- $1,000+ MRR (Monthly Recurring Revenue)
- 70% user retention rate
- 90% content approval rate

## 🆘 Troubleshooting

### Common Issues:
1. **CORS errors**: Check that your frontend domain is in the `origins` list
2. **OpenAI errors**: Verify API key is set correctly
3. **Auth failures**: Check JWT token format and expiration
4. **Database errors**: Ensure database is initialized properly

### Support Resources:
- Backend API docs: `https://your-app.railway.app/docs`
- Health check: `https://your-app.railway.app/health`
- Error logs: Check your hosting provider's dashboard

---

## 🎉 You're Ready to Launch!

Your Lyra MVP is **production-ready** with all core SaaS features implemented. The backend can handle real users, generate AI content, and scale as you grow. 

**Next step**: Deploy and start getting users! 🚀
