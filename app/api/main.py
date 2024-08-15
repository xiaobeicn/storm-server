from fastapi import APIRouter

from app.api.routes import login, users, article

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(article.router, prefix="/article", tags=["article"])
