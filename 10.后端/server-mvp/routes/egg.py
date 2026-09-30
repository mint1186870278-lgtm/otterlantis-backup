import re
import time
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from db.database import insert_retention_submission, get_retention_stats, list_retention_submissions

router = APIRouter()

EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


class EggRequest(BaseModel):
    email: Optional[str] = None
    wechat: Optional[str] = None
    lang: str
    source: str
    ts: Optional[int] = None


@router.post('')
async def submit_egg(request: EggRequest):
    try:
        if not request.lang or not request.source:
            raise HTTPException(status_code=400, detail='lang and source are required')

        if request.lang == 'en' and request.email:
            if not EMAIL_RE.match(request.email):
                raise HTTPException(status_code=400, detail='Invalid email format')

        if request.lang == 'zh' and not request.wechat:
            raise HTTPException(status_code=400, detail='Wechat is required for Chinese users')

        if request.lang == 'en' and not request.email:
            raise HTTPException(status_code=400, detail='Email is required for English users')

        insert_retention_submission({
            'email': request.email,
            'wechat': request.wechat,
            'lang': request.lang,
            'source': request.source,
            'ts': request.ts or int(time.time() * 1000)
        })

        return {'success': True}
    except HTTPException:
        raise
    except Exception as e:
        print(f'Egg submission error: {e}')
        raise HTTPException(status_code=500, detail='Internal server error')


@router.get('/stats')
async def stats():
    try:
        return get_retention_stats()
    except Exception as e:
        print(f'Stats error: {e}')
        raise HTTPException(status_code=500, detail='Internal server error')


@router.get('/submissions')
async def submissions(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    lang: str | None = None,
    source: str | None = None,
    keyword: str | None = None,
):
    try:
        return list_retention_submissions(
            page=page,
            page_size=pageSize,
            lang=lang,
            source=source,
            keyword=keyword,
        )
    except Exception as e:
        print(f'Submissions error: {e}')
        raise HTTPException(status_code=500, detail='Internal server error')
