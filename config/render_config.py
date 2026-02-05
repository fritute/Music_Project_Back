#!/usr/bin/env python3
"""
Configuração específica para deploy no Render
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_render_config():
    """
    Configuração específica para Render
    """
    return {
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 10000)),  # Render usa PORT como variável
        "mongo_url": os.getenv("MONGO_URL"),
        "db_name": os.getenv("DB_NAME", "musicstream"),
        "jwt_secret": os.getenv("JWT_SECRET", "fallback-secret-key"),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "debug": os.getenv("DEBUG", "false").lower() == "true"
    }

def validate_render_config():
    """
    Valida se todas as configurações necessárias estão presentes
    """
    config = get_render_config()
    required_vars = ["MONGO_URL", "JWT_SECRET"]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    return config

if __name__ == "__main__":
    try:
        config = validate_render_config()
        print("✅ Render configuration valid!")
        print(f"   Port: {config['port']}")
        print(f"   Environment: {config['environment']}")
        print(f"   MongoDB URL: {'Set' if config['mongo_url'] else 'Not set'}")
        print(f"   JWT Secret: {'Set' if config['jwt_secret'] else 'Not set'}")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        exit(1)