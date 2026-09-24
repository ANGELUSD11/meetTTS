import asyncio
import os
import base64
import io
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from gtts import gTTS
import urllib.parse
from contextlib import asynccontextmanager

from app.translator import translate_text

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(translation_worker())
    yield

app = FastAPI(title="AI Google Meet Interpreter", lifespan=lifespan)
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

active_websocket = None
translation_queue = asyncio.Queue()

async def generate_audio_base64(text: str, lang: str = 'es') -> str:
    def _create_audio():
        tts = gTTS(text=text, lang=lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return base64.b64encode(fp.read()).decode('utf-8')
    return await asyncio.to_thread(_create_audio)

async def translation_worker():
    global active_websocket
    while True:
        text = await translation_queue.get()
        translation_queue.task_done()
        
        while not translation_queue.empty():
            text += " " + translation_queue.get_nowait()
            translation_queue.task_done()
            
        translated = await translate_text(text)
        if translated and active_websocket:
            try:
                await active_websocket.send_json({"type": "translation", "text": translated})
                audio_b64 = await generate_audio_base64(translated)
                await active_websocket.send_json({"type": "audio", "audio": audio_b64})
            except Exception as e:
                print(f"Error sending to WS: {e}")
                
        await asyncio.sleep(0.5)

async def on_new_caption(text: str):
    global active_websocket
    if text.startswith("[Error]"):
        print(text)
        if active_websocket:
            await active_websocket.send_json({"type": "status", "message": f"<span class='text-red-500'>{text}</span>"})
        return
    elif text.startswith("[Success]"):
        print(text)
        if active_websocket:
            await active_websocket.send_json({"type": "status", "message": f"<span class='text-green-500'>{text}</span>"})
        return
        
    print(f"Captured: {text}")
    if active_websocket:
        try:
            await active_websocket.send_json({"type": "caption", "text": text})
        except:
            pass
    await translation_queue.put(text)

@app.get("/", response_class=HTMLResponse)
async def get_ui(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global active_websocket
    await websocket.accept()
    active_websocket = websocket
    
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("action") == "join":
                mode = data.get("mode")
                if mode == "bookmarklet":
                    await websocket.send_json({"type": "status", "message": "Bookmarklet conectado! Escuchando subtítulos..."})
                else:
                    await websocket.send_json({"type": "status", "message": "Conectado. Usa el marcador para enviar subtítulos."})
                    
            elif data.get("action") == "caption":
                text = data.get("text")
                await on_new_caption(text)
                
    except WebSocketDisconnect:
        if active_websocket == websocket:
            active_websocket = None

if __name__ == "__main__":
    import uvicorn
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    uvicorn.run("web:app", host="0.0.0.0", port=8000, loop="asyncio")
