(function(){
    console.log('[AI Meet] Súper Marcador V4 (Limpio)!');
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
    let pendingBuffer = [];
    let idleTicks = 0;

    setInterval(() => {
        let text = '';
        let elements = document.querySelectorAll('.a4cQT, .CNusmb, .iTTPOb');
        elements.forEach(el => {
            if(el.innerText) { text += el.innerText + ' '; }
        });
        
        const garbageRegex = /language|Español|Inglés|México|format_size|Tamaño de fuente|circle|Color de la fuente|settings|Abrir configuración de subtítulos|Tú|Ir al final|Más opciones|arrow_downward/gi;
        text = text.replace(garbageRegex, ' ');
        text = text.replace(/\s+/g, ' ').trim();

        if (!text) {
            idleTicks++;
            if (pendingBuffer.length > 0 && idleTicks >= 2) {
                iframe.contentWindow.postMessage({action: 'caption', text: pendingBuffer.join(' ')}, '*');
                pendingBuffer = [];
            }
            if (idleTicks >= 2) lastSentText = '';
            return;
        }

        if (text === lastSentText) {
            idleTicks++;
            if (pendingBuffer.length > 0 && idleTicks >= 2) {
                iframe.contentWindow.postMessage({action: 'caption', text: pendingBuffer.join(' ')}, '*');
                pendingBuffer = [];
            }
            return;
        }

        idleTicks = 0;

        if (lastSentText === '') {
            lastSentText = text;
            pendingBuffer = text.split(' ');
            return;
        }

        const normalize = (w) => w.replace(/[.,?!]/g, '').toLowerCase();
        let oldWordsRaw = lastSentText.split(' ');
        let newWordsRaw = text.split(' ');
        let oldWords = oldWordsRaw.map(normalize);
        let newWords = newWordsRaw.map(normalize);

        let newDiff = [];
        let foundOverlap = false;
        
        for (let i = 0; i < oldWords.length; i++) {
            let match = true;
            let matchSize = 0;
            for (let j = 0; j < oldWords.length - i; j++) {
                if (j >= newWords.length || oldWords[i+j] !== newWords[j]) { match = false; break; }
                matchSize++;
            }
            if (match && matchSize >= Math.min(2, oldWords.length)) {
                newDiff = newWordsRaw.slice(matchSize);
                foundOverlap = true;
                break;
            }
        }

        if (foundOverlap) {
            if (newDiff.length > 0) {
                pendingBuffer.push(...newDiff);
                lastSentText = text;
            }
        } else if (newWordsRaw.length >= 2) {
            pendingBuffer.push(...newWordsRaw);
            lastSentText = text;
        }

        if (pendingBuffer.length > 0) {
            let textToCheck = pendingBuffer.join(' ');
            let lastChar = textToCheck.trim().slice(-1);
            if (pendingBuffer.length >= 4 || ['.', '?', '!', ','].includes(lastChar)) {
                iframe.contentWindow.postMessage({action: 'caption', text: textToCheck}, '*');
                pendingBuffer = [];
            }
        }
    }, 1000);
})();
