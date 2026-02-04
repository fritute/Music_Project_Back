from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import MusicResponse, MusicInDB
from auth import get_current_user_id
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
import os
import shutil
from pathlib import Path
import mimetypes

router = APIRouter(prefix="/music", tags=["music"])

# Database dependency - import from server
def get_database():
    from server import db
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    return db

# Use relative paths for Render compatibility
UPLOAD_DIR = Path("uploads/music")
COVER_DIR = Path("uploads/covers")

# Create directories safely
try:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    COVER_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # In production, use /tmp directory if uploads folder is not writable
    import tempfile
    temp_dir = Path(tempfile.gettempdir())
    UPLOAD_DIR = temp_dir / "music"
    COVER_DIR = temp_dir / "covers"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    COVER_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", response_model=MusicResponse, status_code=status.HTTP_201_CREATED)
async def upload_music(
    title: str = Form(...),
    artist: str = Form(...),
    genre: str = Form(...),
    duration: int = Form(...),
    audio: UploadFile = File(...),
    cover: Optional[UploadFile] = File(None),
    user_id: str = Depends(get_current_user_id)
):
    # Validate audio file
    if not audio.content_type or not audio.content_type.startswith('audio/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an audio file"
        )
    
    # Generate unique filename for audio
    file_extension = os.path.splitext(audio.filename)[1]
    unique_filename = f"{ObjectId()}_{title.replace(' ', '_')}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save audio file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save audio file: {str(e)}"
        )
    
    # Handle cover image upload
    cover_url = "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400&h=400&fit=crop"
    if cover:
        # Validate image file
        if not cover.content_type or not cover.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cover must be an image file"
            )
        
        # Generate unique filename for cover
        cover_extension = os.path.splitext(cover.filename)[1]
        unique_cover_filename = f"{ObjectId()}_{title.replace(' ', '_')}{cover_extension}"
        cover_path = COVER_DIR / unique_cover_filename
        
        # Save cover file
        try:
            with open(cover_path, "wb") as buffer:
                shutil.copyfileobj(cover.file, buffer)
            cover_url = f"/api/music/cover/{unique_cover_filename}"
        except Exception as e:
            # Don't fail upload if cover fails, just use default
            print(f"Failed to save cover: {str(e)}")
    
    # Create music document
    music_dict = {
        "title": title,
        "artist": artist,
        "genre": genre,
        "duration": duration,
        "coverUrl": cover_url,
        "audioUrl": f"/api/music/stream/{unique_filename}",
        "uploadedBy": user_id,
        "createdAt": datetime.utcnow()
    }
    
    # Get database connection
    db = get_database()
    result = await db.musics.insert_one(music_dict)
    music_id = str(result.inserted_id)
    
    return MusicResponse(
        id=music_id,
        title=title,
        artist=artist,
        genre=genre,
        duration=duration,
        coverUrl=music_dict['coverUrl'],
        audioUrl=music_dict['audioUrl'],
        uploadedBy=user_id,
        createdAt=music_dict['createdAt']
    )

@router.get("/stream/{filename}")
async def stream_music(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Range, Content-Range"
        }
    )

@router.get("/cover/{filename}")
async def get_cover(filename: str):
    file_path = COVER_DIR / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cover image not found"
        )
    
    # Determine media type from file extension
    media_type = mimetypes.guess_type(filename)[0] or "image/jpeg"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*"
        }
    )

@router.get("", response_model=List[MusicResponse])
async def get_all_musics():
    musics = await db.musics.find().to_list(1000)
    return [
        MusicResponse(
            id=str(music['_id']),
            title=music['title'],
            artist=music['artist'],
            genre=music['genre'],
            duration=music['duration'],
            coverUrl=music['coverUrl'],
            audioUrl=music['audioUrl'],
            uploadedBy=music['uploadedBy'],
            createdAt=music['createdAt']
        )
        for music in musics
    ]

@router.get("/{music_id}", response_model=MusicResponse)
async def get_music(music_id: str):
    music = await db.musics.find_one({"_id": ObjectId(music_id)})
    if not music:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Music not found"
        )
    
    return MusicResponse(
        id=str(music['_id']),
        title=music['title'],
        artist=music['artist'],
        genre=music['genre'],
        duration=music['duration'],
        coverUrl=music['coverUrl'],
        audioUrl=music['audioUrl'],
        uploadedBy=music['uploadedBy'],
        createdAt=music['createdAt']
    )

@router.delete("/{music_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_music(
    music_id: str,
    user_id: str = Depends(get_current_user_id)
):
    music = await db.musics.find_one({"_id": ObjectId(music_id)})
    if not music:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Music not found"
        )
    
    # Check if user is the uploader
    if music['uploadedBy'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this music"
        )
    
    # Delete file
    filename = music['audioUrl'].split('/')[-1]
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        os.remove(file_path)
    
    # Delete from database
    await db.musics.delete_one({"_id": ObjectId(music_id)})
    
    return None