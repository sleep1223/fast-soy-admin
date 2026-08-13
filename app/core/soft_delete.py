"""
软删除 Mixin — 基于 Tortoise ORM Manager 的透明软删除。

使用 ``SoftDeleteManager`` 覆写默认 ``get_queryset()``，
``Model.filter()`` / ``.all()`` / ``.get()`` 自动排除 ``deleted_at IS NOT NULL`` 的行。

访问已删除记录请使用 ``Model.all_objects.filter(...)``。

用法::

    from app.core.soft_delete import SoftDeleteManager, SoftDeleteMixin

    class Product(BaseModel, AuditMixin, SoftDeleteMixin):
        name = fields.CharField(max_length=100, unique=True)
        ...

        class Meta:
            table = "biz_inventory_product"
            # 必须在子类 Meta 中显式声明 — Tortoise 不会从抽象 mixin 的 Meta
            # 合并 manager（``ModelMeta.__new__`` 只读取子类自身的 Meta）
            manager = SoftDeleteManager()

    # 软删除
    await product_controller.soft_remove(id=1)

    # 查询（自动排除已删除）
    await Product.filter(name="示例商品")  # deleted_at IS NULL

    # 查询已删除记录
    await Product.all_objects.filter(deleted_at__isnull=False)

PostgreSQL 优化建议::

    对需要在软删除下保持唯一的字段，添加部分索引以替代普通 UNIQUE 约束：

        CREATE UNIQUE INDEX biz_inventory_product_code_active_uq
            ON biz_inventory_product(code)
            WHERE deleted_at IS NULL;

    这样同一 code 可以有多条已删除记录，但在未删除记录中仍保持唯一。
    SQLite 不支持部分索引（WHERE 子句），需靠应用层保证。
"""

from tortoise import fields
from tortoise.manager import Manager
from tortoise.queryset import QuerySet


class SoftDeleteManager(Manager):
    """默认 Manager：自动过滤 ``deleted_at IS NULL`` 的行。"""

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteMixin:
    """软删除 Mixin。

    添加 ``deleted_at`` 字段。**子类必须在自己的 ``Meta`` 中显式声明
    ``manager = SoftDeleteManager()``** —— Tortoise 不会从抽象 mixin 的
    Meta 合并 ``manager``。

    通过 ``all_objects``（原生 Manager）可访问包含已删除记录的全量数据::

        await MyModel.all_objects.filter(deleted_at__isnull=False)  # 仅已删除
        await MyModel.all_objects.all()  # 全部（含已删除）

    PostgreSQL 优化::

        对需要在软删除下保持唯一的字段，建议用部分索引替代 UNIQUE 约束：
        CREATE UNIQUE INDEX <table>_<field>_active_uq
            ON <table>(<field>) WHERE deleted_at IS NULL;
        SQLite 不支持部分索引，靠应用层保证。
    """

    deleted_at = fields.DatetimeField(null=True, default=None, description="软删除时间，NULL表示未删除")

    all_objects = Manager()

    class Meta:
        abstract = True
        manager = SoftDeleteManager()
