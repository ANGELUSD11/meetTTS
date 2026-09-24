import asyncio
import os
import base64
import io
import difflib
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from gtts import gTTS
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

active_websockets = set()
translation_queue = asyncio.Queue()

# Global state for diffing and language
global_last_text = ""
global_sentence_buffer = []

# Default Language
global_target_lang_name = "Spanish"
global_target_lang_code = "es"

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

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    bookmarklet_path = os.path.join(base_dir, "static", "bookmarklet.js")
    with open(bookmarklet_path, "r", encoding="utf-8") as f:
        raw_js = f.read()
    return templates.TemplateResponse(request=request, name="index.html", context={"raw_js": raw_js})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global global_last_text, global_sentence_buffer
    global global_target_lang_name, global_target_lang_code
    
    await websocket.accept()
    active_websockets.add(websocket)
    
    await websocket.send_json({"type": "status", "message": "Connected to server."})
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("action") == "set_language":
                lang_code = data.get("lang")
                if lang_code in LANGUAGE_MAP:
                    global_target_lang_code = lang_code
                    global_target_lang_name = LANGUAGE_MAP[lang_code]
                    print(f"[Bot] Language changed to {global_target_lang_name}")
            
            elif data.get("action") == "join":
                mode = data.get("mode")
                if mode == "bookmarklet":
                    await websocket.send_json({"type": "status", "message": "Bookmarklet connected! Listening..."})
                    global_last_text = ""
                    global_sentence_buffer = []
                    
            elif data.get("action") == "caption":
                current_text = data.get("text", "").strip()
                if not current_text:
                    continue
                
                old_words = global_last_text.split()
                new_words = current_text.split()
                
                s = difflib.SequenceMatcher(None, old_words, new_words)
                new_chunk = []
                
                for tag, i1, i2, j1, j2 in s.get_opcodes():
                    if tag in ('insert', 'replace'):
                        if j2 == len(new_words):
                            new_chunk.extend(new_words[j1:j2])
                
                if new_chunk:
                    global_sentence_buffer.extend(new_chunk)
                    global_last_text = current_text
                    
                    buffer_str = " ".join(global_sentence_buffer)
                    last_char = buffer_str[-1] if buffer_str else ""
                    
                    if last_char in ['.', '?', '!', ','] or len(global_sentence_buffer) >= 6:
                        print(f"[Bot] Text to translate: {buffer_str}")
                        for ws in active_websockets:
                            try:
                                await ws.send_json({"type": "caption", "text": buffer_str})
                            except:
                                pass
                        await translation_queue.put(buffer_str)
                        global_sentence_buffer = []
                        
    except WebSocketDisconnect:
        print("[Bot] Client disconnected")
        active_websockets.discard(websocket)
    except Exception as e:
        print(f"[WebSocket Error]: {e}")
        active_websockets.discard(websocket)

async def translation_worker():
    while True:
        try:
            text = await translation_queue.get()
            
            # Use the global language at the time of processing
            target_name = global_target_lang_name
            target_code = global_target_lang_code
            
            translated = await translate_text(text, target_name)
            print(f"[Translated to {target_name}] {translated}")
            
            for ws in list(active_websockets):
                try:
                    await ws.send_json({"type": "translation", "text": translated})
                except:
                    pass
            
            if not translated or not translated.strip():
                translation_queue.task_done()
                continue
            
            # Try setting the TTS language
            try:
                # 'zh' in gTTS is 'zh-CN' typically, but 'zh' works as fallback
                lang_for_tts = 'zh-CN' if target_code == 'zh' else target_code
                tts = gTTS(text=translated, lang=lang_for_tts)
            except ValueError:
                # Fallback to English if language is not supported by gTTS
                tts = gTTS(text=translated, lang='en')

            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
            
            for ws in list(active_websockets):
                try:
                    await ws.send_json({"type": "audio", "audio": audio_base64})
                except:
                    pass
            
            translation_queue.task_done()
        except Exception as e:
            print(f"[Translation Error]: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
