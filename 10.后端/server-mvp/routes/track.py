from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any
import time
from db.database import insert_tracking_event, get_tracking_stats, list_tracking_events

router = APIRouter()


class TrackRequest(BaseModel):
    sessionId: str
    event: str
    ts: int | None = None
    # 其他动态字段


@router.post('')
async def track(request: Dict[str, Any]):
    try:
        session_id = request.get('sessionId')
        event = request.get('event')

        if not session_id or not event:
            raise HTTPException(status_code=400, detail='sessionId and event are required')

        ts = request.get('ts', int(time.time() * 1000))
        payload = {k: v for k, v in request.items() if k not in ('sessionId', 'event', 'ts')}

        insert_tracking_event(session_id, event, payload, ts)

        return {'success': True}
    except HTTPException:
        raise
    except Exception as e:
        print(f'Track error: {e}')
        raise HTTPException(status_code=500, detail='Internal server error')


@router.get('/stats')
async def stats():
    try:
        return get_tracking_stats()
    except Exception as e:
        print(f'Stats error: {e}')
        raise HTTPException(status_code=500, detail='Internal server error')


@router.get('/events')
async def events(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    sessionId: str | None = None,
    event: str | None = None,
):
    try:
        return list_tracking_events(
            page=page,
            page_size=pageSize,
            session_id=sessionId,
            event=event,
        )
    except Exception as e:
        print(f'Events error: {e}')
        raise HTTPException(status_code=500, detail='Internal server error')
