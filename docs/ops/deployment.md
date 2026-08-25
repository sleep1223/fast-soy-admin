# 部署

## Docker Compose（推荐）

```bash
git clone https://github.com/sleep1223/fast-soy-admin
cd fast-soy-admin
just docker-db-init
just up  # == docker compose up -d
```

| 服务 | 端口 | 说明 |
|------|------|------|
| nginx | 1880 | 前端 + API 反向代理 |
| app | 9999 | FastAPI 后端 |
| redis | 6379 | 缓存层 |
| postgres | 5432（仅内网） | 主数据库（`postgres:18.3-alpine`，挂卷 `postgres_data`） |

> 默认随容器起一套 PostgreSQL；`app` 通过 compose 内部网络以 `postgres:5432` 连接，端口**不对外暴露**。如需用外部托管 PG，可在 `docker-compose.yml` 中删除 `postgres` 服务，并把 `.env.docker` 的 `DB_URL` 指向外部地址。

### 查看日志

```bash
just logs          # == docker compose logs -f --tail=100
just logs app      # == docker compose logs -f --tail=100 app
just logs app 200  # == docker compose logs -f --tail=200 app
```

### 更新部署

```bash
git pull
just down && just rebuild                       # == docker compose down && docker compose up -d --build
docker compose exec app uv run tortoise migrate # 若本次更新含模型变更
```

## Docker 下的数据库初始化与迁移

> 核心原则：
>
> - **迁移文件**（`migrations/` 目录）由开发者在本地生成、随 git 提交、随镜像 `COPY` 进容器；
> - **迁移执行**（建表 / 升级表结构）由运维在容器里执行。
>
> 启动时**不会**自动迁移——新部署必须手动 `initdb`，后续模型变更必须手动 `migrate`。

### 上线前必改的关键信息（务必修改）

模板默认值是为了开箱即用，**生产环境上线前必须修改**，否则等同于把数据库公开：

