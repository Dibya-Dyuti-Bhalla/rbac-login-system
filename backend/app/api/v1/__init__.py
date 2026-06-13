from fastapi import APIRouter
from .endpoints.auth import router as auth_router
from .endpoints.users import router as users_router
from .endpoints.articles import router as articles_router
from .endpoints.admin import router as admin_router
from .endpoints.notifications import notifications_router, roles_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(articles_router)
api_router.include_router(admin_router)
api_router.include_router(notifications_router)
api_router.include_router(roles_router)
