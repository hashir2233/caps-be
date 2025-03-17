from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from sqlmodel import SQLModel, Field, JSON
from pydantic import BaseModel, EmailStr

class User(SQLModel, table=True):
    """User model"""
    id: UUID = Field(primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: str
    district: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    badge_number: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)  # Store as JSON
    join_date: Optional[datetime] = None
    last_active: Optional[datetime] = None
    profile_complete: Optional[int] = None
    created_at: datetime
    updated_at: datetime

class UserCreate(BaseModel):
    """User create schema"""
    name: str
    email: EmailStr
    password: str
    role: str
    district: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    badge_number: Optional[str] = None

class UserUpdate(SQLModel):
    """User update schema"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    district: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    badge_number: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None  # Changed from List to Dict
    role: Optional[str] = None

class UserRead(BaseModel):
    """User read schema"""
    id: UUID
    name: str
    email: str
    role: str
    district: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    badge_number: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None  # Changed from List to Dict
    join_date: Optional[datetime] = None
    last_active: Optional[datetime] = None
    profile_complete: Optional[int] = None
    
    class Config:
        from_attributes = True  # Updated from orm_mode to from_attributes