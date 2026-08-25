import pytest

from app.core.base_model import StatusType
from app.system.init_data import RADAR_API_REFS, SYSTEM_INIT_DATA, build_system_init_data
from app.system.services import init_helper

pytestmark = pytest.mark.asyncio


async def test_system_init_data_exposes_codegen_menu_to_admin():
    manage_menu = next(menu for menu in SYSTEM_INIT_DATA["menus"] if menu["route_name"] == "manage")
    codegen_menu = next(child for child in manage_menu["children"] if child["route_name"] == "manage_codegen")
    admin_role = next(role for role in SYSTEM_INIT_DATA["roles"] if role["role_code"] == "R_ADMIN")

    assert codegen_menu == {
        "menu_name": "代码生成",
        "route_name": "manage_codegen",
        "route_path": "/manage/codegen",
        "component": "view.manage_codegen",
        "order": 5,
        "icon": "mdi:code-json",
    }
    assert "manage_codegen" in admin_role["menus"]


@pytest.mark.parametrize("radar_enabled", [False, True])
async def test_radar_menu_and_admin_api_seed_follow_enabled_state(radar_enabled):
    init_data = build_system_init_data(radar_enabled=radar_enabled)
    manage_menu = next(menu for menu in init_data["menus"] if menu["route_name"] == "manage")
    radar_menu = next(child for child in manage_menu["children"] if child["route_name"] == "manage_radar")
    admin_role = next(role for role in init_data["roles"] if role["role_code"] == "R_ADMIN")
    expected_status = StatusType.enable if radar_enabled else StatusType.disable

    assert radar_menu["status_type"] == expected_status
    assert all(child["status_type"] == expected_status for child in radar_menu["children"])
    if radar_enabled:
        assert set(RADAR_API_REFS).issubset(set(admin_role["apis"]))
    else:
        assert set(RADAR_API_REFS).isdisjoint(set(admin_role["apis"]))
    assert ("get", "/__radar/api/_boom") not in admin_role["apis"]


async def test_apply_init_data_applies_menus_roles_users_and_dictionaries(monkeypatch):
    calls = []

    async def fake_ensure_menu(**kwargs):
        calls.append(("menu", kwargs))

    async def fake_reconcile_menu_subtree(**kwargs):
        calls.append(("reconcile", kwargs))

    async def fake_ensure_role(**kwargs):
        calls.append(("role", kwargs))

    async def fake_ensure_user(**kwargs):
        calls.append(("user", kwargs))

    async def fake_safe_update_or_create(model, lookup, defaults):
        calls.append(("dictionary", model.__name__, lookup, defaults))
        return object(), True

    monkeypatch.setattr(init_helper, "ensure_menu", fake_ensure_menu)
    monkeypatch.setattr(init_helper, "reconcile_menu_subtree", fake_reconcile_menu_subtree)
    monkeypatch.setattr(init_helper, "ensure_role", fake_ensure_role)
    monkeypatch.setattr(init_helper, "ensure_user", fake_ensure_user)
    monkeypatch.setattr(init_helper, "_safe_update_or_create", fake_safe_update_or_create)

    await init_helper.apply_init_data({
        "menus": [
            {
                "menu_name": "Root",
                "route_name": "root",
                "route_path": "/root",
                "reconcile": {"menus": True, "buttons": True},
                "children": [
                    {
                        "menu_name": "Child",
                        "route_name": "root_child",
                        "route_path": "/root/child",
                        "component": "view.root_child",
                        "reconcile": False,
                        "buttons": [{"button_code": "B_ROOT_CHILD_CREATE", "button_desc": "创建"}],
                    }
                ],
            }
        ],
        "roles": [{"role_name": "Root Admin", "role_code": "R_ROOT_ADMIN"}],
        "users": [{"user_name": "Root", "password": "123456", "role_codes": ["R_ROOT_ADMIN"]}],
        "dictionaries": [{"dict_type": "color", "value": "red", "label": "红色", "order": 1}],
    })

    assert [call[0] for call in calls] == ["menu", "reconcile", "role", "user", "dictionary"]
    menu_payload = calls[0][1]
    assert "reconcile" not in menu_payload
    assert "reconcile" not in menu_payload["children"][0]
    assert calls[1][1] == {
        "root_route": "root",
        "declared_route_names": {"root_child"},
        "declared_button_codes": {"B_ROOT_CHILD_CREATE"},
    }
    assert calls[4][2] == {"dict_type": "color", "value": "red"}
    assert calls[4][3] == {"label": "红色", "order": 1}
