"""
系统初始化辅助服务。

这里承载菜单、角色、种子用户等 system 领域的初始化编排逻辑。

多进程安全说明：
    启动时通过 Redis 分布式锁保证仅一个 worker 执行 init，但仍在
    update_or_create 处增加 IntegrityError 重试，以应对极端时序场景。
"""

from __future__ import annotations

import asyncio
from functools import reduce
from operator import or_
from typing import Any, TypeVar

from fastapi.routing import APIRoute
from tortoise.expressions import Q
from tortoise.models import Model

from app.core.base_model import GenderType, IconType, MenuType
from app.core.data_scope import DataScopeType
from app.core.exceptions import IntegrityError
from app.core.log import log
from app.system.controllers.user import user_controller
from app.system.models import User
from app.system.models.admin import Api, Button, Menu, Role
from app.system.models.dictionary import Dictionary
from app.system.security import get_password_hash

_M = TypeVar("_M", bound=Model)


async def _safe_update_or_create(model: type[_M], lookup: dict[str, Any], defaults: dict[str, Any]) -> tuple[_M, bool]:
    """
    对 update_or_create 的安全封装，处理并发 UNIQUE 冲突。

    当两个协程/进程同时对同一唯一键执行 get→create 时，
    后者会抛 IntegrityError；此处捕获后回退为 update。
    """
    try:
        return await model.update_or_create(defaults=defaults, **lookup)  # type: ignore[return-value]
    except IntegrityError:
        log.debug(f"_safe_update_or_create: IntegrityError on {model.__name__} {lookup}, retrying as update")
        await model.filter(**lookup).update(**defaults)
        instance = await model.get(**lookup)
        return instance, False


async def ensure_menu(
    *,
    parent_route: str | None = None,
    menu_name: str,
    route_name: str,
    route_path: str,
    component: str | None = None,
    icon: str | None = None,
    icon_type: str = "1",
    menu_type: str | None = None,
    order: int = 1,
    i18n_key: str | None = None,
    children: list[dict] | None = None,
    buttons: list[dict] | None = None,
    **extra,
) -> None:
    """
    确保菜单存在且字段与声明一致（幂等，按 route_name 唯一键 get_or_update）。

    Args:
        parent_route: 父菜单的 route_name (如 "manage")，为 None 时创建顶级菜单
        menu_type: 强制指定菜单类型 ("1"=catalog, "2"=menu)，为 None 时自动推断
        children: [{"menu_name", "route_name", "route_path", "component", "order",
                     "icon", ..., "children": [...], "buttons": [...]}]
        buttons: [{"button_code", "button_desc"}] — 挂在当前菜单上。
                 传 None 表示不修改现有按钮，传 [] 表示清空按钮。
        **extra: 传递给 Menu 的额外字段，如 constant, hide_in_menu, props,
                 multi_tab, redirect。active_menu 传 route_name 字符串会自动解析。
    """
    if parent_route is None:
        parent_id = 0
    else:
        parent = await Menu.filter(route_name=parent_route).first()
        if not parent:
            log.warning(f"ensure_menu: parent '{parent_route}' not found, skip '{route_name}'")
            return
        parent_id = parent.id

    if menu_type is not None:
        resolved_type = MenuType(menu_type)
    else:
        resolved_type = MenuType.catalog if children else MenuType.menu
    if parent_id == 0 and component is None and not extra.get("constant"):
        component = "layout.base"

    if "active_menu" in extra and isinstance(extra["active_menu"], str):
        active = await Menu.filter(route_name=extra["active_menu"]).first()
        extra["active_menu"] = active

    defaults = {
        "parent_id": parent_id,
        "menu_type": resolved_type,
        "menu_name": menu_name,
        "route_path": route_path,
        "component": component,
        "order": order,
        "i18n_key": i18n_key or f"route.{route_name}",
        "icon": icon,
        "icon_type": IconType(icon_type) if icon else None,
        **extra,
    }
    main_menu, created = await _safe_update_or_create(Menu, {"route_name": route_name}, defaults)

    if created:
        log.info(f"ensure_menu: created '{route_name}'" + (f" under '{parent_route}'" if parent_route else " as top-level"))
    else:
        log.info(f"ensure_menu: updated '{route_name}'")

    if buttons is not None:
        await main_menu.by_menu_buttons.clear()  # type: ignore[attr-defined]
        for btn in buttons:
            btn_obj, _ = await _safe_update_or_create(Button, {"button_code": btn["button_code"]}, {"button_desc": btn.get("button_desc", "")})
            await main_menu.by_menu_buttons.add(btn_obj)  # type: ignore[attr-defined]

    for child in children or []:
        child_buttons = child.get("buttons")
        child_children = child.get("children")
        child_extra = {
            k: v for k, v in child.items() if k not in ("menu_name", "route_name", "route_path", "component", "order", "icon", "icon_type", "i18n_key", "menu_type", "buttons", "children", "reconcile")
        }
        await ensure_menu(
            parent_route=route_name,
            menu_name=child["menu_name"],
            route_name=child["route_name"],
            route_path=child["route_path"],
            component=child.get("component"),
            icon=child.get("icon"),
            icon_type=child.get("icon_type", "1"),
            menu_type=child.get("menu_type"),
            order=child.get("order", 1),
            i18n_key=child.get("i18n_key"),
            children=child_children,
            buttons=child_buttons,
            **child_extra,
        )


