# HR Business Module Example

The HR module demonstrates RBAC, data scopes, a state machine, and system-user integration in a business module. The current design is centered on the employee lifecycle:

- Employee states: `probation`, `active`, `resigned`
- Valid transitions: `probation -> active`, `probation -> resigned`, `active -> resigned`, `resigned -> probation`
- New onboarding creates a `probation` employee
- Resignation disables the bound system user and invalidates issued tokens
- Rehire enables the bound system user again and moves the employee back to `probation`

This example does not include migration guidance for the old enum values. In development, reset the database after changing the model.

## Data Model

Core models live in `app/business/hr/models.py`:

- `Department`: department tree; `manager_id` stores the manager employee ID
- `Employee`: employee profile bound to one system user and one department
- `Tag`: employee tags
- `EmployeeStatusLog`: status transition log

`Employee.status` is the HR lifecycle state. It is not the generic `StatusType.enable / disable`. Employees in `probation` or `active` should have enabled system users; resignation sets the bound system user to disabled.

## Roles

| Role | Data scope | Menus | Responsibility |
| --- | --- | --- | --- |
| `R_HR_MANAGER` | `all` | My Workspace, Departments, Employees, Tags | HR manager with full department, manager, employee status, and tag capabilities |
| `R_HR_SPECIALIST` | `all` | My Workspace, Employees | HR specialist for onboarding, rehire, basic profile editing, and department transfer |
| `R_DEPT_MGR` | `scope` | My Workspace, My Team | Department manager, limited to their own department |
| `R_EMPLOYEE` | `self` | My Workspace | Employee self-service |

`R_HR_MANAGER` does not automatically include My Team. If an HR manager also manages a department, grant `R_DEPT_MGR` as well. Demo user `hanmei` intentionally has `R_HR_MANAGER + R_DEPT_MGR`.

## Buttons

| Button | Meaning | Default roles |
| --- | --- | --- |
| `B_HR_MY_TAG_EDIT` | Edit own tags | All HR roles and employees |
| `B_HR_MY_AVATAR_EDIT` | Upload own avatar | All HR roles and employees |
| `B_HR_TEAM_TAG_EDIT` | Department manager edits team tags | Department manager |
| `B_HR_TEAM_REGULARIZE` | Department manager regularizes a team member | Department manager |
| `B_HR_DEPT_CREATE` | Create department | HR manager |
| `B_HR_DEPT_EDIT` | Edit department | HR manager |
| `B_HR_DEPT_DELETE` | Delete department | HR manager |
| `B_HR_DEPT_MANAGER` | Appoint/remove department manager | HR manager |
| `B_HR_EMP_ONBOARD` | Onboard employee | HR manager, HR specialist |
| `B_HR_EMP_EDIT` | Edit employee basic fields | HR manager, HR specialist |
| `B_HR_EMP_TRANSFER` | Transfer employee department | HR manager, HR specialist |
| `B_HR_EMP_TAG_EDIT` | HR edits any employee tags | HR manager |
| `B_HR_EMP_REGULARIZE` | HR regularizes employee | HR manager |
| `B_HR_EMP_RESIGN` | Resign employee | HR manager |
| `B_HR_EMP_REHIRE` | Rehire employee | HR manager, HR specialist |
| `B_HR_TAG_CREATE` / `B_HR_TAG_EDIT` / `B_HR_TAG_DELETE` | Tag management | HR manager |

## Main APIs

Management APIs live in `app/business/hr/api/manage.py`:

- `POST /employees`: onboard employee, create a system user, and bind `R_EMPLOYEE`
- `PATCH /employees/{id}`: edit basic fields
- `PATCH /employees/{id}/department`: transfer department
- `PATCH /employees/{id}/tags`: HR edits tags
- `POST /employees/{id}/regularize`: regularize
- `POST /employees/{id}/resign`: resign; `remark` is required
- `POST /employees/{id}/rehire`: rehire
- `GET /employees/{id}/status-logs`: view transition logs
- `PATCH /departments/{id}/manager`: appoint or remove department manager

Team APIs live in `app/business/hr/api/team.py`:

- `POST /team/employees/search`: department manager searches their own team; resigned employees are hidden by default
- `PATCH /team/employees/{id}/tags`: edit a team member's tags
- `POST /team/employees/{id}/regularize`: regularize a team member; managers cannot regularize themselves
- `GET /team/stats`: department overview

Personal APIs live in `app/business/hr/api/my.py`:

- `GET /my/profile`: my profile
- `PATCH /my/profile`: update own phone and email
- `PATCH /my/tags`: update own tags
- `GET /my/department`: view same-department `probation` and `active` colleagues
- `POST /my/avatar`: upload own avatar

## State Machine And Error Codes

Employee status is driven by the generic `StateMachine`, while the HR module explicitly selects its own error code:

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

Calling an action that is invalid for the current state therefore returns `4007` (`HR_INVALID_TRANSITION`). Validation fails before the employee is changed or saved and before an `EmployeeStatusLog` is created.

## Onboarding And Rehire

Onboarding is handled by HR managers or HR specialists:

- Required: `userName`, `name`, `departmentId`
- Optional: `email`, `phone`
- Creates a system user
- Grants `R_EMPLOYEE`
- Creates the employee as `probation`

Rehire is a separate action:

- Only allowed from `resigned`
- Requires an existing bound system user
- Moves the employee to `probation`
- Enables the system user

## Resignation

Only HR managers can resign employees:

- `remark` is required
- Both `probation` and `active` employees can resign
- Employee status becomes `resigned`
- Bound system user becomes disabled
- `token_version` is incremented, invalidating existing access and refresh tokens
- User roles are retained, including `R_EMPLOYEE`

If the employee manages a department, the request must provide a replacement manager. The replacement must be a `probation` or `active` employee in the same department.

## Department Manager Management

HR managers appoint department managers from Department Management:

- New departments do not require a manager
- The manager must belong to the department
- The manager must be `probation` or `active`
- Appointment grants `R_DEPT_MGR`
- Removing or replacing a manager revokes `R_DEPT_MGR` from the old manager if they no longer manage any department

HR managers and HR specialists may transfer employees between departments. If the employee currently manages a department, the request must provide a replacement manager for the old department first.

## Data Scope

- HR manager and HR specialist: `all`, can view all employees
- Department manager: `scope`, limited to own department
- Employee: `self`, limited to personal workspace data

Team lists hide `resigned` by default, but can explicitly filter by that status. My Department always returns only `probation` and `active` colleagues.

## Demo Accounts

| User | Department | Roles |
| --- | --- | --- |
| `hanmei` | HR | `R_HR_MANAGER + R_DEPT_MGR` |
| `liuqing` | HR | `R_HR_SPECIALIST` |
| `zhouhang` / `linyan` / `songyu` / `qinfeng` | Business departments | `R_DEPT_MGR` |
| Other employees | Business departments | `R_EMPLOYEE` |

`hanmei` has both identities, so she can access employee, department, and tag management as HR manager, and My Team for the HR department as department manager.
