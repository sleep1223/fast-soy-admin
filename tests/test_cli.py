import importlib
import json
import subprocess
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from app.cli import cli, git_tools
from app.cli import display as cli_display
from app.cli.display import format_path
from app.cli.generator import gen_api_manage, gen_init_data, gen_module_manifest, gen_schemas, generate_all
from app.cli.options import BackendFeatureOptions, DataScopeOption, resolve_data_scope_map, resolve_field_map
from app.cli.parser import parse_models
from app.cli.prompts import (
    default_exact_field_names,
    default_frontend_list_field_names,
    exact_field_candidates,
    frontend_list_field_candidates,
    frontend_search_field_candidates,
    resolve_model_selection,
)
from app.cli.web_generator import gen_view_drawer, gen_view_index, gen_view_search, generate_web


def test_cli_exposes_full_crud_commands():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "crud" in result.output
    assert "gen-all" in result.output
    assert "init-plan" in result.output
    assert "module-list" in result.output
    assert "check-boundaries" in result.output


def test_format_path_uses_forward_slashes():
    assert format_path(r"app\business\inventory\models.py") == "app/business/inventory/models.py"
    assert format_path(Path("web") / "src" / "views") == "web/src/views"


def test_run_just_format_captures_child_output_on_success(monkeypatch, capsys):
    calls = []
    restores = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args[0], 0, stdout="child output\n", stderr="child error\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(cli_display, "restore_console_modes", lambda: restores.append(True))

    assert cli_display.run_just_format("backend") is True

    _, kwargs = calls[0]
    assert kwargs["cwd"] == cli_display.PROJECT_ROOT
    assert kwargs["check"] is False
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["encoding"] == "utf-8"
    assert kwargs["errors"] == "replace"
    assert "stdout" not in kwargs
    assert "stderr" not in kwargs
    assert restores == [True]
    output = capsys.readouterr().out
    assert "✅ just fmt backend 完成" in output
    assert "child output" not in output
    assert "child error" not in output


def test_run_just_format_prints_child_output_on_failure(monkeypatch, capsys):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout="lint stdout\n", stderr="lint stderr\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(cli_display, "restore_console_modes", lambda: None)

    assert cli_display.run_just_format("frontend") is False

    captured = capsys.readouterr()
    assert "⚠️  just fmt frontend 失败" in captured.out
    assert "lint stdout" in captured.out
    assert "lint stderr" in captured.err


def test_cli_init_does_not_prompt_for_cn_name(tmp_path: Path, monkeypatch):
    init_module = importlib.import_module("app.cli.commands.init")
    monkeypatch.setattr(init_module, "BUSINESS_DIR", tmp_path)
    monkeypatch.setattr(init_module, "relative_path", lambda path: path.relative_to(tmp_path).as_posix())
    monkeypatch.setattr(init_module, "ensure_committed_worktree", lambda: None)

    result = CliRunner().invoke(cli, ["init", "inventory"])

    assert result.exit_code == 0, result.output
    assert "模块中文名" not in result.output
    assert "\033" not in result.output
    assert "✅ 模块 inventory 创建成功！" in result.output

    models_content = (tmp_path / "inventory" / "models.py").read_text(encoding="utf-8")
    assert "inventory — 业务模型定义" in models_content
    assert "just cli-crud inventory" in models_content
    assert 'just cli-undo "--dry-run"' in result.output
    assert "just cli-crud inventory inventory" not in models_content


def test_cli_init_allows_existing_empty_module_dir(tmp_path: Path, monkeypatch):
    init_module = importlib.import_module("app.cli.commands.init")
    module_dir = tmp_path / "utility_fee2"
    (module_dir / "api" / "__pycache__").mkdir(parents=True)
    (module_dir / "api" / "__pycache__" / "manage.cpython-312.pyc").write_bytes(b"cache")
    monkeypatch.setattr(init_module, "BUSINESS_DIR", tmp_path)
    monkeypatch.setattr(init_module, "relative_path", lambda path: path.relative_to(tmp_path).as_posix())
    monkeypatch.setattr(init_module, "ensure_committed_worktree", lambda: None)

    result = CliRunner().invoke(cli, ["init", "utility_fee2"])

    assert result.exit_code == 0, result.output
    assert (module_dir / "__init__.py").exists()
    assert (module_dir / "models.py").exists()


