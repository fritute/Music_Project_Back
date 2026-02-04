from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="MusicStream API", version="1.0.0")

# Root route for main app
@app.get("/")
async def read_root():
    return {
        "message": "🎵 MusicStream API", 
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "api": "/api"
    }

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Health check route
@api_router.get("/")
async def root():
    return {"message": "MusicStream API is running", "status": "healthy"}

# Import and include routers
from routes.auth_routes import router as auth_router
from routes.music_routes import router as music_router
from routes.playlist_routes import router as playlist_router
from routes.favorite_routes import router as favorite_router

api_router.include_router(auth_router)
api_router.include_router(music_router)
api_router.include_router(playlist_router)
api_router.include_router(favorite_router)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()