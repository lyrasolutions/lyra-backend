from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.auth.routes import auth_router
from app.dashboard.routes import dashboard_router, get_current_user
from app.onboarding.routes import onboarding_router
from app.ai.routes import ai_router
from app.automation.routes import automation_router
from app.social.routes import social_router
from app.db.session import init_db

app = FastAPI(title="Lyra Backend API", description="Backend for Lyra.solutions SaaS Platform")

origins = [
    "http://localhost:3000",
    "http://localhost:8080", 
    "https://app.lyra.solutions",
    "https://lyra-ui.pages.dev",
    "https://lyra.solutions",
    "https://code-efficiency-reporter-1xbciqqv.devinapps.com",
    "https://code-efficiency-reporter-pghs32ww.devinapps.com",
    "https://code-efficiency-reporter-pvodt1dx.devinapps.com",
    "https://lyra-enhanced-dashboard.pages.dev"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
app.include_router(onboarding_router, prefix="/onboarding", tags=["onboarding"])
app.include_router(ai_router, prefix="/ai", tags=["ai"])
app.include_router(automation_router, prefix="/automation", tags=["automation"])
app.include_router(social_router, prefix="/social", tags=["social"])

@app.on_event("startup")
def startup_event():
    init_db()

class SummaryRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {
        "message": "Lyra Backend API", 
        "version": "1.0.0",
        "status": "MVP Ready",
        "features": ["Authentication", "Onboarding", "AI Content Generation", "Dashboard", "Automation"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0", "timestamp": "2025-07-02T07:23:58Z"}

@app.post("/ai/summarize")
def summarize_text(request: SummaryRequest, current_user: dict = Depends(get_current_user)):
    text = request.text.strip()
    summary = text[:150] + "..." if len(text) > 150 else text
    return {"summary": f"Summary: {summary}"}