def test_cli_init_rejects_existing_non_empty_module_dir(tmp_path: Path, monkeypatch):
    init_module = importlib.import_module("app.cli.commands.init")
    module_dir = tmp_path / "utility_fee2" / "api"
    module_dir.mkdir(parents=True)
    (module_dir / "manage.py").write_text("existing", encoding="utf-8")
    monkeypatch.setattr(init_module, "BUSINESS_DIR", tmp_path)
    monkeypatch.setattr(init_module, "relative_path", lambda path: path.relative_to(tmp_path).as_posix())
    monkeypatch.setattr(init_module, "ensure_committed_worktree", lambda: None)

    result = CliRunner().invoke(cli, ["init", "utility_fee2"])

    assert result.exit_code != 0
    assert "模块目录已存在: utility_fee2" in result.output
    assert (module_dir / "manage.py").read_text(encoding="utf-8") == "existing"


def test_cli_init_requires_clean_git_before_writing(tmp_path: Path, monkeypatch):
    init_module = importlib.import_module("app.cli.commands.init")
    monkeypatch.setattr(init_module, "BUSINESS_DIR", tmp_path)
    monkeypatch.setattr(init_module, "relative_path", lambda path: path.relative_to(tmp_path).as_posix())
    monkeypatch.setattr(init_module, "ensure_committed_worktree", lambda: (_ for _ in ()).throw(click.ClickException("dirty tree")))

    result = CliRunner().invoke(cli, ["init", "inventory"])

    assert result.exit_code != 0
    assert "dirty tree" in result.output
    assert not (tmp_path / "inventory").exists()


def test_parse_models_uses_first_docstring_line(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        '''
from tortoise import fields

from app.utils import BaseModel


class InventoryItem(BaseModel):
    """库存项。

    这里是较长的业务说明，不应该进入 CLI 标题。
    """

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100, description="名称")

    class Meta:
        table = "biz_inventory_item"
''',
        encoding="utf-8",
    )

    [model] = parse_models(models_path)

    assert model.cn_name == "库存项"


def test_parse_models_supports_positional_enum_fields_and_exact_defaults(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        '''
from enum import IntEnum
from tortoise import fields

from app.utils import BaseModel, StatusType


class PriceTier(IntEnum):
    standard = 1
    premium = 2


class Product(BaseModel):
    """商品"""

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=50, description="商品名称")
    status = fields.CharEnumField(StatusType, default=StatusType.enable, description="状态")
    price_tier = fields.IntEnumField(PriceTier, default=PriceTier.standard, description="价格等级")
''',
        encoding="utf-8",
    )
    [model] = parse_models(models_path)

    fields = {field.name: field for field in model.schema_fields}
    assert fields["status"].enum_type == "StatusType"
    assert fields["price_tier"].enum_type == "PriceTier"

    candidates = exact_field_candidates(model, {"Product": ["name"]})
    defaults = default_exact_field_names(model, candidates)
    assert "status" in defaults
    assert "price_tier" in defaults


def test_resolve_model_selection_supports_indexes_and_names(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        """
from tortoise import fields

from app.utils import BaseModel


class UtilityConfig(BaseModel):
    id = fields.IntField(primary_key=True)


class UtilityPrice(BaseModel):
    id = fields.IntField(primary_key=True)


class UtilityReading(BaseModel):
    id = fields.IntField(primary_key=True)
""",
        encoding="utf-8",
    )
    models = parse_models(models_path)

    selected = resolve_model_selection(models, "1,UtilityReading")

    assert [model.name for model in selected] == ["UtilityConfig", "UtilityReading"]


