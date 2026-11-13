# 工票工时管理（work_ticket_management）

围绕现有 `order_management.Order` 的月度工票、人员分配、工时登记与月度核对模块。**不复制订单表，不修改订单唯一性和业务语义**；订单只通过外键和快照字段被引用。

## 数据模型

表前缀 `biz_work_ticket_management_`，共 10 张表。

| 模型 | 表 | 职责 | 关键约束 |
| --- | --- | --- | --- |
| `ProductionUnit` | `production_unit` | 生产单位主数据 | `code` 唯一 |
| `Worker` | `worker` | 生产人员，可关联默认生产单位 | `worker_no` 唯一；单位删除 `SET NULL` |
| `OrderUnitMapping` | `order_unit_mapping` | 订单与生产单位的多对多映射 | `(order, production_unit)` 唯一 |
| `WorkMonth` | `work_month` | 月度任务，状态机载体 | `(year_month, production_unit)` 唯一；`revision` 乐观锁 |
| `MonthlyImportBatch` | `monthly_import_batch` | 每次计划/实际清单导入批次 | `content_hash` 用于幂等提示；可作废 |
| `MonthlyImportRow` | `monthly_import_row` | 原始导入行，保留原始值与匹配结果 | `(batch, row_number)` 唯一；重复行指向 `duplicate_of_row` |
| `WorkTicket` | `work_ticket` | 工票台账，保存订单快照和工票码 | `(work_month, ticket_code_key)` 唯一；`revision` 乐观锁 |
| `WorkTicketAssignment` | `work_ticket_assignment` | 工票与人员的一对多分配 | `(ticket, worker)` 唯一 |
| `WorkTimeEntry` | `work_time_entry` | 某工票某人员某日期的工时 | `(assignment, work_date)` 唯一；金额为 `Decimal(5,2)` |
| `WorkMonthStatusLog` | `work_month_status_log` | 月度状态迁移审计 | 记录前后状态、动作、原因和统计快照 |

关系主线：`WorkMonth → WorkTicket → WorkTicketAssignment → WorkTimeEntry`。生产单位只挂在 `WorkMonth` 上，工票通过所属月份间接归属单位；工时只通过分配关联工票和人员，避免多路径重复事实。

`WorkTicket` 快照字段：`order_no_snapshot`、`part_no_snapshot`、`name_snapshot`；`ticket_code_key` 为去空白转大写后的比较键，展示值 `ticket_code` 保留原始大小写和前导零。

## 业务规则

### 订单匹配

- 仅在同一生产单位的订单范围内自动匹配。
- 只做项目号**精确**匹配（先区分大小写，再补充 `iexact` 精确匹配）；禁止模糊/包含匹配。
- 命中唯一且该订单已确认属于当前单位 → `matched`（`match_source=auto`）。
- 命中多个当前单位订单 → `ambiguous`，必须人工选择。
- 命中订单但未映射当前单位 → `unassigned`；只映射到其他单位 → `other_unit`。
- 查无订单 → `missing`；项目号为空或超长 → `invalid`。
- 自动匹配**从不创建订单**，也不修改订单字段。
- 人工确认写入 `OrderUnitMapping`，并记录 `match_source=manual`。

### 工票码

- `rules.py` 中的 `TicketCodeRule` 必须携带真实样本，注册时 `validate_samples()` 失败即拒绝加载。
- 当前 `RULE_REGISTRY` 为空：**在拿到用户确认的样本和规则前，不生成自动工票码**，只能手工录入或粘贴。
- 粘贴/OCR 候选会保留重复项，以便核对重复工票码。
- OCR 只做通用文本识别和候选提取，业务侧负责数字纠错（`O→0`、`I/l→1`、`S→5`）和人工确认；不持久化图片。
- 批量生成在事务内按 `(work_month, ticket_code_key)` 唯一约束保证幂等；重复码返回冲突而不是静默覆盖。

### 月度状态机

```
draft → in_progress → verified → closed
                         ↑          │
                         └── reopen ┘
```

- `open` 创建或复用 `draft` 月份；首次导入/工票操作进入 `in_progress`。
- `verify` 要求无 blocking 核对项；`close` 允许在确认警告后关闭。
- `closed` 后禁止导入、建票、分配、登记/修改工时；`reopen` 必须填写原因并写状态日志。
- 状态变更通过行锁 + `revision` CAS，防止并发覆盖。

