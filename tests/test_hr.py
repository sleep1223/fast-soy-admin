import pytest
from httpx import AsyncClient

from app.core.code import Code
from app.core.data_scope import build_scope_filter
from app.core.sqids import encode_id

pytestmark = pytest.mark.asyncio(loop_scope="session")

PREFIX = "/api/v1/business/hr"


async def test_hr_manifest_uses_business_slots():
    from app.business.hr.init_data import INIT_DATA
    from app.core.autodiscover import discover_business_data_policies, discover_business_modules

    [module] = [item for item in discover_business_modules() if item.name == "hr"]

    assert module.source == "manifest"
    assert len(module.routers) == 4
    assert len(module.events) == 4
    assert {policy.name for policy in discover_business_data_policies()} >= {"hr.employees.read", "hr.employees.update"}

    role_api_refs = [api for role in INIT_DATA["roles"] for api in role["apis"]]
    assert role_api_refs
    assert all(isinstance(api, str) and api.startswith("hr.") for api in role_api_refs)


# ===================== Department CRUD =====================


class TestDepartmentCRUD:
    async def test_create_department(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            f"{PREFIX}/departments",
            json={"name": "Marketing", "code": "MKT", "description": "Marketing Dept"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        assert "createdId" in data["data"]

    async def test_list_departments(self, auth_client: AsyncClient, hr_data):
        resp = await auth_client.post(
            f"{PREFIX}/departments/search",
            json={"current": 1, "size": 10},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        assert len(data["data"]["records"]) >= 1

    async def test_list_departments_filter_by_name(self, auth_client: AsyncClient, hr_data):
        resp = await auth_client.post(
            f"{PREFIX}/departments/search",
            json={"current": 1, "size": 10, "name": "Engineering"},
        )
        assert resp.status_code == 200
        records = resp.json()["data"]["records"]
        assert any(r["name"] == "Engineering" for r in records)

    async def test_update_department(self, auth_client: AsyncClient, hr_data):
        dept_id = encode_id(hr_data["department"].id)
        resp = await auth_client.patch(
            f"{PREFIX}/departments/{dept_id}",
            json={"description": "Updated description"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == "0000"

    async def test_delete_department(self, auth_client: AsyncClient):
        # Create a temp department to delete
        create_resp = await auth_client.post(
            f"{PREFIX}/departments",
            json={"name": "TempDept", "code": "TMP"},
        )
        dept_id = create_resp.json()["data"]["createdId"]

        resp = await auth_client.delete(f"{PREFIX}/departments/{dept_id}")
        assert resp.status_code == 200
        assert resp.json()["code"] == "0000"



# ===================== Tag CRUD =====================


class TestTagCRUD:
    async def test_create_tag(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            f"{PREFIX}/tags",
            json={"name": "Go", "category": "Language"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == "0000"

    async def test_list_tags(self, auth_client: AsyncClient, hr_data):
        resp = await auth_client.post(f"{PREFIX}/tags/search", json={"current": 1, "size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        assert len(data["data"]["records"]) >= 2  # Python, JavaScript from seed

    async def test_update_tag(self, auth_client: AsyncClient, hr_data):
        tag_id = encode_id(hr_data["tags"][0].id)
        resp = await auth_client.patch(
            f"{PREFIX}/tags/{tag_id}",
            json={"description": "Programming language"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == "0000"

    async def test_delete_tag(self, auth_client: AsyncClient):
        # Create a temp tag to delete
        create_resp = await auth_client.post(
            f"{PREFIX}/tags",
            json={"name": "TempTag", "category": "Temp"},
        )
        tag_id = create_resp.json()["data"]["createdId"]

        resp = await auth_client.delete(f"{PREFIX}/tags/{tag_id}")
        assert resp.status_code == 200
        assert resp.json()["code"] == "0000"


# ===================== Employee CRUD =====================


class TestEmployeeCRUD:
    async def test_list_employees(self, auth_client: AsyncClient, hr_data):
        """List employees — verifies select_related/prefetch_related returns relations."""
        resp = await auth_client.post(
            f"{PREFIX}/employees/search",
            json={"current": 1, "size": 10},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        records = data["data"]["records"]
        assert len(records) >= 1
        # Verify relations are loaded
        emp = records[0]
        assert "departmentName" in emp
        assert "tagNames" in emp

    async def test_list_employees_filter_by_department(self, auth_client: AsyncClient, hr_data):
        dept_id = encode_id(hr_data["department"].id)
        resp = await auth_client.post(
            f"{PREFIX}/employees/search",
            json={"current": 1, "size": 10, "departmentId": dept_id},
        )
        assert resp.status_code == 200
        records = resp.json()["data"]["records"]
        assert len(records) >= 1

    async def test_scoped_employee_query_limits_to_department(self, hr_data):
        from app.business.hr.models import Department, Employee
        from app.business.hr.schemas import EmployeeSearch
        from app.business.hr.services import build_employee_list_query, list_employees_with_relations

        other_dept = await Department.create(name="Scoped Other", code="SCOPE-OTHER", description="Other Department")
        await Employee.create(
            name="Other Department Employee",
            employee_no="EMP-SCOPE-OTHER",
            email="scope-other@test.com",
            department=other_dept,
        )

        search = EmployeeSearch(current=1, size=50)
        q = build_employee_list_query(search)
        q &= build_scope_filter(
            scope="scope",
            user_id=hr_data["user"].id,
            scope_id=hr_data["department"].id,
            user_id_field="user_id",
            scope_id_field="department_id",
        )

        total, records = await list_employees_with_relations(search, search=q)

        assert total >= 1
        assert all(record["departmentId"] == encode_id(hr_data["department"].id) for record in records)
        assert all(record["departmentId"] != encode_id(other_dept.id) for record in records)

    async def test_create_employee(self, auth_client: AsyncClient, hr_data):
        """Create employee — auto-creates system user."""
        dept_id = encode_id(hr_data["department"].id)
        resp = await auth_client.post(
            f"{PREFIX}/employees",
            json={
                "userName": "13800001111",
                "name": "New Employee",
                "email": "newemp@test.com",
                "departmentId": dept_id,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        assert "employee_id" in data["data"]
        assert "raw_password" in data["data"]
        assert "employee_no" in data["data"]

    async def test_create_employee_no_department(self, auth_client: AsyncClient):
        """Onboarding requires a department."""
        resp = await auth_client.post(
            f"{PREFIX}/employees",
            json={
                "userName": "13800002222",
                "name": "NoDept",
                "email": "nodept@test.com",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == Code.REQUEST_VALIDATION

    async def test_get_employee(self, auth_client: AsyncClient, hr_data):
        emp_id = encode_id(hr_data["employee"].id)
        resp = await auth_client.get(f"{PREFIX}/employees/{emp_id}")
        assert resp.status_code == 200
        assert resp.json()["code"] == "0000"

    async def test_update_employee(self, auth_client: AsyncClient, hr_data):
        emp_id = encode_id(hr_data["employee"].id)
        resp = await auth_client.patch(
            f"{PREFIX}/employees/{emp_id}",
            json={"position": "Senior Engineer"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == "0000"

    async def test_update_employee_too_many_tags(self, auth_client: AsyncClient, hr_data):
        emp_id = encode_id(hr_data["employee"].id)
        # MAX_TAGS_PER_EMPLOYEE default is 10, send 11 fake ids
        resp = await auth_client.patch(
            f"{PREFIX}/employees/{emp_id}/tags",
            json={"tagIds": [encode_id(i) for i in range(1, 12)]},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == Code.HR_TAGS_EXCEED_LIMIT

    async def test_employee_lifecycle_regularize_resign_rehire(self, auth_client: AsyncClient, hr_data):
        from app.business.hr.models import Employee, EmployeeStatus
        from app.system.models import StatusType, User

        dept_id = encode_id(hr_data["department"].id)
        create_resp = await auth_client.post(
            f"{PREFIX}/employees",
            json={
                "userName": "13800003333",
                "name": "Lifecycle Employee",
                "departmentId": dept_id,
            },
        )
        assert create_resp.status_code == 200
        payload = create_resp.json()["data"]
        emp = await Employee.get(id=payload["employee_id"])
        assert emp.status == EmployeeStatus.probation

        regularize_resp = await auth_client.post(f"{PREFIX}/employees/{encode_id(emp.id)}/regularize", json={})
        assert regularize_resp.status_code == 200
        assert regularize_resp.json()["code"] == "0000"
        emp = await Employee.get(id=emp.id)
        assert emp.status == EmployeeStatus.active

        resign_resp = await auth_client.post(
            f"{PREFIX}/employees/{encode_id(emp.id)}/resign",
            json={"remark": "contract ended"},
        )
        assert resign_resp.status_code == 200
        assert resign_resp.json()["code"] == "0000"
        emp = await Employee.get(id=emp.id)
        user = await User.get(id=payload["user_id"])
        assert emp.status == EmployeeStatus.resigned
        assert user.status_type == StatusType.disable

        rehire_resp = await auth_client.post(f"{PREFIX}/employees/{encode_id(emp.id)}/rehire", json={})
        assert rehire_resp.status_code == 200
        assert rehire_resp.json()["code"] == "0000"
        emp = await Employee.get(id=emp.id)
        user = await User.get(id=payload["user_id"])
        assert emp.status == EmployeeStatus.probation
        assert user.status_type == StatusType.enable

        logs_resp = await auth_client.get(f"{PREFIX}/employees/{encode_id(emp.id)}/status-logs")
        assert logs_resp.status_code == 200
        logs = logs_resp.json()["data"]
        assert [log["toStatus"] for log in logs][:3] == ["probation", "resigned", "active"]

    async def test_invalid_regularize_returns_hr_code_without_side_effects(self, auth_client: AsyncClient, hr_data):
        from app.business.hr.models import Employee, EmployeeStatus, EmployeeStatusLog

        create_resp = await auth_client.post(
            f"{PREFIX}/employees",
            json={
                "userName": "13800004444",
                "name": "Invalid Transition Employee",
                "departmentId": encode_id(hr_data["department"].id),
            },
        )
        assert create_resp.status_code == 200
        employee_id = create_resp.json()["data"]["employee_id"]
        encoded_employee_id = encode_id(employee_id)

        regularize_resp = await auth_client.post(f"{PREFIX}/employees/{encoded_employee_id}/regularize", json={})
        assert regularize_resp.status_code == 200
        assert regularize_resp.json()["code"] == Code.SUCCESS

        log_count = await EmployeeStatusLog.filter(employee_id=employee_id).count()
        invalid_resp = await auth_client.post(f"{PREFIX}/employees/{encoded_employee_id}/regularize", json={})

        assert invalid_resp.status_code == 200
        assert invalid_resp.json()["code"] == Code.HR_INVALID_TRANSITION
        employee = await Employee.get(id=employee_id)
        assert employee.status == EmployeeStatus.active
        assert await EmployeeStatusLog.filter(employee_id=employee_id).count() == log_count


# ===================== Manager Operations =====================


class TestManagerOperations:
    async def test_view_department_employees(self, auth_client: AsyncClient, hr_data):
        """Manager searches employees in their department (paginated)."""
        resp = await auth_client.post(f"{PREFIX}/team/employees/search", json={"current": 1, "size": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        records = data["data"]["records"]
        assert len(records) >= 1
        assert "tagNames" in records[0]

    async def test_edit_subordinate_tags(self, auth_client: AsyncClient, hr_data):
        """Manager edits a subordinate's tags."""
        emp_id = encode_id(hr_data["employee"].id)
        tag_ids = [encode_id(t.id) for t in hr_data["tags"]]
        resp = await auth_client.patch(
            f"{PREFIX}/team/employees/{emp_id}/tags",
            json={"tagIds": tag_ids},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == "0000"

    async def test_edit_tags_employee_not_in_dept(self, auth_client: AsyncClient, hr_data):
        """Editing tags of an employee not in the manager's department fails."""
        resp = await auth_client.patch(
            f"{PREFIX}/team/employees/{encode_id(99999)}/tags",
            json={"tagIds": [encode_id(hr_data["tags"][0].id)]},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == Code.HR_EMPLOYEE_NOT_IN_DEPT


# ===================== Personal Operations =====================


class TestPersonalOperations:
    async def test_my_profile(self, auth_client: AsyncClient, hr_data):
        """Get own profile with department and tags."""
        resp = await auth_client.get(f"{PREFIX}/my/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        profile = data["data"]
        assert "departmentName" in profile
        assert "tags" in profile

    async def test_my_tags(self, auth_client: AsyncClient, hr_data):
        """Edit own tags."""
        tag_ids = [encode_id(hr_data["tags"][0].id)]
        resp = await auth_client.patch(
            f"{PREFIX}/my/tags",
            json={"tagIds": tag_ids},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == "0000"

    async def test_my_department(self, auth_client: AsyncClient, hr_data):
        """View colleagues in own department."""
        resp = await auth_client.get(f"{PREFIX}/my/department")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        records = data["data"]
        assert len(records) >= 1
        assert "tagNames" in records[0]

    async def test_my_profile_no_auth(self, client: AsyncClient):
        resp = await client.get(f"{PREFIX}/my/profile")
        assert resp.status_code == 200
        assert resp.json()["code"] == Code.INVALID_TOKEN
