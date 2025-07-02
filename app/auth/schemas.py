from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