def test_gen_api_manage_uses_explicit_exact_fields(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        '''
from tortoise import fields

from app.utils import BaseModel, StatusType


class UtilityPrice(BaseModel):
    """水电费单价表"""

    id = fields.IntField(primary_key=True)
    remark = fields.CharField(max_length=500, null=True, description="备注")
    enabled = fields.BooleanField(default=True, description="是否启用")
    status = fields.CharEnumField(enum_type=StatusType, default=StatusType.enable, description="状态")
''',
        encoding="utf-8",
    )
    [model] = parse_models(models_path)

    content = gen_api_manage(
        "utility_fee",
        [model],
        {"UtilityPrice": ["remark"]},
        {"UtilityPrice": ["enabled"]},
    )

    assert "contains_fields=['remark']" in content
    assert "exact_fields=['enabled']" in content
    assert "exact_fields=['status']" not in content
    assert 'route_key_prefix="utility_fee.utility_prices"' in content
    assert 'router = APIRouter(tags=["utility_fee"])' in content
    assert "DependPermission" not in content


def test_gen_api_manage_generates_data_scope_list_override(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        '''
from tortoise import fields

from app.utils import AuditMixin, BaseModel


class Product(BaseModel, AuditMixin):
    """商品"""

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=50, description="姓名")
    owner_id = fields.IntField(null=True, description="负责人")
    warehouse_id = fields.IntField(description="所属仓库")
''',
        encoding="utf-8",
    )
    [model] = parse_models(models_path)

    content = gen_api_manage(
        "inventory",
        [model],
        {"Product": ["name"]},
        {"Product": ["warehouse_id"]},
        backend_options=BackendFeatureOptions(data_scope={"Product": DataScopeOption("owner_id", "warehouse_id")}),
    )

    assert '@product_crud.override("list")' in content
    assert "scope = await get_current_data_scope(request.app.state.redis)" in content
    assert 'user_id_field="owner_id"' in content
    assert 'scope_id_field="warehouse_id"' in content
    assert "return SuccessExtra" in content

    data_scope = resolve_data_scope_map([model], ["Product:created_by,warehouse_id"])
    assert data_scope["Product"] == DataScopeOption("created_by", "warehouse_id")


def test_gen_api_manage_list_cache_uses_explicit_cache_todo_instead_of_decorator(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        '''
from tortoise import fields

from app.utils import BaseModel


class DictItem(BaseModel):
    """字典项"""

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=50, description="名称")
''',
        encoding="utf-8",
    )
    [model] = parse_models(models_path)

    content = gen_api_manage(
        "dict",
        [model],
        {"DictItem": ["name"]},
        {"DictItem": []},
        backend_options=BackendFeatureOptions(list_cache_ttl={"DictItem": 60}),
    )

    compile(content, "manage.py", "exec")
    assert "from fastapi_cache.decorator import cache" not in content
    assert "@cache(" not in content
    assert "SuccessExtra" in content
    assert "TTL=60s" in content


def test_gen_init_data_includes_business_menus(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        '''
from tortoise import fields

from app.utils import BaseModel


class UtilityPrice(BaseModel):
    """水电费单价表"""

    id = fields.IntField(primary_key=True)
    remark = fields.CharField(max_length=500, null=True, description="备注")


class UtilityReading(BaseModel):
    """水电费读数表"""

    id = fields.IntField(primary_key=True)
    source = fields.CharField(max_length=50, description="来源")
''',
        encoding="utf-8",
    )
    models = parse_models(models_path)

    content = gen_init_data("utility_fee2", models, module_title="水电费2")

    compile(content, "init_data.py", "exec")
    assert "from app.system.services import apply_init_data" in content
    assert "INIT_DATA = {'menus':" in content
    assert "'menu_name': '水电费2'" in content
    assert "'route_name': 'utility-fee2'" in content
    assert "'route_name': 'utility-fee2_utility-price'" in content
    assert "'route_path': '/utility-fee2/utility-price'" in content
    assert "'component': 'view.utility-fee2_utility-price'" in content
    assert "'i18n_key': 'route.utility-fee2_utility-price'" in content
    assert "'reconcile': {'menus': True, 'buttons': False}" in content
    assert "await apply_init_data(INIT_DATA)" in content
    assert "await ensure_menu(**_build_menu_tree())" not in content
    assert 'parent_route = "_".join(parts[:level])' not in content
    assert "\\" not in content

    content_with_buttons = gen_init_data("utility_fee2", models, module_title="水电费2", button_auth_models={"UtilityPrice"})
    assert "'reconcile': {'menus': True, 'buttons': True}" in content_with_buttons
    assert "'button_code': 'B_UTILITY_FEE2_UTILITY_PRICE_CREATE'" in content_with_buttons
    assert "'button_desc': '创建水电费单价表'" in content_with_buttons


