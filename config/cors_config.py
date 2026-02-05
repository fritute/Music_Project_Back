"""
Configurações de CORS para a aplicação MusicStream API
"""
import os
from typing import List

def get_cors_origins() -> List[str]:
    """
    Retorna lista de origens permitidas para CORS
    """
    # Origens padrão para desenvolvimento
    default_origins = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:5173",  # Vite
        "http://localhost:4200",  # Angular
        "https://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://127.0.0.1:3000",
        # Adicionar domínios de produção conhecidos
        "https://music-project-front-3.vercel.app",
        "https://music-project-backend.onrender.com",
        "https://music-project-back-4.onrender.com"
    ]
    
    # Origens de produção do arquivo .env
    env_origins = os.getenv('CORS_ORIGINS', '*')
    
    if env_origins == '*':
        # Em desenvolvimento, permitir todas as origens
        return ["*"]
    else:
        # Em produção, usar origens específicas
        prod_origins = [origin.strip() for origin in env_origins.split(',')]
        return default_origins + prod_origins

def get_cors_config() -> dict:
    """
    Retorna configuração completa de CORS
    """
    return {
        "allow_origins": get_cors_origins(),
        "allow_credentials": True,
        "allow_methods": [
            "GET", 
            "POST", 
            "PUT", 
            "DELETE", 
            "OPTIONS", 
            "PATCH", 
            "HEAD"
        ],
        "allow_headers": [
            "Accept",
            "Accept-Language", 
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
            "X-CSRF-Token",
            "Cache-Control",
            "Pragma",
            "Range",
            "Content-Range"
        ],
        "expose_headers": ["*"],
        "max_age": 600
    }