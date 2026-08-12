"""Run once: python -m scripts.seed_rbac"""
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.user import Role, Permission, User
from app.core.security import hash_password

PERMISSIONS = [
    "documents.read", "documents.upload", "documents.delete",
    "users.read", "users.update", "users.delete",
    "chat.use", "analytics.read", "rules.manage", "settings.manage",
]

ROLE_PERMS = {
    "Admin": PERMISSIONS,
    "Reviewer": ["documents.read", "chat.use", "analytics.read"],
    "User": ["documents.read", "documents.upload", "chat.use"],
}

async def seed():
    async with AsyncSessionLocal() as db:
        perm_objs = {code: Permission(code=code) for code in PERMISSIONS}
        for p in perm_objs.values():
            db.add(p)
        await db.flush()

        role_objs = {}
        for role_name, perm_codes in ROLE_PERMS.items():
            role = Role(name=role_name, permissions=[perm_objs[c] for c in perm_codes])
            db.add(role)
            role_objs[role_name] = role
        await db.flush()

        admin = User(email="admin@example.com", hashed_password=hash_password("Admin123!"),
                      full_name="Admin", roles=[role_objs["Admin"]])
        db.add(admin)
        await db.commit()
        print("Seeded roles, permissions, admin user (admin@example.com / Admin123!)")

if __name__ == "__main__":
    asyncio.run(seed())