def test_gen_module_manifest_declares_business_module():
    content = gen_module_manifest("utility_fee", module_title="水电费")

    compile(content, "module.py", "exec")
    assert "from app.business.utility_fee.api import router" in content
    assert "from app.business.utility_fee.init_data import INIT_DATA" in content
    assert 'name="utility_fee"' in content
    assert 'title="水电费"' in content
    assert 'routers=[BusinessRouter(router=router, auth="permission")]' in content
    assert "permissions=PermissionSpec(init_data=INIT_DATA)" in content


def test_generate_web_uses_elegant_router_official_route_keys(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        '''
from tortoise import fields

from app.utils import BaseModel


class UtilityPrice(BaseModel):
    """水电费单价表"""

    id = fields.IntField(primary_key=True)
    remark = fields.CharField(max_length=500, null=True, description="备注")
''',
        encoding="utf-8",
    )
    [model] = parse_models(models_path)
    web_root = tmp_path / "web"
    (web_root / "src" / "service" / "api").mkdir(parents=True)
    (web_root / "src" / "service" / "api" / "index.ts").write_text("", encoding="utf-8")

    results = generate_web(
        web_root,
        "utility_fee2",
        "水电费2",
        [model],
        list_fields_map={"UtilityPrice": ["remark"]},
        search_fields_map={},
    )

    created_paths = {path for path, status in results if status == "created"}
    assert "src/views/utility-fee2/utility-price/index.vue" in created_paths
    assert "src/views/utility-fee2/utility-price/modules/utility-price-search.vue" in created_paths

    zh_content = (web_root / "src" / "locales" / "langs" / "_generated" / "utility_fee2" / "zh-cn.ts").read_text(encoding="utf-8")
    assert "'utility-fee2': '水电费2'" in zh_content
    assert "'utility-fee2_utility-price': '水电费单价表'" in zh_content


def test_codegen_dry_run_reports_changes_without_writing_files(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        '''
from tortoise import fields

from app.utils import BaseModel


class UtilityPrice(BaseModel):
    """水电费单价表"""

    id = fields.IntField(primary_key=True)
    remark = fields.CharField(max_length=500, null=True, description="备注")
''',
        encoding="utf-8",
    )
    [model] = parse_models(models_path)

    module_dir = tmp_path / "app" / "business" / "utility_fee"
    backend_results = generate_all(module_dir, "utility_fee", [model], {"UtilityPrice": ["remark"]}, dry_run=True)

    web_root = tmp_path / "web"
    (web_root / "src" / "service" / "api").mkdir(parents=True)
    (web_root / "src" / "service" / "api" / "index.ts").write_text("", encoding="utf-8")
    frontend_results = generate_web(
        web_root,
        "utility_fee",
        "水电费",
        [model],
        list_fields_map={"UtilityPrice": ["remark"]},
        search_fields_map={},
        dry_run=True,
    )

    assert ("schemas.py", "would-create") in backend_results
    assert ("module.py", "would-create") in backend_results
    assert ("src/service/api/utility_fee-manage.ts", "would-create") in frontend_results
    assert ("src/service/api/index.ts", "would-append") in frontend_results
    assert not (module_dir / "schemas.py").exists()
    assert not (web_root / "src" / "service" / "api" / "utility_fee-manage.ts").exists()
    assert (web_root / "src" / "service" / "api" / "index.ts").read_text(encoding="utf-8") == ""


