# HR 业务模块示例

HR 模块演示一套带 RBAC、数据范围、状态机和系统用户联动的业务模块。当前版本以“员工生命周期”为核心：

- 员工状态：`probation` 待转正、`active` 在职、`resigned` 已离职
- 合法流转：`probation -> active`、`probation -> resigned`、`active -> resigned`、`resigned -> probation`
- 新入职默认进入 `probation`
- 离职会禁用绑定系统用户并失效已签发 token
- 返聘会重新启用绑定系统用户，并回到 `probation`

本示例不提供历史迁移说明；调整字段或枚举后，开发环境可直接重置数据库。

## 数据模型

核心模型位于 `app/business/hr/models.py`：

- `Department`：部门树，`manager_id` 指向部门主管员工 ID
- `Employee`：员工档案，绑定系统用户和部门，可关联多个标签
- `Tag`：员工标签
- `EmployeeStatusLog`：员工状态流转日志

`Employee.status` 是业务生命周期状态，不是系统通用 `StatusType.enable / disable`。只有 `probation` 和 `active` 员工应保持系统用户启用；`resigned` 员工离职动作会禁用系统用户。

## 角色设计

| 角色 | 数据范围 | 菜单 | 职责 |
| --- | --- | --- | --- |
| `R_HR_MANAGER` | `all` | 我的工作台、部门管理、员工管理、标签管理 | HR 主管，负责部门、主管任命、员工状态、标签等全量维护 |
| `R_HR_SPECIALIST` | `all` | 我的工作台、员工管理 | 人事专员，办理入职、返聘、基础资料和部门调整 |
| `R_DEPT_MGR` | `scope` | 我的工作台、我的团队 | 部门主管，只管理本部门团队 |
| `R_EMPLOYEE` | `self` | 我的工作台 | 普通员工，只维护自己的资料/标签并查看同部门同事 |

`R_HR_MANAGER` 不自动拥有“我的团队”。如果 HR 主管同时也是某个部门主管，需要同时授予 `R_DEPT_MGR`。演示数据中的 `hanmei` 即为 `R_HR_MANAGER + R_DEPT_MGR`。

## 按钮权限

| 按钮 | 说明 | 默认角色 |
| --- | --- | --- |
| `B_HR_MY_TAG_EDIT` | 编辑自己的标签 | HR 主管、人事专员、部门主管、员工 |
| `B_HR_MY_AVATAR_EDIT` | 上传自己的头像 | HR 主管、人事专员、部门主管、员工 |
| `B_HR_TEAM_TAG_EDIT` | 部门主管编辑本部门员工标签 | 部门主管 |
| `B_HR_TEAM_REGULARIZE` | 部门主管办理本部门员工转正 | 部门主管 |
| `B_HR_DEPT_CREATE` | 创建部门 | HR 主管 |
| `B_HR_DEPT_EDIT` | 编辑部门 | HR 主管 |
| `B_HR_DEPT_DELETE` | 删除部门 | HR 主管 |
| `B_HR_DEPT_MANAGER` | 任命/移除部门主管 | HR 主管 |
| `B_HR_EMP_ONBOARD` | 办理入职 | HR 主管、人事专员 |
| `B_HR_EMP_EDIT` | 编辑员工基础资料 | HR 主管、人事专员 |
| `B_HR_EMP_TRANSFER` | 调整员工部门 | HR 主管、人事专员 |
| `B_HR_EMP_TAG_EDIT` | HR 编辑任意员工标签 | HR 主管 |
| `B_HR_EMP_REGULARIZE` | HR 办理员工转正 | HR 主管 |
| `B_HR_EMP_RESIGN` | 办理离职 | HR 主管 |
| `B_HR_EMP_REHIRE` | 办理返聘 | HR 主管、人事专员 |
| `B_HR_TAG_CREATE` / `B_HR_TAG_EDIT` / `B_HR_TAG_DELETE` | 标签管理 | HR 主管 |

## 主要接口

管理端接口位于 `app/business/hr/api/manage.py`：

