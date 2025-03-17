from uuid import UUID
from pydantic import BaseModel, EmailStr, validator

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    user_id: UUID
    role: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str
    
    @validator('password')
    def password_strength(cls, v):
        # Simple validation - in a real app you'd want more comprehensive checks
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
    
    @validator('role')
    def valid_role(cls, v):
        valid_roles = ["analyst", "officer", "admin"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirmRequest(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v