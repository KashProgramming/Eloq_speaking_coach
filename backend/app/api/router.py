from fastapi import APIRouter

from app.api import auth, practice, roleplay

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(practice.router)
api_router.include_router(roleplay.router)
