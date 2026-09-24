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

base_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

active_websocket = None
translation_queue = asyncio.Queue()

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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
                if text:
                    print(f"[Bot] Texto a traducir: {text}")
                    await translation_queue.put(text)
    
    except WebSocketDisconnect:
        print("[Bot] Cliente desconectado")
        if active_websocket == websocket:
            active_websocket = None
    except Exception as e:
        print(f"[Error WebSocket]: {e}")
        if active_websocket == websocket:
            active_websocket = None

async def translation_worker():
    global active_websocket
    while True:
        try:
            text = await translation_queue.get()
            
            translated = await translate_text(text)
            print(f"[Traducido] {translated}")
            
            tts = gTTS(text=translated, lang='es', tld='com.mx')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
            
            if active_websocket:
                await active_websocket.send_json({
                    "type": "audio",
                    "audio": audio_base64
                })
            
            translation_queue.task_done()
        except Exception as e:
            print(f"[Error de Traducción]: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
