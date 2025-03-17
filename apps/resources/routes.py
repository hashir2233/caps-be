from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Dict, Any
from sqlmodel import Session

from apps.users.models import User
from core.database import get_session
from core.utils.common import ResponseModel
from core.utils.security import get_current_user, check_permissions

router = APIRouter()

@router.get("/allocation", response_model=dict)
async def get_resource_allocation(
    district: Optional[str] = None,
    resource_type: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get current resource allocation data"""
    try:
        # In a real application, we'd fetch this from the database
        # For now, we'll return mock data
        return ResponseModel.success(
            data={
                "totalResources": {
                    "officers": 124,
                    "vehicles": 42
                },
                "allocation": [
                    {
                        "district": "downtown",
                        "risk": "high",
                        "resources": {
                            "officers": 45,
                            "vehicles": 18
                        },
                        "coverage": 85,
                        "responseTime": 7.2
                    },
                    {
                        "district": "westside",
                        "risk": "medium",
                        "resources": {
                            "officers": 25,
                            "vehicles": 10
                        },
                        "coverage": 72,
                        "responseTime": 8.5
                    },
                    {
                        "district": "eastside",
                        "risk": "medium",
                        "resources": {
                            "officers": 20,
                            "vehicles": 8
                        },
                        "coverage": 68,
                        "responseTime": 9.1
                    },
                    {
                        "district": "northside",
                        "risk": "low",
                        "resources": {
                            "officers": 18,
                            "vehicles": 7
                        },
                        "coverage": 65,
                        "responseTime": 9.8
                    },
                    {
                        "district": "southside",
                        "risk": "low",
                        "resources": {
                            "officers": 16,
                            "vehicles": 6
                        },
                        "coverage": 60,
                        "responseTime": 10.5
                    }
                ]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving resource allocation data: {str(e)}"
        )

@router.get("/schedule", response_model=dict)
async def get_patrol_schedule(
    district: Optional[str] = None,
    date: str = Query(None, description="Schedule date (YYYY-MM-DD)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get patrol schedule information"""
    try:
        # In a real application, we'd fetch this from the database
        # For now, we'll return mock data
        return ResponseModel.success(
            data={
                "date": date or "2025-03-15",
                "schedules": [
                    {
                        "district": "downtown",
                        "shifts": [
                            {
                                "name": "Morning",
                                "timeRange": "06:00-14:00",
                                "officers": 12,
                                "vehicles": 5,
                                "priorityAreas": ["Transit Hubs", "Commercial District"],
                                "supervisor": "Officer Johnson"
                            },
                            {
                                "name": "Afternoon",
                                "timeRange": "14:00-22:00",
                                "officers": 18,
                                "vehicles": 8,
                                "priorityAreas": ["Commercial District", "Entertainment Zone"],
                                "supervisor": "Officer Williams"
                            },
                            {
                                "name": "Night",
                                "timeRange": "22:00-06:00",
                                "officers": 15,
                                "vehicles": 7,
                                "priorityAreas": ["Entertainment Zone", "Transit Hubs"],
                                "supervisor": "Officer Davis"
                            }
                        ]
                    },
                    {
                        "district": "westside",
                        "shifts": [
                            {
                                "name": "Morning",
                                "timeRange": "06:00-14:00",
                                "officers": 8,
                                "vehicles": 3,
                                "priorityAreas": ["Residential Areas", "Schools"],
                                "supervisor": "Officer Miller"
                            },
                            {
                                "name": "Afternoon",
                                "timeRange": "14:00-22:00",
                                "officers": 10,
                                "vehicles": 4,
                                "priorityAreas": ["Shopping Centers", "Parks"],
                                "supervisor": "Officer Brown"
                            },
                            {
                                "name": "Night",
                                "timeRange": "22:00-06:00",
                                "officers": 7,
                                "vehicles": 3,
                                "priorityAreas": ["Residential Areas", "Commercial Areas"],
                                "supervisor": "Officer Wilson"
                            }
                        ]
                    }
                ]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving patrol schedule: {str(e)}"
        )

@router.post("/optimize", response_model=dict)
async def optimize_resources(
    optimization_data: Dict[str, Any],
    session: Session = Depends(get_session),
    _: User = Depends(check_permissions(["manage_resources"]))
):
    """Generate optimized resource allocation recommendations"""
    try:
        # Validate constraints
        constraints = optimization_data.get("constraints", {})
        if constraints.get("minCoverage", 0) > 90:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_constraints",
                    "message": "Resource constraints cannot be satisfied",
                    "details": "Minimum coverage requirements cannot be met with the specified number of officers"
                }
            )
        
        # In a real application, we'd use actual optimization algorithms
        # For now, we'll return mock data
        return ResponseModel.success(
            data={
                "optimizationId": "opt_123456",
                "status": "completed",
                "currentAllocation": {
                    "downtown": {
                        "officers": 45,
                        "vehicles": 18
                    },
                    "westside": {
                        "officers": 25,
                        "vehicles": 10
                    },
                    "eastside": {
                        "officers": 20,
                        "vehicles": 8
                    },
                    "northside": {
                        "officers": 18,
                        "vehicles": 7
                    },
                    "southside": {
                        "officers": 16,
                        "vehicles": 6
                    }
                },
                "recommendedAllocation": {
                    "downtown": {
                        "officers": 42,
                        "vehicles": 16
                    },
                    "westside": {
                        "officers": 28,
                        "vehicles": 11
                    },
                    "eastside": {
                        "officers": 24,
                        "vehicles": 9
                    },
                    "northside": {
                        "officers": 16,
                        "vehicles": 6
                    },
                    "southside": {
                        "officers": 14,
                        "vehicles": 5
                    }
                },
                "impact": {
                    "responseTime": {
                        "downtown": "-0.2 min",
                        "westside": "-0.8 min",
                        "eastside": "-0.7 min",
                        "northside": "+0.3 min",
                        "southside": "+0.5 min"
                    },
                    "coverage": {
                        "downtown": "-2%",
                        "westside": "+5%",
                        "eastside": "+4%",
                        "northside": "-1%",
                        "southside": "-2%"
                    },
                    "overall": {
                        "averageResponseTime": "-0.2 min",
                        "averageCoverage": "+1.5%",
                        "predictedCrimeReduction": "+3.2%"
                    }
                }
            }
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error optimizing resources: {str(e)}"
        )
