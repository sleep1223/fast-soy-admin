<!-- markdownlint-disable MD033 MD041 -->

<p align="center">
  <a href="https://github.com/sleep1223/"><img src="web/public/favicon.svg" width="180" height="180" alt="FastSoyAdmin"></a>
</p>

<div align="center">

# FastSoyAdmin

[![license](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![github stars](https://img.shields.io/github/stars/sleep1223/fast-soy-admin)](https://github.com/sleep1223/fast-soy-admin)
![python](https://img.shields.io/badge/python-3.12+-blue?logo=python&logoColor=edb641)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi&logoColor=edb641)
![Pydantic](https://img.shields.io/badge/Pydantic_v2-e92063?logo=pydantic&logoColor=edb641)
![uv](https://img.shields.io/badge/uv-managed-blueviolet)
[![basedpyright](https://img.shields.io/badge/types-basedpyright-797952.svg?logo=python&logoColor=edb641)](https://github.com/DetachHead/basedpyright)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

<span><a href="./README.en.md">English</a> | 中文</span>

**FastAPI + Vue3 全栈后台管理模板，开箱即用**

</div>

## 简介

开箱即用的全栈后台管理模板，可作为中后台脚手架，也可作为全栈开发参考。

- **后端** — FastAPI · Pydantic v2 · Tortoise ORM · Redis
- **前端** — Vue3 · Vite8 · TypeScript · Naive UI · UnoCSS · Pinia · Alova · Elegant Router
- **基础设施** — Docker Compose（Nginx + FastAPI + Redis）、多 worker 启动锁、fastapi-guard 限流、内置 Radar 监控面板（默认关闭，按需开启）
- **代码生成器** — `cli-init` 起骨架，编辑 `models.py`，`cli-crud` 一键产出前后端 CRUD

## 特性

- **AI Coding 友好** — 内置 [CLAUDE.md](CLAUDE.md) 与完整项目规范
- **一键 CRUD** — Tortoise 模型生成前后端 CRUD、类型与 i18n
- **可覆写路由工厂** — `CRUDRouter` 生成标准接口，`@crud.override` 按需定制
- **模块化业务** — `app/business/<name>/` 自动发现，跨模块走事件总线
- **多数据库支持** — PostgreSQL / SQLite / MySQL / SQL Server / Oracle
- **RBAC 权限体系** — 菜单 / API / 按钮 + 行级 `data_scope`
- **IaC 初始化对账** — 菜单、角色、API 启动时可声明式同步
- **统一接口契约** — `{code, msg, data}`、camelCase、Sqid 对外 ID
- **全栈类型检查** — basedpyright + vue-tsc + 静态 i18n 校验
- **内置运维能力** — Radar 监控（默认关闭）、Redis 缓存降级、限流与 IP 封禁
- **Docker 部署** — Nginx + FastAPI + Redis 开箱即用

## 相关链接

- [在线预览](https://fast-soy-admin.sleep0.de/)
- [项目文档](https://sleep1223.github.io/fast-soy-admin-docs/)
- [快速开始](https://sleep1223.github.io/fast-soy-admin-docs/getting-started/quick-start)
- [开发指南](https://sleep1223.github.io/fast-soy-admin-docs/getting-started/workflow)
- [命令参考](https://sleep1223.github.io/fast-soy-admin-docs/reference/commands)
- [Apidog 接口文档](https://fast-soy-admin.apidog.io)

## 交流群

[点击加入 FastSoyAdmin QQ 交流群](https://qm.qq.com/q/JHL7VHvDa)，一起交流使用、二开和部署经验。

## 分支说明

| 分支      | 用途                                                |
| --------- | --------------------------------------------------- |
| `main`    | 纯净骨架，无业务示例（默认分支）                    |

## 快速开始

### 环境要求

| 工具             | 版本     |
| ---------------- | -------- |
| Python           | >= 3.12  |
| Node.js          | >= 20.19 |
| uv · pnpm · just | 最新     |

### Docker 部署（推荐）

```bash
git clone https://github.com/sleep1223/fast-soy-admin.git
cd fast-soy-admin
just docker-db-init  # 首次先启动依赖服务并初始化数据库
just up              # 启动完整栈并写入默认/业务种子数据
```

访问 `http://localhost:1880`。

> `initdb` 只在全新数据库执行一次；启动**不会**自动迁移。默认用户、菜单、角色、API 与业务种子数据会在最后一步 app 正常启动时写入。详见 [部署文档](https://sleep1223.github.io/fast-soy-admin-docs/ops/deployment)。

### 本地开发

```bash
git clone https://github.com/sleep1223/fast-soy-admin.git
cd fast-soy-admin
just install          # 后端 uv sync + 前端 pnpm install
cp .env.example .env  # 复制环境变量模板，按需修改 SECRET_KEY / DB_URL / REDIS_URL 等
just db-init          # 首次建表 + 基础数据
just run              # 并行启动后端(:9999) + 前端(:9527)，Ctrl+C 一起停
```

### Radar 监控（默认关闭）

出于敏感数据保护考虑，Radar 默认关闭。默认状态下不会挂载 `/__radar/api` 路由，不会启用请求、SQL 与异常采集，管理菜单中的 Radar 入口也处于禁用状态。

确需排障时，本地开发在项目 `.env` 中显式开启；Docker 部署则修改构建时复制为 `.env` 的 `.env.docker`：

```bash
RADAR_ENABLED=true
```

修改后需要重启应用。启用后仅 `R_ADMIN` 与 `R_SUPER` 可以访问 Radar；匿名用户和普通用户无权访问，`/api/v1/auth/` 下的登录、注册等认证请求始终不会被采集。采集到的敏感字段会统一脱敏，但仍应仅在确有诊断需求时开启。

关闭时将配置恢复为 `RADAR_ENABLED=false` 并重启。关闭 Radar 不会自动删除数据库中已有的历史记录；历史数据处置前应先备份，并按事故响应流程取得删除确认。完整配置、访问控制和数据处理规则见 [Radar 监控文档](https://sleep1223.github.io/fast-soy-admin-docs/ops/radar)。

## 常用命令

全部命令封装在 `justfile`，运行 `just --list` 查看完整列表。

| 命令                                         | 作用                                      |
| -------------------------------------------- | ----------------------------------------- |
| `just install`                               | 安装后端 + 前端依赖                       |
| `just run`                                   | 同时启动后端 + 前端开发服务器             |
| `just run backend` / `just run frontend`     | 仅启动后端 / 前端                         |
| `just check`                                 | 跑完后端 + 前端所有质量检查（提交前必跑） |
| `just check backend` / `just check frontend` | 仅检查后端 / 前端                         |
| `just mm`                                    | `makemigrations` + `migrate`              |
| `just cli-init xxx`                          | 创建业务模块骨架                          |
| `just cli-gen xxx`                           | 选择模型与模糊/精确查询字段，生成后端代码 |
| `just cli-gen-web xxx 中文名`                | 选择模型与列表/搜索字段，生成前端代码     |
| `just cli-gen-all xxx 中文名`                | 一次选择并生成前后端代码                  |
| `just cli-crud xxx 中文名`                   | 同上，完整 CRUD 生成别名                  |
| `just up` / `just down` / `just logs`        | Docker 启停与日志                         |

完整清单参见 [命令参考](https://sleep1223.github.io/fast-soy-admin-docs/reference/commands)。

## 新增业务模块

以 `inventory`（库存管理）为例：

```bash
just cli-init inventory                   # 1. 创建模块骨架
$EDITOR app/business/inventory/models.py  # 2. 定义 Tortoise 模型
just cli-crud inventory 库存管理          # 3. 生成前后端 CRUD（i18n 自动并入）
just mm                                   # 4. 迁移
just run                                  # 5. 启动验证
just check                                # 6. 提交前检查
```

完整流程与字段类型映射见 [开发指南](https://sleep1223.github.io/fast-soy-admin-docs/getting-started/workflow)。

## 架构

```
app/
├── core/           # 框架基础设施（CRUDBase / CRUDRouter / Schema / 鉴权 / 缓存 / 事件 / Sqids）
├── system/         # 系统模块（auth / user / role / menu / api / dictionary / radar）
├── business/       # 业务模块（autodiscover 自动加载）
├── cli/            # 代码生成器
└── utils/          # 业务模块对外统一 import 入口
web/src/
├── views/          # 页面（Elegant Router 源）
├── service/api/    # Alova HTTP 封装
├── typings/api/    # TS 类型
├── store/modules/  # Pinia
├── router/         # Elegant Router + 守卫
└── locales/        # vue-i18n
```

分层：`api/` → `services/` → `controllers/` → `models + schemas`。业务模块**禁止**反向 import `app.system.*`（少数显式暴露的 service 除外），**禁止**互相 import；跨模块走事件总线。详见 [架构](https://sleep1223.github.io/fast-soy-admin-docs/getting-started/architecture)。

## 切换数据库

修改 `.env` 中的 `DB_URL`，运行 `just db-init`。支持 PostgreSQL / SQLite / MySQL / SQL Server / Oracle。

默认依赖已包含 PostgreSQL（`tortoise-orm[asyncpg]`）与 SQLite（`aiosqlite`，tortoise 自带），其他数据库按需安装：

```bash
uv sync --extra mysql   # MySQL (asyncmy)
uv sync --extra mssql   # SQL Server (asyncodbc)
uv sync --extra oracle  # Oracle (asyncodbc)
```

业务模块可在自己的 `config.py` 声明独立 `DB_URL`，autodiscover 会注册为 `conn_<biz>`；跨模型事务用 `get_db_conn(Model)` 取连接名。详见 [切换数据库](https://sleep1223.github.io/fast-soy-admin-docs/ops/database)。

## 响应码

所有接口返回 `{"code": "xxxx", "msg": "...", "data": ...}`，HTTP 状态恒 200。

| 段          | 含义                               | 前端典型行为           |
| ----------- | ---------------------------------- | ---------------------- |
| `0000`      | 成功                               | 正常处理               |
| `1xxx`      | 系统内部错误 / 序列化失败          | 框架自动弹错           |
| `21xx`      | 认证失败（token / session）        | 登出 / 弹窗 / 自动刷新 |
| `22xx`      | 授权失败（RBAC / 按钮 / 角色）     | 显示错误消息           |
| `23xx`      | 资源冲突（唯一键）                 | 显示错误消息           |
| `24xx`      | 通用业务失败                       | 显示错误消息           |
| `25xx`      | 限流 / 安全策略                    | 显示错误消息           |
| `26xx`      | Schema 必填兜底                    | 显示错误消息           |
| `4000–9999` | 用户自定义（业务模块从 `4000` 起） | 业务自行处理           |

详细码表见 [响应码文档](https://sleep1223.github.io/fast-soy-admin-docs/reference/codes)。

## 前端代码同步

`web/` 由独立仓库 [fast-soy-admin-frontend](https://github.com/sleep1223/fast-soy-admin-frontend) 维护，与本仓库**无共同祖先**。同步上游需手动 `git subtree`，参考历史 commit `chore(web): sync with fast-soy-admin-frontend@...`。

## 示例图片

![首页-中文](https://sleep1223.github.io/fast-soy-admin-docs/screenshots/home-zh.png)
![首页-英文](https://sleep1223.github.io/fast-soy-admin-docs/screenshots/home-en.png)
![性能监控-仪表盘](https://sleep1223.github.io/fast-soy-admin-docs/screenshots/radar-dashboard.png)
![性能监控-请求列表](https://sleep1223.github.io/fast-soy-admin-docs/screenshots/radar-requests.png)
![性能监控-SQL查询](https://sleep1223.github.io/fast-soy-admin-docs/screenshots/radar-sql.png)
![性能监控-异常列表](https://sleep1223.github.io/fast-soy-admin-docs/screenshots/radar-exceptions.png)

## TODO

- [x] Redis 优化
- [x] Docker 一键部署
- [x] CLI 代码生成器（后端 + 前端）
- [x] 内置 Radar 监控（请求 / SQL / 异常 / 埋点）
- [x] `main` 纯净分支
- [ ] 端到端测试

## 贡献

欢迎提交 [Pull Request](https://github.com/sleep1223/fast-soy-admin/pulls) 或创建 [Issue](https://github.com/sleep1223/fast-soy-admin/issues/new)。

<a href="https://github.com/sleep1223/fast-soy-admin/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=sleep1223/fast-soy-admin" />
</a>

## 开源协议

[MIT © 2024](./LICENSE)
