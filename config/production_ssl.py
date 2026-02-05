"""
Configuração específica SSL para MongoDB em ambientes de produção
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import ssl

def get_production_mongo_client(mongo_url: str):
    """
    Criar cliente MongoDB otimizado para produção/Render
    """
    
    # Configuração SSL mais permissiva para Render
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Opções de conexão otimizadas para Render
    client_options = {
        "serverSelectionTimeoutMS": 45000,  # Aumentar timeout
        "connectTimeoutMS": 45000,
        "socketTimeoutMS": 45000,
        "maxPoolSize": 5,  # Reduzir para free tier
        "minPoolSize": 1,
        "retryWrites": True,
        "w": "majority",
        "server_api": ServerApi('1'),
        # SSL settings
        "ssl": True,
        "tlsAllowInvalidCertificates": True,
        "tlsAllowInvalidHostnames": True,
        "ssl_context": ssl_context
    }
    
    return AsyncIOMotorClient(mongo_url, **client_options)

def get_render_compatible_url(base_url: str) -> str:
    """
    Ajustar URL para compatibilidade com Render
    """
    if "?" in base_url:
        # Adicionar parâmetros SSL se já existem parâmetros
        return f"{base_url}&ssl=true&ssl_cert_reqs=CERT_NONE&tlsAllowInvalidCertificates=true"
    else:
        # Adicionar parâmetros SSL se não existem parâmetros
        return f"{base_url}?ssl=true&ssl_cert_reqs=CERT_NONE&tlsAllowInvalidCertificates=true"