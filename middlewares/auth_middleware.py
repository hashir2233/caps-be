from typing import List
import re
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.security import decode_token

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication"""
    
    async def dispatch(self, request: Request, call_next):
        # Public paths that don't require authentication
        public_paths = [
            r"^/api/auth/login",
            r"^/api/auth/register",
            r"^/api/auth/refresh",
            r"^/api/auth/reset-password",
            r"^/$",  # Root path
            r"^/docs",  # Swagger docs
            r"^/redoc",  # ReDoc
            r"^/openapi.json",  # OpenAPI schema
        ]
        
        # Check if the path is public
        path = request.url.path
        if any(re.match(pattern, path) for pattern in public_paths):
            return await call_next(request)
        
        # Check for auth token in header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": {
                        "code": "unauthorized",
                        "message": "Authentication required for this endpoint"
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract and validate token
        token = auth_header.split(' ')[1]
        payload = decode_token(token)
        
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": {
                        "code": "invalid_token",
                        "message": "The provided token is invalid or expired"
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Set user info in request state for use in endpoint handlers
        request.state.user_id = payload.get("sub")
        request.state.user_role = payload.get("role")
        
        return await call_next(request)