"""
work_ticket_management business module manifest.
"""

from app.business.work_ticket_management.api import router
from app.business.work_ticket_management.init_data import INIT_DATA
from app.utils import BusinessModule, BusinessRouter, PermissionSpec

module = BusinessModule(
    name="work_ticket_management",
    title="工票工时管理",
    version="0.1.0",
    routers=[BusinessRouter(router=router, auth="permission")],
    permissions=PermissionSpec(init_data=INIT_DATA),
)
