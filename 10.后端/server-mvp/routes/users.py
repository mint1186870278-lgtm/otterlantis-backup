import re

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Literal, Optional

from db.database import create_user, get_user_by_otter_id, get_user_stats, link_guardian_child, list_users

router = APIRouter()

EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
OTTER_ID_RE = re.compile(r'^OT-[A-Z0-9-]{3,24}$')


class UserCreateRequest(BaseModel):
    role: Literal['child', 'guardian']
    displayName: str = Field(min_length=1, max_length=40)
    lang: str = 'zh'
    email: Optional[str] = None
    otterId: Optional[str] = None


class LinkRequest(BaseModel):
    guardianOtterId: str
    childOtterId: str


@router.post('')
async def create(request: UserCreateRequest):
    try:
        email = request.email.strip().lower() if request.email else None
        otter_id = request.otterId.strip().upper() if request.otterId else None

        if request.role == 'guardian':
            if not email:
                raise HTTPException(status_code=400, detail='email is required for guardian')
            if not EMAIL_RE.match(email):
                raise HTTPException(status_code=400, detail='Invalid email format')

        if otter_id and not OTTER_ID_RE.match(otter_id):
            raise HTTPException(status_code=400, detail='Invalid otterId format')

        user = create_user({
            'role': request.role,
            'displayName': request.displayName,
            'lang': request.lang,
            'email': email,
            'otterId': otter_id,
        })

        return {'success': True, 'user': user}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        print(f'Create user error: {e}')
        raise HTTPException(status_code=500, detail='Internal server error')


@router.get('/stats')
async def stats():
    try:
        return get_user_stats()
    except Exception as e:
        print(f'User stats error: {e}')
        raise HTTPException(status_code=500, detail='Internal server error')


@router.get('')
async def users(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    role: str | None = None,
    keyword: str | None = None,
):
    try:
        if role and role not in ('child', 'guardian'):
            raise HTTPException(status_code=400, detail='Invalid role')
        return list_users(page=page, page_size=pageSize, role=role, keyword=keyword)
    except HTTPException:
        raise
    except Exception as e:
        print(f'List users error: {e}')
        raise HTTPException(status_code=500, detail='Internal server error')


@router.get('/{otter_id}')
async def get_user(otter_id: str):
    try:
        user = get_user_by_otter_id(otter_id)
        if not user:
            raise HTTPException(status_code=404, detail='User not found')
        return {'success': True, 'user': user}
    except HTTPException:
        raise
    except Exception as e:
        print(f'Get user error: {e}')
        raise HTTPException(status_code=500, detail='Internal server error')


@router.post('/link')
async def link(request: LinkRequest):
    try:
        result = link_guardian_child(request.guardianOtterId, request.childOtterId)
        return {'success': True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f'Link user error: {e}')
        raise HTTPException(status_code=500, detail='Internal server error')
