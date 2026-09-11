from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.database import users_collection
from app.services.auth_service import SECRET_KEY, ALGORITHM


security = HTTPBearer()


# ==========================================
# Get Current Logged-in User
# ==========================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    # Find user in MongoDB
    user = users_collection.find_one(
        {"id": str(user_id)}
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    # Remove MongoDB internal ID from returned object
    user.pop("_id", None)

    return user


# ==========================================
# Role-based Access Control
# ==========================================

def require_role(required_role: str):

    def role_checker(
        current_user=Depends(get_current_user)
    ):
        if current_user.get("role") != required_role:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this resource"
            )

        return current_user

    return role_checker