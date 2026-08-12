# ===== app/schemas/auth.py =====
from pydantic import BaseModel, EmailStr, field_validator

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_strength(cls, v):
        if len(v) < 8 or not any(c.isdigit() for c in v) or not any(c.isupper() for c in v):
            raise ValueError("Password must be 8+ chars with an uppercase letter and a digit")
        return v

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    role_names: list[str] = ["User"]

class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None
    is_active: bool
    roles: list[str]

    class Config:
        from_attributes = True