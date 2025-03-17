from fastapi import APIRouter, Depends, HTTPException, status, Body, Security
from fastapi.security import OAuth2PasswordRequestForm
from apps.auth.models import LoginRequest, RegisterRequest, RefreshTokenRequest, ResetPasswordRequest, TokenResponse
from apps.auth.services import AuthService
from apps.users.models import UserRead
from core.database import get_session
from core.utils.common import ResponseModel
from sqlmodel import Session

router = APIRouter()

@router.post("/login", response_model=dict)
async def login(
    request: LoginRequest,
    session: Session = Depends(get_session)
):
    """Login with email and password"""
    try:
        user, token, refresh_token = AuthService.authenticate_user(
            session=session,
            email=request.email,
            password=request.password
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    return ResponseModel.success(
        data={
            "user": UserRead.model_validate(user),
            "token": token,
            "refreshToken": refresh_token
        }
    )

# Add this endpoint specifically for Swagger UI
@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """Login to get access token for Swagger UI"""
    try:
        user, access_token, refresh_token = AuthService.authenticate_user(
            session=session,
            email=form_data.username,  # OAuth2 form uses username field
            password=form_data.password
        )
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            # Include any additional fields you need
            user_id=user.id,
            role=user.role
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=dict)
async def register(
    request: RegisterRequest,
    session: Session = Depends(get_session)
):
    """Register a new user"""
    try:
        user = AuthService.register_user(
            session=session,
            email=request.email,
            password=request.password,
            name=request.name,
            role=request.role
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": str(e),
                "fields": {
                    "email": "This email is already registered"
                }
            }
        )
    
    return ResponseModel.success(
        data={
            "user": UserRead.from_orm(user)
        }
    )

@router.post("/refresh", response_model=dict)
async def refresh_token(
    request: RefreshTokenRequest,
    session: Session = Depends(get_session)
):
    """Refresh an expired JWT token"""
    try:
        token, refresh_token = AuthService.refresh_token(
            session=session,
            refresh_token=request.refresh_token
        )
    except ValueError as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "invalid_token",
                "message": "Refresh token is invalid or expired"
            }
        )
    
    return ResponseModel.success(
        data={
            "token": token,
            "refreshToken": refresh_token
        }
    )

@router.post("/reset-password", response_model=dict)
async def reset_password_request(
    request: ResetPasswordRequest,
    session: Session = Depends(get_session)
):
    """Initiate password reset process"""
    try:
        AuthService.request_password_reset(
            session=session,
            email=request.email
        )
    except ValueError:
        # Return success regardless to prevent email enumeration
        pass
    
    return ResponseModel.success(
        message="Password reset instructions sent to your email"
    )