async def ensure_role(
    *,
    role_name: str,
    role_code: str,
    role_desc: str = "",
    home_route: str = "home",
    data_scope: DataScopeType | None = None,
    menus: list[str] | None = None,
    buttons: list[str] | None = None,
    apis: list[tuple[str, str] | str] | None = None,
) -> None:
    """
    确保角色存在且字段/权限与声明一致（幂等，按 role_code 唯一键 get_or_update）。

    关系同步语义：None=不修改，[]=清空，[...]=替换为声明的集合。

    Args:
        data_scope: 行级数据范围（``all`` / ``scope`` / ``self`` / ``custom``）。
            None 时不写入该字段，沿用 Role 模型默认值（``all``）。
        menus: route_name 列表
        buttons: button_code 列表
        apis: [(method, path), ...] 或 route key 字符串列表
    """
    home_menu = await Menu.filter(route_name=home_route).first()
    defaults: dict[str, Any] = {
        "role_name": role_name,
        "role_desc": role_desc,
        "by_role_home_id": home_menu.id if home_menu else 1,
    }
    if data_scope is not None:
        defaults["data_scope"] = data_scope
    role, created = await _safe_update_or_create(
        Role,
        {"role_code": role_code},
        defaults,
    )

    # 批量解析菜单/按钮/API，并发执行清空 → 重新挂载，避免逐条 query 的 N+1
    async def _sync_menus() -> None:
        if menus is None:
            return
        found = await Menu.filter(route_name__in=menus)
        by_name = {m.route_name: m for m in found}
        missing = [rn for rn in menus if rn not in by_name]
        await role.by_role_menus.clear()  # type: ignore[attr-defined]
        if found:
            await role.by_role_menus.add(*found)  # type: ignore[attr-defined]
        if missing:
            log.warning(f"ensure_role '{role_code}': missing menus {missing} (route renamed or deleted?)")

    async def _sync_buttons() -> None:
        if buttons is None:
            return
        found = await Button.filter(button_code__in=buttons)
        by_code = {b.button_code: b for b in found}
        missing = [c for c in buttons if c not in by_code]
        await role.by_role_buttons.clear()  # type: ignore[attr-defined]
        if found:
            await role.by_role_buttons.add(*found)  # type: ignore[attr-defined]
        if missing:
            log.warning(f"ensure_role '{role_code}': missing buttons {missing} (button_code renamed or deleted?)")

    async def _sync_apis() -> None:
        if apis is None:
            return
        resolved_apis, missing_route_keys = _resolve_api_refs(apis)
        if resolved_apis:
            cond = reduce(or_, (Q(api_method=m, api_path=p) for m, p in resolved_apis))
            found = await Api.filter(cond)
        else:
            found = []
        by_key = {(a.api_method, a.api_path): a for a in found}
        missing = [(m, p) for m, p in resolved_apis if (m, p) not in by_key]
        await role.by_role_apis.clear()  # type: ignore[attr-defined]
        if found:
            await role.by_role_apis.add(*found)  # type: ignore[attr-defined]
        if missing_route_keys:
            log.warning(f"ensure_role '{role_code}': missing route keys {missing_route_keys} (route name changed?)")
        if missing:
            log.warning(f"ensure_role '{role_code}': missing apis {missing} (route signature changed?)")

    await asyncio.gather(_sync_menus(), _sync_buttons(), _sync_apis())

    log.info(f"ensure_role: {'created' if created else 'updated'} role '{role_code}'")


