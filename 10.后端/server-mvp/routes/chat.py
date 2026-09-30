import os
import httpx
from typing import List, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

ARK_CHAT_URL = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
ARK_CHAT_MODEL = os.getenv('ARK_CHAT_MODEL', 'doubao-seed-2-0-lite-260428')
CHAT_TIMEOUT_MS = 90000


class ChatMessage(BaseModel):
    role: Literal['system', 'user', 'assistant'] = Field(description='消息角色')
    content: str = Field(min_length=1, description='消息内容')


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(min_length=1, description='完整对话消息列表，前端多轮对话时应携带历史消息')
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description='采样温度，值越高回复越发散')
    maxTokens: int = Field(default=2048, ge=1, le=8192, description='本次回复最大输出 token 数')
    topP: float = Field(default=0.7, ge=0.0, le=1.0, description='核采样阈值')


class ChatUsage(BaseModel):
    promptTokens: int = 0
    completionTokens: int = 0
    totalTokens: int = 0
    reasoningTokens: int = 0


class ChatResponse(BaseModel):
    id: str = Field(description='上游请求 ID')
    model: str = Field(description='实际调用的模型 ID')
    reply: str = Field(description='助手回复文本')
    reasoning: str | None = Field(default=None, description='模型返回的思考摘要，若上游提供则返回')
    usage: ChatUsage = Field(description='token 使用统计')
    message: ChatMessage = Field(description='标准化后的 assistant 消息对象')


async def create_chat_completion(request: ChatRequest, api_key: str) -> ChatResponse:
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }

    payload = {
        'model': ARK_CHAT_MODEL,
        'messages': [message.model_dump() for message in request.messages],
        'temperature': request.temperature,
        'max_tokens': request.maxTokens,
        'top_p': request.topP,
        'stream': False,
    }

    timeout = httpx.Timeout(connect=30.0, read=CHAT_TIMEOUT_MS / 1000, write=30.0, pool=30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(ARK_CHAT_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

    choices = result.get('choices') or []
    if not choices:
        raise Exception('No choices in response')

    message = choices[0].get('message') or {}
    reply = message.get('content')
    if not reply:
        raise Exception('No assistant reply in response')

    usage = result.get('usage') or {}
    completion_details = usage.get('completion_tokens_details') or {}

    assistant_message = ChatMessage(role='assistant', content=reply)

    return ChatResponse(
        id=result.get('id', ''),
        model=result.get('model', ARK_CHAT_MODEL),
        reply=reply,
        reasoning=message.get('reasoning_content'),
        usage=ChatUsage(
            promptTokens=usage.get('prompt_tokens', 0),
            completionTokens=usage.get('completion_tokens', 0),
            totalTokens=usage.get('total_tokens', 0),
            reasoningTokens=completion_details.get('reasoning_tokens', 0),
        ),
        message=assistant_message,
    )


@router.post('', response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        api_key = os.getenv('ARK_API_KEY')

        print(
            f'[chat] Request received: messagesCount={len(request.messages)}, '
            f'temperature={request.temperature}, maxTokens={request.maxTokens}'
        )

        if not api_key or api_key == 'your_ark_api_key_here':
            print('[chat] ARK_API_KEY not configured')
            raise HTTPException(status_code=500, detail='ARK_API_KEY not configured')

        return await create_chat_completion(request, api_key)
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        detail = e.response.text or str(e)
        print(f'Chat completion error: {detail}')
        raise HTTPException(status_code=500, detail=detail)
    except Exception as e:
        print(f'Chat completion error: {e}')
        raise HTTPException(status_code=500, detail=str(e) or 'Chat completion failed')
