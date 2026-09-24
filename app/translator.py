import os
from groq import AsyncGroq

# Configuración de Groq
client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

async def translate_text(text: str, target_language: str = "Spanish") -> str:
    if not text or not text.strip():
        return ""
    
    prompt = f"Translate the following text to {target_language}. Respond ONLY with the translation, no notes, no quotes, no extra text. Text: {text}"
    
    try:
        completion = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional interpreter. You always respond ONLY with the direct translation of the provided text, without quotes, without introductory text, and without explaining."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Error Groq API]: {e}")
        return ""
