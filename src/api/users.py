from fastapi import APIRouter, Depends
from src.api.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.models.user import User
from sqlalchemy import select

router = APIRouter()

@router.get('/me')
async def me(current_user: dict = Depends(get_current_user)):
    return current_user
