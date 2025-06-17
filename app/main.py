from fastapi import FastAPI
from app.auth.routes import auth_router
from app.dashboard.routes import dashboard_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Lyra.solutions backend API"}