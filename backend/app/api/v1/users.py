from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import UserCreate, UserOut
from app.repositories.user_repository import UserRepository
from app.dependencies.auth import require_permission
from app.core.security import hash_password
from app.models.user import User, Role

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db), _=Depends(require_permission("users.read"))):
    users = await UserRepository(db).list_all()
    return [UserOut(id=u.id, email=u.email, full_name=u.full_name, is_active=u.is_active, roles=[r.name for r in u.roles]) for u in users]

@router.post("", response_model=UserOut)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db), _=Depends(require_permission("users.update"))):
    from sqlalchemy import select
    result = await db.execute(select(Role).where(Role.name.in_(payload.role_names)))
    roles = result.scalars().all()
    user = User(email=payload.email, hashed_password=hash_password(payload.password), full_name=payload.full_name, roles=roles)
    user = await UserRepository(db).create(user)
    # ===== app/api/v1/users.py — in create_user() =====
    created = await UserRepository(db).create(user)
    user = await UserRepository(db).get_by_id(created.id)  # re-fetch with roles eagerly loaded
    return UserOut(id=user.id, email=user.email, full_name=user.full_name, is_active=user.is_active, roles=[r.name for r in user.roles])
    
