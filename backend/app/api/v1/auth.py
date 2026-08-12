from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, ChangePasswordRequest
from app.services.auth_service import AuthService
from app.dependencies.auth import get_current_user
from app.core.security import verify_password, hash_password
from app.core.exceptions import AuthenticationError

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).authenticate(payload.email, payload.password)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).refresh(payload.refresh_token)

@router.post("/logout")
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    await AuthService(db).logout(payload.refresh_token)
    return {"success": True}

@router.post("/logout-all")
async def logout_all(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await AuthService(db).logout_all(user.id)
    return {"success": True}

@router.post("/change-password")
async def change_password(payload: ChangePasswordRequest, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not verify_password(payload.old_password, user.hashed_password):
        raise AuthenticationError("Old password incorrect")
    user.hashed_password = hash_password(payload.new_password)
    await db.commit()
    return {"success": True}
