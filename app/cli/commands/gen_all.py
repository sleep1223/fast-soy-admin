"""gen-all / crud 命令 — 一次生成完整前后端 CRUD。"""

from __future__ import annotations

from pathlib import Path

import click

from app.cli.display import echo_file_result, echo_lines, format_path, has_written_files, relative_path, run_just_format
from app.cli.generator import generate_all
from app.cli.git_tools import ensure_committed_worktree
from app.cli.options import all_choice_names, build_backend_feature_options, prompt_data_scope_map, resolve_field_map
from app.cli.parser import parse_models
from app.cli.prompts import (
    default_exact_field_names,
    default_frontend_list_field_names,
    default_frontend_search_field_names,
    exact_field_candidates,
    frontend_list_field_candidates,
    frontend_search_field_candidates,
    fuzzy_field_candidates,
    prompt_contains_fields,
    prompt_exact_fields,
    prompt_fields,
    prompt_model_selection,
    resolve_model_selection,
)
from app.cli.web_generator import generate_web

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BUSINESS_DIR = PROJECT_ROOT / "app" / "business"
WEB_ROOT = PROJECT_ROOT / "web"

GUIDE_LINES = [
    "",
    "✅ 前后端 CRUD 生成完成！",
    "",
    "📋 后续步骤：",
    "",
    "  1. 搜索生成代码中的 TODO，补充外键 / 枚举的 options 数据源",
    "  2. init_data.py 已生成业务菜单；按需调整图标/排序，并补充业务逻辑、角色、种子数据",
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
    "",
    "  6. 提交前运行完整质量检查：",
    "",
    "     just check",
]


def _format_generated_crud(backend_results: list[tuple[str, str]], frontend_results: list[tuple[str, str]]) -> None:
    """Format generated backend and frontend files through project recipes."""
    if has_written_files(backend_results):
        run_just_format("backend")
    else:
        click.echo("")
        click.echo("  ➖ 没有新写入的后端文件，跳过格式化")

    if has_written_files(frontend_results):
        run_just_format("frontend")
    else:
        click.echo("")
        click.echo("  ➖ 没有新写入的前端文件，跳过格式化")


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"], "max_content_width": 120}