def _route_key_index() -> dict[str, tuple[str, str]]:
    try:
        from app import fastapi_app
    except Exception:
        return {}

    result: dict[str, tuple[str, str]] = {}
    for route in fastapi_app.routes:
        if not isinstance(route, APIRoute) or not route.include_in_schema or not route.name:
            continue
        methods = sorted(m.lower() for m in route.methods if m.lower() not in {"head", "options"})
        if not methods:
            continue
        result[route.name] = (methods[0], route.path_format)
    return result


def _resolve_api_refs(api_refs: list[tuple[str, str] | str]) -> tuple[list[tuple[str, str]], list[str]]:
    route_keys = _route_key_index()
    resolved: list[tuple[str, str]] = []
    missing_route_keys: list[str] = []
    for item in api_refs:
        if isinstance(item, str):
            api_ref = route_keys.get(item)
            if api_ref is None:
                missing_route_keys.append(item)
                continue
            resolved.append(api_ref)
        else:
            method, path = item
            resolved.append((method, path))
    return resolved, missing_route_keys


async def reconcile_menu_subtree(
    *,
    root_route: str,
    declared_route_names: set[str],
    declared_button_codes: set[str] | None = None,
) -> None:
    """
    对齐菜单子树：删除根路由下未在声明集合中的菜单与按钮，用于业务模块 init_data 把自身当作
    single-source-of-truth 时的"多余项清理"。幂等。

    语义（严格限定在子树内，不会误伤其他模块）：
        - 以 `root_route` 对应菜单为根，递归收集子树中所有菜单。
        - 子树中 `route_name` 不在 `declared_route_names ∪ {root_route}` 的菜单会被删除。
        - 若传入 `declared_button_codes`，子树菜单关联的按钮中 `button_code` 不在该集合内的
          会被删除（级联清理 Menu/Role 的多对多关系）。传 None 表示不处理按钮。

    Args:
        root_route: 业务模块菜单子树根的 route_name，例如 demo 模块传 "demo"。
        declared_route_names: 当前声明保留的子路由名集合（不含 root 本身）。
        declared_button_codes: 当前声明保留的按钮 code 集合；传 None 表示跳过按钮对账。

    注意：
        - 一旦启用此函数，业务模块 init_data 就成为该子树的 single-source-of-truth，
          从 Web 端手动新建的 Inventory 子菜单会在下次启动时被清掉。
        - 按钮对账是"子树内使用过的按钮"为基准，不会触及其他子树的按钮。
    """
    root = await Menu.filter(route_name=root_route).first()
    if not root:
        log.warning(f"reconcile_menu_subtree: root '{root_route}' not found, skip")
        return

    # 递归收集子树所有菜单 id（BFS）
    subtree_ids: set[int] = {root.id}
    frontier = [root.id]
    while frontier:
        children = await Menu.filter(parent_id__in=frontier).values("id")
        next_ids = [c["id"] for c in children]
        if not next_ids:
            break
        frontier = next_ids
        subtree_ids.update(next_ids)

    # 删除子树中未声明的菜单
    allowed = declared_route_names | {root_route}
    stale_menus = await Menu.filter(id__in=subtree_ids).exclude(route_name__in=allowed).all()
    for m in stale_menus:
        log.warning(f"reconcile_menu_subtree: removing stale menu '{m.route_name}' (under '{root_route}')")
        await m.delete()
        subtree_ids.discard(m.id)

    # 对齐按钮：仅处理"挂在本子树菜单上"的按钮
    if declared_button_codes is not None and subtree_ids:
        stale_buttons = await Button.filter(by_button_menus__id__in=subtree_ids).exclude(button_code__in=declared_button_codes).distinct()
        for b in stale_buttons:
            log.warning(f"reconcile_menu_subtree: removing stale button '{b.button_code}' (under '{root_route}')")
            await b.delete()


