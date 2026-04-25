"""API routers package."""

from car_agent.backend.routers.customers import router as customers_router
from car_agent.backend.routers.recommendations import router as recommendations_router
from car_agent.backend.routers.chat import router as chat_router
from car_agent.backend.routers.admin import router as admin_router
from car_agent.backend.routers.mypage import router as mypage_router

__all__ = [
    "customers_router",
    "recommendations_router",
    "chat_router",
    "admin_router",
    "mypage_router",
]
