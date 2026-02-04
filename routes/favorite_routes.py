from fastapi import APIRouter, HTTPException, status, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import MusicResponse
from auth import get_current_user_id
from bson import ObjectId
from typing import List

router = APIRouter(prefix="/favorite", tags=["favorite"])

from server import db

@router.post("/{music_id}", status_code=status.HTTP_200_OK)
async def toggle_favorite(
    music_id: str,
    user_id: str = Depends(get_current_user_id)
):
    # Check if music exists
    music = await db.musics.find_one({"_id": ObjectId(music_id)})
    if not music:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Music not found"
        )
    
    # Get user
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    favorite_ids = user.get('favoriteIds', [])
    
    # Toggle favorite
    if music_id in favorite_ids:
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"favoriteIds": music_id}}
        )
        return {"message": "Removed from favorites", "isFavorite": False}
    else:
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"favoriteIds": music_id}}
        )
        return {"message": "Added to favorites", "isFavorite": True}

@router.get("", response_model=List[MusicResponse])
async def get_favorites(user_id: str = Depends(get_current_user_id)):
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    favorite_ids = user.get('favoriteIds', [])
    
    if not favorite_ids:
        return []
    
    # Get all favorite musics
    musics = await db.musics.find(
        {"_id": {"$in": [ObjectId(fid) for fid in favorite_ids]}}
    ).to_list(1000)
    
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