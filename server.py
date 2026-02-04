from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from datetime import datetime
from cors_config import get_cors_config
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

# Root route for main app
@app.get("/")
async def read_root():
    db_status = "disconnected"
    db_info = {}
    
    if client and db:
        try:
            # Test database connection
            await client.admin.command('ping')
            db_status = "connected"
            
            # Get database info
            server_info = await client.server_info()
            db_info = {
                "name": db.name,
                "mongodb_version": server_info.get("version", "unknown"),
                "connection_time": "< 1s"
            }
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
            "health": "/test-cors"
        }
    }

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Health check route
@api_router.get("/")
async def root():
    return {"message": "MusicStream API is running", "status": "healthy"}

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
async def options_handler():
    return {"message": "OK"}

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

# Configure CORS middleware BEFORE including routers
cors_config = get_cors_config()
app.add_middleware(CORSMiddleware, **cors_config)

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
    success = await init_database()
    if not success:
        logger.warning("⚠️ API running without database connection")
        logger.info("💡 To connect to database:")
        logger.info("   1. Check your internet connection")
        logger.info("   2. Verify MongoDB Atlas credentials in .env")
        logger.info("   3. Or install MongoDB locally")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    if client:
        client.close()
        logger.info("📦 MongoDB connection closed")