from tortoise import fields

from .utils import BaseModel, TimestampMixin, GenderType, IconType, MenuType, MethodType, StatusType, LogType, LogDetailType


class User(BaseModel, TimestampMixin):
    id = fields.IntField(pk=True, description="用户ID")
    user_name = fields.CharField(max_length=20, unique=True, description="用户名称")
    password = fields.CharField(max_length=128, description="密码")
    nick_name = fields.CharField(max_length=30, null=True, description="昵称")
    user_gender = fields.CharEnumField(enum_type=GenderType, default=GenderType.unknow, description="性别")
    user_email = fields.CharField(max_length=255, unique=True, description="邮箱")
    user_phone = fields.CharField(max_length=20, null=True, description="电话")
    last_login = fields.DatetimeField(null=True, description="最后登录时间")
    roles = fields.ManyToManyField("app_system.Role", related_name="user_roles")
    status = fields.CharEnumField(enum_type=StatusType, default=StatusType.enable, description="状态")

    class Meta:
        table = "users"


class Role(BaseModel, TimestampMixin):
    id = fields.IntField(pk=True, description="角色ID")
    role_name = fields.CharField(max_length=20, unique=True, description="角色名称")
    role_code = fields.CharField(max_length=20, unique=True, description="角色编码")
    role_desc = fields.CharField(max_length=500, null=True, blank=True, description="角色描述")
    role_home = fields.CharField(default="home", max_length=100, description="角色首页")
    status = fields.CharEnumField(enum_type=StatusType, default=StatusType.enable, description="状态")

    menus = fields.ManyToManyField("app_system.Menu", related_name="role_menus")
    apis = fields.ManyToManyField("app_system.Api", related_name="role_apis")
    buttons = fields.ManyToManyField("app_system.Button", related_name="role_buttons")

    class Meta:
        table = "roles"


class Api(BaseModel, TimestampMixin):
    id = fields.IntField(pk=True, description="API ID")
    path = fields.CharField(max_length=100, description="API路径")
    method = fields.CharEnumField(MethodType, description="请求方法")
    summary = fields.CharField(max_length=500, description="请求简介")
    tags = fields.JSONField(max_length=500, description="API标签")
    status = fields.CharEnumField(enum_type=StatusType, default=StatusType.enable, description="状态")

    class Meta:
        table = "apis"


class Menu(BaseModel, TimestampMixin):
    id = fields.IntField(pk=True, description="菜单ID")
    menu_name = fields.CharField(max_length=100, description="菜单名称")
    menu_type = fields.CharEnumField(MenuType, description="菜单类型")
    route_name = fields.CharField(max_length=100, description="路由名称")
    route_path = fields.CharField(max_length=200, description="路由路径")

    path_param = fields.CharField(null=True, max_length=200, description="路径参数")
    route_param = fields.JSONField(null=True, description="路由参数, List[dict]")
    order = fields.IntField(default=0, description="菜单顺序")
    component = fields.CharField(null=True, max_length=100, description="路由组件")

    parent_id = fields.IntField(default=0, max_length=10, description="父菜单ID")
    i18n_key = fields.CharField(max_length=100, description="用于国际化的展示文本，优先级高于title")

    icon = fields.CharField(null=True, max_length=100, description="图标名称")
    icon_type = fields.CharEnumField(IconType, null=True, description="图标类型")

    href = fields.CharField(null=True, max_length=200, description="外链")
    multi_tab = fields.BooleanField(default=False, description="是否支持多页签")
    keep_alive = fields.BooleanField(default=False, description="是否缓存")
    hide_in_menu = fields.BooleanField(default=False, description="是否在菜单隐藏")
    active_menu = fields.CharField(null=True, max_length=100, description="隐藏的路由需要激活的菜单")  # 枚举
    fixed_index_in_tab = fields.IntField(null=True, max_length=10, description="固定在页签的序号")
    status = fields.CharEnumField(enum_type=StatusType, default=StatusType.enable, description="状态")

    redirect = fields.CharField(null=True, max_length=200, description="重定向路径")
    props = fields.BooleanField(default=False, description="是否为首路由")
    constant = fields.BooleanField(default=False, description="是否为公共路由")

    buttons = fields.ManyToManyField("app_system.Button", related_name="menu_buttons")

    class Meta:
        table = "menus"


class Button(BaseModel, TimestampMixin):
    id = fields.IntField(pk=True, description="菜单ID")
    button_code = fields.CharField(max_length=200, description="按钮编码")
    button_desc = fields.CharField(max_length=200, description="按钮描述")
    status = fields.CharEnumField(enum_type=StatusType, default=StatusType.enable, description="状态")

    class Meta:
        table = "buttons"


class Log(BaseModel):
    id = fields.IntField(pk=True, description="日志ID")
    log_type = fields.CharEnumField(LogType, description="日志类型")
    by_user = fields.ForeignKeyField("app_system.User", null=True, on_delete=fields.NO_ACTION, description="操作人")
    api_log = fields.ForeignKeyField("app_system.APILog", null=True, on_delete=fields.SET_NULL, description="API日志")
    log_detail_type = fields.CharEnumField(LogDetailType, null=True, description="日志详情类型")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "logs"


class APILog(BaseModel):
    id = fields.IntField(pk=True, description="API日志ID")
    ip_address = fields.CharField(max_length=60, description="IP地址")
    user_agent = fields.CharField(max_length=800, description="User-Agent")
    request_url = fields.CharField(max_length=255, description="请求URL")
    request_params = fields.JSONField(null=True, description="请求参数")
    request_data = fields.JSONField(null=True, description="请求数据")
    response_data = fields.JSONField(null=True, description="响应数据")
    response_code = fields.CharField(max_length=6, null=True, description="响应业务码")
    create_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    process_time = fields.FloatField(null=True, description="请求处理时间")

    class Meta:
        table = "api_logs"


__all__ = ["User", "Role", "Api", "Menu", "Button", "Log", "APILog"]
