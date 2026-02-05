#!/usr/bin/env python3
"""
Script de inicialização otimizado para Render
"""
import uvicorn
import os
import logging
from pathlib import Path
from render_config import get_render_config, validate_render_config

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Inicializar servidor para Render"""
    
    try:
        # Validate configuration
        config = validate_render_config()
        logger.info("🚀 Starting MusicStream API on Render...")
        logger.info(f"   Environment: {config['environment']}")
        logger.info(f"   Port: {config['port']}")
        
        # Create upload directories
        upload_dirs = [
            Path("uploads/music"),
            Path("uploads/covers")
        ]
        
        for dir_path in upload_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ Directory created: {dir_path}")
        
        # Start server with Render-optimized settings
        uvicorn.run(
            "server:app",
            host=config["host"],
            port=config["port"],
            log_level="info",
            access_log=True,
            # Render-specific optimizations
            workers=1,  # Single worker for free tier
            loop="uvloop",  # Faster event loop if available
            http="httptools",  # Faster HTTP parser if available
            reload=False  # Never reload in production
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        raise

if __name__ == "__main__":
    main()