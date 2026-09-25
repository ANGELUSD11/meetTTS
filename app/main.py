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

from app.translator import translate_text

app = FastAPI(title="AI Google Meet Interpreter")

base_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

LANGUAGE_MAP = {
    "es": "Spanish",
    "en": "English",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ja": "Japanese",
    "zh": "Chinese"
}

class RoomState:
    def __init__(self):
        self.websockets = set()
        self.translated_length = 0
        self.target_lang_name = "Spanish"
        self.target_lang_code = "es"

rooms = {}

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    bookmarklet_path = os.path.join(base_dir, "static", "bookmarklet.js")
    with open(bookmarklet_path, "r", encoding="utf-8") as f:
        raw_js = f.read()
    return templates.TemplateResponse(request=request, name="index.html", context={"raw_js": raw_js})

async def process_translation(room_id: str, text: str, target_name: str, target_code: str):
    try:
        translated = await translate_text(text, target_name)
        print(f"[Room {room_id} -> {target_name}] {translated}")
        
        room = rooms.get(room_id)
        if not room: return
            
        for ws in list(room.websockets):
            try:
                await ws.send_json({"type": "translation", "text": translated})
            except:
                pass
                
        if not translated or not translated.strip():
            return
            
        # TTS
        try:
            lang_for_tts = 'zh-CN' if target_code == 'zh' else target_code
            tts = gTTS(text=translated, lang=lang_for_tts)
        except ValueError:
            tts = gTTS(text=translated, lang='en')

        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
        
        room = rooms.get(room_id)
        if room:
            for ws in list(room.websockets):
                try:
                    await ws.send_json({"type": "audio", "audio": audio_base64})
                except:
                    pass
            
    except Exception as e:
        print(f"[Translation Error]: {e}")


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    
    if room_id not in rooms:
        rooms[room_id] = RoomState()
    room = rooms[room_id]
    room.websockets.add(websocket)
    
    await websocket.send_json({"type": "status", "message": f"Connected to server (Room: {room_id})."})
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("action") == "set_language":
                lang_code = data.get("lang")
                if lang_code in LANGUAGE_MAP:
                    room.target_lang_code = lang_code
                    room.target_lang_name = LANGUAGE_MAP[lang_code]
                    print(f"[Room {room_id}] Language changed to {room.target_lang_name}")
            
            elif data.get("action") == "join":
                mode = data.get("mode")
                if mode == "bookmarklet":
                    await websocket.send_json({"type": "status", "message": "Bookmarklet connected! Listening..."})
                    room.translated_length = 0
                    
            elif data.get("action") == "caption":
                current_text = data.get("text", "").replace("( )", "").replace("()", "").strip()
                if not current_text:
                    continue
                
                # Si el contenedor de Google Meet se limpió (nuevo bloque de subtítulos), reseteamos
                if room.translated_length > len(current_text):
                    room.translated_length = 0
                    
                pending_text = current_text[room.translated_length:].strip()
                if not pending_text:
                    continue
                    
                words = pending_text.split()
                last_char = pending_text[-1]
                
                # Esperamos puntuación o mínimo 8 palabras para enviar una frase con buen contexto
                if last_char in ['.', '?', '!', ','] or len(words) >= 8:
                    chunk_to_translate = pending_text
                    
                    chunk_index = current_text.find(chunk_to_translate, room.translated_length)
                    if chunk_index != -1:
                        room.translated_length = chunk_index + len(chunk_to_translate)
                    else:
                        room.translated_length = len(current_text)
                        
                    print(f"[Room {room_id}] Text to translate: {chunk_to_translate}")
                    
                    for ws in list(room.websockets):
                        try:
                            await ws.send_json({"type": "caption", "text": chunk_to_translate})
                        except:
                            pass
                        
                    asyncio.create_task(
                        process_translation(
                            room_id, 
                            chunk_to_translate, 
                            room.target_lang_name, 
                            room.target_lang_code
                        )
                    )
                        
    except WebSocketDisconnect:
        print(f"[Room {room_id}] Client disconnected")
        if websocket in room.websockets:
            room.websockets.remove(websocket)
        if not room.websockets:
            del rooms[room_id]
            print(f"[Room {room_id}] Destroyed (empty).")
    except Exception as e:
        print(f"[WebSocket Error]: {e}")
        if websocket in room.websockets:
            room.websockets.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
