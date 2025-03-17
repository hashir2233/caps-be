from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from sqlmodel import Session
import logging

# Import the actual models and services - removing the comments
from apps.incidents.models import IncidentCreate, IncidentUpdate
from apps.incidents.services import IncidentService, SchemaMismatchError
from apps.users.models import User
from core.database import get_session
from core.utils.common import ResponseModel
from core.utils.security import get_current_user, check_permissions

# Set up logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=dict)
async def list_incidents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    district: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    severity: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List incidents with optional filtering"""
    try:
        result = IncidentService.list_incidents(
            session=session,
            page=page,
            limit=limit,
            type=type,
            district=district,
            start_date=start_date,
            end_date=end_date,
            severity=severity
        )
        
        # Normal successful result
        return ResponseModel.success(data=result)
    except SchemaMismatchError as e:
        # Handle schema mismatch error specifically and return a 500 error
        logger.error(f"Schema mismatch error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "schema_mismatch_error",
                "message": str(e)
            }
        )
    except ValueError as e:
        logger.error(f"Error listing incidents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "database_error",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in list_incidents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "server_error",
                "message": f"An unexpected error occurred: {str(e)}"
            }
        )

@router.get("/{incident_id}", response_model=dict)
async def get_incident(
    incident_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get incident details"""
    try:
        incident = IncidentService.get_incident(session=session, incident_id=incident_id)
        
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "not_found",
                    "message": f"Incident with ID {incident_id} not found"
                }
            )
        
        return ResponseModel.success(data={"incident": incident})
    except ValueError as e:
        logger.error(f"Database error getting incident {incident_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "database_error",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_incident: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "server_error",
                "message": "An unexpected error occurred"
            }
        )

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident_data: IncidentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new incident"""
    try:
        incident = IncidentService.create_incident(
            session=session,
            incident_data=incident_data,
            user_id=current_user.id
        )
        return ResponseModel.success(data={"incident": incident})
    except ValueError as e:
        if str(e).startswith("Database error:"):
            logger.error(f"Database error creating incident: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "database_error",
                    "message": str(e)
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "validation_error",
                    "message": "Invalid incident data",
                    "fields": {"error": str(e)}
                }
            )
    except Exception as e:
        logger.error(f"Unexpected error in create_incident: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "server_error",
                "message": "An unexpected error occurred"
            }
        )

@router.put("/{incident_id}", response_model=dict)
async def update_incident(
    incident_id: UUID,
    incident_data: IncidentUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update an incident"""
    try:
        incident = IncidentService.get_incident(session=session, incident_id=incident_id)
        
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "not_found",
                    "message": f"Incident with ID {incident_id} not found"
                }
            )
        
        updated_incident = IncidentService.update_incident(
            session=session,
            incident_id=incident_id,
            incident_data=incident_data,
            user_id=current_user.id
        )
        
        return ResponseModel.success(data={"incident": updated_incident})
    except ValueError as e:
        logger.error(f"Database error updating incident {incident_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "database_error",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in update_incident: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "server_error",
                "message": "An unexpected error occurred"
            }
        )

@router.delete("/{incident_id}", response_model=dict)
async def delete_incident(
    incident_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(check_permissions(["delete_incidents"]))
):
    """Delete an incident"""
    try:
        incident = IncidentService.get_incident(session=session, incident_id=incident_id)
        
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "not_found",
                    "message": f"Incident with ID {incident_id} not found"
                }
            )
        
        result = IncidentService.delete_incident(session=session, incident_id=incident_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "deletion_error",
                    "message": "Failed to delete incident"
                }
            )
        
        return ResponseModel.success(message="Incident successfully deleted")
    except ValueError as e:
        logger.error(f"Database error deleting incident {incident_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "database_error",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in delete_incident: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "server_error",
                "message": "An unexpected error occurred"
            }
        )