def test_cli_gen_dry_run_skips_clean_worktree_preflight(tmp_path: Path, monkeypatch):
    gen_module = importlib.import_module("app.cli.commands.gen")
    business_dir = tmp_path / "business"
    module_dir = business_dir / "inventory"
    module_dir.mkdir(parents=True)
    (module_dir / "models.py").write_text(
        '''
from tortoise import fields

from app.utils import BaseModel


class InventoryItem(BaseModel):
    """库存项"""

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=50, description="名称")
''',
        encoding="utf-8",
    )
    monkeypatch.setattr(gen_module, "BUSINESS_DIR", business_dir)
    monkeypatch.setattr(gen_module, "relative_path", lambda path: Path(path).as_posix())
    monkeypatch.setattr(gen_module, "ensure_committed_worktree", lambda: (_ for _ in ()).throw(click.ClickException("dirty tree")))

    result = CliRunner().invoke(cli, ["gen", "inventory", "--yes", "--dry-run", "--no-format"])

    assert result.exit_code == 0
    assert "将创建" in result.output
    assert not (module_dir / "schemas.py").exists()


def test_frontend_field_options_accept_relation_id_fields(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        '''
from tortoise import fields

from app.utils import BaseModel


class Product(BaseModel):
    """商品"""

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=50, description="商品名称")
    warehouse_id: int
    warehouse = fields.ForeignKeyField("models.Warehouse", description="所属仓库")
''',
        encoding="utf-8",
    )
    [model] = parse_models(models_path)

    list_fields = resolve_field_map(
        [model],
        ["Product:name,warehouse_id"],
        frontend_list_field_candidates,
        option_name="--list-fields",
    )
    search_fields = resolve_field_map(
        [model],
        ["Product:name,warehouse_id"],
        frontend_search_field_candidates,
        option_name="--search-fields",
    )

    assert list_fields["Product"] == ["name", "warehouse_id"]
    assert search_fields["Product"] == ["name", "warehouse_id"]


def test_frontend_list_fields_accept_non_default_fields_after_sixth(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        '''
from tortoise import fields

from app.utils import BaseModel, StatusType


class InspectionRecord(BaseModel):
    """巡检记录"""

    id = fields.IntField(primary_key=True)
    station = fields.ForeignKeyField("models.Station", related_name="inspection_records", description="所属站点")
    record_no = fields.CharField(max_length=50, description="记录编号")
    inspector_name = fields.CharField(max_length=50, description="巡检人")
    equipment_name = fields.CharField(max_length=100, description="设备名称")
    score = fields.IntField(default=100, description="评分")
    category = fields.CharField(max_length=50, description="巡检类型")
    is_urgent = fields.BooleanField(default=False, description="是否紧急")
    status = fields.CharEnumField(enum_type=StatusType, default=StatusType.enable, description="状态")
''',
        encoding="utf-8",
    )
    [model] = parse_models(models_path)

    list_fields = resolve_field_map(
        [model],
        ["InspectionRecord:record_no,status"],
        frontend_list_field_candidates,
        option_name="--list-fields",
    )
    default_fields = resolve_field_map(
        [model],
        [],
        frontend_list_field_candidates,
        default_names_fn=default_frontend_list_field_names,
        defaults_when_missing=True,
        option_name="--list-fields",
    )

    assert list_fields["InspectionRecord"] == ["record_no", "status"]
    assert default_fields["InspectionRecord"] == [
        "record_no",
        "inspector_name",
        "equipment_name",
        "score",
        "category",
        "is_urgent",
        "station_id",
    ]