- `POST /employees`：办理入职，创建系统用户并绑定 `R_EMPLOYEE`
- `PATCH /employees/{id}`：编辑基础资料
- `PATCH /employees/{id}/department`：调整部门
- `PATCH /employees/{id}/tags`：HR 编辑标签
- `POST /employees/{id}/regularize`：办理转正
- `POST /employees/{id}/resign`：办理离职，备注必填
- `POST /employees/{id}/rehire`：办理返聘
- `GET /employees/{id}/status-logs`：查看状态日志
- `PATCH /departments/{id}/manager`：任命或移除部门主管

团队接口位于 `app/business/hr/api/team.py`：

- `POST /team/employees/search`：部门主管查看本部门员工，默认隐藏离职员工
- `PATCH /team/employees/{id}/tags`：编辑本部门员工标签
- `POST /team/employees/{id}/regularize`：办理本部门员工转正，不能给自己转正
- `GET /team/stats`：本部门概览

个人接口位于 `app/business/hr/api/my.py`：

- `GET /my/profile`：我的资料
- `PATCH /my/profile`：维护自己的电话和邮箱
- `PATCH /my/tags`：维护自己的标签
- `GET /my/department`：查看同部门待转正/在职同事
- `POST /my/avatar`：上传自己的头像

## 状态机与错误码

员工状态由通用 `StateMachine` 驱动，但 HR 模块显式配置自己的错误码：

```python
EMPLOYEE_FSM = StateMachine(
    transitions={
        "probation": ["active", "resigned"],
        "active": ["resigned"],
        "resigned": ["probation"],
    },
    error_code=Code.HR_INVALID_TRANSITION,
)
```

因此，对当前状态执行不允许的动作会返回 `4007`（`HR_INVALID_TRANSITION`）。状态机在校验失败后立即抛错，不会修改员工状态、保存员工或新增 `EmployeeStatusLog`。

## 入职与返聘

首次入职由 HR 主管或人事专员办理：

- 必填：`userName`、`name`、`departmentId`
- 可空：`email`、`phone`
- 自动创建系统用户
- 自动绑定 `R_EMPLOYEE`
- 员工状态为 `probation`

返聘是独立动作：

- 只允许对 `resigned` 员工执行
- 必须已绑定系统用户
- 执行后员工回到 `probation`
- 系统用户恢复启用

## 离职

离职只能由 HR 主管办理：

- `remark` 必填
- `probation` 和 `active` 都可以离职
- 离职后员工状态为 `resigned`
- 绑定系统用户设置为 `disable`
- 递增 `token_version`，使现有 access/refresh token 失效
- 保留用户角色，不清理 `R_EMPLOYEE`

如果离职员工是部门主管，必须先指定接任主管；接任主管必须是同部门 `probation` 或 `active` 员工。

## 部门主管管理

部门主管由 HR 主管在部门管理中任命：

- 新部门不要求立即指定主管
- 主管必须属于该部门
- 主管状态必须是 `probation` 或 `active`
- 任命后自动授予 `R_DEPT_MGR`
- 移除或替换主管后，如果旧主管不再管理任何部门，自动回收 `R_DEPT_MGR`

HR 主管或人事专员可以调整员工部门。如果被调整员工当前管理部门，必须先指定原部门接任主管。

## 数据范围

- HR 主管、人事专员：`all`，可查看全公司员工
- 部门主管：`scope`，只看自己部门
- 普通员工：`self`，只看自己和个人工作台允许的数据

团队列表默认隐藏 `resigned`，但可以显式按状态筛选离职员工。个人“同部门同事”始终只返回 `probation` 和 `active`。

## 演示账号

| 用户 | 部门 | 角色 |
| --- | --- | --- |
| `hanmei` | 人事部 | `R_HR_MANAGER + R_DEPT_MGR` |
| `liuqing` | 人事部 | `R_HR_SPECIALIST` |
| `zhouhang` / `linyan` / `songyu` / `qinfeng` | 各业务部门 | `R_DEPT_MGR` |
| 其他员工 | 各业务部门 | `R_EMPLOYEE` |

`hanmei` 同时拥有 HR 主管和部门主管身份，因此既能进入员工/部门/标签管理，也能进入“我的团队”查看人事部团队。