@click.command("gen-all", context_settings=CONTEXT_SETTINGS)
@click.argument("module_name")
@click.option("--cn-name", default=None, help="模块中文名（用于 i18n）")
@click.option("--models", "models_spec", default=None, help="要生成 CRUD 的模型，逗号分隔；支持序号、类名、all")
@click.option("-y", "--yes", "assume_yes", is_flag=True, help="不进入交互，使用全模型与推荐默认配置")
@click.option("--contains", "contains_specs", multiple=True, help="后端模糊查询字段；普通 CharField/TextField 优先放这里，例: Product:name,code")
@click.option("--exact", "exact_specs", multiple=True, help="后端精确查询字段；适合外键 *_id、布尔、枚举字段/枚举类、唯一字段或字典值等，例: Product:status_type,warehouse_id")
@click.option("--list-fields", "list_field_specs", multiple=True, help="前端列表字段，例: Product:name,warehouse_id,status_type")
@click.option("--search-fields", "search_field_specs", multiple=True, help="前端搜索字段，例: Product:name,status_type")
@click.option("--list-order", "list_order_specs", multiple=True, help="后端列表默认排序，例: Product:-created_at,id")
@click.option("--enable-routes", "enable_route_specs", multiple=True, help="启用标准路由，例: Product:list,get,create")
@click.option("--exclude-fields", "exclude_field_specs", multiple=True, help="to_dict 排除字段，例: Product:secret")
@click.option("--soft-delete", "soft_delete_specs", multiple=True, help="启用软删除的模型，例: Product 或 all")
@click.option("--tree", "tree_specs", multiple=True, help="生成 tree 端点的模型，例: Category 或 all")
@click.option("--button-auth", is_flag=True, help="为 create/edit/delete 生成按钮权限与菜单按钮声明")
@click.option("--data-scope", "data_scope_specs", multiple=True, help="列表行级权限字段，例: Product:owner_id,warehouse_id")
@click.option("--list-cache", "list_cache_specs", multiple=True, help="列表接口缓存 TTL 秒数，例: Dict:60")
@click.option("--rate-limit", "rate_limit_specs", multiple=True, help="输出 guard 限流配置提示，例: LoginLog:30/60")
@click.option("--force", is_flag=True, help="强制覆盖已存在的文件")
@click.option("--dry-run", is_flag=True, help="只预览将创建/覆盖/追加的文件，不写入磁盘")
@click.option("--no-format", is_flag=True, help="跳过 just fmt backend/frontend")
def gen_all(
    module_name: str,
    cn_name: str | None,
    models_spec: str | None,
    assume_yes: bool,
    contains_specs: tuple[str, ...],
    exact_specs: tuple[str, ...],
    list_field_specs: tuple[str, ...],
    search_field_specs: tuple[str, ...],
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
    """根据 models.py 一次生成后端 + 前端 CRUD 代码。

    示例:

      uv run python -m app.cli crud inventory --cn-name 库存 --yes
      uv run python -m app.cli crud inventory --models Product --contains Product:name \
        --exact Product:status_type --list-fields Product:name,status_type \
        --data-scope Product:owner_id,warehouse_id --button-auth
    """
    module_dir = BUSINESS_DIR / module_name
    models_path = module_dir / "models.py"

    if not module_dir.exists():
        raise click.ClickException(f"模块目录不存在: {relative_path(module_dir)}\n  请先运行: uv run python -m app.cli init {module_name}")

    if not models_path.exists():
        raise click.ClickException(f"models.py 不存在: {relative_path(models_path)}")

    if not WEB_ROOT.exists():
        raise click.ClickException(f"找不到前端目录 {format_path(WEB_ROOT)}")

    if not dry_run:
        ensure_committed_worktree()

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

    if cn_name or assume_yes:
        module_cn: str = cn_name or module_name
    else:
        click.echo("")
        module_cn = click.prompt("  模块中文名 (用于 i18n)", default=module_name)

    click.echo("")
    click.echo("🧩 后端 CRUD 配置")
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

    click.echo("")
    click.echo("🖥️  前端 CRUD 配置")
    if list_field_specs or assume_yes:
        list_fields = resolve_field_map(
            models,
            list_field_specs,
            frontend_list_field_candidates,
            default_names_fn=default_frontend_list_field_names,
            defaults_when_missing=assume_yes,
            option_name="--list-fields",
        )
    else:
        list_fields = prompt_fields(
            models,
            "列表展示字段",
            frontend_list_field_candidates,
            default_names_fn=default_frontend_list_field_names,
        )

    if search_field_specs or assume_yes:
        search_fields = resolve_field_map(
            models,
            search_field_specs,
            frontend_search_field_candidates,
            default_names_fn=default_frontend_search_field_names([contains_map, exact_map]),
            defaults_when_missing=assume_yes,
            option_name="--search-fields",
        )
    else:
        search_fields = prompt_fields(
            models,
            "搜索字段",
            frontend_search_field_candidates,
            default_names_fn=default_frontend_search_field_names([contains_map, exact_map]),
        )

    click.echo("")
    click.echo("🚀 写入后端文件")
    backend_results = generate_all(
        module_dir,
        module_name,
        models,
        contains_map,
        exact_map=exact_map,
        module_title=module_cn,
        backend_options=backend_options,
        force=force,
        dry_run=dry_run,
    )
    for rel_path, status in backend_results:
        echo_file_result(f"app/business/{module_name}/{rel_path}", status)

    click.echo("")
    click.echo("🎛️  写入前端文件")
    frontend_results = generate_web(
        WEB_ROOT,
        module_name,
        module_cn,
        models,
        list_fields_map=list_fields,
        search_fields_map=search_fields,
        button_auth_models=backend_options.button_auth_models,
        force=force,
        dry_run=dry_run,
    )
    for rel_path, status in frontend_results:
        echo_file_result(f"web/{rel_path}", status)

    if not no_format:
        _format_generated_crud(backend_results, frontend_results)

    echo_lines(GUIDE_LINES)
