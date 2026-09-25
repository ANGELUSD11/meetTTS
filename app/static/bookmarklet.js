(function(){
    console.log('[AI Meet] Super Bookmarklet V6 (Ultra-Fast Celeron Edition)!');
    if (document.getElementById('ai-meet-bridge')) {
        alert('The bot is already running.');
        return;
    }

    let wsDomain = window.prompt("Enter your TTS Meet server URL (without https://):", "web-production-ad4ac.up.railway.app");
    if (!wsDomain) return;
    wsDomain = wsDomain.replace('http://', '').replace('https://', '').replace(/\/$/, '');

    const iframe = document.createElement('iframe');
    iframe.id = 'ai-meet-bridge';
    const protocol = wsDomain.includes('localhost') ? 'http://' : 'https://';
    iframe.src = protocol + wsDomain + '/static/bridge.html';
    iframe.style.display = 'none';
    document.body.appendChild(iframe);

    const overlay = document.createElement('div');
    overlay.id = 'ai-meet-overlay';
    overlay.style.position = 'fixed';
    overlay.style.bottom = '20px';
    overlay.style.right = '20px';
    overlay.style.background = 'rgba(255, 255, 255, 0.95)';
    overlay.style.color = '#202124';
    overlay.style.padding = '16px 24px';
    overlay.style.borderRadius = '8px';
    overlay.style.fontFamily = 'Roboto, Arial, sans-serif';
    overlay.style.zIndex = '999999';
    overlay.style.border = '1px solid #dadce0';
    overlay.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
    
    const title = document.createElement('b');
    title.style.color = '#1a73e8';
    title.textContent = '🎙️ AI Interpreter';
    const br = document.createElement('br');
    const statusSpan = document.createElement('span');
    statusSpan.id = 'ai-status';
    statusSpan.style.fontSize = '13px';
    statusSpan.style.color = '#5f6368';
    statusSpan.textContent = 'Connecting tunnel...';
    
    overlay.appendChild(title);
    overlay.appendChild(br);
    overlay.appendChild(statusSpan);
    document.body.appendChild(overlay);

    window.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'status') {
            document.getElementById('ai-status').textContent = event.data.message;
        } else if (event.data && event.data.type === 'audio') {
            audioQueue.push('data:audio/mp3;base64,' + event.data.audio);
            playNextAudio();
        }
    });

    let audioQueue = [];
    let isPlaying = false;

    async function playNextAudio() {
        if (isPlaying || audioQueue.length === 0) return;
        isPlaying = true;
        let a = new Audio(audioQueue.shift());
        a.onended = () => { isPlaying = false; playNextAudio(); };
        try { await a.play(); } catch(e) { console.error('Audio error', e); isPlaying = false; }
    }

    let lastSentText = '';

    // Optimizacion extrema para PCs lentos (Celeron/2GB RAM)
    // Se ejecuta más rapido (800ms) para menor retraso, pero usa textContent en vez de innerText
    // para evitar el recálculo de CSS (Layout Thrashing) que congela los navegadores.
    setInterval(() => {
        let text = '';
        let elements = document.querySelectorAll('.a4cQT, .CNusmb, .iTTPOb');
        let len = elements.length;
        
        for(let i = 0; i < len; i++) {
            let content = elements[i].textContent;
            if(content) { text += content + ' '; }
        }
        
        const garbageRegex = /language|Español|Inglés|México|format_size|Tamaño de fuente|circle|Color de la fuente|settings|Abrir configuración de subtítulos|Tú|Ir al final|Más opciones|arrow_downward/gi;
        text = text.replace(garbageRegex, ' ');
        text = text.replace(/\s+/g, ' ').trim();

        if (text && text !== lastSentText) {
            iframe.contentWindow.postMessage({action: 'caption', text: text}, '*');
            lastSentText = text;
        }
    }, 800);
})();
