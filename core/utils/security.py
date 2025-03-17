from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlmodel import Session, select
from passlib.context import CryptContext
from uuid import UUID

from core.config import settings
from core.database import get_session
from apps.users.models import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Update the OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PREFIX}/auth/token",  # Point to the new token endpoint
    description="JWT authentication",
    auto_error=True,
    scheme_name="JWT"
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """Hash a password for storing"""
    return pwd_context.hash(password)

def create_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token with an optional expiration time"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_access_token(data: Dict[str, Any]) -> str:
    """Create an access token"""
    return create_token(
        data, 
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a refresh token"""
    return create_token(
        data, 
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

def decode_token(token: str) -> Dict[str, Any]:
    """Decode a JWT token"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY,  # Changed from JWT_SECRET_KEY
            algorithms=[settings.ALGORITHM]  # Changed from JWT_ALGORITHM
        )
        return payload
    except jwt.PyJWTError:
        return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "unauthorized",
            "message": "Could not validate credentials"
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        # Convert string UUID to UUID object
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise credentials_exception
        
        # Use string parameter binding for UUID - this fixes the 'hex' attribute error
        user = session.exec(select(User).where(User.id == user_id)).first()
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    return user

def check_permissions(required_permissions: List[str]):
    """Check if user has required permissions"""
    async def _check_permissions(
        current_user: User = Depends(get_current_user)
    ) -> User:
        # Admin role has all permissions
        if current_user.role == "admin":
            return current_user
        
        # Check if user has all required permissions
        user_permissions = current_user.permissions or {}
        user_permission_keys = list(user_permissions.keys()) if isinstance(user_permissions, dict) else []
        
        if not all(perm in user_permission_keys for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "permission_denied",
                    "message": "You do not have permission to perform this action"
                }
            )
        
        return current_user
    
    return _check_permissions