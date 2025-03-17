from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from sqlmodel import SQLModel, Field as SQLField, JSON

class Location(BaseModel):
    address: str
    city: Optional[str] = None
    zip_code: Optional[str] = None
    district: str
    location_type: Optional[str] = None
    coordinates: List[float]
    neighborhood: Optional[str] = None
    lighting: Optional[str] = None
    population_density: Optional[float] = None
    average_income: Optional[float] = None 
    unemployment_rate: Optional[float] = None 

class EnvironmentalFactors(BaseModel):
    weather: Optional[str] = None 
    temperature: Optional[float] = None
    visibility: Optional[str] = None
    time_of_day: Optional[str] = None
    day_of_week: Optional[str] = None
    is_holiday: Optional[bool] = False
    is_weekend: Optional[bool] = None
    precipitation: Optional[float] = None 

class SocioeconomicFactors(BaseModel):
    poverty_rate: Optional[float] = None 
    education_level: Optional[str] = None
    housing_density: Optional[float] = None
    public_transport_access: Optional[str] = None
    police_presence: Optional[str] = None
    nearby_facilities: Optional[List[str]] = None
    crime_history: Optional[float] = None 

class Flag(BaseModel):
    repeat_offender: Optional[bool] = False
    related_cases: Optional[bool] = False
    requires_followup: Optional[bool] = False
    involves_minor: Optional[bool] = False
    gang_related: Optional[bool] = False
    domestic_violence: Optional[bool] = False

class Incident(SQLModel, table=True):
    id: UUID = SQLField(primary_key=True)
    title: str
    description: Optional[str] = None
    type: str
    date: datetime
    location: Dict[str, Any] = SQLField(sa_type=JSON)
    severity: str
    status: str
    reporting_officer: Optional[str] = None
    notes: Optional[str] = None
    flags: Optional[Dict[str, bool]] = SQLField(default=None, sa_type=JSON)
    
    environmental_factors: Optional[Dict[str, Any]] = SQLField(default=None, sa_type=JSON)
    socioeconomic_factors: Optional[Dict[str, Any]] = SQLField(default=None, sa_type=JSON)
    weapon_used: Optional[str] = None
    victim_count: Optional[int] = None
    suspect_count: Optional[int] = None
    estimated_loss_value: Optional[float] = None
    response_time_minutes: Optional[int] = None
    related_incidents: Optional[List[str]] = SQLField(default=None, sa_type=JSON)
    risk_score: Optional[float] = None
    
    created_at: datetime
    updated_at: datetime

class IncidentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    type: str
    date: str
    location: Location
    severity: str
    status: str = "open"
    reporting_officer: Optional[str] = None
    notes: Optional[str] = None
    flags: Optional[Flag] = None
    environmental_factors: Optional[EnvironmentalFactors] = None
    socioeconomic_factors: Optional[SocioeconomicFactors] = None
    weapon_used: Optional[str] = None
    victim_count: Optional[int] = None
    suspect_count: Optional[int] = None
    estimated_loss_value: Optional[float] = None

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    date: Optional[str] = None
    location: Optional[Location] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    reporting_officer: Optional[str] = None
    notes: Optional[str] = None
    flags: Optional[Flag] = None
    environmental_factors: Optional[EnvironmentalFactors] = None
    socioeconomic_factors: Optional[SocioeconomicFactors] = None
    weapon_used: Optional[str] = None
    victim_count: Optional[int] = None
    suspect_count: Optional[int] = None
    estimated_loss_value: Optional[float] = None
    response_time_minutes: Optional[int] = None
    risk_score: Optional[float] = None

class IncidentRead(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    type: str
    date: str
    location: Dict[str, Any]
    severity: str
    status: str
    reporting_officer: Optional[Dict[str, Any]]
    notes: Optional[str]
    flags: Optional[Dict[str, bool]]
    environmental_factors: Optional[Dict[str, Any]]
    socioeconomic_factors: Optional[Dict[str, Any]]
    weapon_used: Optional[str]
    victim_count: Optional[int]
    suspect_count: Optional[int]
    estimated_loss_value: Optional[float]
    response_time_minutes: Optional[int]
    related_incidents: Optional[List[str]]
    risk_score: Optional[float]
    created_at: str
    updated_at: str
