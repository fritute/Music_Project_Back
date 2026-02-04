from fastapi import APIRouter, HTTPException, status, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import PlaylistCreate, PlaylistUpdate, PlaylistResponse, AddMusicToPlaylist
from auth import get_current_user_id
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter(prefix="/playlist", tags=["playlist"])

from server import db

@router.post("", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
async def create_playlist(
    playlist: PlaylistCreate,
    user_id: str = Depends(get_current_user_id)
):
    playlist_dict = {
        "name": playlist.name,
        "description": playlist.description or "",
        "userId": user_id,
        "musicIds": [],
        "createdAt": datetime.utcnow()
    }
    
    result = await db.playlists.insert_one(playlist_dict)
    playlist_id = str(result.inserted_id)
    
    return PlaylistResponse(
        id=playlist_id,
        name=playlist.name,
        description=playlist.description,
        userId=user_id,
        musicIds=[],
        createdAt=playlist_dict['createdAt']
    )

@router.get("", response_model=List[PlaylistResponse])
async def get_user_playlists(user_id: str = Depends(get_current_user_id)):
    playlists = await db.playlists.find({"userId": user_id}).to_list(1000)
    return [
        PlaylistResponse(
            id=str(playlist['_id']),
            name=playlist['name'],
            description=playlist.get('description', ''),
            userId=playlist['userId'],
            musicIds=playlist.get('musicIds', []),
            createdAt=playlist['createdAt']
        )
        for playlist in playlists
    ]

@router.get("/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(
    playlist_id: str,
    user_id: str = Depends(get_current_user_id)
):
    playlist = await db.playlists.find_one({"_id": ObjectId(playlist_id)})
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    if playlist['userId'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this playlist"
        )
    
    return PlaylistResponse(
        id=str(playlist['_id']),
        name=playlist['name'],
        description=playlist.get('description', ''),
        userId=playlist['userId'],
        musicIds=playlist.get('musicIds', []),
        createdAt=playlist['createdAt']
    )

@router.put("/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: str,
    playlist: PlaylistUpdate,
    user_id: str = Depends(get_current_user_id)
):
    db_playlist = await db.playlists.find_one({"_id": ObjectId(playlist_id)})
    if not db_playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    if db_playlist['userId'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this playlist"
        )
    
    update_data = {k: v for k, v in playlist.dict().items() if v is not None}
    if update_data:
        await db.playlists.update_one(
            {"_id": ObjectId(playlist_id)},
            {"$set": update_data}
        )
    
    updated_playlist = await db.playlists.find_one({"_id": ObjectId(playlist_id)})
    return PlaylistResponse(
        id=str(updated_playlist['_id']),
        name=updated_playlist['name'],
        description=updated_playlist.get('description', ''),
        userId=updated_playlist['userId'],
        musicIds=updated_playlist.get('musicIds', []),
        createdAt=updated_playlist['createdAt']
    )

@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlist(
    playlist_id: str,
    user_id: str = Depends(get_current_user_id)
):
    playlist = await db.playlists.find_one({"_id": ObjectId(playlist_id)})
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    if playlist['userId'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this playlist"
        )
    
    await db.playlists.delete_one({"_id": ObjectId(playlist_id)})
    return None

@router.post("/{playlist_id}/add", response_model=PlaylistResponse)
async def add_music_to_playlist(
    playlist_id: str,
    music_data: AddMusicToPlaylist,
    user_id: str = Depends(get_current_user_id)
):
    playlist = await db.playlists.find_one({"_id": ObjectId(playlist_id)})
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    if playlist['userId'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this playlist"
        )
    
    # Check if music exists
    music = await db.musics.find_one({"_id": ObjectId(music_data.musicId)})
    if not music:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Music not found"
        )
    
    # Add music if not already in playlist
    if music_data.musicId not in playlist.get('musicIds', []):
        await db.playlists.update_one(
            {"_id": ObjectId(playlist_id)},
            {"$push": {"musicIds": music_data.musicId}}
        )
    
    updated_playlist = await db.playlists.find_one({"_id": ObjectId(playlist_id)})
    return PlaylistResponse(
        id=str(updated_playlist['_id']),
        name=updated_playlist['name'],
        description=updated_playlist.get('description', ''),
        userId=updated_playlist['userId'],
        musicIds=updated_playlist.get('musicIds', []),
        createdAt=updated_playlist['createdAt']
    )

@router.delete("/{playlist_id}/remove/{music_id}", response_model=PlaylistResponse)
async def remove_music_from_playlist(
    playlist_id: str,
    music_id: str,
    user_id: str = Depends(get_current_user_id)
):
    playlist = await db.playlists.find_one({"_id": ObjectId(playlist_id)})
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    if playlist['userId'] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this playlist"
        )
    
    await db.playlists.update_one(
        {"_id": ObjectId(playlist_id)},
        {"$pull": {"musicIds": music_id}}
    )
    
    updated_playlist = await db.playlists.find_one({"_id": ObjectId(playlist_id)})
    return PlaylistResponse(
        id=str(updated_playlist['_id']),
        name=updated_playlist['name'],
        description=updated_playlist.get('description', ''),
        userId=updated_playlist['userId'],
        musicIds=updated_playlist.get('musicIds', []),
        createdAt=updated_playlist['createdAt']
    )