from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from datetime import datetime
from cors_config import get_cors_config
from production_cors import ProductionCORSMiddleware
from database_utils import init_collections, check_database_health
import os
import logging
import asyncio
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection with error handling
client = None
db = None

async def init_database():
    """Initialize database connection"""
    global client, db
    
    mongo_url = os.getenv('MONGO_URL')
    mongo_local_url = os.getenv('MONGO_LOCAL_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'musicstream')
    
    if not mongo_url:
        logger.warning("MONGO_URL not found, running without database")
        return False
    
    # Try Atlas first with ServerApi, then local if it fails
    connection_configs = [
        {
            "url": mongo_url,
            "type": "Atlas",
            "options": {
                "serverSelectionTimeoutMS": 15000,
                "connectTimeoutMS": 15000,
                "socketTimeoutMS": 15000,
                "maxPoolSize": 10,
                "minPoolSize": 1,
                "server_api": ServerApi('1')
            }
        },
        {
            "url": mongo_local_url,
            "type": "Local",
            "options": {
                "serverSelectionTimeoutMS": 5000,
                "connectTimeoutMS": 5000,
                "socketTimeoutMS": 5000,
                "maxPoolSize": 10,
                "minPoolSize": 1
            }
        }
    ]
    
    for config in connection_configs:
        try:
            logger.info(f"🔌 Trying {config['type']} MongoDB connection...")
            
            # Create client with appropriate settings
            client = AsyncIOMotorClient(config["url"], **config["options"])
            
            # Test connection
            await client.admin.command('ping')
            db = client[db_name]
            
            logger.info(f"✅ MongoDB connected successfully ({config['type']}) to database: {db_name}")
            
            # Initialize collections and indexes
            await init_collections(db)
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ {config['type']} MongoDB connection failed: {e}")
            if client:
                client.close()
            client = None
            db = None
            continue
    
    logger.error("❌ All MongoDB connection attempts failed")
    return False

# Initialize connection synchronously for startup
try:
    mongo_url = os.getenv('MONGO_URL')
    db_name = os.getenv('DB_NAME', 'musicstream')
    
    if mongo_url:
        logger.info("Setting up MongoDB client...")
        client = AsyncIOMotorClient(
            mongo_url,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        db = client[db_name]
        logger.info("MongoDB client configured")
except Exception as e:
    logger.error(f"Failed to setup MongoDB client: {e}")
    client = None
    db = None

# Create the main app without a prefix
app = FastAPI(title="MusicStream API", version="1.0.0")

# Global CORS headers middleware - MUST be first
@app.middleware("http")
async def add_cors_headers(request, call_next):
    """Add CORS headers to all responses including errors"""
    try:
        response = await call_next(request)
    except Exception as e:
        # Even if there's an error, return with CORS headers
        from fastapi.responses import JSONResponse
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # Add CORS headers to ALL responses
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Range, Cache-Control"
    response.headers["Access-Control-Expose-Headers"] = "*"
    
    return response

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Global exception handler that preserves CORS
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all exceptions while preserving CORS headers"""
    logger.error(f"Global exception: {exc}")
    
    response = JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if os.getenv("DEBUG") == "true" else "Server error"
        }
    )
    
    # Ensure CORS headers are always present
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler_with_cors(request: Request, exc: HTTPException):
    """Handle HTTP exceptions while preserving CORS headers"""
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    
    # Add CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Health check route
@api_router.get("/")
async def root():
    return {"message": "MusicStream API is running", "status": "healthy"}

# Simple health check for Render
@app.get("/health")  
async def simple_health_check():
    """Simple health check for Render platform"""
    return {
        "status": "healthy",
        "service": "MusicStream API",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

# Render-specific root endpoint
@app.get("/")
async def render_root():
    """Root endpoint optimized for Render health checks"""
    try:
        db_status = "disconnected"
        db_info = {}
        
        if client and db:
            try:
                # Quick ping test
                await asyncio.wait_for(client.admin.command('ping'), timeout=2.0)
                db_status = "connected"
                db_info = {"name": db.name}
            except asyncio.TimeoutError:
                db_status = "timeout"
            except Exception as e:
                db_status = f"error: {str(e)}"
        
        return {
            "message": "🎵 MusicStream API", 
            "version": "1.0.0",
            "status": "online",
            "database": {
                "status": db_status,
                **db_info
            },
            "endpoints": {
                "docs": "/docs",
                "api": "/api",
                "health": "/health"
            },
            "render_ready": True
        }
    except Exception as e:
        # Never fail health check - Render needs this to work
        return {
            "message": "🎵 MusicStream API", 
            "version": "1.0.0",
            "status": "online",
            "error": str(e),
            "render_ready": True
        }

# API health check  
@api_router.get("/health")
async def health_check():
    if not client or not db:
        return {
            "api": "healthy",
            "database": {
                "status": "disconnected",
                "message": "Database client not initialized"
            },
            "timestamp": datetime.utcnow()
        }
    
    try:
        # Check database health
        db_health = await check_database_health(db)
        
        return {
            "api": "healthy",
            "database": db_health,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        return {
            "api": "healthy",
            "database": {
                "status": "error",
                "error": str(e)
            },
            "timestamp": datetime.utcnow()
        }

# Database connection test
@api_router.get("/db-test")
async def test_database_connection():
    """Test database connection manually"""
    if not client or not db:
        # Try to reconnect
        logger.info("🔄 Attempting to reconnect to database...")
        success = await init_database()
        
        if not success:
            return {
                "status": "failed",
                "message": "Could not connect to database",
                "suggestions": [
                    "Check internet connection",
                    "Verify MongoDB credentials", 
                    "Install MongoDB locally",
                    "Check DNS resolution"
                ]
            }
    
    try:
        # Test connection
        await client.admin.command('ping')
        db_health = await check_database_health(db)
        
        return {
            "status": "success",
            "message": "Database connected successfully!",
            "health": db_health
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Database connection failed: {str(e)}",
            "suggestions": [
                "Check MongoDB server status",
                "Verify network connectivity",
                "Check authentication credentials"
            ]
        }

# Import and include routers
from routes.auth_routes import router as auth_router
from routes.music_routes import router as music_router
from routes.playlist_routes import router as playlist_router
from routes.favorite_routes import router as favorite_router

api_router.include_router(auth_router)
api_router.include_router(music_router)
api_router.include_router(playlist_router)
api_router.include_router(favorite_router)

# Add OPTIONS handler for CORS preflight
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return {
        "message": "CORS preflight OK",
        "path": full_path,
        "methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    }

# CORS test endpoint
@app.get("/test-cors")
async def test_cors():
    db_status = "disconnected"
    collections_count = 0
    
    if client and db:
        try:
            await client.admin.command('ping')
            db_status = "connected"
            collections = await db.list_collection_names()
            collections_count = len(collections)
        except Exception as e:
            db_status = f"error: {str(e)}"
    
    return {
        "message": "🔥 CORS and Database working!", 
        "status": "ok",
        "timestamp": datetime.utcnow(),
        "database": {
            "status": db_status,
            "collections": collections_count
        },
        "cors_headers": {
            "origin": "*",
            "methods": "GET, POST, PUT, DELETE, OPTIONS",
            "credentials": True
        }
    }

# Include the router in the main app
app.include_router(api_router)

# Rota de teste para CORS
@app.get("/test-cors")
async def test_cors():
    return {
        "message": "CORS working!", 
        "status": "ok",
        "timestamp": datetime.utcnow(),
        "database": "connected" if db is not None else "disconnected"
    }

@app.on_event("startup") 
async def startup_event():
    """Initialize database connection on startup"""
    try:
        success = await init_database()
        if not success:
            logger.warning("⚠️ API running without database connection")
            logger.info("💡 To connect to database:")
            logger.info("   1. Check your internet connection")
            logger.info("   2. Verify MongoDB Atlas credentials in environment variables")
            logger.info("   3. Check if MONGO_URL environment variable is set")
            
            # For production (Render), this is critical
            if os.getenv("ENVIRONMENT") == "production":
                logger.error("🚨 Production environment requires database connection!")
                # Don't fail startup, but log the error
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        # In production, continue anyway to allow health checks

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    if client:
        client.close()
        logger.info("📦 MongoDB connection closed")