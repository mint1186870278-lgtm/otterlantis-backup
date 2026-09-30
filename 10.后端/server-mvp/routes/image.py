import os
import time
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

ARK_URL = 'https://ark.cn-beijing.volces.com/api/v3/images/generations'
ARK_MODEL = 'doubao-seedream-4-0-250828'
MAX_ATTEMPTS = 5
ATTEMPT_TIMEOUT_MS = 90000
RETRY_BACKOFF_MS = 1200


class ImageRequest(BaseModel):
    prompt: str
    images: List[str] = []
    size: str


async def generate_image(prompt: str, images: List[str], size: str, api_key: str) -> str:
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': ARK_MODEL,
        'prompt': prompt,
        'image': images,
        'sequential_image_generation': 'disabled',
        'response_format': 'url',
        'size': size,
        'stream': False,
        'watermark': False
    }

    timeout = httpx.Timeout(connect=30.0, read=ATTEMPT_TIMEOUT_MS / 1000, write=30.0, pool=30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(ARK_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        url = result.get('data', [{}])[0].get('url')
        if not url:
            raise Exception('No image URL in response')

        return url


async def generate_with_retry(prompt: str, images: List[str], size: str, api_key: str) -> str:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(f'Image generation attempt {attempt}/{MAX_ATTEMPTS}')
            return await generate_image(prompt, images, size, api_key)
        except Exception as e:
            print(f'Attempt {attempt} failed: {e}')
            if attempt >= MAX_ATTEMPTS:
                raise
            await async_sleep(RETRY_BACKOFF_MS * attempt)

    raise Exception('Unexpected error in retry loop')


def async_sleep(ms: int):
    import asyncio
    return asyncio.sleep(ms / 1000)


@router.post('')
async def generate(request: ImageRequest):
    try:
        api_key = os.getenv('ARK_API_KEY')

        print(f'[generate-image] Request received: prompt={request.prompt[:50] if request.prompt else ""}, imagesCount={len(request.images)}, size={request.size}')

        if not request.prompt or not request.size:
            print('[generate-image] Missing required fields')
            raise HTTPException(status_code=400, detail='prompt and size are required')

        if not api_key or api_key == 'your_ark_api_key_here':
            print('[generate-image] ARK_API_KEY not configured')
            raise HTTPException(status_code=500, detail='ARK_API_KEY not configured')

        url = await generate_with_retry(request.prompt, request.images or [], request.size, api_key)

        return {'url': url}
    except HTTPException:
        raise
    except Exception as e:
        print(f'Image generation error: {e}')
        raise HTTPException(status_code=500, detail=str(e) or 'Image generation failed')
