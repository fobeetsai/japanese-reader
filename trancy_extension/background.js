/**
 * Trancy Dual - Background Service Worker
 * Native Edge Neural Speech (ja-JP-NanamiNeural / ja-JP-KeitaNeural) Synthesizer
 */

const WIN_EPOCH = 11644473600;
const S_TO_NS = 1e9;
const TRUSTED_CLIENT_TOKEN = '6A5AA1D4EAFF4E9FB37E23D68491D6F4';

// Generate dynamic Sec-MS-GEC token for Edge TTS
async function generateSecMsGec() {
  let ticks = Date.now() / 1000 + WIN_EPOCH;
  ticks -= ticks % 300;
  ticks *= S_TO_NS / 100;
  const str = `${ticks.toFixed(0)}${TRUSTED_CLIENT_TOKEN}`;
  const enc = new TextEncoder().encode(str);
  const hashBuf = await crypto.subtle.digest('SHA-256', enc);
  return Array.from(new Uint8Array(hashBuf))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')
    .toUpperCase();
}

function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  }).replace(/-/g, '').toUpperCase();
}

// Convert ArrayBuffer / Uint8Array to base64 Data URL
function bufferToDataUrl(buffer, mimeType = 'audio/mp3') {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return `data:${mimeType};base64,${btoa(binary)}`;
}

// Synthesize Microsoft Edge Neural Voice via WebSocket
async function synthesizeEdgeNeuralTTS(text, voice = 'ja-JP-NanamiNeural', speed = 1.0) {
  return new Promise(async (resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('Edge TTS timeout'));
    }, 6000);

    try {
      const secMsGec = await generateSecMsGec();
      const connId = generateUUID();
      const reqId = generateUUID();
      const nowStr = new Date().toUTCString();

      const wsUrl = `wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=${TRUSTED_CLIENT_TOKEN}&Sec-MS-GEC=${secMsGec}&Sec-MS-GEC-Version=1-130.0.2849.68&ConnectionId=${connId}`;
      const ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';

      const audioChunks = [];

      // Rate in SSML: e.g. +20% or -15%
      const ratePct = Math.round((speed - 1) * 100);
      const rateStr = (ratePct >= 0 ? `+${ratePct}%` : `${ratePct}%`);

      const configMsg = 
        'Content-Type:application/json; charset=utf-8\r\nPath:speech.config\r\n\r\n' +
        JSON.stringify({
          context: {
            synthesis: {
              audio: {
                metadataoptions: {
                  sentenceBoundaryEnabled: false,
                  wordBoundaryEnabled: false
                },
                outputFormat: 'audio-24khz-48kbitrate-mono-mp3'
              }
            }
          }
        });

      const ssmlMsg = 
        `X-RequestId:${reqId}\r\n` +
        'Content-Type:application/ssml+xml\r\n' +
        `X-Timestamp:${nowStr}\r\n` +
        'Path:ssml\r\n\r\n' +
        `<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ja-JP">` +
        `<voice name="${voice}">` +
        `<prosody pitch="+0Hz" rate="${rateStr}">${text}</prosody>` +
        `</voice></speak>`;

      ws.onopen = () => {
        ws.send(configMsg);
        ws.send(ssmlMsg);
      };

      ws.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
          const view = new DataView(event.data);
          if (view.byteLength > 2) {
            const headerLen = view.getUint16(0);
            if (headerLen > 0 && view.byteLength >= headerLen + 2) {
              const headerBytes = new Uint8Array(event.data, 2, headerLen);
              const headerText = new TextDecoder().decode(headerBytes);
              if (headerText.includes('Path:audio')) {
                const audioData = new Uint8Array(event.data, headerLen + 2);
                audioChunks.push(audioData);
              }
            }
          }
        } else if (typeof event.data === 'string') {
          if (event.data.includes('Path:turn.end')) {
            clearTimeout(timeout);
            ws.close();

            // Merge all audio chunks
            const totalLen = audioChunks.reduce((acc, c) => acc + c.length, 0);
            const combined = new Uint8Array(totalLen);
            let offset = 0;
            for (let chunk of audioChunks) {
              combined.set(chunk, offset);
              offset += chunk.length;
            }

            const dataUrl = bufferToDataUrl(combined.buffer);
            resolve(dataUrl);
          }
        }
      };

      ws.onerror = (err) => {
        clearTimeout(timeout);
        reject(err);
      };

      ws.onclose = () => {
        clearTimeout(timeout);
      };

    } catch (err) {
      clearTimeout(timeout);
      reject(err);
    }
  });
}

// Fallback: Google Cloud HD Natural Voice
async function fetchGoogleCloudTTS(text) {
  const url = `https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=ja&q=${encodeURIComponent(text.slice(0, 180))}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error('Google TTS HTTP error ' + resp.status);
  const buf = await resp.arrayBuffer();
  return bufferToDataUrl(buf);
}

// Message Dispatcher
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'synthesize_speech') {
    const text = request.text || '';
    const voiceChoice = request.voice || 'nanami'; // 'nanami', 'keita', 'google-hd'
    const speed = request.speed || 1.0;

    let voiceName = 'ja-JP-NanamiNeural';
    if (voiceChoice === 'keita') {
      voiceName = 'ja-JP-KeitaNeural';
    }

    if (voiceChoice === 'google-hd') {
      fetchGoogleCloudTTS(text)
        .then(audioUrl => sendResponse({ success: true, audioUrl }))
        .catch(err => sendResponse({ success: false, error: err.toString() }));
      return true;
    }

    // Edge Neural TTS with Google Cloud HD Fallback
    synthesizeEdgeNeuralTTS(text, voiceName, speed)
      .then(audioUrl => {
        sendResponse({ success: true, audioUrl });
      })
      .catch(err => {
        console.warn('Edge TTS direct websocket failed, falling back to Google Cloud HD:', err);
        fetchGoogleCloudTTS(text)
          .then(audioUrl => sendResponse({ success: true, audioUrl }))
          .catch(e => sendResponse({ success: false, error: e.toString() }));
      });

    return true; // async sendResponse
  }
});
