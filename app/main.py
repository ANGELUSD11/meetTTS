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

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    bookmarklet_path = os.path.join(base_dir, "static", "bookmarklet.js")
    with open(bookmarklet_path, "r", encoding="utf-8") as f:
        raw_js = f.read()
    return templates.TemplateResponse(request=request, name="index.html", context={"raw_js": raw_js})


async def process_translation(websocket: WebSocket, text: str, target_name: str, target_code: str):
    try:
        translated = await translate_text(text, target_name)
        print(f"[Translated to {target_name}] {translated}")
        
        try:
            await websocket.send_json({"type": "translation", "text": translated})
        except:
            return
            
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
        
        try:
            await websocket.send_json({"type": "audio", "audio": audio_base64})
        except:
            pass
            
    except Exception as e:
        print(f"[Translation Error]: {e}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # State scoped specifically to this user's connection
    session_last_text = ""
    session_sentence_buffer = []
    session_target_lang_name = "Spanish"
    session_target_lang_code = "es"
    
    await websocket.send_json({"type": "status", "message": "Connected to server."})
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("action") == "set_language":
                lang_code = data.get("lang")
                if lang_code in LANGUAGE_MAP:
                    session_target_lang_code = lang_code
                    session_target_lang_name = LANGUAGE_MAP[lang_code]
                    print(f"[Bot] Client language changed to {session_target_lang_name}")
            
            elif data.get("action") == "join":
                mode = data.get("mode")
                if mode == "bookmarklet":
                    await websocket.send_json({"type": "status", "message": "Bookmarklet connected! Listening..."})
                    session_last_text = ""
                    session_sentence_buffer = []
                    
            elif data.get("action") == "caption":
                current_text = data.get("text", "").strip()
                if not current_text:
                    continue
                
                old_words = session_last_text.split()
                new_words = current_text.split()
                
                s = difflib.SequenceMatcher(None, old_words, new_words)
                new_chunk = []
                
                for tag, i1, i2, j1, j2 in s.get_opcodes():
                    if tag in ('insert', 'replace'):
                        if j2 == len(new_words):
                            new_chunk.extend(new_words[j1:j2])
                
                if new_chunk:
                    session_sentence_buffer.extend(new_chunk)
                    session_last_text = current_text
                    
                    buffer_str = " ".join(session_sentence_buffer)
                    last_char = buffer_str[-1] if buffer_str else ""
                    
                    if last_char in ['.', '?', '!', ','] or len(session_sentence_buffer) >= 6:
                        print(f"[Bot] Text to translate: {buffer_str}")
                        
                        try:
                            await websocket.send_json({"type": "caption", "text": buffer_str})
                        except:
                            pass
                            
                        # Fire and forget translation task for this specific user
                        asyncio.create_task(
                            process_translation(
                                websocket, 
                                buffer_str, 
                                session_target_lang_name, 
                                session_target_lang_code
                            )
                        )
                        
                        session_sentence_buffer = []
                        
    except WebSocketDisconnect:
        print("[Bot] Client disconnected")
    except Exception as e:
        print(f"[WebSocket Error]: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
