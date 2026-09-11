from fastapi import APIRouter, Depends, HTTPException

from app.database import users_collection
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ==========================================
# Register User
# ==========================================

@router.post(
    "/register",
    response_model=UserResponse
)
def register_user(
    user_data: UserCreate
):
    # Check whether email already exists
    existing_user = users_collection.find_one(
        {
            "email": user_data.email
        }
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Validate role
    allowed_roles = [
        "Quality Engineer",
        "Factory Supervisor"
    ]

    if user_data.role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

    # Create MongoDB user object
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(
            user_data.password
        ),
        role=user_data.role
    )

    # Insert user into MongoDB
    users_collection.insert_one(
        new_user.to_dict()
    )

    return new_user.to_response_dict()


# ==========================================
# Login User
# ==========================================

@router.post("/login")
def login_user(
    user_data: UserLogin
):
    # Find user in MongoDB
    user = users_collection.find_one(
        {
            "email": user_data.email
        }
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(
        user_data.password,
        user["password_hash"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create JWT token
    access_token = create_access_token(
        {
            "sub": str(user["id"]),
            "role": user["role"]
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }


# ==========================================
# Current User Profile
# ==========================================

@router.get(
    "/me",
    response_model=UserResponse
)
def get_my_profile(
    current_user=Depends(get_current_user)
):
    # get_current_user() returns a MongoDB dictionary
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"]
    }