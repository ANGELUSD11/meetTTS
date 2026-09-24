(function(){
    console.log('[AI Meet] Súper Marcador V5 (Smart Cloud Sync)!');
    if (document.getElementById('ai-meet-bridge')) {
        alert('El bot ya esta corriendo.');
        return;
    }

    let wsDomain = window.prompt("Ingresa la URL de tu servidor TTS Meet (sin https://):", "web-production-ad4ac.up.railway.app");
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
    overlay.style.background = 'rgba(15, 23, 42, 0.9)';
    overlay.style.color = 'white';
    overlay.style.padding = '15px 25px';
    overlay.style.borderRadius = '12px';
    overlay.style.fontFamily = 'sans-serif';
    overlay.style.zIndex = '999999';
    overlay.style.border = '1px solid #3b82f6';
    overlay.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.5)';
    
    const title = document.createElement('b');
    title.style.color = '#3b82f6';
    title.textContent = '🎙️ AI Interpreter';
    const br = document.createElement('br');
    const statusSpan = document.createElement('span');
    statusSpan.id = 'ai-status';
    statusSpan.textContent = 'Conectando túnel...';
    
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

    setInterval(() => {
        let text = '';
        let elements = document.querySelectorAll('.a4cQT, .CNusmb, .iTTPOb');
        elements.forEach(el => {
            if(el.innerText) { text += el.innerText + ' '; }
        });
        
        const garbageRegex = /language|Español|Inglés|México|format_size|Tamaño de fuente|circle|Color de la fuente|settings|Abrir configuración de subtítulos|Tú|Ir al final|Más opciones|arrow_downward/gi;
        text = text.replace(garbageRegex, ' ');
        text = text.replace(/\s+/g, ' ').trim();

        if (text && text !== lastSentText) {
            // Mandamos todo el cuadro de texto limpio al servidor Python.
            // Python se encargará de hacer el "Diff" inteligente y extraer solo las palabras nuevas.
            iframe.contentWindow.postMessage({action: 'caption', text: text}, '*');
            lastSentText = text;
        }
    }, 1500); // 1.5 segundos para no saturar
})();
