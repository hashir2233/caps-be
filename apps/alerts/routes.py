from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from sqlmodel import Session

from apps.alerts.models import AlertCreate, AlertUpdate
from apps.alerts.services import AlertService
from apps.users.models import User
from core.database import get_session
from core.utils.common import ResponseModel
from core.utils.security import get_current_user, check_permissions

router = APIRouter()

@router.get("/", response_model=dict)
async def list_alerts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    district: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List alerts with optional filtering"""
    alerts = AlertService.list_alerts(
        session=session,
        page=page,
        limit=limit,
        severity=severity,
        status=status,
        district=district
    )
    
    return ResponseModel.success(data=alerts)

@router.get("/{alert_id}", response_model=dict)
async def get_alert(
    alert_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get alert details"""
    alert = AlertService.get_alert(session=session, alert_id=alert_id)
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"Alert with ID {alert_id} not found"
            }
        )
    
    return ResponseModel.success(data={"alert": alert})

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new alert"""
    try:
        alert = AlertService.create_alert(
            session=session,
            alert_data=alert_data,
            user_id=current_user.id
        )
        return ResponseModel.success(data={"alert": alert})
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "Invalid alert data",
                "fields": {"error": str(e)}
            }
        )

@router.put("/{alert_id}", response_model=dict)
async def update_alert(
    alert_id: UUID,
    alert_data: AlertUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update an alert"""
    alert = AlertService.get_alert(session=session, alert_id=alert_id)
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"Alert with ID {alert_id} not found"
            }
        )
    
    updated_alert = AlertService.update_alert(
        session=session,
        alert_id=alert_id,
        alert_data=alert_data
    )
    
    return ResponseModel.success(data={"alert": updated_alert})

@router.delete("/{alert_id}", response_model=dict)
async def delete_alert(
    alert_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(check_permissions(["delete_alerts"]))
):
    """Delete an alert"""
    alert = AlertService.get_alert(session=session, alert_id=alert_id)
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"Alert with ID {alert_id} not found"
            }
        )
    
    AlertService.delete_alert(session=session, alert_id=alert_id)
    
    return ResponseModel.success(message="Alert successfully deleted")