async def ensure_user(
    *,
    user_name: str,
    password: str,
    role_codes: list[str],
    user_email: str | None = None,
    nick_name: str | None = None,
    user_phone: str | None = None,
    user_gender: str | None = None,
    must_change_password: bool = False,
    reset_password: bool = False,
) -> "User":
    """
    确保用户存在且角色与声明一致。

    语义：
    - 首次不存在时创建
    - 已存在时同步基础资料和角色
    - 默认不重置密码，避免每次启动覆盖已有账号密码
    """
    base_payload = {
        "nick_name": nick_name or user_name,
        "must_change_password": must_change_password,
    }
    if user_email is not None:
        base_payload["user_email"] = user_email
    if user_phone is not None:
        base_payload["user_phone"] = user_phone
    if user_gender is not None:
        base_payload["user_gender"] = user_gender

    user = await User.filter(user_name=user_name).first()
    if user:
        payload = base_payload.copy()
        if reset_password:
            payload["password"] = get_password_hash(password)
        await User.filter(id=user.id).update(**payload)
        user = await User.get(id=user.id)
    else:
        payload = base_payload.copy()
        payload.setdefault("user_gender", GenderType.unknow)
        try:
            user = await User.create(
                user_name=user_name,
                password=get_password_hash(password),
                **payload,
            )
        except IntegrityError:
            # 并发进程已创建该用户，回退为更新
            user = await User.get(user_name=user_name)
            await User.filter(id=user.id).update(**base_payload)

    await user_controller.update_roles_by_code(user, role_codes)
    log.info(f"ensure_user: synced user '{user_name}'")
    return user


def _strip_menu_control_keys(menu: dict[str, Any]) -> dict[str, Any]:
    payload = {key: value for key, value in menu.items() if key != "reconcile"}
    if "children" in payload:
        payload["children"] = [_strip_menu_control_keys(child) for child in payload.get("children") or []]
    return payload


def _collect_menu_route_names(menus: list[dict[str, Any]]) -> set[str]:
    result: set[str] = set()
    for menu in menus:
        route_name = menu.get("route_name")
        if route_name:
            result.add(route_name)
        result.update(_collect_menu_route_names(menu.get("children") or []))
    return result


def _collect_menu_button_codes(menus: list[dict[str, Any]]) -> set[str]:
    result: set[str] = set()
    for menu in menus:
        for button in menu.get("buttons") or []:
            button_code = button.get("button_code")
            if button_code:
                result.add(button_code)
        result.update(_collect_menu_button_codes(menu.get("children") or []))
    return result


def _resolve_reconcile_config(reconcile: Any) -> tuple[bool, bool]:
    if reconcile is True:
        return True, True
    if not reconcile:
        return False, False
    if isinstance(reconcile, dict):
        return bool(reconcile.get("menus", True)), bool(reconcile.get("buttons", False))
    return False, False


async def _apply_menu_reconcile(menu: dict[str, Any]) -> None:
    root_route = menu["route_name"]
    reconcile_menus, reconcile_buttons = _resolve_reconcile_config(menu.get("reconcile"))
    if reconcile_menus:
        declared_routes = _collect_menu_route_names([menu])
        declared_routes.discard(root_route)
        await reconcile_menu_subtree(
            root_route=root_route,
            declared_route_names=declared_routes,
            declared_button_codes=_collect_menu_button_codes([menu]) if reconcile_buttons else None,
        )

    for child in menu.get("children") or []:
        await _apply_menu_reconcile(child)


async def _apply_dictionary_seeds(seeds: list[dict[str, Any]]) -> None:
    for seed in seeds:
        await _safe_update_or_create(
            Dictionary,
            {"dict_type": seed["dict_type"], "value": seed["value"]},
            {key: value for key, value in seed.items() if key not in {"dict_type", "value"}},
        )


async def apply_init_data(spec: dict[str, Any]) -> None:
    """
    Apply a declarative init-data spec.

    Supported keys:
    - menus: menu tree declarations. Buttons stay nested under the menu that owns them.
    - roles: ensure_role payloads.
    - users: ensure_user payloads.
    - dictionaries: system dictionary seeds keyed by (dict_type, value).
    """
    for menu in spec.get("menus") or []:
        await ensure_menu(**_strip_menu_control_keys(menu))
        await _apply_menu_reconcile(menu)

    for role_seed in spec.get("roles") or []:
        await ensure_role(**role_seed)

    for user_seed in spec.get("users") or []:
        await ensure_user(**user_seed)

    await _apply_dictionary_seeds(spec.get("dictionaries") or [])
