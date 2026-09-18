"""API v1 router — aggregates all sub-routers."""
from fastapi import APIRouter

from src.api.v1 import auth, dashboard, opportunities, actions, audit, assistant, missions

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(opportunities.router, prefix="/opportunities", tags=["Opportunities"])
router.include_router(actions.router, prefix="/actions", tags=["Actions"])
router.include_router(audit.router, prefix="/audit", tags=["Audit"])
router.include_router(assistant.router, prefix="/assistant", tags=["AI Assistant"])
router.include_router(missions.router, prefix="/missions", tags=["Missions"])
