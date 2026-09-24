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

# LIST of all connected websockets (Dashboard + Bookmarklets)
active_websockets = set()
translation_queue = asyncio.Queue()

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.add(websocket)
    
    # Immediately send a connection success to whatever just connected
    await websocket.send_json({"type": "status", "message": "Servidor listo y escuchando."})
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("action") == "join":
                mode = data.get("mode")
                if mode == "bookmarklet":
                    await websocket.send_json({"type": "status", "message": "Bookmarklet conectado! Escuchando subtítulos..."})
                    
            elif data.get("action") == "caption":
                text = data.get("text")
                if text:
                    print(f"[Bot] Texto a traducir: {text}")
                    # Broadcast the original text to all clients (so Dashboard can show it)
                    for ws in active_websockets:
                        try:
                            await ws.send_json({"type": "caption", "text": text})
                        except:
                            pass
                    await translation_queue.put(text)
    
    except WebSocketDisconnect:
        print("[Bot] Cliente desconectado")
        active_websockets.discard(websocket)
    except Exception as e:
        print(f"[Error WebSocket]: {e}")
        active_websockets.discard(websocket)

async def translation_worker():
    while True:
        try:
            text = await translation_queue.get()
            
            translated = await translate_text(text)
            print(f"[Traducido] {translated}")
            
            # Broadcast translation text
            for ws in list(active_websockets):
                try:
                    await ws.send_json({"type": "translation", "text": translated})
                except:
                    pass
            
            if not translated or not translated.strip():
                translation_queue.task_done()
                continue

            # Generate TTS
            tts = gTTS(text=translated, lang='es', tld='com.mx')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
            
            # Broadcast audio
            for ws in list(active_websockets):
                try:
                    await ws.send_json({"type": "audio", "audio": audio_base64})
                except:
                    pass
            
            translation_queue.task_done()
        except Exception as e:
            print(f"[Error de Traducción]: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
