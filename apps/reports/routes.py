from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from sqlmodel import Session

from apps.reports.models import ReportCreate, ReportUpdate
from apps.reports.services import ReportService
from apps.users.models import User
from core.database import get_session
from core.utils.common import ResponseModel
from core.utils.security import get_current_user, check_permissions

router = APIRouter()

@router.get("/", response_model=dict)
async def list_reports(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List reports with optional filtering"""
    reports = ReportService.list_reports(
        session=session,
        page=page,
        limit=limit,
        type=type,
        district=district,
        start_date=start_date,
        end_date=end_date
    )
    
    return ResponseModel.success(data=reports)

@router.get("/{report_id}", response_model=dict)
async def get_report(
    report_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get report details"""
    report = ReportService.get_report(session=session, report_id=report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"Report with ID {report_id} not found"
            }
        )
    
    return ResponseModel.success(data={"report": report})

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: ReportCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(check_permissions(["create_reports"]))
):
    """Create a new report"""
    try:
        report = ReportService.create_report(
            session=session,
            report_data=report_data,
            user_id=current_user.id
        )
        return ResponseModel.success(data={"report": report})
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "Invalid report data",
                "fields": {"error": str(e)}
            }
        )

@router.put("/{report_id}", response_model=dict)
async def update_report(
    report_id: UUID,
    report_data: ReportUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a report"""
    report = ReportService.get_report(session=session, report_id=report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"Report with ID {report_id} not found"
            }
        )
    
    updated_report = ReportService.update_report(
        session=session,
        report_id=report_id,
        report_data=report_data,
        user_id=current_user.id
    )
    
    return ResponseModel.success(data={"report": updated_report})

@router.delete("/{report_id}", response_model=dict)
async def delete_report(
    report_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(check_permissions(["delete_reports"]))
):
    """Delete a report"""
    report = ReportService.get_report(session=session, report_id=report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"Report with ID {report_id} not found"
            }
        )
    
    ReportService.delete_report(session=session, report_id=report_id)
    
    return ResponseModel.success(message="Report successfully deleted")

@router.get("/{report_id}/export", response_model=dict)
async def export_report(
    report_id: UUID,
    format: str = Query("pdf", description="Export format (pdf, csv, json)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Export a report in the specified format"""
    report = ReportService.get_report(session=session, report_id=report_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"Report with ID {report_id} not found"
            }
        )
    
    if format not in ["pdf", "csv", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_format",
                "message": "Unsupported export format. Supported formats: pdf, csv, json"
            }
        )
    
    # In a real application, this would generate and return the file
    # For now, we'll just return a success message
    return ResponseModel.success(
        message=f"Report exported successfully in {format.upper()} format"
    )
