from uuid import UUID, uuid4
from typing import Optional, Tuple, List
from datetime import datetime
from sqlmodel import Session, select

from apps.users.models import User, UserCreate, UserRead, UserUpdate
from core.utils.security import hash_password

class UserService:
    """Service for user-related operations"""
    
    @staticmethod
    def get_users(
        session: Session, 
        page: int = 1, 
        limit: int = 20,
        role: Optional[str] = None,
        district: Optional[str] = None
    ) -> Tuple[List[UserRead], int]:
        """Get users with optional filtering"""
        query = select(User)
        
        # Apply filters if provided
        if role:
            query = query.where(User.role == role)
        if district:
            query = query.where(User.district == district)
        
        # Get total count
        total = session.exec(query).count()
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        # Execute query
        users = session.exec(query).all()
        
        # Convert to UserRead models
        user_reads = [
            UserRead.from_orm(user) for user in users
        ]
        
        return user_reads, total
    
    @staticmethod
    def get_user_by_id(session: Session, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        # Ensure user_id is a UUID object
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return None
                
        # Query using the UUID object
        return session.exec(select(User).where(User.id == user_id)).first()
    
    @staticmethod
    def get_user_by_email(session: Session, email: str) -> Optional[User]:
        """Get a user by email"""
        return session.exec(select(User).where(User.email == email)).first()
    
    @staticmethod
    def create_user(session: Session, user_data: UserCreate) -> UserRead:
        """Create a new user"""
        # Check if email already exists
        existing_user = UserService.get_user_by_email(session, user_data.email)
        if existing_user:
            raise ValueError("Email already in use")
            
        # Check if badge number exists and is unique
        if user_data.badge_number:
            badge_exists = session.exec(
                select(User).where(User.badge_number == user_data.badge_number)
            ).first()
            if badge_exists:
                raise ValueError("Badge number must be unique")
        
        # Create user instance
        user = User(
            id=uuid4(),
            name=user_data.name,
            email=user_data.email,
            password=hash_password(user_data.password),
            role=user_data.role,
            district=user_data.district,
            department=user_data.department,
            phone=user_data.phone,
            badge_number=user_data.badge_number,
            # Set default permissions based on role
            permissions=UserService._get_default_permissions(user_data.role)
        )
        
        # Save to database
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return UserRead.from_orm(user)
    
    @staticmethod
    def update_user(
        session: Session, 
        user_id: UUID, 
        user_data: UserUpdate
    ) -> Optional[UserRead]:
        """Update a user"""
        user = session.exec(select(User).where(User.id == user_id)).first()
        
        if not user:
            return None
            
        # Check email uniqueness if being updated
        if user_data.email and user_data.email != user.email:
            existing_email = session.exec(
                select(User).where(User.email == user_data.email)
            ).first()
            if existing_email:
                raise ValueError("Email already in use")
                
        # Check badge number uniqueness if being updated
        if user_data.badge_number and user_data.badge_number != user.badge_number:
            badge_exists = session.exec(
                select(User).where(User.badge_number == user_data.badge_number)
            ).first()
            if badge_exists:
                raise ValueError("Badge number must be unique")
        
        # Update user fields
        user_data_dict = user_data.dict(exclude_unset=True)
        for key, value in user_data_dict.items():
            setattr(user, key, value)
            
        # Update timestamps
        user.updated_at = datetime.utcnow()
        
        # Save changes
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return UserRead.from_orm(user)
    
    @staticmethod
    def delete_user(session: Session, user_id: UUID) -> bool:
        """Delete a user"""
        user = session.exec(select(User).where(User.id == user_id)).first()
        
        if not user:
            return False
            
        session.delete(user)
        session.commit()
        
        return True
    
    @staticmethod
    def _get_default_permissions(role: str) -> List[str]:
        """Get default permissions based on role"""
        permission_map = {
            "admin": ["admin"],  # Admin has all permissions
            "analyst": [
                "view_incidents", "view_reports", "create_reports", 
                "view_alerts", "view_analytics"
            ],
            "officer": [
                "view_incidents", "create_incidents", "update_incidents",
                "view_alerts", "view_reports"
            ],
            "supervisor": [
                "view_incidents", "create_incidents", "update_incidents", "delete_incidents",
                "view_users", "view_reports", "create_reports", "view_alerts", "create_alerts",
                "view_analytics"
            ]
        }
        
        return permission_map.get(role.lower(), [])