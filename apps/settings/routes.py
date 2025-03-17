from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import Dict, Any

from apps.users.models import User
from core.database import get_session
from core.utils.common import ResponseModel
from core.utils.security import get_current_user, check_permissions

router = APIRouter()

@router.get("/system", response_model=dict)
async def get_system_settings(
    session: Session = Depends(get_session),
    _: User = Depends(check_permissions(["view_system_settings"]))
):
    """Get system settings"""
    # In a real application, we'd fetch this from the database
    # For now, we'll return mock data
    return ResponseModel.success(
        data={
            "settings": {
                "general": {
                    "systemName": "Crime Analysis Platform",
                    "defaultLanguage": "en",
                    "defaultTimezone": "America/New_York",
                    "dateFormat": "MM/DD/YYYY"
                },
                "security": {
                    "sessionTimeout": 30,
                    "passwordPolicy": {
                        "minLength": 8,
                        "requireUppercase": True,
                        "requireLowercase": True,
                        "requireNumbers": True,
                        "requireSpecialChars": True,
                        "expiryDays": 90
                    },
                    "twoFactorAuthEnabled": True
                },
                "notifications": {
                    "emailEnabled": True,
                    "pushEnabled": True,
                    "alertThreshold": "medium"
                },
                "analytics": {
                    "dataRetentionDays": 365,
                    "predictiveModelVersion": "v2.3.1",
                    "autoRefreshInterval": 5
                }
            }
        }
    )

@router.put("/system", response_model=dict)
async def update_system_settings(
    settings_data: Dict[str, Any],
    session: Session = Depends(get_session),
    _: User = Depends(check_permissions(["update_system_settings"]))
):
    """Update system settings"""
    # Validate settings (would be more comprehensive in a real app)
    if "security" in settings_data and "sessionTimeout" in settings_data["security"]:
        timeout = settings_data["security"]["sessionTimeout"]
        if timeout < 15 or timeout > 120:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "validation_error",
                    "message": "Invalid settings data",
                    "fields": {
                        "security.sessionTimeout": "Session timeout must be between 15 and 120 minutes"
                    }
                }
            )
    
    # In a real application, we'd save this to the database
    # For now, we'll just return success with the mock data
    return ResponseModel.success(
        data={
            "settings": {
                "general": {
                    "systemName": "Crime Analysis Platform",
                    "defaultLanguage": settings_data.get("general", {}).get("defaultLanguage", "en"),
                    "defaultTimezone": settings_data.get("general", {}).get("defaultTimezone", "America/New_York"),
                    "dateFormat": settings_data.get("general", {}).get("dateFormat", "MM/DD/YYYY")
                },
                "security": {
                    "sessionTimeout": settings_data.get("security", {}).get("sessionTimeout", 30),
                    "passwordPolicy": settings_data.get("security", {}).get("passwordPolicy", {
                        "minLength": 8,
                        "requireUppercase": True,
                        "requireLowercase": True,
                        "requireNumbers": True,
                        "requireSpecialChars": True,
                        "expiryDays": 90
                    }),
                    "twoFactorAuthEnabled": settings_data.get("security", {}).get("twoFactorAuthEnabled", True)
                },
                "notifications": {
                    "emailEnabled": settings_data.get("notifications", {}).get("emailEnabled", True),
                    "pushEnabled": settings_data.get("notifications", {}).get("pushEnabled", True),
                    "alertThreshold": settings_data.get("notifications", {}).get("alertThreshold", "medium")
                },
                "analytics": {
                    "dataRetentionDays": settings_data.get("analytics", {}).get("dataRetentionDays", 365),
                    "predictiveModelVersion": settings_data.get("analytics", {}).get("predictiveModelVersion", "v2.3.1"),
                    "autoRefreshInterval": settings_data.get("analytics", {}).get("autoRefreshInterval", 5)
                }
            }
        }
    )

@router.get("/user", response_model=dict)
async def get_user_settings(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get settings for the current user"""
    # In a real application, we'd fetch this from the database
    # For now, we'll return mock data
    return ResponseModel.success(
        data={
            "settings": {
                "preferences": {
                    "language": "en",
                    "timezone": "America/New_York",
                    "dateFormat": "MM/DD/YYYY",
                    "theme": "light",
                    "density": "comfortable"
                },
                "notifications": {
                    "email": True,
                    "push": True,
                    "highRiskAlerts": True,
                    "predictiveAlerts": True,
                    "reportGeneration": True
                },
                "dashboard": {
                    "defaultView": "overview",
                    "autoRefresh": True,
                    "refreshInterval": 5,
                    "widgets": [
                        "crime-heatmap",
                        "recent-alerts",
                        "crime-type-chart",
                        "predictive-analysis"
                    ]
                }
            }
        }
    )

@router.put("/user", response_model=dict)
async def update_user_settings(
    settings_data: Dict[str, Any],
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update settings for the current user"""
    # Validate settings (would be more comprehensive in a real app)
    if "dashboard" in settings_data and "widgets" in settings_data["dashboard"]:
        widgets = settings_data["dashboard"]["widgets"]
        if len(widgets) > 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "validation_error",
                    "message": "Invalid settings data",
                    "fields": {
                        "dashboard.widgets": "Maximum of 4 widgets allowed"
                    }
                }
            )
    
    # In a real application, we'd save this to the database
    # For now, we'll just return success with the mock data
    return ResponseModel.success(
        data={
            "settings": {
                "preferences": {
                    "language": settings_data.get("preferences", {}).get("language", "en"),
                    "timezone": settings_data.get("preferences", {}).get("timezone", "America/New_York"),
                    "dateFormat": settings_data.get("preferences", {}).get("dateFormat", "MM/DD/YYYY"),
                    "theme": settings_data.get("preferences", {}).get("theme", "light"),
                    "density": settings_data.get("preferences", {}).get("density", "comfortable")
                },
                "notifications": {
                    "email": settings_data.get("notifications", {}).get("email", True),
                    "push": settings_data.get("notifications", {}).get("push", True),
                    "highRiskAlerts": settings_data.get("notifications", {}).get("highRiskAlerts", True),
                    "predictiveAlerts": settings_data.get("notifications", {}).get("predictiveAlerts", True),
                    "reportGeneration": settings_data.get("notifications", {}).get("reportGeneration", True)
                },
                "dashboard": {
                    "defaultView": settings_data.get("dashboard", {}).get("defaultView", "overview"),
                    "autoRefresh": settings_data.get("dashboard", {}).get("autoRefresh", True),
                    "refreshInterval": settings_data.get("dashboard", {}).get("refreshInterval", 5),
                    "widgets": settings_data.get("dashboard", {}).get("widgets", [
                        "crime-heatmap",
                        "recent-alerts",
                        "crime-type-chart",
                        "predictive-analysis"
                    ])
                }
            }
        }
    )
