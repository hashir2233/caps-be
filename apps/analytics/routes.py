from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from sqlmodel import Session, select, func
from datetime import datetime, timedelta
import json

from apps.users.models import User
from apps.incidents.models import Incident
from core.database import get_session, engine
from core.utils.common import ResponseModel
from core.utils.security import get_current_user
from core.rag.analytics_service import AnalyticsService
from core.rag.incidents_vectorstore import get_similar_incidents

router = APIRouter()

@router.get("/crime-statistics", response_model=dict)
async def get_crime_statistics(
    start_date: str = Query(..., description="Start date for analysis period (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date for analysis period (YYYY-MM-DD)"),
    district: Optional[str] = None,
    crime_type: Optional[str] = None,
    group_by: str = Query("month", description="Group results by (day, week, month, type, district)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get crime statistics with AI-enhanced analysis"""
    try:
        # Validate dates
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            if start > end:
                raise ValueError("Start date must be before end date")
            
            # Limit to 12 months range
            if (end - start).days > 366:
                raise ValueError("Date range must not exceed 12 months")
                
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_parameters",
                    "message": "Invalid date range specified",
                    "details": str(e)
                }
            )
            
        # Validate group_by parameter
        if group_by not in ["day", "week", "month", "type", "district"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_parameters",
                    "message": "Invalid groupBy parameter",
                    "details": "Must be one of: day, week, month, type, district"
                }
            )
        
        # Query incidents within the date range
        query = select(Incident).where(
            Incident.date >= start,
            Incident.date <= end
        )
        
        # Apply optional filters
        if district:
            query = query.where(Incident.location["district"].as_string() == district)
        
        if crime_type:
            query = query.where(Incident.type == crime_type)
        
        # Execute query
        incidents = session.exec(query).all()
        
        # If no incidents found, return empty statistics
        if not incidents:
            return ResponseModel.success(
                data={
                    "timeframe": {
                        "start": start_date,
                        "end": end_date
                    },
                    "totalIncidents": 0,
                    "groupedBy": group_by,
                    "statistics": [],
                    "trends": {
                        "overall": "0%",
                        "byType": {}
                    }
                }
            )
        
        # Use AnalyticsService to generate statistics with LLM enhancement
        stats = AnalyticsService.generate_crime_statistics(
            incidents=incidents,
            start_date=start,
            end_date=end,
            group_by=group_by,
            district=district,
            crime_type=crime_type
        )
        
        return ResponseModel.success(data=stats)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "statistics_error",
                "message": f"Error retrieving crime statistics: {str(e)}"
            }
        )

@router.get("/heatmap", response_model=dict)
async def get_heatmap_data(
    resolution: str = Query("medium", description="Data resolution (high, medium, low)"),
    district: Optional[str] = None,
    crime_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get data for crime heatmap visualization with AI-enhanced hotspot detection"""
    try:
        # Validate resolution parameter
        if resolution not in ["high", "medium", "low"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_parameters",
                    "message": "Invalid resolution specified",
                    "details": "Resolution must be one of: high, medium, low"
                }
            )
        
        # Prepare query with filters
        query = select(Incident)
        
        if district:
            query = query.where(Incident.location["district"].as_string() == district)
            
        if crime_type:
            query = query.where(Incident.type == crime_type)
            
        if start_date:
            query = query.where(Incident.date >= datetime.fromisoformat(start_date))
            
        if end_date:
            query = query.where(Incident.date <= datetime.fromisoformat(end_date))
        
        # Execute query
        incidents = session.exec(query).all()
        
        if not incidents:
            return ResponseModel.success(
                data={
                    "resolution": resolution,
                    "district": district or "all",
                    "crimeType": crime_type or "all",
                    "points": [],
                    "clusters": [],
                    "totalIncidents": 0
                }
            )
        
        # Use AnalyticsService to generate heatmap data
        heatmap_data = AnalyticsService.generate_heatmap_data(
            incidents=incidents,
            resolution=resolution,
            district=district,
            crime_type=crime_type
        )
        
        return ResponseModel.success(data=heatmap_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "heatmap_error",
                "message": f"Error generating heatmap data: {str(e)}"
            }
        )

@router.get("/predictive", response_model=dict)
async def get_predictive_analysis(
    days_ahead: int = Query(7, ge=1, le=30, description="Number of days to predict (1-30)"),
    crime_type: Optional[str] = None,
    district: Optional[str] = None,
    confidence: int = Query(70, ge=0, le=100, description="Minimum confidence threshold (0-100)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get predictive crime analysis using LLM and RAG"""
    try:
        # Use the analytics service to generate predictions
        predictions = AnalyticsService.generate_predictive_analysis(
            session=session,
            days_ahead=days_ahead,
            crime_type=crime_type,
            district=district,
            confidence_threshold=confidence
        )
        
        return ResponseModel.success(data=predictions)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "prediction_error",
                "message": str(e)
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "prediction_error",
                "message": f"Error generating predictive analysis: {str(e)}"
            }
        )