def test_generated_frontend_uses_button_auth_and_option_props(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        '''
from tortoise import fields

from app.utils import BaseModel, StatusType, StrEnum


class ProductState(StrEnum):
    available = "available"


class Product(BaseModel):
    """商品"""

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=50, description="商品名称")
    status = fields.CharEnumField(enum_type=StatusType, default=StatusType.enable, description="状态")
    product_state = fields.CharEnumField(enum_type=ProductState, default=ProductState.available, description="商品状态")
    warehouse_id: int
    warehouse = fields.ForeignKeyField("models.Warehouse", description="所属仓库")
''',
        encoding="utf-8",
    )
    [model] = parse_models(models_path)

    index = gen_view_index(
        "inventory",
        model,
        ["name", "warehouse_id", "product_state"],
        search_field_names=["name", "warehouse_id", "product_state"],
        button_auth=True,
    )
    search = gen_view_search("inventory", model, ["name", "warehouse_id", "product_state"])
    drawer = gen_view_drawer("inventory", model)

    assert "import { useAuth } from '@/hooks/business/auth';" in index
    assert "const { hasAuth } = useAuth();" in index
    assert "hasAuth('B_INVENTORY_PRODUCT_CREATE')" in index
    assert "hasAuth('B_INVENTORY_PRODUCT_EDIT')" in index
    assert "hasAuth('B_INVENTORY_PRODUCT_DELETE')" in index
    assert "const warehouseOptions = ref<SelectOptionItem[]>([]);" in index
    assert "const productStateOptions = ref<SelectOptionItem[]>([]);" in index
    assert "const defaultSearchParams: Api.InventoryManage.ProductSearchParams = {" in index
    assert "  name: null," in index
    assert "  warehouseId: null," in index
    assert "  productState: null," in index
    assert ':warehouse-options="warehouseOptions"' in index
    assert ':product-state-options="productStateOptions"' in index
    assert '@reset="resetSearchParams"' in index
    assert "function resetSearchParams()" in index
    assert "getDataByPage(1);" in index
    assert '@add="handleAdd"' not in index

    assert "(e: 'reset'): void;" in search
    assert "warehouseOptions?: SelectOptionItem[];" in search
    assert "productStateOptions?: SelectOptionItem[];" in search
    assert ':options="props.warehouseOptions"' in search
    assert ':options="props.productStateOptions"' in search
    assert ':options="[]"' not in search
    assert "emit('reset');" in search
    assert "resetModel" not in search
    assert "jsonClone" not in search

    assert "warehouseOptions?: SelectOptionItem[];" in drawer
    assert "productStateOptions?: SelectOptionItem[];" in drawer
    assert ':options="props.warehouseOptions"' in drawer
    assert ':options="props.productStateOptions"' in drawer
    assert ':options="[]"' not in drawer


def test_gen_schemas_imports_custom_enums_from_business_models(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        '''
from tortoise import fields

from app.utils import BaseModel, StatusType, StrEnum


class ReadingSource(StrEnum):
    external = "external"
    manual = "manual"


class UtilityReading(BaseModel):
    """水电费读数表"""

    id = fields.IntField(primary_key=True)
    source = fields.CharEnumField(enum_type=ReadingSource, default=ReadingSource.external, description="来源")
    status = fields.CharEnumField(enum_type=StatusType, default=StatusType.enable, description="状态")
''',
        encoding="utf-8",
    )
    models = parse_models(models_path)

    content = gen_schemas("utility_fee", models)

    utils_import = next(line for line in content.splitlines() if line.startswith("from app.utils import"))
    assert "from app.business.utility_fee.models import ReadingSource" in content
    assert "StatusType" in utils_import
    assert "ReadingSource" not in utils_import


def test_gen_view_drawer_skips_unused_form_rules_for_optional_models(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        '''
from tortoise import fields

from app.utils import BaseModel


class UtilityConfig(BaseModel):
    """水电费配置表"""

    id = fields.IntField(primary_key=True)
    external_token = fields.TextField(null=True, description="外部接口 token")
    sync_enabled = fields.BooleanField(default=True, description="是否开启自动同步")
''',
        encoding="utf-8",
    )
    [model] = parse_models(models_path)

    content = gen_view_drawer("utility_fee", model)

    assert "useFormRules" not in content
    assert "defaultRequiredRule" not in content
    assert "const rules: Record<string, App.Global.FormRule> = {};" in content
    assert ':value="Boolean(model.syncEnabled)"' in content


def test_gen_frontend_controls_are_typecheck_friendly(tmp_path: Path):
    models_path = tmp_path / "models.py"
    models_path.write_text(
        '''
from tortoise import fields

from app.utils import BaseModel


class UtilityReading(BaseModel):
    """水电费读数表"""

    id = fields.IntField(primary_key=True)
    reading_time = fields.DatetimeField(description="读数时间")
    enabled = fields.BooleanField(default=True, description="是否启用")
    raw_data = fields.JSONField(null=True, description="原始数据")
''',
        encoding="utf-8",
    )
    [model] = parse_models(models_path)

    drawer = gen_view_drawer("utility_fee", model)
    search = gen_view_search("utility_fee", model, ["enabled"])

    assert 'v-model:formatted-value="model.readingTime"' in drawer
    assert 'value-format="yyyy-MM-dd HH:mm:ss"' in drawer
    assert "readingTime: null" in drawer
    assert "formatJsonInput(model.rawData)" in drawer
    assert "model.rawData = parseJsonInput(value)" in drawer
    assert ':value="model.enabled as any"' in search
    assert "value => (model.enabled = value as boolean | null)" in search