### 工时

- 工时以「工票 × 人员 × 日期」唯一，通过分配记录归属人员。
- `accounting_month` 仅用于跨月归属；为空时按工票所属月份统计。
- 工时必须在所属月份处于可编辑状态时写入；关闭月份只读。
- 矩阵批量保存按工票 `revision` 校验；空值表示删除，已存在记录需显式提交删除。

### 月度核对

核对项按需计算，不落冗余核对表：

- `ambiguous`：多条候选订单；
- `unassigned`：订单未映射当前单位；
- `no_time`：已分配但无工时；
- `ticket_without_order` / `actual_without_ticket` / `plan_missing_actual` / `actual_missing_plan`；
- `duplicate_code`：同月重复工票码；
- `cross_month_duplicate`：跨月重复工票码。

每条核对项给出稳定业务键，可执行 `ignore`（写处理状态和原因）或修正源数据。核对汇总区分 blocking 与 warning；blocking 阻止 `verify`。

## API

基础路径由框架挂载为 `/api/v1/business/work_ticket_management`（以实际 OpenAPI 为准），权限使用 `require_buttons`。

| 分组 | 主要端点 |
| --- | --- |
| 主数据 | `GET /options/production_units`、`GET /options/workers`、`POST /orders/candidates` |
| 月度 | `POST /work_months/open`、`GET /work_months/{id}/summary`、`/status-logs`、`POST /verify`、`/close`、`/reopen`、`/export` |
| 导入 | `POST /monthly_import_batches/preview`、`/commit`、`/manual`、`/{id}/void`、`POST /monthly_import_rows/search`、`PATCH /{id}`、`POST /{id}/match`、`/{id}/ignore`、`/batch-match` |
| 工票 | `POST /work_tickets/search`、`GET /{id}`、`POST /`、`PATCH /{id}`、`/{id}/void`、`/assign`、`/unassign`、`/batch-assign`、`/reconcile`、`/export` |
| 工票码 | `POST /work_tickets/code-preview`、`/code-confirm`、`/codes/import`、`/code-lookup`、`/ocr-candidates` |
| 工时 | `POST /work_time_entries/matrix`、`/search`、`/batch-save`、`PATCH /{id}`、`DELETE /{id}`、`/export` |
| 核对 | `GET /work_months/{id}/reconciliation/summary`、`POST /reconciliation/search` |
| 报表 | `POST /reports/monthly`、`/worker-hours`、`/worker-dates`、`/ticket-status`、`/anomalies`、`/export` |

简单主数据仍使用生成式 `CRUDRouter`；聚合根（工票、导入、工时、月度）使用显式路由 + `services/`，`controllers` 不依赖 FastAPI。

## 导入与导出

- Excel 导入先预览再提交；预览返回逐行原始值、规范化值、匹配状态和错误，不写库。
- 保留前导零；项目号规范化只做 NFKC、去零宽字符、空白折叠和大写。
- 公式注入防护由 `parse_excel` / `write_excel_sheets` 统一处理，导出单元格不会被当作公式执行。
- 单次导入行数、导出上限由服务层校验并显式报错，不静默截断。
- 月度工作簿包含 4 个工作表：工票汇总、工时明细、人员统计、异常核对。

## 权限

按钮码集中在 `constants.py`，种子在 `init_data.py`。菜单包含：月度工作台、工票台账、工时登记、月度核对、统计报表、人员与生产单位。业务角色显式声明 `data_scope`；写接口均挂按钮权限依赖。

## 尚未由代码决定、需要人工确认的规则

1. **工票码生成规则**：需要用户提供真实订单号 → 工票码样本。未确认前，`RULE_REGISTRY` 保持为空，只能手工/粘贴/OCR 录码。
2. **迁移执行**：`migrations/app_system/0008_auto_20261113_2208.py` 已生成并审查，尚未 apply；必须经用户确认后再执行 `just migrate`。
3. **跨月工时口径**：默认按工票所属月份，`accounting_month` 显式覆盖；需财务确认是否所有跨月场景都归入实际生产月。
4. **导入模板列名**：当前解析器接受宽松列别名；正式模板列名需以用户实际清单确认后固化。
