from fastapi import APIRouter

from app.business.work_ticket_management.api import imports, master_data, months, reconciliation, reports, tickets, timesheet
from app.business.work_ticket_management.api.manage import router as manage_router

router = APIRouter()
router.include_router(manage_router)
router.include_router(master_data.router)
router.include_router(months.router)
router.include_router(imports.router)
router.include_router(tickets.router)
router.include_router(timesheet.router)
router.include_router(reconciliation.router)
router.include_router(reports.router)
