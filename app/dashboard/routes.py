from fastapi import APIRouter, Depends
from app.auth.routes import jwt, ALGORITHM
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from typing import Dict

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
dashboard_router = APIRouter()

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    try:
        payload = jwt.decode(token, jwt.SECRET_KEY, algorithms=[ALGORITHM])
        return {"username": payload.get("sub")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")

@dashboard_router.get("/")
def read_dashboard(user: Dict = Depends(get_current_user)):
    return {"message": f"Welcome to your dashboard, {user['username']}!"}