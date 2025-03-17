from typing import Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from jose import jwt, JWTError

from core.config import settings

class RateLimiter(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        # Dictionary to track requests: {ip_or_user: [(timestamp, requests_count)]}
        self.requests: Dict[str, list] = {}
        # Time window for rate limiting (60 seconds)
        self.window_size = 60
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier (user_id if authenticated, IP otherwise)
        identifier = await self._get_identifier(request)
        
        # Get current time
        current_time = time.time()
        
        # Check if identifier exists in requests dict
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove expired timestamps (older than window_size)
        self.requests[identifier] = [
            (timestamp, count) for timestamp, count in self.requests[identifier]
            if timestamp > current_time - self.window_size
        ]
        
        # Count total requests in current window
        total_requests = sum(count for _, count in self.requests[identifier])
        
        # Check if rate limit is exceeded
        authenticated = await self._is_authenticated(request)
        rate_limit = 100 if authenticated else 20  # Authenticated: 100 per minute, Unauthenticated: 20 per minute
        
        if total_requests >= rate_limit:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "rate_limit_exceeded",
                        "message": "Rate limit exceeded. Please try again later.",
                        "retryAfter": self.window_size
                    }
                }
            )
        
        # Add current request to the requests list
        self.requests[identifier].append((current_time, 1))
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = rate_limit - total_requests - 1
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_size))
        
        return response
    
    async def _get_identifier(self, request: Request) -> str:
        """Get client identifier (user_id if authenticated, IP otherwise)"""
        # Try to extract user_id from token
        user_id = await self._extract_user_id(request)
        
        if user_id:
            return f"user_{user_id}"
        
        # Fall back to client's IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip_{ip}"
    
    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user_id from authorization header token"""
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return None
        
        token = auth.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            return user_id
        except JWTError:
            return None
    
    async def _is_authenticated(self, request: Request) -> bool:
        """Check if request is authenticated"""
        return await self._extract_user_id(request) is not None