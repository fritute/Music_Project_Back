"""
Middleware personalizado para CORS
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import logging

logger = logging.getLogger(__name__)

class CORSMiddleware(BaseHTTPMiddleware):
    """
    Middleware personalizado para lidar com CORS
    """
    
    async def dispatch(self, request: Request, call_next):
        # Log da requisição para debug
        logger.info(f"CORS Request: {request.method} {request.url}")
        logger.info(f"Origin: {request.headers.get('origin', 'No origin')}")
        
        # Se for uma requisição OPTIONS (preflight), responder imediatamente
        if request.method == "OPTIONS":
            response = StarletteResponse()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
            response.headers["Access-Control-Allow-Headers"] = (
                "Accept, Accept-Language, Content-Language, Content-Type, "
                "Authorization, X-Requested-With, Range, Cache-Control"
            )
            response.headers["Access-Control-Max-Age"] = "3600"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
        
        # Processar requisição normal
        response = await call_next(request)
        
        # Adicionar headers CORS à resposta
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "*"
        
        return response