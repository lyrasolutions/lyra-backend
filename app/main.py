from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.auth.routes import auth_router
from app.dashboard.routes import dashboard_router, get_current_user

app = FastAPI(title="Lyra Backend API", description="Backend for Lyra.solutions MVP")

origins = [
    "https://app.lyra.solutions",
    "https://lyra-ui.pages.dev"
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

class SummaryRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "Lyra Backend API", "version": "1.0.0"}

@app.post("/ai/summarize")
def summarize_text(request: SummaryRequest, current_user: dict = Depends(get_current_user)):
    text = request.text.strip()
    summary = text[:150] + "..." if len(text) > 150 else text
    return {"summary": f"Summary: {summary}"}