@router.get("/trends", response_model=dict)
async def get_trend_analysis(
    start_date: str = Query(..., description="Start date for analysis period (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date for analysis period (YYYY-MM-DD)"),
    crime_type: Optional[str] = None,
    district: Optional[str] = None,
    interval: str = Query("weekly", description="Analysis interval (daily, weekly, monthly)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get crime trend analysis with AI-enhanced pattern detection"""
    try:
        # Validate dates
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            if start > end:
                raise ValueError("Start date must be before end date")
                
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_parameters",
                    "message": "Invalid date range specified",
                    "details": str(e)
                }
            )
            
        # Validate interval parameter
        if interval not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_parameters",
                    "message": "Invalid interval specified",
                    "details": "Interval must be one of: daily, weekly, monthly"
                }
            )
        
        # Query incidents within the date range
        query = select(Incident).where(
            Incident.date >= start,
            Incident.date <= end
        )
        
        # Apply optional filters
        if district:
            query = query.where(Incident.location["district"].as_string() == district)
        
        if crime_type:
            query = query.where(Incident.type == crime_type)
        
        # Execute query
        incidents = session.exec(query).all()
        
        if not incidents:
            return ResponseModel.success(
                data={
                    "timeframe": {
                        "start": start_date,
                        "end": end_date
                    },
                    "interval": interval,
                    "trends": [],
                    "emergingPatterns": []
                }
            )
        
        # Use AnalyticsService to generate trend analysis with LLM enhancement
        trend_data = AnalyticsService.generate_trend_analysis(
            incidents=incidents,
            start_date=start,
            end_date=end,
            interval=interval,
            district=district,
            crime_type=crime_type
        )
        
        return ResponseModel.success(data=trend_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "trend_analysis_error",
                "message": f"Error generating trend analysis: {str(e)}"
            }
        )

@router.get("/risk-factors", response_model=dict)
async def get_risk_factor_analysis(
    crime_type: Optional[str] = None,
    district: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get analysis of risk factors contributing to crimes"""
    try:
        # Build query with filters
        query = select(Incident)
        
        if district:
            query = query.where(Incident.location["district"].as_string() == district)
            
        if crime_type:
            query = query.where(Incident.type == crime_type)
        
        # Limit to the most recent 200 incidents for analysis
        query = query.order_by(Incident.date.desc()).limit(200)
        
        # Execute query
        incidents = session.exec(query).all()
        
        if not incidents:
            return ResponseModel.success(
                data={
                    "riskFactors": [],
                    "crimeType": crime_type or "all",
                    "district": district or "all",
                    "totalIncidentsAnalyzed": 0
                }
            )
        
        # Use AnalyticsService to identify risk factors
        risk_factors = AnalyticsService.analyze_risk_factors(
            incidents=incidents,
            crime_type=crime_type,
            district=district
        )
        
        return ResponseModel.success(data=risk_factors)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "risk_factor_error",
                "message": f"Error analyzing risk factors: {str(e)}"
            }
        )

@router.get("/similar-incidents/{incident_id}", response_model=dict)
async def get_similar_incidents_analysis(
    incident_id: str,
    k: int = Query(5, ge=1, le=20, description="Number of similar incidents to return"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Find incidents similar to a specified incident using vector similarity"""
    try:
        from uuid import UUID
        
        # Convert string ID to UUID
        try:
            incident_uuid = UUID(incident_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_id",
                    "message": "Invalid incident ID format"
                }
            )
        
        # Get the source incident
        source_incident = session.get(Incident, incident_uuid)
        if not source_incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "not_found",
                    "message": f"Incident with ID {incident_id} not found"
                }
            )
        
        # Create a search query from the incident details
        search_query = f"Type: {source_incident.type}, District: {source_incident.location.get('district', '')}, Severity: {source_incident.severity}"
        
        # Use vector similarity to find similar incidents
        similar_incidents_meta = get_similar_incidents(
            query=search_query,
            filters=None,  # No additional filters
            k=k + 1  # Get one extra to remove the source incident if included
        )
        
        # Remove the source incident if it's in the results
        similar_incidents_meta = [
            inc for inc in similar_incidents_meta 
            if inc["id"] != str(incident_uuid)
        ][:k]
        
        # Get full incident details for the found incidents
        similar_incidents_data = []
        for inc_meta in similar_incidents_meta:
            inc_uuid = UUID(inc_meta["id"])
            inc = session.get(Incident, inc_uuid)
            if inc:
                from apps.incidents.services import IncidentService
                inc_data = IncidentService._format_incident(inc)
                inc_data["similarity_score"] = inc_meta.get("score", 1.0)
                similar_incidents_data.append(inc_data)
        
        return ResponseModel.success(
            data={
                "sourceIncident": {
                    "id": str(source_incident.id),
                    "title": source_incident.title,
                    "type": source_incident.type
                },
                "similarIncidents": similar_incidents_data,
                "analysis": AnalyticsService.analyze_incident_similarities(
                    source_incident=source_incident,
                    similar_incidents=similar_incidents_data
                )
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "similarity_error",
                "message": f"Error finding similar incidents: {str(e)}"
            }
        )

