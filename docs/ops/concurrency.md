# Tortoise ORM 高并发业务指南

接口只被一个人、一秒一次调用时，什么并发控制都不需要；但后台管理系统里有几种操作不满足这个假设：

- 商品状态流转、工单审批、订单状态机——**同一条记录**可能被同时点两下
- 库存扣减、额度冻结、计数器——**多条请求**都想写同一行
- 批量导入、定时对账、一次性初始化——**只想有一个 worker 在跑**

FastSoyAdmin 里可用的三把武器——**事务**、**乐观锁（含状态机）**、**Redis 分布式锁**——以及它们分别对应的场景。

## 部署拓扑：进程与线程

项目用 [Granian](https://github.com/emmett-framework/granian) 作为 ASGI 服务器（见 `run.py`），支持三种并发拓扑。选哪种决定上面的工具够不够用。

### 1) 单进程多线程（`workers=1, threads=N` 或 `blocking_threads=N`）

改 `run.py` 的 `main()`：

```python
server = Granian(
    target="app:app",
    address="0.0.0.0",
    port=9999,
    workers=1,                   # ← 单进程
    threads=1,                   # 事件循环线程数，保持 1
    blocking_threads=16,         # ← 阻塞调用卸载线程数
    interface=Interfaces.ASGI,
    log_level=LogLevels.info,
    # 下面这些"健壮性 / 内存保护"参数仍可填, 但只有崩溃后整进程 respawn 有效
    respawn_failed_workers=True,
    workers_lifetime=3600 * 4,
    workers_max_rss=512,
    workers_kill_timeout=30,
    backpressure=64,
    backlog=1024,
)
```

- **一个进程 + 一个 asyncio 事件循环**，`blocking_threads` 用于把阻塞调用卸载到线程池（`asyncio.to_thread`、`run_in_executor`）。
- 进程内共享内存，Python 对象、模块级 `dict`、`asyncio.Lock` / `Semaphore`、应用 `state` 全部可见。
- 适合：**开发机 / 小流量单机**、本地调试 `python run.py`。
- 并发注意：GIL 仍在，CPU 密集任务不会因多线程变快；事件循环只有一条，`await` 链中任何一处阻塞都会拖垮全 worker。**别在事件循环里跑 CPU 重活**——丢 `asyncio.to_thread`。
- 本页列的 `asyncio.Semaphore`、乐观锁、事务全部开箱即用，**不需要 Redis 分布式锁**。
- ⚠️ **不能自动杀死阻塞进程**：见 [进程级健壮性的前置条件](#进程级健壮性的前置条件)。

### 2) 多进程单线程（`workers=N, threads=1`）— 项目默认

`run.py` 现有写法即是此模式，读环境变量 `WORKERS`，默认 `min(cpu, 4)`：

```python
workers = int(os.getenv("WORKERS", min(multiprocessing.cpu_count(), 4)))
server = Granian(
    target="app:app",
    workers=workers,             # ← 多进程
    # threads 默认 1, 不传即可
    ...
)
```

部署时只需 `WORKERS=8 python run.py` 调整进程数。

- **N 个 worker 进程 × 每进程一个事件循环**，是 Python 下最常见的"绕过 GIL"水平扩展姿势。
- 进程间**不共享内存**：
  - 模块级变量、`app.state`、`asyncio.Lock` **跨 worker 无效**；
  - Redis / 数据库是**唯一**的共享状态源；
  - 定时任务、一次性初始化必须借助 [Redis leader worker 选举](../develop/init-data.md)，否则 N 个 worker 会并发触发 N 次。
- 适合：**生产部署**。容器多副本场景也都是这种拓扑（每容器 N worker）。
- 并发注意：
  - "同一条记录被同时改"在多 worker 下是**常态**，乐观锁 / `select_for_update` / `F` 表达式必须用对；
  - 想做"只有一个 worker 跑"的逻辑（定时对账、批量导入）一律走 **Redis 分布式锁**；
  - 进程启动顺序不确定，不要依赖"第一个 worker 做初始化"——用 leader 选举。
- ✅ **可以自动杀死阻塞 worker**：`workers_kill_timeout` / `workers_max_rss` / `workers_lifetime` 在此拓扑下真正生效。

### 3) 多进程多线程（`workers=N, threads=M`）

在默认基础上再加线程：

```python
server = Granian(
    target="app:app",
    workers=workers,             # ← 多进程
    threads=1,                   # 事件循环线程保持 1
    blocking_threads=16,         # ← 每个 worker 额外的阻塞卸载线程
    runtime_threads=1,           # 默认即可
    ...
)
```

- 前两者的叠加：**N 进程 × 每进程 1 个事件循环 + M 个线程**。
- 线程一般仍是 **blocking offload** 用途（阻塞 IO、CPU 卸载），事件循环依旧只有一条/进程。
- 适合：业务里混了相当比例的**同步阻塞调用**（老的 requests / 同步 DB 驱动 / CPU bound），需要在不膨胀进程数的前提下再压一点吞吐。
- 并发注意：
  - 同一 worker 内的线程共享 Python 对象，但**不共享事件循环**，不要在线程里直接 `await`——用 `loop.call_soon_threadsafe` / `asyncio.run_coroutine_threadsafe` 回到主循环；
  - Tortoise / asyncpg 的连接池**不是**线程安全地让你跨线程共享——让 DB 调用留在事件循环里，只把纯 CPU / 同步 IO 丢到线程池；
  - 跨进程协调仍然只能靠 Redis / DB，和 (2) 一致。
- ✅ **可以自动杀死阻塞 worker**（同 2）。单个线程卡死不会独立被回收，但整进程 RSS / 生命周期 / kill_timeout 依然按进程粒度生效。

### 进程级健壮性的前置条件

`run.py` 里这几个参数只在 **`workers >= 2`** 时真正有意义：

| 参数 | 作用 | 为什么需要多进程 |
|---|---|---|
| `respawn_failed_workers=True` | worker 崩溃自动重启 | 单 worker 崩了整个服务就挂了，"重启"再快也有服务中断 |
| `workers_kill_timeout=30` | worker **卡死**（事件循环被阻塞、无响应心跳）超 30s 强制 kill | 单 worker 被 kill = 整个服务 down；多进程下仅影响它一个，其它继续接流量 |
| `workers_lifetime=3600*4` | 每 4h 回收一次，防内存泄漏 | 单 worker 回收时有数秒不可用窗口；多进程下 Granian 滚动回收，服务无感 |
| `workers_max_rss=512` | 单 worker RSS 超限自动重启 | 同上 |

换句话说，**"自动杀死阻塞进程"这件事本身就需要多进程**——Python 没有办法在同一进程内把一个卡死的线程/协程强制 kill 掉（没有安全的"线程终止"API，GIL 也不允许中断已持有 GIL 的 C 扩展）。唯一可靠的兜底是**由父进程 SIGKILL 子进程并重启**，这就必须 `workers >= 2`，否则被杀的就是你自己。

所以开发机 `workers=1` 时：

- 请求卡死 → 只能自己手动 Ctrl+C 重启；
- 内存涨到 2GB → 不会被回收，得自己重启；
- 进程 panic → `respawn_failed_workers` 会重启它，但重启窗口内服务不可用。

**生产部署务必保持多进程（至少 `workers=2`）**，这是 `run.py` 那套自愈参数生效的前提。

### 选型速查

| 你在做什么 | 推荐拓扑 | 不够用时升级为 |
|---|---|---|
| 本地开发 / 调试 | 单进程多线程（`workers=1`） | — |
| 生产单机 / 多副本容器 | **多进程单线程（默认）** | 有阻塞卸载需求 → 多进程多线程 |
| 业务含较多同步阻塞 IO / CPU 任务 | 多进程多线程 | 仍瓶颈 → 拆独立 worker 服务 |
| 想跑定时任务 / 单次初始化 | 任何多 worker 拓扑 + **Redis leader / 分布式锁** | — |

一句话：**只要 `workers > 1`，进程内的任何同步原语（`asyncio.Lock`、模块级计数器、`app.state`）都不再可信；共享状态必须落到 DB 或 Redis。**

## 先选对工具

| 场景 | 推荐手段 | 说明 |
|---|---|---|
| 一次性写多张表要么都成功要么都回滚 | `in_transaction` | 最基础的 ACID 语义 |
| 读一行马上改这行（同进程内、同 DB） | `select_for_update()`（悲观锁） | 行级排他锁，简单直接但会阻塞其它事务 |
| 单行状态/计数/余额的并发更新 | 乐观锁（`version` 字段 + 带条件 `update`） | 低冲突场景首选，无阻塞、可重试 |
| 状态机流转要"同时只有一次生效" | 状态机 + 乐观锁 | FSM 校验合法性，乐观锁保证"只有一次 `pending→active` 会赢" |
| 跨 worker / 跨进程 / 跨服务 的串行化（如批量导入、幂等提交、定时任务 leader） | Redis 分布式锁 | 覆盖 uvicorn 多 worker、docker 多副本场景 |
| DB + Redis / DB + 外部 HTTP 的一致性 | 事务 + 事件总线 + 补偿 | 强一致做不到；用先写 DB 再发事件 + 对账 |

一句话：**能在数据库层面解决的问题不要上 Redis 锁；能用乐观锁不要用悲观锁；能用悲观锁不要用分布式锁。** 粒度越大越容易误伤。

## 一、事务

### 1.1 基础用法

所有事务都走 `tortoise.transactions.in_transaction`，**不要手工 `begin / commit`**：

```python
from tortoise.transactions import in_transaction
from app.utils import get_db_conn
from app.business.inventory.models import Product, Tag

async with in_transaction(get_db_conn(Product)):
    emp = await Product.create(...)
    await emp.tags.add(*tags)
```

`get_db_conn(Model)` 返回模型所在的连接名，必要（参见 [切换数据库](./database.md#业务模块独立数据库-进阶)）。**如果业务模块注册了独立数据库却忘了传连接名，事务会默默打在主库上导致部分写失败——这是最常见的坑。**

源码：[`app/core/crud.py`](../../../app/core/crud.py)。`CRUDBase.update` 内部已经自带事务，业务层一般只在**跨 controller 的组合写入**时显式用 `in_transaction`，例如 `create_product` 这类业务服务同时写 `User + Product + Tag` 关联表时。

### 1.2 嵌套与保存点

Tortoise 的 `in_transaction` 支持嵌套，内层会走 `SAVEPOINT`：

```python
async with in_transaction(conn) as outer:
    await Product.create(...)
    try:
        async with in_transaction(conn) as inner:
            await _send_welcome_mail(...)      # 若失败
    except MailError:
        pass                                   # inner 回滚，outer 继续
```

> 嵌套事务**不能**用来"临时提交"，它只是保存点。真正需要"先落库再做副作用"的时候，把事件 / HTTP 调用放到 `in_transaction` 块**外面**。

### 1.3 悲观锁 `select_for_update()`

在事务里读一行并独占它：

```python
async with in_transaction(get_db_conn(Account)) as conn:
    acc = await Account.select_for_update().using_db(conn).get(id=account_id)
    acc.balance -= amount
    await acc.save(update_fields=["balance"])
```

- 必须在事务里使用，否则 `SELECT ... FOR UPDATE` 会立刻释放锁。
- SQLite **不支持** `FOR UPDATE`（会被静默忽略）——生产环境如果依赖悲观锁，请切到 Postgres / MySQL。见 [切换数据库](./database.md)。
- 对同一行的并发请求会**排队**，吞吐随并发下降。高冲突场景优先考虑乐观锁。

### 1.4 只在事务里做"改数据库"

别在事务里调外部 HTTP、写 Redis、发消息队列，这些操作不会随事务回滚。**DB 和非 DB 的副作用必须分开**：

```python
async with in_transaction(get_db_conn(Order)) as conn:
    order = await Order.create(...)

# 事务提交之后再发事件
await emit("order.created", order_id=order.id)
```

## 二、状态机 + 乐观锁

[状态机](../develop/state-machine.md) 只校验 `from → to` 合法，**不防止两个请求同时把 `pending` 改成 `active`**。要做到"同时只有一次流转生效"，搭配**乐观锁**。

### 2.1 在模型上加 `version`

```python
# app/business/inventory/models.py
class Product(BaseModel):
    status = fields.CharField(max_length=20, default="pending")
    version = fields.IntField(default=0)                  # 乐观锁版本
    ...
```

### 2.2 带版本号的更新

关键点：**用 `QuerySet.filter(id=..., version=...).update(...)` 的返回值判断是否抢到**，返回 `0` 说明版本已被别人改过：

```python
from app.core.exceptions import BizError
from app.core.code import Code

async def try_transition(product: Product, to_state: str) -> None:
    # FSM 负责合法性
    if not PRODUCT_FSM.allowed(product.status, to_state):
        raise TransitionError(code=Code.STATE_TRANSITION_INVALID, msg=...)

    # 乐观锁: 同时匹配 id + version 才真正 update
    affected = await Product.filter(id=product.id, version=product.version).update(
        status=to_state,
        version=product.version + 1,
    )
    if affected == 0:
        raise BizError(code=Code.CONFLICT, msg="记录已被其他人修改, 请刷新后重试")
```

对 Tortoise 熟悉一点的读者会问：`obj.save(update_fields=[...])` 能做同样的事吗？不能——`save()` 只按主键更新，不会带上 `version` 条件。**必须走 `QuerySet.update` 才能拿到影响行数。**

### 2.3 自动重试（低冲突场景）

业务上能接受"重试几次直到成功"的话，写个小装饰器：

```python
import asyncio

async def retry_optimistic(fn, *, attempts: int = 3, backoff: float = 0.05):
    for i in range(attempts):
        try:
            return await fn()
        except BizError as e:
            if e.code != Code.CONFLICT or i == attempts - 1:
                raise
            await asyncio.sleep(backoff * (2 ** i))
```

重试只适合**读一次→改一次**的幂等操作。涉及外部副作用（扣费、发短信）时**不要**自动重试，把冲突原样抛给用户。

### 2.4 计数 / 余额的原子更新

单字段加减其实不需要 version，用 Tortoise 的 `F` 表达式直接在 DB 侧自增，天然是原子的：

```python
from tortoise.expressions import F

await Account.filter(id=account_id, balance__gte=amount).update(
    balance=F("balance") - amount,
)
```

- `balance__gte=amount` 把"余额够"做进 `WHERE`，`update()` 返回 `0` 就是"不够扣"。
- 比起 `obj.balance -= amount; await obj.save()`，省掉一次 round-trip 且不存在 lost-update。

## 三、Redis 分布式锁

什么时候才需要它？——**乐观锁和事务都解决不了的时候**：

- uvicorn 跑了 4 个 worker，定时任务需要"只在其中一个跑"
- 批量导入按钮被连点了，希望第二次点击直接返回"正在导入中"
- 一段逻辑要先查 Redis 再写 DB，数据库单行锁覆盖不到"查"那一步
- 幂等提交：在 DB 有唯一索引之前，先用锁顶住短时间的重复请求

项目推荐 [`redis-lock-py`](https://pypi.org/project/redis-lock-py/) ——基于 Redis + Lua，支持超时自动释放、阻塞等待，API 与异步 redis 客户端直连。

```bash
uv add redis-lock-py
```

### 3.1 服务层用法

在 service 层拿到 `AioRedis` 依赖后即可使用：

```python
# app/business/xxx/services.py
from redis_lock.asyncio import RedisLock
from redis.asyncio import Redis
from app.utils import Fail, Success


async def commit_once(redis: Redis, biz_key: str):
    # 加锁, 防止重复提交 / 并发跳过检测
    lock = RedisLock(
        redis,
        name=f"biz:commit:{biz_key}",      # 锁名按业务维度拼, 不要用全局单点
        blocking_timeout=1,                # 最多等 1s, 超时即视为系统繁忙
        expire_timeout=60,                 # 60s 自动释放, 兜底崩溃场景
    )
    if not await lock.acquire():
        return Fail(msg="系统繁忙, 请稍后再试")
    try:
        # ---- 临界区 ----
        # 在这里做"查 → 判断 → 写"的复合逻辑
        ...
        return Success(msg="提交成功")
    finally:
        await lock.release()
```

### 3.2 在 API 层拿到 Redis

路由层直接注入 `AioRedis`，服务层接收参数：

```python
# app/business/xxx/api/manage.py
from app.utils import AioRedis
from app.business.xxx.services import commit_once


@router.post("/pxdp/commit")
async def _(redis: AioRedis, body: CommitIn):
    return await commit_once(redis, biz_key=body.order_no)
```

### 3.3 参数怎么选

| 参数 | 含义 | 选型建议 |
|---|---|---|
| `name` | Redis key | 按**最细的业务维度**拼，例如 `order:pay:{order_id}`；粒度越大并发度越低 |
| `blocking_timeout` | 拿不到锁时最多等几秒 | 接口类建议 `0~1`（拿不到立刻返回）；后台任务可以更长 |
| `expire_timeout` | 锁最长持有时间 | **比临界区最坏耗时再长 2 倍**。太短会被别人抢走，太长会放大故障窗口 |

### 3.4 常见陷阱

1. **锁名拼错 = 串行化失败**。统一一个小工具函数生成 key，不要在多处手拼字符串。
2. **`expire_timeout` 设小了**：临界区还没跑完锁就过期，别人进来，你以为自己还持有锁就去 `release()` ——会误删别人的锁。`redis-lock-py` 内部用 token 防误删，但仍应给够余量。
3. **不要在锁里等外部 HTTP**：超时策略不明确的 IO 会把锁的持有时间拉爆，阻塞后续所有请求。能异步推出去就异步推。
4. **锁不是事务**。锁范围内的 DB 写入**仍然需要自己开事务**——锁只保证"没人和我抢"，不保证"我一起写的两张表要么都成要么都回滚"。
5. **单 worker 场景别上锁**：开发时 `python run.py` 是单进程，加了锁也看不出效果；上了 docker 多副本才真正有意义。

## 四、httpx 并发请求

接口里调外部系统（第三方 API、内部微服务、OSS、OAuth 回调）用的是 `httpx.AsyncClient`。真正影响性能和稳定性的是两件事：**连接复用**和**并发扇出的收敛**。

### 4.1 复用一个共享 `AsyncClient`

**不要**每个请求 `async with httpx.AsyncClient() as client:` ——那是教程写法，每次都走完整的 TLS 握手和连接建立，量大时 CPU 全耗在握手上。生产做法是在 lifespan 里启动一个共享 client，挂到 `app.state`，用 FastAPI 依赖注入：

```python
# app/core/http.py
from typing import Annotated
import httpx
from fastapi import Depends, Request


async def init_http() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(connect=3.0, read=10.0, write=10.0, pool=5.0),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        headers={"User-Agent": "fast-soy-admin/1.0"},
    )


async def close_http(client: httpx.AsyncClient) -> None:
    await client.aclose()


def get_http(request: Request) -> httpx.AsyncClient:
    return request.app.state.http  # type: ignore[no-any-return]


HttpClient = Annotated[httpx.AsyncClient, Depends(get_http)]
```

在 lifespan 里注册（和 Redis 同一处）：

```python
# app/__init__.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await init_redis()
    app.state.http = await init_http()
    yield
    await close_http(app.state.http)
    await close_redis(app.state.redis)
```

用法和 `AioRedis` 完全一致：

```python
from app.utils import HttpClient

@router.get("/gitee/user")
async def _(http: HttpClient, token: str):
    r = await http.get("https://gitee.com/api/v5/user", params={"access_token": token})
    r.raise_for_status()
    return Success(data=r.json())
```

### 4.2 超时必须给

没有配 timeout 的 httpx 请求默认 **永远等**——一个外部服务慢几秒，worker 就会被打满。用 `httpx.Timeout` 把四个维度分别设死：

| 项 | 含义 | 建议值 |
|---|---|---|
| `connect` | 建连接 | `2~3s` |
| `read` | 读响应体 | 按对端 SLA，通常 `5~10s` |
| `write` | 写请求体 | 上传大文件时加大 |
| `pool` | 从连接池拿连接 | `5s`，避免连接池耗尽时无限排队 |

单次请求可以覆盖全局超时：

```python
r = await http.get(url, timeout=30.0)         # 这一次允许慢
```

### 4.3 并发扇出: `asyncio.gather` + `Semaphore`

一次接口要拉 N 个外部资源时，**不要串行 `for`**——那是纯粹的等待。但 `gather(*tasks)` 也不能无脑展开，否则几千个任务同时打到对端会直接被限流。中间加一个 `Semaphore` 做自身并发限流：

```python
import asyncio
import httpx


async def fetch_users(http: httpx.AsyncClient, ids: list[int]) -> list[dict]:
    sem = asyncio.Semaphore(10)                   # 同时最多 10 个在飞

    async def _one(uid: int) -> dict | None:
        async with sem:
            try:
                r = await http.get(f"/users/{uid}")
                r.raise_for_status()
                return r.json()
            except httpx.HTTPError:
                return None                       # 单点失败不炸整批

    results = await asyncio.gather(*[_one(i) for i in ids])
    return [x for x in results if x is not None]
```

- `return_exceptions=True` vs 在协程内 `try/except`：前者把异常揉进结果列表，需要调用方再过滤；后者把成败判断下沉到协程内部，调用方拿到的就是"干净的结果 + None"。两种都行，**在一个项目里选一种**。
- `Semaphore(N)` 的 `N` 一般等于对端允许的 QPS 或者连接池 `max_connections` 的 30%——比对端承受极限小一点，给重试留空间。

### 4.4 失败重试

httpx 本身没内置重试，用 [`tenacity`](https://tenacity.readthedocs.io/) 装饰函数，仅对**可重试**的错误类型重试：

```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=0.2, max=2.0),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
)
async def _call(http: httpx.AsyncClient, url: str):
    r = await http.get(url)
    r.raise_for_status()
    return r.json()
```

- **不要对 `4xx` 重试**——参数错了重 N 次还是错。
- **幂等才重试**。POST 创建订单这种场景重试要配合 `Idempotency-Key` 请求头。

## 五、接口中的并发请求 + 事务

> **一句话总结：事务里只做 DB，HTTP 调用放到事务外。**

这是项目里最容易被写错的一类代码。重复讲一遍核心原因：

- 事务一旦 `rollback`，**已经发出去的 HTTP 请求 / Redis 写 / 消息并不会被撤销**。
- 事务一旦进入，连接就被这个协程独占；如果你在事务里 `await` 一个慢 HTTP，连接池会被快速耗尽。

### 5.1 错误示范

```python
# ❌ 反面教材: HTTP 调用穿插在事务里
async with in_transaction(get_db_conn(Order)):
    order = await Order.create(...)
    await http.post("https://payment/charge", json={...})   # 如果下面 raise, 钱已经扣了
    await Ledger.create(order_id=order.id, ...)
```

### 5.2 正确模式: "先查外部 → 再开事务写 DB"

大多数"查询聚合后入库"的场景，把 HTTP fan-out 做完再进入事务：

```python
async def sync_products_from_hrp(http: HttpClient, company_id: int):
    # 1) 事务外: 并发拉取外部数据
    sem = asyncio.Semaphore(10)
    async def _fetch(page: int):
        async with sem:
            r = await http.get(f"/inventory/products", params={"company": company_id, "page": page})
            r.raise_for_status()
            return r.json()["rows"]

    batches = await asyncio.gather(*[_fetch(p) for p in range(1, 11)])
    rows = [row for batch in batches for row in batch]

    # 2) 事务内: 只做 DB 写
    async with in_transaction(get_db_conn(Product)):
        for row in rows:
            await Product.update_or_create(
                defaults=row,
                external_id=row["id"],
            )
    return Success(data={"count": len(rows)})
```

### 5.3 正确模式: "先落库占位 → 再调外部 → 再回写结果"

当外部调用本身是副作用（扣费、下单）时，按 **pending → external call → settle** 三步走：

```python
async def pay_order(http: HttpClient, order_id: int, amount: int):
    # 1) 开一个 pending 订单行, 保证即使后面崩掉也能 reconcile
    async with in_transaction(get_db_conn(Order)) as conn:
        order = await Order.create(id=order_id, status="pending", amount=amount, using_db=conn)

    # 2) 事务外: 调外部支付. 失败就抛, 让对账兜底
    try:
        r = await http.post("https://payment/charge", json={"order_id": order_id, "amount": amount})
        r.raise_for_status()
        txn_id = r.json()["txnId"]
    except httpx.HTTPError:
        # 不要把 order 删掉 — 留着对账任务处理
        raise

    # 3) 再开一个事务把结果回写
    async with in_transaction(get_db_conn(Order)):
        await Order.filter(id=order_id, status="pending").update(status="paid", txn_id=txn_id)
```

这个模式需要配一个**对账任务**（cron）扫 `status="pending"` 且超时的记录，主动去查外部真实状态。正是[事件总线](../develop/events.md)里强调的"先写 DB 再发副作用"的延伸。

### 5.4 并发写：同一请求内多张表

同一请求内要写多张表时，**不要**对这些 DB 操作用 `asyncio.gather` "提速"：

```python
# ❌ 反面教材: 同一连接上的事务里并发 await 会串
async with in_transaction(get_db_conn(Product)):
    await asyncio.gather(
        Product.create(...),
        Profile.create(...),
        Audit.create(...),
    )
```

单个事务持有的是**一个** DB 连接，`gather` 里的 await 在这条连接上只能排队执行，不会真正并行，反而让错误处理更难——任何一个失败，其它几个已经写了一半。老实一条一条 `await`，让事务语义清楚。

需要"并行写多张表"的真正手段是**拆到多个独立事务 + 事件总线**：

```python
async with in_transaction(get_db_conn(Product)):
    emp = await Product.create(...)

# 事务提交后再并发扇出
await asyncio.gather(
    emit("product.created", product_id=emp.id),     # 订阅方在各自事务里写 Profile / Audit
    _push_welcome_mail(http, emp.email),
)
```

### 5.5 接口层的取舍速查

| 场景 | 建议 |
|---|---|
| 只读：并发拉多个外部源拼装返回 | `Semaphore` + `gather`，无事务 |
| 读外部 → 写内部 | 先 HTTP 扇出，拿到所有数据再开 `in_transaction` |
| 写外部 → 写内部 | pending → HTTP → settle 三步，配对账兜底 |
| 写内部 → 写外部（外部失败允许回滚） | 外部调用放 `try`，失败时手动反向写 DB（补偿），**不要**期待事务帮你回滚 |
| 同一请求要写多张表 | 一个事务里顺序 `await`，不要 `gather` |
| 写完内部想并发触发多个副作用 | 事务**外**用 `gather(emit(...), http.post(...))` |

## 六、组合使用

真实业务里三把武器常常同时出现。以"批量导入商品"为例：

```python
async def import_products(redis: Redis, file_id: str, rows: list[ProductCreate]):
    # 1) 分布式锁: 同一个文件只允许一个 worker 在跑
    lock = RedisLock(redis, name=f"inventory:import:{file_id}", blocking_timeout=0, expire_timeout=300)
    if not await lock.acquire():
        return Fail(msg="该文件正在导入中")
    try:
        # 2) 事务: 批量写入要么全部成功要么整体回滚
        async with in_transaction(get_db_conn(Product)):
            for row in rows:
                emp = await Product.create(**row.model_dump())
                # 3) 乐观锁: 对同一个团队的 head_count 做原子 +1
                await Team.filter(id=row.team_id).update(
                    head_count=F("head_count") + 1,
                )
        return Success(msg="导入成功")
    finally:
        await lock.release()
```

层次分工清楚：

- **分布式锁** 防跨 worker 重复任务
- **事务** 管本次 DB 写入的原子性
- **乐观锁（F 表达式）** 管单字段的并发累加

## 七、测试这些并发路径

### 乐观锁

用 `asyncio.gather` 并发触发同一条记录的流转，断言**只有一次成功**：

```python
async def test_transition_is_single_winner():
    emp = await Product.create(status="pending", version=0, ...)
    results = await asyncio.gather(
        try_transition(emp, "onboarding"),
        try_transition(emp, "onboarding"),
        return_exceptions=True,
    )
    wins = [r for r in results if not isinstance(r, Exception)]
    assert len(wins) == 1
```

### 分布式锁

跑一个 `fakeredis`（或本地 Redis）+ 两个并发协程，第二个应该立即拿不到锁：

```python
async def test_lock_is_exclusive(redis):
    lock_a = RedisLock(redis, name="t", blocking_timeout=0, expire_timeout=5)
    lock_b = RedisLock(redis, name="t", blocking_timeout=0, expire_timeout=5)
    assert await lock_a.acquire() is True
    assert await lock_b.acquire() is False
    await lock_a.release()
```

## 相关

- [切换数据库](./database.md) — 业务模块独立库场景下 `get_db_conn` 的用法
- [CRUDBase](../develop/crud.md) — `CRUDBase.update` 内部已经带事务
- [状态机](../develop/state-machine.md) — FSM 只管合法性，想防并发请叠乐观锁
- [事件总线](../develop/events.md) — 事务提交后再发事件的推荐姿势
- [Tortoise 事务官方文档](https://tortoise.github.io/query.html#transactions)
- [redis-lock-py 仓库](https://github.com/miintto/redis-lock)