def test_git_preflight_rejects_dirty_worktree(monkeypatch):
    def fake_run_git(args, *, check=True):
        if args == ["rev-parse", "--show-toplevel"]:
            return subprocess.CompletedProcess(["git", *args], 0, stdout=f"{git_tools.PROJECT_ROOT}\n", stderr="")
        if args == ["rev-parse", "--verify", "HEAD"]:
            return subprocess.CompletedProcess(["git", *args], 0, stdout="abc123\n", stderr="")
        if args == ["status", "--porcelain=v1", "--untracked-files=all"]:
            return subprocess.CompletedProcess(
                ["git", *args],
                0,
                stdout=" M app/cli/generator.py\n?? web/src/views/demo/index.vue\n",
                stderr="",
            )
        raise AssertionError(args)

    monkeypatch.setattr(git_tools, "_run_git", fake_run_git)

    with pytest.raises(click.ClickException) as exc_info:
        git_tools.ensure_committed_worktree()

    message = str(exc_info.value)
    assert "代码生成前需要一个已提交且干净的工作区" in message
    assert "app/cli/generator.py" in message
    assert "web/src/views/demo/index.vue" in message


def test_collect_codegen_changes_keeps_non_codegen_paths(monkeypatch):
    def fake_run_git(args, *, check=True):
        if args == ["rev-parse", "--show-toplevel"]:
            return subprocess.CompletedProcess(["git", *args], 0, stdout=f"{git_tools.PROJECT_ROOT}\n", stderr="")
        if args == ["rev-parse", "--verify", "HEAD"]:
            return subprocess.CompletedProcess(["git", *args], 0, stdout="abc123\n", stderr="")
        if args == ["status", "--porcelain=v1", "--untracked-files=all"]:
            return subprocess.CompletedProcess(
                ["git", *args],
                0,
                stdout=(" M app/business/inventory/schemas.py\n M README.md\n M web/src/router/elegant/routes.ts\n M web/src/typings/components.d.ts\n?? web/src/locales/langs/_generated/inventory/zh-cn.ts\n"),
                stderr="",
            )
        raise AssertionError(args)

    monkeypatch.setattr(git_tools, "_run_git", fake_run_git)

    selected, skipped = git_tools.collect_codegen_changes()

    assert [change.path for change in selected] == [
        "app/business/inventory/schemas.py",
        "web/src/router/elegant/routes.ts",
        "web/src/typings/components.d.ts",
        "web/src/locales/langs/_generated/inventory/zh-cn.ts",
    ]
    assert [change.path for change in skipped] == ["README.md"]


def test_backup_and_undo_codegen_changes_use_git(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(git_tools, "PROJECT_ROOT", tmp_path)
    source = tmp_path / "app/business/inventory/schemas.py"
    source.parent.mkdir(parents=True)
    source.write_text("generated schema", encoding="utf-8")

    changes = [
        git_tools.GitChange(" M", "app/business/inventory/schemas.py"),
        git_tools.GitChange("??", "web/src/views/inventory/product/index.vue"),
    ]

    backup_path = git_tools.backup_codegen_changes(changes, tmp_path / "codegen_backups")
    manifest = json.loads((backup_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["changes"][0]["path"] == "app/business/inventory/schemas.py"
    assert (backup_path / "app/business/inventory/schemas.py").read_text(encoding="utf-8") == "generated schema"

    calls: list[list[str]] = []

    def fake_run_git(args, *, check=True):
        calls.append(args)
        return subprocess.CompletedProcess(["git", *args], 0, stdout="", stderr="")

    monkeypatch.setattr(git_tools, "_run_git", fake_run_git)

    git_tools.undo_codegen_changes(changes)

    assert calls == [
        ["restore", "--staged", "--worktree", "--", "app/business/inventory/schemas.py"],
        ["clean", "-fd", "--", "web/src/views/inventory/product/index.vue"],
    ]
