from fastapi import APIRouter, HTTPException, status, Depends, Response
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import UserRegister, UserLogin, UserResponse, UserInDB, TokenResponse
from auth import hash_password, verify_password, create_access_token, get_current_user_id
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])

# Test endpoint that doesn't require database
@router.get("/test")
async def test_auth_endpoint():
    """Test endpoint to verify auth routes are working without database"""
    return {
        "message": "Auth routes working!",
        "status": "healthy",
        "cors": "enabled",
        "database_required": False,
        "timestamp": datetime.utcnow()
    }

# Database dependency - import from server
async def get_database():
    """Get database connection with better error handling"""
    from server import db, client
    
    if db is None or client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Database service unavailable",
                "message": "The database is currently not connected. Please check environment variables.",
                "suggestions": [
                    "Verify MONGO_URL environment variable is set",
                    "Check MongoDB Atlas connectivity", 
                    "Contact system administrator"
                ],
                "cors_working": True
            }
        )
    
    # Test if connection is actually working
    try:
        await client.admin.command('ping')
        return db
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Database connection failed",
                "message": f"Database ping failed: {str(e)}",
                "cors_working": True
            }
        )

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister, response: Response):
    # Add CORS headers manually
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    
    # Get database connection with error handling
    db = await get_database()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_dict = user.dict()
    user_dict['password'] = hash_password(user_dict['password'])
    user_dict['favoriteIds'] = []
    user_dict['createdAt'] = datetime.utcnow()
    
    result = await db.users.insert_one(user_dict)
    user_id = str(result.inserted_id)
    
    # Create access token
    access_token = create_access_token(data={"sub": user_id})
    
    # Return token and user info
    user_response = UserResponse(
        id=user_id,
        name=user.name,
        email=user.email,
        favoriteIds=[],
        createdAt=user_dict['createdAt']
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin, response: Response):
    # Add CORS headers manually
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    
    # Get database connection with error handling
    db = await get_database()
    
    # Find user
    db_user = await db.users.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(user.password, db_user['password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create access token
    user_id = str(db_user['_id'])
    access_token = create_access_token(data={"sub": user_id})
    
    # Return token and user info
    user_response = UserResponse(
        id=user_id,
        name=db_user['name'],
        email=db_user['email'],
        favoriteIds=db_user.get('favoriteIds', []),
        createdAt=db_user['createdAt']
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    # Get database connection with error handling
    db = await get_database()
    
    db_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(db_user['_id']),
        name=db_user['name'],
        email=db_user['email'],
        favoriteIds=db_user.get('favoriteIds', []),
        createdAt=db_user['createdAt']
    )