| 位置 | 字段 | 默认值 | 必改原因 |
|---|---|---|---|
| [`docker-compose.yml`](https://github.com/sleep1223/fast-soy-admin/blob/main/docker-compose.yml) `postgres.environment` | `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | 均为 `fastsoyadmin` | 弱口令；任何能进入 compose 网络的容器都能直连 |
| [`.env.docker`](https://github.com/sleep1223/fast-soy-admin/blob/main/.env.docker) | `DB_URL` | `postgres://fastsoyadmin:fastsoyadmin@postgres:5432/fastsoyadmin` | 必须与 compose 中的账号密码保持一致 |
| [`.env.docker`](https://github.com/sleep1223/fast-soy-admin/blob/main/.env.docker) | `SECRET_KEY` | 模板自带 | JWT 签名密钥，泄露=任意伪造 token；用 `openssl rand -hex 32` 重新生成 |
| [`.env.docker`](https://github.com/sleep1223/fast-soy-admin/blob/main/.env.docker) | `CORS_ORIGINS` | `["*"]` | 生产改成具体域名白名单 |
| [`.env.docker`](https://github.com/sleep1223/fast-soy-admin/blob/main/.env.docker) | `APP_DEBUG` | 已是 `false`，确认不要改回 `true` | 调试模式会泄露堆栈与内部细节 |
| [`.env.docker`](https://github.com/sleep1223/fast-soy-admin/blob/main/.env.docker) | `RADAR_ENABLED` | 已是 `false` | 默认保持关闭；确需启用时，仅向 `R_ADMIN` / `R_SUPER` 开放并纳入敏感数据运维 |

> 修改 PG 密码后若已经起过容器，需要 `docker compose down -v` 清掉 `postgres_data` 卷再重启——否则会沿用首次初始化时写入的旧密码。生产更稳的做法：用 `${PG_PASSWORD}` 等占位符 + 部署机的环境变量注入，避免明文入库。

### 数据持久化前置检查

默认 `docker-compose.yml` 声明了 `redis_data` / `static_data` / `postgres_data` 三个卷，PostgreSQL 数据存放在 `postgres_data`（容器内 `/var/lib/postgresql/data`），`docker compose down` 后**保留**，仅 `docker compose down -v` 才会删除。

不使用内置 PG 而切到外部托管库时，请把 `.env.docker` 的 `DB_URL` 指向外部地址，并删除 `docker-compose.yml` 中的 `postgres` 服务以及 `app.depends_on.postgres`、`volumes.postgres_data` 块。

### 首次部署（initdb）

`just up` / `docker compose up -d` **不会自动建表**。新库第一次启动时，如果直接启动完整栈，后端会在启动初始化阶段查询 `menus` 等基础表并失败（PostgreSQL 日志常见 `relation "menus" does not exist`）。

首次部署请先执行封装好的 Docker 初始化命令，再启动完整栈：

```bash
just docker-db-init  # 首次先启动依赖服务并初始化数据库
just up                                         # == docker compose up -d
```

`initdb` 只负责生成/应用初始迁移；默认用户、菜单、角色、API、业务种子数据会在最后一步 app 正常启动时由 leader worker 自动写入。

几个容易踩的点：

- **`initdb` 必须在容器里跑，不能在宿主机跑**。`just docker-db-init` 已封装为 `docker compose run --rm app ...`；宿主机的 `just db-init` 会按本地 `.env` 走，连不到容器内的 PG。
- **首次不要用 `docker compose exec app ... initdb` 当唯一方案**。空库下 app 可能已经因缺表退出，`exec` 会找不到可用容器；`just docker-db-init` 会创建一次性 app 容器，更适合首次初始化。
- **`initdb` 只能在全新库上跑一次**，它不是幂等建表，表已存在会报错。之后任何模型变更一律走 `migrate`（见下一节）。
- **判断该 `initdb` 还是 `migrate`**：

  ```bash
  docker compose exec app uv run tortoise history
  ```

  报错 / 无输出 → 空库，跑 `initdb`；有历史但不是最新 → 跑 `migrate`。

- **直连 PG 排查**：

  ```bash
  docker compose exec postgres psql -U fastsoyadmin -d fastsoyadmin -c '\dt'
  ```

### 日常模型变更（makemigrations + migrate）

推荐流程：**本地生成迁移、提交 git、服务器重建并执行**。

```bash
# --- 本地（开发机） ---
# 1. 改 app/**/models.py
just makemigrations                              # == uv run tortoise makemigrations
git add migrations/ app/
git commit -m "feat(xxx): ..."
git push

# --- 服务器 ---
git pull
just rebuild                                     # == docker compose up -d --build
docker compose exec app uv run tortoise migrate
docker compose exec app uv run tortoise history  # 确认迁移已应用
```

为什么不在容器里 `makemigrations`：容器内生成的迁移文件在 `docker compose down` 后会随容器销毁，且不会回流到 git，下次重建会重新生成冲突。**迁移文件属于代码，必须在本地生成并入库。**

### 业务模块 `init_data.init()` 何时跑

不是迁移——是**每次启动由 Redis leader worker 自动执行**的幂等对账（菜单 / 角色 / API / 业务种子数据）。所以：

- 新增业务模块 / 修改 `init_data.py` 后，执行 `just rebuild`（等价 `docker compose up -d --build`）即可，**不需要手动触发**；
- 但表结构变更仍然要先 `migrate`，`init_data` 依赖表已存在。

启动期的完整顺序见 [启动初始化与对账](../develop/init-data.md)。

### 常用排错命令

```bash
docker compose exec app uv run tortoise history            # 查看已应用的迁移
docker compose exec app uv run tortoise heads              # 查看最新迁移头
just logs app | grep -iE "migrate|tortoise"                # == docker compose logs -f --tail=100 app | grep -iE "migrate|tortoise"
docker compose exec app sh -c 'ls -la migrations/models/'  # 确认迁移文件已随镜像打包
```

### 回滚

生产回滚推荐方案：

1. 先从备份恢复数据库（PG 用 `pg_restore` / 快照还原；外部托管库走 DBA 通道）；
2. `git revert` 对应的代码 + 迁移提交；
3. `just rebuild`（等价 `docker compose up -d --build`）。

不要试图在生产用 `tortoise downgrade` 回滚结构变更。建议为 `postgres_data` 卷配置定期备份（`pg_dump` cron 或宿主机快照）。

## 手动部署

### 后端

```bash
uv sync --no-dev
uvicorn app:app --host 0.0.0.0 --port 9999 --workers 4
```

### 前端

```bash
cd web && pnpm install && pnpm build
# 将 dist/ 部署到 Web 服务器
```

### Nginx 配置

```nginx
server {
    listen 80;
    root /path/to/web/dist;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:9999;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 上线前安全清单

模板默认携带方便本地开发的演示数据（预填账号、明文 `123456`、占位短信网关）。**上线前必须逐项清理**，否则等同于把后台公开。建议在第一次发版前一次性做完，并写进运维 runbook。

### 1. 移除登录页快捷登录与默认填充账号

文件：[`web/src/views/_builtin/login/modules/pwd-login.vue`](https://github.com/sleep1223/fast-soy-admin/blob/main/web/src/views/_builtin/login/modules/pwd-login.vue)

需要改两处：

**a. 清空 `model` 默认值**（避免输入框预填管理员账号 / 密码）：

```ts
// before
const model: FormModel = reactive({
  userName: 'Soybean',
  password: '123456'
});

// after
const model: FormModel = reactive({
  userName: '',
  password: ''
});
```

**b. 删除快捷登录按钮区**（`accounts` 数组 + `handleAccountLogin` + 模板里渲染这些按钮的 `NSpace`）。生产环境绝不能在 UI 上暴露任何账号。

校验：

```bash
cd web && pnpm dev                                                   # 打开登录页确认账号框为空、底部无快捷登录按钮
grep -RnE "Soybean|Super|Admin|123456" web/src/views/_builtin/login  # 应无业务命中
```

### 2. 删除 / 禁用模板内置用户

模板的 [`app/system/init_data.py`](https://github.com/sleep1223/fast-soy-admin/blob/main/app/system/init_data.py) 在首次启动时会创建以下账号（密码全部是 `123456`）：

| 用户名 | 角色 | 密码 | 用途 |
|---|---|---|---|
| Soybean | R_SUPER | 123456 | 演示超管 |
| Super | R_SUPER | 123456 | 演示超管 |
| Admin | R_ADMIN | 123456 | 演示管理员 |
| User | R_USER | 123456 | 演示普通用户 |

**生产推荐：保留 1 个真实超管，其他全部删除。** 步骤：

1. **创建你自己的超管**（推荐先做这一步，避免锁死后台）：用任一 `Soybean / Super` 登录 → 系统管理 → 用户管理 → 新增 → 设置强密码 → 角色勾选 `R_SUPER`。
2. **退出登录，用新账号登录**，验证权限正常。
3. **逐个删除模板账号**：用户管理列表里删除 `Soybean / Super / Admin / User`（或先批量「禁用」观察一周再删）。
4. **如果不打算让访客自助注册**：把前端 [`pwd-login.vue`](https://github.com/sleep1223/fast-soy-admin/blob/main/web/src/views/_builtin/login/modules/pwd-login.vue) 底部的 `register` 跳转按钮一并删除；同时考虑在后端 [`auth.py`](https://github.com/sleep1223/fast-soy-admin/blob/main/app/system/api/auth.py) 注释掉 `/auth/register`（或加 IP 白名单 / 邀请码）。
5. **如果你修改了 `init_data.py` 删除了模板用户的种子数据**，注意 `init_data.py` 仅 upsert（不会主动删数据库里已存在的用户），所以**老库需要手工清理一次**，新库则不会再生成。

> **注意**：当前 `init_data.py` 的用户种子是无条件插入的——如果你只在数据库里删了用户没改种子文件，重启后会被重新创建。建议同时把种子里的演示用户也注释掉。

### 3. 重新规划普通用户角色

模板自带 `R_USER` 角色，菜单 / API / 按钮权限是按演示场景配置的（包含一些后台演示页）。生产环境普通用户**通常不应**直接复用 `R_USER`，建议：

**做法 A（推荐）：新建生产专用角色，原 `R_USER` 留空备用 / 删除**

1. 系统管理 → 角色管理 → 新增角色，例如 `R_BIZ_USER`（中文名"业务用户"）。
2. 在该角色的「菜单权限」里，只勾选用户实际需要看到的页面（一般只有 `home` + 你的业务模块菜单）。
3. 「按钮权限」里只勾选这些菜单下需要暴露的按钮码（如 `B_INVENTORY_WAREHOUSE_VIEW`，但不勾 `B_INVENTORY_WAREHOUSE_DELETE`）。
4. 「接口权限」一定要把对应的 `(method, path)` 也勾上——按钮在前端隐藏不等于后端拒绝（参见 [RBAC](../develop/rbac.md)）。
5. 「数据范围」按需选 `self` / `scope` / `custom`，不要保留默认 `all`。
6. 把所有真实业务用户从 `R_USER` 改挂到 `R_BIZ_USER`。

**做法 B：直接修改 `R_USER`**

如果不想新建角色，在角色管理里编辑 `R_USER`，按上面 (2)~(5) 重新勾权限即可。但要注意 [`init_data.py`](../develop/init-data.md) 里 `ensure_role` 是 upsert + clear-and-readd（菜单/按钮/接口），意味着**重启会被种子覆盖回演示配置**——做法 B 必须同步修改 `init_data.py` 里 `R_USER` 的种子定义，否则改动会被回滚。

校验：

```bash
# 用 R_BIZ_USER 用户登录后台
# - 侧边栏只剩允许的菜单
# - 直接 curl 一个未授权接口应返回 2200/PERMISSION_DENIED
curl -H "Authorization: Bearer <user_token>" http://your-host/api/v1/system/users/search -X POST -d '{}'
```

### 4. 接入真实短信网关替换验证码占位

当前 [`app/system/services/captcha.py`](https://github.com/sleep1223/fast-soy-admin/blob/main/app/system/services/captcha.py) 的 `send_captcha()` **只把验证码写进 Redis 并打日志**，并未真正发送。这意味着：注册 / 验证码登录 / 忘记密码三条链路在生产环境形同虚设——任何人能看到日志（或拿到 Redis）就能登录任意账号。

替换步骤（以阿里云 SMS 为例，腾讯云 / 华为云 / Twilio 思路一致）：

1. **添加依赖**：

   ```bash
   uv add alibabacloud_dysmsapi20170525
   ```

2. **加配置项**到 `.env` 与 `app/core/config.py`：

   ```env
   SMS_PROVIDER=aliyun                # aliyun / tencent / mock，留 mock 等价当前占位
   SMS_ACCESS_KEY_ID=xxx
   SMS_ACCESS_KEY_SECRET=xxx
   SMS_SIGN_NAME=your-sign            # 阿里云已审核的签名
   SMS_TEMPLATE_CODE=SMS_xxxxx        # 已审核的模板码，模板内容要含 ${code}
   SMS_DAILY_LIMIT_PER_PHONE=10       # 单号单日上限
   SMS_COOLDOWN_SECONDS=60            # 同号两次发送冷却
   ```

3. **改写 `send_captcha`**，把 `radar_log("...开发模式...")` 替换为真实 SDK 调用，并加频控：

   ```python
   async def send_captcha(redis: Redis, phone: str) -> bool:
       cooldown_key = f"captcha_cd:{phone}"
       if await redis.get(cooldown_key):
           return False                                    # 命中冷却
       daily_key = f"captcha_daily:{phone}:{date.today()}"
       if int(await redis.get(daily_key) or 0) >= APP_SETTINGS.SMS_DAILY_LIMIT_PER_PHONE:
           return False                                    # 命中日上限

       code = _generate_code()
       await redis.set(f"{_CAPTCHA_PREFIX}{phone}", code, ex=_CAPTCHA_EXPIRE)

       ok = await _provider_send(phone, code)              # 调阿里云 SDK
       if not ok:
           return False

       await redis.set(cooldown_key, "1", ex=APP_SETTINGS.SMS_COOLDOWN_SECONDS)
       await redis.incr(daily_key)
       await redis.expire(daily_key, 86400)
       return True
   ```

4. **加测试 + 灰度**：先在 staging 用真实手机号验证一遍登录 / 注册 / 重置密码三条链路，再切生产。**生产环境一定要把 `radar_log` 里打印 `code` 的那一行删掉**。认证路径虽不会进入 Radar 请求库，但 `radar_log` 默认仍写 Loguru；普通业务 `code` / `msg` 也不会自动脱敏，验证码仍会明文留在文件日志中。

5. **加风控**：建议把 `/auth/captcha`、`/auth/register`、`/auth/reset-password` 三个端点单独配 IP 限流（参考 `app/core` 里 `GUARD_*` 配置），防止短信轰炸。

### 5. 受影响版本升级后的 Radar 处置

Radar 默认关闭。升级后先确认 `.env` / `.env.docker` 中的 `RADAR_ENABLED`；只有确有诊断需求时才设为 `true` 并重启。启用后，匿名和普通用户访问 `/__radar/api/*` 应分别得到认证失败和权限不足，只有 `R_ADMIN` / `R_SUPER` 可用。

如果旧版本曾在公网开启 Radar：

1. 检查 Nginx、网关或 WAF 中 `/__radar/api` 的历史访问日志；
2. 先使可能暴露的 token 失效并重置密码、API key 等凭据；若怀疑签名密钥泄露或需要全局失效，再评估 Sqids 影响后轮换 `SECRET_KEY`；
3. 注意修复只会在 API 读取时再次脱敏，不会改写旧的数据库记录；
4. Radar 表位于 `DB_URL` 对应数据库并随其正常备份 / 恢复；如需清理 `radar_requests` 及级联的 `radar_queries` / `radar_user_logs`，必须先备份、明确范围，并按破坏性操作流程另行取得确认。补丁不会自动清理数据或修改表结构。

详见 [Radar 的敏感数据边界与历史数据处置](./radar.md#升级后的历史数据处置)。

### 上线前最终检查

```bash
# 后端
grep -RnE "password.*123456|Soybean|Super|Admin" app/                               # 应只剩注释 / 文档
docker compose exec app uv run python -c "from app.system.models import User; ..."  # 列表应为你的真实账号

# 前端
grep -RnE "userName: 'Soybean'|password: '123456'" web/src/                         # 应无命中
curl -s https://your-host/login | grep -iE "soybean|123456"                         # 应无命中

# 短信
APP_DEBUG=false python -c "import asyncio; from app.system.services.captcha import send_captcha; ..."
# 用真实手机号收一条短信确认

# Radar（默认应为 false；若显式开启，再验证匿名 / 普通用户 / 管理员三类访问）
grep '^RADAR_ENABLED=' .env .env.docker
```

完成上述五项才视为生产就绪。建议把这份清单挂到 PR 模板或上线 checklist 里，避免以后新环境复发。
