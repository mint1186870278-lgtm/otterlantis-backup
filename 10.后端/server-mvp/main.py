import os
import time
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import init_db
from routes.track import router as track_router
from routes.egg import router as egg_router
from routes.image import router as image_router
from routes.chat import router as chat_router
from routes.fish_tts import router as fish_tts_router
from routes.users import router as users_router

load_dotenv()

app = FastAPI(title='Otter Planet Server')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
async def startup():
    init_db()


@app.get('/health')
async def health():
    return {'status': 'ok', 'timestamp': int(time.time() * 1000)}


app.include_router(track_router, prefix='/api/track')
app.include_router(egg_router, prefix='/api/otter-egg')
app.include_router(image_router, prefix='/api/generate-image')
app.include_router(chat_router, prefix='/api/chat')
app.include_router(fish_tts_router, prefix='/api/fish-tts')
app.include_router(users_router, prefix='/api/users')

if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv('PORT', 3001))
    uvicorn.run(app, host='0.0.0.0', port=port)
