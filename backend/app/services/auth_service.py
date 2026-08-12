# ===== app/services/auth_service.py =====
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.models.user import RefreshToken
from app.core.security import verify_password, create_access_token, create_refresh_token, hash_password
from app.core.config import settings
from app.core.exceptions import AuthenticationError

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)

    async def authenticate(self, email: str, password: str) -> dict:
        user = await self.users.get_by_email(email)
        if not user:
            raise AuthenticationError("Invalid credentials")

        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise AuthenticationError("Account locked. Try again later.")

        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                from datetime import timedelta
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_MINUTES)
            await self.db.commit()
            raise AuthenticationError("Invalid credentials")

        if not user.is_active:
            raise AuthenticationError("Account disabled")

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)

        roles = [r.name for r in user.roles]
        permissions = list({p.code for r in user.roles for p in r.permissions})

        access_token = create_access_token(user.id, roles, permissions)
        refresh_token, expires_at = create_refresh_token(user.id)

        self.db.add(RefreshToken(user_id=user.id, token=refresh_token, expires_at=expires_at))
        await self.db.commit()

        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    async def refresh(self, refresh_token: str) -> dict:
        from sqlalchemy import select
        from app.core.security import decode_token, create_access_token

        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise AuthenticationError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        # result = await self.db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
        # stored = result.scalar_one_or_none()
        
        # if not stored or stored.revoked or stored.expires_at < datetime.now(timezone.utc):
        #     raise AuthenticationError("Refresh token expired or revoked")

        result = await self.db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
        stored = result.scalar_one_or_none()

        from datetime import timezone
        expires_at = stored.expires_at.replace(tzinfo=None) if stored and stored.expires_at.tzinfo else (stored.expires_at if stored else None)
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

        if not stored or stored.revoked or (expires_at and expires_at < now_naive):
            raise AuthenticationError("Refresh token expired or revoked")



        user = await self.users.get_by_id(payload["sub"])
        roles = [r.name for r in user.roles]
        permissions = list({p.code for r in user.roles for p in r.permissions})
        access_token = create_access_token(user.id, roles, permissions)
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    async def logout(self, refresh_token: str):
        from sqlalchemy import select
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
        stored = result.scalar_one_or_none()
        if stored:
            stored.revoked = True
            await self.db.commit()

    async def logout_all(self, user_id: str):
        from sqlalchemy import select
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked == False))
        for token in result.scalars().all():
            token.revoked = True
        await self.db.commit()
