import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import re

async def run_bot(url, websocket):
    await websocket.send_json({"type": "status", "message": "Iniciando navegador virtual en la nube..."})
    print(f"[Bot] Iniciando navegador para {url}")
    
    async with async_playwright() as p:
        # Usar argumentos para evadir detección básica
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--window-size=1920,1080',
                '--use-fake-ui-for-media-stream',
                '--use-fake-device-for-media-stream'
            ]
        )
        
        # Emular un dispositivo real
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            permissions=['microphone', 'camera']
        )
        
        page = await context.new_page()
        await stealth_async(page)
        
        await websocket.send_json({"type": "status", "message": "Navegando a la llamada..."})
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Dismiss any popups if they appear (like Got it / Entendido)
            try:
                await page.click('button:has-text("Got it")', timeout=3000)
            except:
                pass
            try:
                await page.click('button:has-text("Entendido")', timeout=3000)
            except:
                pass
                
            await websocket.send_json({"type": "status", "message": "Escribiendo nombre del bot..."})
            
            # Wait for the name input box (Guest join)
            # Try multiple possible selectors for the input box
            input_box = page.locator('input[type="text"]')
            await input_box.wait_for(state="visible", timeout=15000)
            await input_box.fill("AI Interpreter Bot")
            
            await websocket.send_json({"type": "status", "message": "Solicitando unirse (Acepta al bot en la llamada)..."})
            
            # Click "Ask to join" / "Solicitar unirse"
            join_btn = page.locator('button:has-text("Ask to join"), button:has-text("Solicitar unirse")').first
            await join_btn.click()
            
            await websocket.send_json({"type": "status", "message": "Esperando a ser admitido..."})
            
            # Wait until the CC button appears (meaning we are inside the call)
            # CC button usually has aria-label="Turn on captions" or "Activar subtítulos"
            cc_btn = page.locator('button[aria-label*="caption"], button[aria-label*="subtítulo"], button[aria-label*="Captions"]')
            await cc_btn.wait_for(state="visible", timeout=60000) # Wait up to 1 minute to be admitted
            
            await websocket.send_json({"type": "status", "message": "¡Admitido! Encendiendo subtítulos..."})
            
            # Click CC button to turn it on if it's not already on
            aria_pressed = await cc_btn.get_attribute('aria-pressed')
            if aria_pressed != 'true':
                await cc_btn.click()
                
            await websocket.send_json({"type": "status", "message": "¡Bot activo! Escuchando la reunión..."})
            
            # Scrape Loop
            last_text = ""
            pending_buffer = []
            
            while True:
                await asyncio.sleep(1)
                
                # Get all caption text
                elements = await page.query_selector_all('.a4cQT, .CNusmb, .V8sq0b, .bhbHJ')
                text = ""
                for el in elements:
                    inner = await el.inner_text()
                    text += inner + " "
                
                text = text.strip()
                if not text:
                    continue
                    
                # Basic overlap/difference logic
                if text != last_text and len(text) > len(last_text):
                    new_chunk = text[len(last_text):].strip()
                    if new_chunk:
                        # Send to websocket logic
                        await websocket.send_json({"type": "caption", "text": text}) # For simplicity, send full text or chunks
                
                last_text = text
                
        except Exception as e:
            print(f"[Bot Error]: {e}")
            await websocket.send_json({"type": "status", "message": f"Error del bot: {str(e)}"})
        finally:
            await browser.close()
