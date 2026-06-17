from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.config.settings import get_settings
from src.db.session import get_db
from src.models.user import User
from src.models.auth_tokens import RefreshToken, PasswordResetToken
from src.api.auth import create_access_token, get_password_hash, get_password_hash as hash_pw

settings = get_settings()
router = APIRouter()

class RefreshRequest(BaseModel):
    refresh_token: str

class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

@router.post('/refresh', response_model=RefreshResponse)
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    q = select(RefreshToken).where(RefreshToken.token == payload.refresh_token)
    result = await db.execute(q)
    token_obj = result.scalar_one_or_none()
    if not token_obj or token_obj.revoked or token_obj.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail='Invalid or expired refresh token')
    q = select(User).where(User.id == token_obj.user_id)
    res = await db.execute(q)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail='User not found')
    access = create_access_token(str(user.id))
    return RefreshResponse(access_token=access)

@router.post('/password-reset/request')
async def password_reset_request(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    q = select(User).where(User.email == payload.email)
    result = await db.execute(q)
    user = result.scalar_one_or_none()
    if not user:
        # Do not reveal existence
        return {'status': 'ok'}
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=1)
    pr = PasswordResetToken(user_id=user.id, token=token, expires_at=expires)
    db.add(pr)
    await db.commit()
    # In production, send email. For now return token URL for testing.
    reset_url = f"/reset-password?token={token}"
    return {'status': 'ok', 'reset_url': reset_url}

@router.post('/password-reset/confirm')
async def password_reset_confirm(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    q = select(PasswordResetToken).where(PasswordResetToken.token == payload.token)
    result = await db.execute(q)
    token_obj = result.scalar_one_or_none()
    if not token_obj or token_obj.used or token_obj.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail='Invalid or expired token')
    q = select(User).where(User.id == token_obj.user_id)
    res = await db.execute(q)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail='User not found')
    user.hashed_password = get_password_hash(payload.new_password)
    token_obj.used = True
    db.add(user)
    db.add(token_obj)
    await db.commit()
    return {'status': 'ok'}
