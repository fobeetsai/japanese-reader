'use strict';
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const WebSocket = require('ws');
const services = require('../../static/master/reader-services.js');
const port = Number(process.env.READER_SPEECH_PORT || 17863);
const root = path.resolve(__dirname, '../..');
const origins = new Set(['https://fobeetsai.github.io', `http://127.0.0.1:${port}`, `http://localhost:${port}`]);
let active = 0;
class MicrosoftSocket extends WebSocket {
    constructor(url) {
        super(url, { handshakeTimeout: 15000, headers: {
            Origin: 'chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.3650.75 Safari/537.36 Edg/143.0.3650.75',
            Cookie: 'MUID=' + crypto.randomBytes(16).toString('hex').toUpperCase()
        } });
    }
}
const env = { WebSocket: MicrosoftSocket, crypto: crypto.webcrypto, Blob, setTimeout, clearTimeout };
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.wasm': 'application/wasm', '.bin': 'application/octet-stream' };
function json(res, status, value) { res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' }); res.end(JSON.stringify(value)); }
const server = http.createServer(async (req, res) => {
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    if (![ `127.0.0.1:${port}`, `localhost:${port}` ].includes(req.headers.host)) return json(res, 403, { error: 'Invalid host' });
    const origin = req.headers.origin;
    if (origin && !origins.has(origin)) return json(res, 403, { error: 'Origin not allowed' });
    if (origin) {
        res.setHeader('Access-Control-Allow-Origin', origin);
        res.setHeader('Vary', 'Origin');
    }
    if (req.method === 'OPTIONS') {
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
        res.setHeader('Access-Control-Allow-Private-Network', 'true');
        res.writeHead(204); return res.end();
    }
    const url = new URL(req.url, `http://127.0.0.1:${port}`);
    if (req.method === 'GET' && url.pathname === '/health') return json(res, 200, { service: 'japanese-reader-speech-relay', version: 1, voices: services.azureVoices });
    if (req.method === 'POST' && url.pathname === '/speech') {
        if (!origin || !/^application\/json(?:;|$)/i.test(req.headers['content-type'] || '')) return json(res, 403, { error: 'Use the reader website' });
        if (active >= 2) return json(res, 429, { error: '語音服務忙碌，請稍後重試。' });
        const parts = []; let size = 0;
        try {
            for await (const part of req) {
                size += part.length;
                if (size > 20000) return json(res, 413, { error: '請分段朗讀。' });
                parts.push(part);
            }
            const { text, voice } = JSON.parse(Buffer.concat(parts).toString('utf8'));
            if (typeof text !== 'string' || !text.trim() || text.length > 1800 || !services.azureVoices.includes(voice)) return json(res, 400, { error: '語音或文字格式不正確。' });
            active++;
            const controller = new AbortController();
            const cancel = () => { if (!res.writableEnded) controller.abort(); };
            res.on('close', cancel);
            try {
                const blob = await services.edgeAudio(env, text, voice, controller.signal);
                if (controller.signal.aborted) return;
                res.writeHead(200, { 'Content-Type': 'audio/mpeg', 'Content-Length': blob.size });
                res.end(Buffer.from(await blob.arrayBuffer()));
            } finally { active--; res.off('close', cancel); }
        } catch (error) {
            if (!res.destroyed && !res.headersSent) json(res, 502, { error: '微軟語音暫時無法取得，請確認網路並重試。' });
        }
        return;
    }
    if (req.method !== 'GET') return json(res, 404, { error: 'Not found' });
    // Serve only the reader and its public assets; never expose .git, tools or user files.
    const name = url.pathname === '/' ? '/index.html' : url.pathname;
    if (['/master.html', '/kanji.html', '/flashcard.html'].includes(name)) { res.writeHead(302, { Location: 'https://fobeetsai.github.io/japanese-reader' + name }); return res.end(); }
    if (!(name === '/index.html' || name === '/japanese_reader.html' || name.startsWith('/static/')) || name.split('/').some(segment => segment.startsWith('.'))) return json(res, 404, { error: 'Not found' });
    const file = path.resolve(root, '.' + name);
    if (!file.startsWith(root + path.sep)) return json(res, 404, { error: 'Not found' });
    try {
        const data = await fs.readFile(file);
        res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' }); res.end(data);
    } catch { json(res, 404, { error: 'Not found' }); }
});
server.listen(port, '127.0.0.1', () => console.log(`Japanese Reader Chrome: http://127.0.0.1:${port}/index.html`));
server.on('error', error => { console.error(error.code === 'EADDRINUSE' ? 'Reader speech port is already in use.' : error.message); process.exitCode = 1; });
