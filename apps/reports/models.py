from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, JSON

class DateRange(BaseModel):
    start: str
    end: str

class ReportParameters(BaseModel):
    crime_types: Optional[List[str]] = None
    include_charts: Optional[bool] = True
    include_recommendations: Optional[bool] = True
    compare_with_previous: Optional[bool] = False

class Report(SQLModel, table=True):
    id: UUID = Field(primary_key=True)
    title: str
    description: Optional[str] = None
    type: str
    district: str
    date_range: Dict[str, Any] = Field(sa_type=JSON)  # Use JSON type for dict
    content: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)  # Use JSON type for dict
    parameters: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)  # Use JSON type for dict
    status: str
    created_by: str
    estimated_completion: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class ReportCreate(BaseModel):
    title: str
    description: Optional[str] = None
    type: str
    district: str
    date_range: DateRange
    parameters: Optional[ReportParameters] = None

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class ReportRead(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    type: str
    district: str
    date_range: Dict[str, str]
    content: Optional[Dict[str, Any]]
    status: str
    created_by: Dict[str, str]
    estimated_completion: Optional[str]
    created_at: str
    updated_at: str
