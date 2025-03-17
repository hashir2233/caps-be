from datetime import datetime, timedelta
from typing import Tuple, Optional
from uuid import uuid4, UUID

from sqlmodel import Session, select
from jose import jwt, JWTError
from passlib.context import CryptContext

from apps.users.models import User
from core.config import settings
from core.utils.email import send_email

class AuthService:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    @classmethod
    def get_password_hash(cls, password: str) -> str:
        """Generate password hash"""
        return cls.pwd_context.hash(password)
    
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return cls.pwd_context.verify(plain_password, hashed_password)
    
    @classmethod
    def create_access_token(cls, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @classmethod
    def create_refresh_token(cls, data: dict) -> str:
        """Create refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @classmethod
    def authenticate_user(cls, session: Session, email: str, password: str) -> Tuple[User, str, str]:
        """Authenticate user and return user, access token and refresh token"""
        # Find the user by email
        user = session.exec(select(User).where(User.email == email)).first()
        if user is None or not cls.verify_password(password, user.hashed_password):
            return None, None, None
        
        # Create access and refresh tokens
        # Ensure user_id is converted to string for JWT payload
        access_token = cls.create_access_token({"sub": str(user.id)})
        refresh_token = cls.create_refresh_token({"sub": str(user.id)})
        
        return user, access_token, refresh_token
    
    @classmethod
    def register_user(cls, session: Session, email: str, password: str, name: str, role: str) -> User:
        """Register a new user"""
        # Check if email is already registered
        existing_user = session.exec(select(User).where(User.email == email)).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Set default permissions based on role
        permissions = {}
        if role == "admin":
            permissions = {
                "view_users": True,
                "create_users": True,
                "update_users": True,
                "delete_users": True,
                "view_incidents": True,
                "create_incidents": True,
                "update_incidents": True,
                "delete_incidents": True,
                "view_reports": True,
                "create_reports": True,
                "delete_reports": True,
                "view_system_settings": True,
                "update_system_settings": True,
                "manage_resources": True
            }
        elif role == "analyst":
            permissions = {
                "view_incidents": True,
                "create_incidents": True,
                "view_reports": True,
                "create_reports": True
            }
        elif role == "officer":
            permissions = {
                "view_incidents": True,
                "create_incidents": True,
                "update_incidents": True
            }
        
        # Generate a unique ID
        user_id = uuid4()
        
        # Create new user
        hashed_password = cls.get_password_hash(password)
        user = User(
            id=user_id,  # Explicitly set the ID
            email=email,
            hashed_password=hashed_password,
            name=name,
            role=role,
            permissions=permissions,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return user
    
    @classmethod
    def refresh_token(cls, session: Session, refresh_token: str) -> Tuple[str, str]:
        """Create new access token and refresh token from refresh token"""
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id_str = payload.get("sub")
            
            if user_id_str is None:
                raise ValueError("Invalid refresh token")
            
            # Convert string UUID to UUID object    
            try:
                user_id = UUID(user_id_str)
            except ValueError:
                raise ValueError("Invalid user ID in token")
                
            # Use proper query instead of session.get
            user = session.exec(select(User).where(User.id == user_id)).first()
            if not user:
                raise ValueError("User not found")
                
            # Create new tokens
            access_token = cls.create_access_token(data={"sub": user_id_str})
            new_refresh_token = cls.create_refresh_token(data={"sub": user_id_str})
            
            return access_token, new_refresh_token
            
        except JWTError:
            raise ValueError("Invalid refresh token")
    
    @classmethod
    def request_password_reset(cls, session: Session, email: str) -> None:
        """Send password reset email to user"""
        user = session.exec(select(User).where(User.email == email)).first()
        
        if not user:
            raise ValueError("User not found")
            
        # Generate reset token
        reset_token = cls.create_access_token(
            data={"sub": str(user.id), "type": "password_reset"},
            expires_delta=timedelta(hours=1)
        )
        
        # In a real application, you would send an email with a link to reset password
        # For this example, we'll just print it
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        # Send email with reset link
        send_email(
            to_email=user.email,
            subject="Password Reset Request",
            body=f"Click the link below to reset your password:\n{reset_url}"
        )
