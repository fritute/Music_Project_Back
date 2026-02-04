from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# User Models
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    favoriteIds: List[str] = []
    createdAt: datetime

    class Config:
        json_encoders = {ObjectId: str}

class UserInDB(BaseModel):
    name: str
    email: str
    password: str
    favoriteIds: List[str] = []
    createdAt: datetime = Field(default_factory=datetime.utcnow)

# Music Models
class MusicCreate(BaseModel):
    title: str
    artist: str
    genre: str
    duration: int
    coverUrl: Optional[str] = None

class MusicResponse(BaseModel):
    id: str
    title: str
    artist: str
    genre: str
    duration: int
    coverUrl: Optional[str]
    audioUrl: str
    uploadedBy: str
    createdAt: datetime

    class Config:
        json_encoders = {ObjectId: str}

class MusicInDB(BaseModel):
    title: str
    artist: str
    genre: str
    duration: int
    coverUrl: Optional[str]
    audioUrl: str
    uploadedBy: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)

# Playlist Models
class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class PlaylistUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]

class PlaylistResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    userId: str
    musicIds: List[str] = []
    createdAt: datetime

    class Config:
        json_encoders = {ObjectId: str}

class PlaylistInDB(BaseModel):
    name: str
    description: Optional[str] = ""
    userId: str
    musicIds: List[str] = []
    createdAt: datetime = Field(default_factory=datetime.utcnow)

# Other Models
class AddMusicToPlaylist(BaseModel):
    musicId: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse