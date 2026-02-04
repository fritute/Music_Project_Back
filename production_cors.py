"""
Middleware CORS personalizado para garantir funcionamento em produção
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from typing import List
import os

class ProductionCORSMiddleware(BaseHTTPMiddleware):
    """
    Middleware CORS personalizado para produção
    """
    
    def __init__(self, app, allowed_origins: List[str] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        
    def is_cors_preflight(self, request: Request) -> bool:
        """Verifica se é uma requisição preflight CORS"""
        return (
            request.method == "OPTIONS" and
            "origin" in request.headers and
            "access-control-request-method" in request.headers
        )
        
    def is_cors_request(self, request: Request) -> bool:
        """Verifica se é uma requisição CORS"""
        return "origin" in request.headers
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if self.is_cors_preflight(request):
            response = StarletteResponse()
            response.headers["access-control-allow-origin"] = "*"
            response.headers["access-control-allow-methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
            response.headers["access-control-allow-headers"] = (
                "accept, accept-language, content-language, content-type, "
                "authorization, x-requested-with, range, cache-control"
            )
            response.headers["access-control-max-age"] = "3600"
            response.headers["access-control-allow-credentials"] = "true"
            return response
        
        # Handle actual requests
        response = await call_next(request)
        
        # Add CORS headers to all responses
        if self.is_cors_request(request):
            response.headers["access-control-allow-origin"] = "*"
            response.headers["access-control-allow-credentials"] = "true"
            response.headers["access-control-expose-headers"] = "*"
            response.headers["vary"] = "Origin"
        
        return response