@router.get("/correlation", response_model=dict)
async def get_correlation_analysis(
    factor1: str = Query(..., description="First factor to analyze (e.g., time_of_day, weather, district)"),
    factor2: str = Query(..., description="Second factor to analyze"),
    crime_type: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Analyze correlation between two factors in crime incidents"""
    try:
        valid_factors = [
            "time_of_day", "day_of_week", "weather", "district", 
            "severity", "type", "location_type", "lighting", 
            "population_density", "income_level"
        ]
        
        # Validate factors
        if factor1 not in valid_factors or factor2 not in valid_factors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_parameters",
                    "message": "Invalid factor specified",
                    "details": f"Factors must be one of: {', '.join(valid_factors)}"
                }
            )
            
        if factor1 == factor2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_parameters",
                    "message": "Factors must be different"
                }
            )
        
        # Build query with filters
        query = select(Incident)
        
        if crime_type:
            query = query.where(Incident.type == crime_type)
        
        # Execute query - limit to recent 500 incidents for analysis
        query = query.order_by(Incident.date.desc()).limit(500)
        incidents = session.exec(query).all()
        
        if not incidents:
            return ResponseModel.success(
                data={
                    "factor1": factor1,
                    "factor2": factor2,
                    "crimeType": crime_type or "all",
                    "correlationStrength": 0,
                    "correlationMatrix": {},
                    "analysis": "Insufficient data for correlation analysis"
                }
            )
        
        # Use AnalyticsService to analyze correlation
        correlation_data = AnalyticsService.analyze_factor_correlation(
            incidents=incidents,
            factor1=factor1,
            factor2=factor2,
            crime_type=crime_type
        )
        
        return ResponseModel.success(data=correlation_data)
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "correlation_error",
                "message": f"Error analyzing correlation: {str(e)}"
            }
        )

@router.get("/time-patterns", response_model=dict)
async def get_time_pattern_analysis(
    time_factor: str = Query("hour_of_day", description="Time factor to analyze (hour_of_day, day_of_week, month_of_year)"),
    crime_type: Optional[str] = None,
    district: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Analyze crime patterns across different time periods"""
    try:
        valid_time_factors = ["hour_of_day", "day_of_week", "month_of_year"]
        
        # Validate time factor
        if time_factor not in valid_time_factors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_parameters",
                    "message": "Invalid time factor specified",
                    "details": f"Time factor must be one of: {', '.join(valid_time_factors)}"
                }
            )
        
        # Build query with filters
        query = select(Incident)
        
        if district:
            query = query.where(Incident.location["district"].as_string() == district)
            
        if crime_type:
            query = query.where(Incident.type == crime_type)
        
        # Execute query - get incidents from the last 2 years
        two_years_ago = datetime.now() - timedelta(days=730)
        query = query.where(Incident.date >= two_years_ago)
        incidents = session.exec(query).all()
        
        if not incidents:
            return ResponseModel.success(
                data={
                    "timeFactor": time_factor,
                    "crimeType": crime_type or "all",
                    "district": district or "all",
                    "patterns": [],
                    "analysis": "Insufficient data for time pattern analysis"
                }
            )
        
        # Use AnalyticsService to analyze time patterns
        time_patterns = AnalyticsService.analyze_time_patterns(
            incidents=incidents,
            time_factor=time_factor,
            crime_type=crime_type,
            district=district
        )
        
        return ResponseModel.success(data=time_patterns)
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "time_pattern_error",
                "message": f"Error analyzing time patterns: {str(e)}"
            }
        )
