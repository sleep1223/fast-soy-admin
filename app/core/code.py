"""
业务响应码分类定义。

码段说明：
  0000        — 成功
  1000-1999   — 系统内部错误（异常捕获）
  2000-2999   — 业务逻辑错误（认证、权限、资源等）
  3000-3999   — 内部保留
  4000-9999   — 用户自定义业务码（框架不使用）

约定：每一个不同的失败场景都应使用唯一的业务码，便于前端与测试精确断言。

前端 .env 映射：
  VITE_SERVICE_SUCCESS_CODE=0000
  VITE_SERVICE_LOGOUT_CODES=2100,2101,2104,2105
  VITE_SERVICE_MODAL_LOGOUT_CODES=2102,2106
  VITE_SERVICE_EXPIRED_TOKEN_CODES=2103
"""


class Code:
    """全应用统一响应码分类定义。每个不同业务场景使用唯一的码。"""

    # ---- 0000 成功 ----
    SUCCESS = "0000"

    # ==== 1xxx 系统内部错误 ====

    # 10xx — 服务器错误
    INTERNAL_ERROR = "1000"  # 通用/未处理异常

    # 11xx — 数据库错误
    INTEGRITY_ERROR = "1100"  # 约束冲突（唯一键、外键等）
    NOT_FOUND = "1101"  # 记录不存在

    # 12xx — 数据校验错误
    REQUEST_VALIDATION = "1200"  # 请求参数/请求体校验失败（FastAPI 层）
    RESPONSE_VALIDATION = "1201"  # 响应序列化失败

    # ==== 2xxx 业务逻辑错误 ====

    # 21xx — 认证（Token/会话相关，前端会根据特定码触发登出/刷新逻辑）
    INVALID_TOKEN = "2100"  # Token 缺失/解码失败/格式无效（前端登出）
    INVALID_SESSION = "2101"  # Token 类型错误/用户不存在（前端登出）
    ACCOUNT_DISABLED = "2102"  # 用户账号已被禁用（前端弹窗后登出）
    TOKEN_EXPIRED = "2103"  # 访问 Token 已过期（前端触发刷新）
    REFRESH_TOKEN_MISSING = "2104"  # 刷新令牌缺失或为空
    NOT_REFRESH_TOKEN = "2105"  # 传入的令牌不是 refresh token
    SESSION_INVALIDATED = "2106"  # token_version 已被递增，旧 token 已失效
    REFRESH_TOKEN_EXPIRED = "2107"  # refresh token 已过期，需要重新登录

    # 22xx — 授权
    API_DISABLED = "2200"  # API 接口已被禁用
    PERMISSION_DENIED = "2201"  # RBAC 接口权限不足
    MISSING_BUTTON_PERMISSION = "2202"  # 缺少指定按钮权限（全部匹配语义）
    NEED_ANY_BUTTON_PERMISSION = "2203"  # 需任一按钮权限（任一匹配语义）
    MISSING_ROLE = "2204"  # 缺少指定角色（全部匹配语义）
    NEED_ANY_ROLE = "2205"  # 需任一角色（任一匹配语义）
    SUPER_ADMIN_ONLY = "2206"  # 仅超级管理员可操作
    USER_NO_ROLE = "2207"  # 用户未绑定任何角色

    # 23xx — 资源冲突（唯一键重复）
    DUPLICATE_RESOURCE = "2300"  # 通用资源重复（兜底）
    DUPLICATE_ROLE_CODE = "2301"  # 角色编码已存在
    DUPLICATE_USER_EMAIL = "2302"  # 邮箱已被注册
    DUPLICATE_USER_PHONE = "2303"  # 手机号已被注册
    DUPLICATE_USER_NAME = "2304"  # 用户名已存在
    DUPLICATE_MENU_ROUTE = "2305"  # 菜单路由路径已存在

    # 24xx — 通用业务失败（每种情况都有自己的码）
    FAIL = "2400"  # 未归类通用失败（兜底，尽量避免使用）
    WRONG_CREDENTIALS = "2401"  # 用户名或密码错误
    CAPTCHA_INVALID = "2402"  # 验证码错误或已过期
    CAPTCHA_SEND_FAILED = "2403"  # 验证码发送失败
    PHONE_NOT_REGISTERED = "2404"  # 手机号未注册
    OLD_PASSWORD_WRONG = "2405"  # 修改密码时原密码错误
    TARGET_USER_NOT_FOUND = "2406"  # 操作目标用户不存在（模拟登录等）
    STATE_TRANSITION_INVALID = "2407"  # 不允许的状态流转

    # 25xx — 限流/安全
    RATE_LIMITED = "2500"  # 请求过于频繁
    IP_BANNED = "2501"  # IP 已被临时封禁
    ACCESS_DENIED = "2502"  # 被安全策略拦截

    # 26xx — Schema 必填字段校验（业务 Schema 层）
    PARAM_REQUIRED = "2600"  # 通用必填兜底
    USERNAME_REQUIRED = "2601"  # 用户名不能为空
    PASSWORD_REQUIRED = "2602"  # 密码不能为空
    USER_ROLE_REQUIRED = "2603"  # 用户至少需要一个角色
    USER_EMAIL_REQUIRED = "2604"  # 用户邮箱不能为空
    ROLE_NAME_REQUIRED = "2605"  # 角色名称不能为空
    ROLE_CODE_REQUIRED = "2606"  # 角色编码不能为空
    ROUTE_NAME_REQUIRED = "2607"  # 路由名称不能为空
    ROUTE_PATH_REQUIRED = "2608"  # 路由路径不能为空

    # ==== 3xxx 内部保留 ====
    # （暂未使用，为未来框架扩展预留）

    # ==== 4000-9999 用户自定义业务码 ====
    # （框架不使用——供项目专属业务逻辑使用）

    # 40xx — HR 业务模块（example 分支专属）
    HR_DEPARTMENT_REQUIRED = "4000"  # 超级管理员创建员工需要指定部门
    HR_MANAGER_REQUIRED = "4001"  # 仅部门主管可创建员工
    HR_CREATE_FORBIDDEN = "4002"  # 无权限创建员工
    HR_TAGS_EXCEED_LIMIT = "4003"  # 员工标签数量超出上限
    HR_EMPLOYEE_NOT_IN_DEPT = "4004"  # 该员工不在当前主管部门中
    HR_USER_NOT_EMPLOYEE = "4005"  # 当前用户未关联员工信息
    HR_MANAGER_ONLY = "4006"  # 仅部门主管可执行此操作
    HR_INVALID_TRANSITION = "4007"  # 不允许的状态流转
