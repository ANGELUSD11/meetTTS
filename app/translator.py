import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# We can dynamically use Groq if the user provides a key!
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

groq_client = None
if GROQ_API_KEY:
    try:
        from groq import AsyncGroq
        groq_client = AsyncGroq(api_key=GROQ_API_KEY)
    except ImportError:
        pass

gemini_client = None
if GEMINI_API_KEY and not groq_client:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except ImportError:
        pass

async def translate_text(text: str, target_language: str = "Spanish") -> str:
    if not text.strip():
        return ""
        
    prompt = (
        f"You are a professional real-time interpreter.\\n"
        f"Translate the following text into {target_language}.\\n"
        f"Context: The speaker is in a Google Meet video call.\\n"
        f"Output ONLY the translated text, without markdown, quotes, or any additional context.\\n"
        f"Make it sound natural for spoken audio.\\n\\n"
        f"TEXT TO TRANSLATE:\\n{text}"
    )
    
    try:
        if groq_client:
            # GROQ IS INCREDIBLY FAST AND FREE
            response = await groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="openai/gpt-oss-20b",
            )
            return response.choices[0].message.content.strip()
        elif gemini_client:
            response = await gemini_client.aio.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
            )
            return response.text.strip()
        else:
            return "[Error: No API key provided for Groq or Gemini in .env]"
    except Exception as e:
        print(f"[Translator Error]: {e}")
        return ""
