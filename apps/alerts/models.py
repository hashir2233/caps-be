from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, JSON

class AlertLocation(BaseModel):
    address: str
    district: str
    coordinates: List[float]

class AlertRelatedIncident(BaseModel):
    id: UUID
    title: str
    type: str
    date: str

class Alert(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    title: str
    description: Optional[str] = None
    severity: str
    location: Dict[str, Any] = Field(sa_type=JSON)  # Use JSON type for dict
    timestamp: datetime
    source: str
    related_incidents: Optional[List[Dict[str, Any]]] = Field(default=None, sa_type=JSON)  # Use JSON type for list of dicts
    recommendations: Optional[List[str]] = Field(default=None, sa_type=JSON)  # Use JSON type for list
    reviewed: bool = False
    created_at: datetime
    updated_at: datetime

class AlertCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str
    location: AlertLocation
    related_incidents: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

class AlertUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    reviewed: Optional[bool] = None
    recommendations: Optional[List[str]] = None

class AlertRead(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    severity: str
    location: Dict[str, Any]
    timestamp: str
    source: str
    related_incidents: Optional[List[Dict[str, Any]]]
    recommendations: Optional[List[str]]
    reviewed: bool
    created_at: str
    updated_at: str
