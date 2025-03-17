from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from uuid import UUID, uuid4

from apps.users.models import User, UserCreate, UserUpdate
from core.database import get_session
from core.utils.common import ResponseModel
from core.utils.security import get_current_user, check_permissions
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    district: Optional[str] = None,
    session: Session = Depends(get_session),
    _: User = Depends(check_permissions(["view_users"]))
):
    """List users with optional filtering"""
    # In a real application, we'd implement proper filtering and pagination
    # For now, we'll return mock data
    users = [
        {
            "id": "usr_123456",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "role": "analyst",
            "district": "downtown",
            "lastActive": "2025-03-14T20:15:00Z"
        },
        {
            "id": "usr_123457",
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "role": "officer",
            "district": "westside",
            "lastActive": "2025-03-14T18:30:00Z"
        }
    ]
    
    return ResponseModel.success(
        data={
            "users": users,
            "pagination": {
                "total": 42,
                "page": page,
                "limit": limit,
                "pages": 3
            }
        }
    )

@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get user details"""
    # Allow users to view their own profile or users with view_users permission
    if current_user.id != user_id and "view_users" not in (current_user.permissions or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": "You do not have permission to view this user"
            }
        )
    
    # In a real application, we'd fetch from the database
    # For now, mock data
    if user_id == "usr_123456":
        user = {
            "id": "usr_123456",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "role": "analyst",
            "district": "downtown",
            "phone": "+1-555-123-4567",
            "badgeNumber": "A12345",
            "department": "Crime Analysis Unit",
            "joinDate": "2023-06-15T00:00:00Z",
            "permissions": ["view_incidents", "edit_incidents", "view_reports", "create_reports"],
            "lastActive": "2025-03-14T20:15:00Z",
            "profileComplete": 75
        }
        return ResponseModel.success(data={"user": user})
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "code": "not_found",
            "message": f"User with ID {user_id} not found"
        }
    )

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    session: Session = Depends(get_session),
    _: User = Depends(check_permissions(["create_users"]))
):
    """Create a new user"""
    try:
        # In a real application, we'd check for duplicate email/badge number
        # and save to the database
        
        user = {
            "id": uuid4(),
            "name": user_data.name,
            "email": user_data.email,
            "role": user_data.role,
            "district": user_data.district,
            "department": user_data.department,
            "phone": user_data.phone,
            "badgeNumber": user_data.badge_number,
            "joinDate": datetime.utcnow().isoformat(),
            "createdAt": datetime.utcnow().isoformat()
        }
        
        return ResponseModel.success(data={"user": user})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": str(e),
                "fields": {
                    "email": "Email already in use",
                    "badgeNumber": "Badge number must be unique"
                }
            }
        )

@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a user"""
    # Allow users to update their own profile or users with update_users permission
    if current_user.id != user_id and "update_users" not in (current_user.permissions or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": "You do not have permission to update this user"
            }
        )
    
    # In a real application, we'd update the database
    # For now, mock response
    user = {
        "id": user_id,
        "name": user_data.name if user_data.name else "Robert M. Johnson",
        "email": user_data.email if user_data.email else "robert.johnson@example.com",
        "role": user_data.role if user_data.role else "officer",
        "district": user_data.district if user_data.district else "eastside",
        "department": user_data.department if user_data.department else "Special Investigations Unit",
        "updatedAt": datetime.utcnow().isoformat()
    }
    
    return ResponseModel.success(data={"user": user})

@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(check_permissions(["delete_users"]))
):
    """Delete a user"""
    # In a real application, we'd delete from the database
    # For now, mock response
    return ResponseModel.success(message="User successfully deleted")