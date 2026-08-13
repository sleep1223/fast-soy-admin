"""gen 命令 — 解析 models.py 并生成 schemas / controllers / api 等文件。"""

from __future__ import annotations

from pathlib import Path

import click

from app.cli.display import echo_file_result, echo_lines, has_written_files, relative_path, run_just_format
from app.cli.generator import generate_all
from app.cli.git_tools import ensure_committed_worktree
from app.cli.options import all_choice_names, build_backend_feature_options, prompt_data_scope_map, resolve_field_map
from app.cli.parser import parse_models
from app.cli.prompts import (
    default_exact_field_names,
    exact_field_candidates,
    fuzzy_field_candidates,
    prompt_contains_fields,
    prompt_exact_fields,
    prompt_model_selection,
    resolve_model_selection,
)

BUSINESS_DIR = Path(__file__).resolve().parents[2] / "business"

GUIDE_LINES = [
    "",
    "✅ 代码生成完成！",
    "",
    "📋 后续步骤：",
    "",
    "  1. 按需修改 services.py 中的业务逻辑",
    "  2. init_data.py 已生成业务菜单；按需调整图标/排序，并补充角色、种子数据",
    "  3. 如需撤销本次生成，先预览再执行：",
    "",
    '     just cli-undo "--dry-run"',
    "     just cli-undo",
    "",
    "  4. 执行数据库迁移：",
    "",
    "     just mm",
    "",
    "  5. 启动服务验证：",
    "",
    "     just run",
]


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"], "max_content_width": 120}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("module_name")
@click.option("--models", "models_spec", default=None, help="要生成 CRUD 的模型，逗号分隔；支持序号、类名、all")
@click.option("-y", "--yes", "assume_yes", is_flag=True, help="不进入交互，使用全模型与推荐默认配置")
@click.option("--contains", "contains_specs", multiple=True, help="模糊查询字段；普通 CharField/TextField 优先放这里，例: User:name,nick_name;Role:role_name")
@click.option("--exact", "exact_specs", multiple=True, help="精确查询字段；适合外键 *_id、布尔、枚举字段/枚举类、唯一字段或字典值等，例: User:status_type,tenant_id")
@click.option("--list-order", "list_order_specs", multiple=True, help="列表默认排序，例: User:-created_at,id")
@click.option("--enable-routes", "enable_route_specs", multiple=True, help="启用标准路由，例: User:list,get,create")
@click.option("--exclude-fields", "exclude_field_specs", multiple=True, help="to_dict 排除字段，例: User:password,secret")
@click.option("--soft-delete", "soft_delete_specs", multiple=True, help="启用软删除的模型，例: User 或 all")
@click.option("--tree", "tree_specs", multiple=True, help="生成 tree 端点的模型，例: Category 或 all")
@click.option("--button-auth", is_flag=True, help="为 create/edit/delete 生成按钮权限与菜单按钮声明")
@click.option("--data-scope", "data_scope_specs", multiple=True, help="列表行级权限字段，例: Product:owner_id,warehouse_id")
@click.option("--list-cache", "list_cache_specs", multiple=True, help="列表接口缓存 TTL 秒数，例: Dict:60")
@click.option("--rate-limit", "rate_limit_specs", multiple=True, help="输出 guard 限流配置提示，例: LoginLog:30/60")
@click.option("--force", is_flag=True, help="强制覆盖已存在的文件")
@click.option("--dry-run", is_flag=True, help="只预览将创建/覆盖的文件，不写入磁盘")
@click.option("--no-format", is_flag=True, help="跳过 just fmt backend")
def gen(
    module_name: str,
    models_spec: str | None,
    assume_yes: bool,
    contains_specs: tuple[str, ...],
    exact_specs: tuple[str, ...],
    list_order_specs: tuple[str, ...],
    enable_route_specs: tuple[str, ...],
    exclude_field_specs: tuple[str, ...],
    soft_delete_specs: tuple[str, ...],
    tree_specs: tuple[str, ...],
    button_auth: bool,
    data_scope_specs: tuple[str, ...],
    list_cache_specs: tuple[str, ...],
    rate_limit_specs: tuple[str, ...],
    force: bool,
    dry_run: bool,
    no_format: bool,
):
    """根据 models.py 生成 schemas / controllers / api 等文件。

    MODULE_NAME: 业务模块名（app/business/<MODULE_NAME>/）

    示例:

      uv run python -m app.cli gen inventory --yes --models Product,Warehouse
      uv run python -m app.cli gen inventory --models Product --contains Product:name --exact Product:status_type --data-scope Product:owner_id,warehouse_id
    """
    module_dir = BUSINESS_DIR / module_name
    models_path = module_dir / "models.py"

    if not module_dir.exists():
        raise click.ClickException(f"模块目录不存在: {relative_path(module_dir)}\n  请先运行: uv run python -m app.cli init {module_name}")

    if not models_path.exists():
        raise click.ClickException(f"models.py 不存在: {relative_path(models_path)}")

    if not dry_run:
        ensure_committed_worktree()

    # 1. 解析模型
    models = parse_models(models_path)
    if not models:
        raise click.ClickException("未在 models.py 中发现任何继承 BaseModel 的模型类")

    click.echo("")
    click.echo(f"  ✅ 解析模块: {relative_path(models_path)}")
    click.echo(f"  ✅ 发现模型: {', '.join(f'{m.name} ({m.cn_name})' for m in models)}")
    if models_spec:
        models = resolve_model_selection(models, models_spec)
        click.echo(f"  ✅ 本次生成 CRUD: {', '.join(model.name for model in models)}")
    elif assume_yes:
        click.echo(f"  ✅ 本次生成 CRUD: {', '.join(model.name for model in models)}")
    else:
        models = prompt_model_selection(models)

    # 2. 交互选择搜索字段
    if contains_specs or assume_yes:
        contains_map = resolve_field_map(
            models,
            contains_specs,
            fuzzy_field_candidates,
            default_names_fn=all_choice_names,
            defaults_when_missing=assume_yes,
            option_name="--contains",
        )
    else:
        contains_map = prompt_contains_fields(models)

    if exact_specs or assume_yes:
        exact_map = resolve_field_map(
            models,
            exact_specs,
            lambda model: exact_field_candidates(model, contains_map),
            default_names_fn=default_exact_field_names,
            defaults_when_missing=assume_yes,
            option_name="--exact",
        )
    else:
        exact_map = prompt_exact_fields(models, contains_map)

    data_scope_map = None if data_scope_specs or assume_yes else prompt_data_scope_map(models)
    backend_options = build_backend_feature_options(
        models,
        list_order_specs=list_order_specs,
        enable_route_specs=enable_route_specs,
        exclude_field_specs=exclude_field_specs,
        soft_delete_specs=soft_delete_specs,
        tree_specs=tree_specs,
        button_auth=button_auth,
        data_scope_specs=data_scope_specs,
        data_scope_map=data_scope_map,
        list_cache_specs=list_cache_specs,
        rate_limit_specs=rate_limit_specs,
    )

    # 3. 生成文件
    click.echo("")
    results = generate_all(
        module_dir,
        module_name,
        models,
        contains_map,
        exact_map=exact_map,
        backend_options=backend_options,
        force=force,
        dry_run=dry_run,
    )

    for rel_path, status in results:
        echo_file_result(f"app/business/{module_name}/{rel_path}", status)

    # 4. project formatter
    if not no_format:
        if has_written_files(results):
            run_just_format("backend")
        else:
            click.echo("")
            click.echo("  ➖ 没有新写入的后端文件，跳过格式化")

    echo_lines(GUIDE_LINES)
