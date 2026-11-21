"""
labor_management business module manifest.
"""

from app.business.labor_management.api import router
from app.business.labor_management.init_data import INIT_DATA
from app.utils import BusinessModule, BusinessRouter, PermissionSpec

module = BusinessModule(
    name="labor_management",
    title="劳务管理",
    version="0.1.0",
    routers=[BusinessRouter(router=router, auth="permission")],
    permissions=PermissionSpec(init_data=INIT_DATA),
)
