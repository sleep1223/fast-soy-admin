import pytest
from httpx import AsyncClient

from app.core.cache import get_user_role_codes
from app.core.code import Code
from app.core.constants import SUPER_ADMIN_ROLE
from app.core.sqids import decode_id
from app.system.models import User

pytestmark = pytest.mark.asyncio(loop_scope="session")


class TestUserList:
    async def test_get_user_list(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/system-manage/users/search",
            json={
                "current": 1,
                "size": 10,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        assert "records" in data["data"]

    async def test_get_user_list_with_filter(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/system-manage/users/search",
            json={
                "current": 1,
                "size": 10,
                "userName": "Soybean",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        records = data["data"]["records"]
        assert len(records) >= 1
        assert any(r["userName"] == "Soybean" for r in records)


class TestUserCRUD:
    async def test_create_user(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/system-manage/users",
            json={
                "userName": "new_test_user",
                "password": "test123456",
                "userEmail": "newtest@test.com",
                "byUserRoleCodeList": ["R_USER"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        assert "createdId" in data["data"]

    async def test_create_user_duplicate_email(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/system-manage/users",
            json={
                "userName": "dup_email_user",
                "password": "test123456",
                "userEmail": "admin@admin.com",
                "byUserRoleCodeList": ["R_USER"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == Code.DUPLICATE_USER_EMAIL

    async def test_create_user_no_email(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/system-manage/users",
            json={
                "userName": "no_email_user",
                "password": "test123456",
                "byUserRoleCodeList": ["R_USER"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        user = await User.get(id=decode_id(data["data"]["createdId"]))
        assert user.user_email is None

    async def test_create_super_user_refreshes_role_cache(self, auth_client: AsyncClient, app):
        resp = await auth_client.post(
            "/api/v1/system-manage/users",
            json={
                "userName": "managed_super_user",
                "password": "test123456",
                "userEmail": "managed-super@test.com",
                "byUserRoleCodeList": [SUPER_ADMIN_ROLE],
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        user_id = decode_id(data["data"]["createdId"])
        assert await get_user_role_codes(app.state.redis, user_id) == [SUPER_ADMIN_ROLE]

    async def test_create_user_no_role(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/system-manage/users",
            json={
                "userName": "no_role_user",
                "password": "test123456",
                "userEmail": "norole@test.com",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == Code.USER_ROLE_REQUIRED

    async def test_update_user(self, auth_client: AsyncClient, seed_data):
        # First create a user to update
        create_resp = await auth_client.post(
            "/api/v1/system-manage/users",
            json={
                "userName": "update_me",
                "password": "test123456",
                "userEmail": "updateme@test.com",
                "byUserRoleCodeList": ["R_USER"],
            },
        )
        user_id = create_resp.json()["data"]["createdId"]

        resp = await auth_client.patch(
            f"/api/v1/system-manage/users/{user_id}",
            json={
                "nickName": "UpdatedNick",
                "password": "newpass123",
                "byUserRoleCodeList": ["R_USER"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        user = await User.get(id=decode_id(user_id))
        assert user.updated_by == seed_data.user_name

        list_resp = await auth_client.post(
            "/api/v1/system-manage/users/search",
            json={"current": 1, "size": 10, "userName": "update_me"},
        )
        list_data = list_resp.json()
        assert list_data["code"] == "0000"
        assert list_data["data"]["records"][0]["updatedBy"] == seed_data.user_name

    async def test_update_user_allows_empty_email_and_phone(self, auth_client: AsyncClient):
        create_resp = await auth_client.post(
            "/api/v1/system-manage/users",
            json={
                "userName": "clear_contact_user",
                "password": "test123456",
                "userEmail": "clear-contact@test.com",
                "userPhone": "18800000001",
                "byUserRoleCodeList": ["R_USER"],
            },
        )
        user_id = create_resp.json()["data"]["createdId"]

        resp = await auth_client.patch(
            f"/api/v1/system-manage/users/{user_id}",
            json={
                "userEmail": None,
                "userPhone": "",
                "byUserRoleCodeList": ["R_USER"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        user = await User.get(id=decode_id(user_id))
        assert user.user_email is None
        assert user.user_phone is None

    async def test_update_user_refreshes_role_cache(self, auth_client: AsyncClient, app):
        create_resp = await auth_client.post(
            "/api/v1/system-manage/users",
            json={
                "userName": "role_cache_user",
                "password": "test123456",
                "byUserRoleCodeList": ["R_USER"],
            },
        )
        user_id = create_resp.json()["data"]["createdId"]

        resp = await auth_client.patch(
            f"/api/v1/system-manage/users/{user_id}",
            json={
                "nickName": "RefreshRoleCache",
                "byUserRoleCodeList": [SUPER_ADMIN_ROLE],
            },
        )

        assert resp.status_code == 200
        assert resp.json()["code"] == "0000"
        assert await get_user_role_codes(app.state.redis, decode_id(user_id)) == [SUPER_ADMIN_ROLE]

    async def test_update_user_no_role(self, auth_client: AsyncClient):
        create_resp = await auth_client.post(
            "/api/v1/system-manage/users",
            json={
                "userName": "update_no_role_user",
                "password": "test123456",
                "byUserRoleCodeList": ["R_USER"],
            },
        )
        user_id = create_resp.json()["data"]["createdId"]

        resp = await auth_client.patch(
            f"/api/v1/system-manage/users/{user_id}",
            json={"nickName": "NoRole", "byUserRoleCodeList": []},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == Code.USER_ROLE_REQUIRED

    async def test_delete_user(self, auth_client: AsyncClient):
        # First create a user to delete
        create_resp = await auth_client.post(
            "/api/v1/system-manage/users",
            json={
                "userName": "delete_me",
                "password": "test123456",
                "userEmail": "deleteme@test.com",
                "byUserRoleCodeList": ["R_USER"],
            },
        )
        user_id = create_resp.json()["data"]["createdId"]

        resp = await auth_client.delete(f"/api/v1/system-manage/users/{user_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
