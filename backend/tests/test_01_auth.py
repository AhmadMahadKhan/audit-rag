# ===== tests/test_01_auth.py =====
"""Phase 2 — Authentication & RBAC."""
import pytest

pytestmark = pytest.mark.asyncio


class TestAuth:
    async def test_login_success(self, client, admin_user):
        resp = await client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Admin123!"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body and "refresh_token" in body
        assert body["token_type"] == "bearer"

    async def test_login_wrong_password(self, client, admin_user):
        resp = await client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "wrong"})
        assert resp.status_code in (400, 401)

    async def test_login_nonexistent_user(self, client):
        resp = await client.post("/api/v1/auth/login", json={"email": "ghost@test.com", "password": "whatever"})
        assert resp.status_code in (400, 401)

    async def test_account_lockout_after_failed_attempts(self, client, admin_user, db_session):
        from app.core.config import settings
        for _ in range(settings.MAX_FAILED_LOGIN_ATTEMPTS):
            await client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "wrong"})
        resp = await client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Admin123!"})
        assert resp.status_code in (400, 401)
        assert "lock" in resp.text.lower()

    async def test_refresh_token_flow(self, client, admin_user):
        login = await client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Admin123!"})
        refresh_token = login.json()["refresh_token"]
        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_logout_invalidates_refresh_token(self, client, admin_user):
        login = await client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Admin123!"})
        refresh_token = login.json()["refresh_token"]
        logout_resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
        assert logout_resp.status_code == 200
        reuse_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert reuse_resp.status_code in (400, 401)

    async def test_protected_endpoint_requires_token(self, client):
        resp = await client.get("/api/v1/users")
        assert resp.status_code in (401, 422)

    async def test_protected_endpoint_rejects_invalid_token(self, client):
        resp = await client.get("/api/v1/users", headers={"Authorization": "Bearer garbage.token.here"})
        assert resp.status_code == 401

    async def test_permission_enforcement_denies_unprivileged_user(self, client, user_headers):
        """normal_user lacks users.read — should be forbidden."""
        resp = await client.get("/api/v1/users", headers=user_headers)
        assert resp.status_code == 403

    async def test_admin_can_create_user(self, client, admin_headers, seeded_rbac):
        resp = await client.post("/api/v1/users", headers=admin_headers, json={
            "email": "newperson@test.com", "password": "NewPass123!", "full_name": "New Person", "role_names": ["User"],
        })
        assert resp.status_code == 200
        assert resp.json()["email"] == "newperson@test.com"

    async def test_change_password(self, client, admin_headers, admin_user):
        resp = await client.post("/api/v1/auth/change-password", headers=admin_headers,
                                   json={"old_password": "Admin123!", "new_password": "NewAdmin123!"})
        assert resp.status_code == 200
        relogin = await client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "NewAdmin123!"})
        assert relogin.status_code == 200

    async def test_weak_password_rejected(self, client, admin_headers):
        resp = await client.post("/api/v1/auth/change-password", headers=admin_headers,
                                   json={"old_password": "Admin123!", "new_password": "weak"})
        assert resp.status_code == 422