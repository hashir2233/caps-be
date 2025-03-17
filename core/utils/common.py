from typing import Dict, Any, Optional, List, TypeVar, Generic
from datetime import datetime, date
from uuid import UUID

T = TypeVar('T')

class ResponseModel(Generic[T]):
    """Standard response model for API endpoints"""
    @staticmethod
    def success(data: Optional[Dict[str, Any]] = None, message: Optional[str] = None) -> Dict[str, Any]:
        """Standard success response"""
        response = {"success": True}
        
        if data:
            response["data"] = data
            
        if message:
            response["message"] = message
            
        return response
    
    @staticmethod
    def error(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Standard error response"""
        error_data = {
            "code": code,
            "message": message
        }
        
        if details:
            error_data.update({"details": details})
            
        return {
            "success": False,
            "error": error_data
        }

def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO 8601 format"""
    if not dt:
        return None
    return dt.isoformat()

def format_date(d: date) -> str:
    """Format date to ISO 8601 format"""
    if not d:
        return None
    return d.isoformat()

def paginate_response(
    items: List[Any], 
    page: int, 
    limit: int, 
    total: int
) -> Dict[str, Any]:
    """Create a paginated response"""
    return {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }
    }

def ensure_uuid(uuid_value):
    """
    Ensure a value is a UUID object
    
    Args:
        uuid_value: String or UUID object
        
    Returns:
        UUID object
    """
    if isinstance(uuid_value, str):
        return UUID(uuid_value)
    return uuid_value