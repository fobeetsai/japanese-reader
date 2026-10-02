const assert = require('node:assert/strict');
const path = require('node:path');
const { spawn } = require('node:child_process');
const port = 17864, base = `http://127.0.0.1:${port}`;
const child = spawn(process.execPath, [path.join(__dirname, '../tools/speech-relay/server.cjs')], {
    env: { ...process.env, READER_SPEECH_PORT: String(port) }, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe']
});
async function main() {
    await new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error('relay startup timeout')), 5000);
        child.stdout.once('data', () => { clearTimeout(timer); resolve(); });
        child.once('exit', code => { clearTimeout(timer); reject(new Error('relay exited ' + code)); });
    });
    assert.equal((await (await fetch(base + '/health')).json()).service, 'japanese-reader-speech-relay');
    assert.equal((await fetch(base + '/index.html')).status, 200);
    for (const route of ['/.git/config', '/tools/speech-relay/server.cjs', '/static/../.git/config']) assert.equal((await fetch(base + route)).status, 404);
    const body = { text: 'こんにちは。', voice: 'https://invalid.example/audio' };
    const post = (origin, value, type = 'application/json') => fetch(base + '/speech', { method: 'POST', headers: { Origin: origin, 'Content-Type': type }, body: JSON.stringify(value) });
    assert.equal((await post('https://invalid.example', body)).status, 403);
    assert.equal((await post('https://fobeetsai.github.io', body, 'text/plain')).status, 403);
    assert.equal((await post('https://fobeetsai.github.io', body)).status, 400);
    assert.equal((await post(base, { text: 'あ'.repeat(1801), voice: 'ja-JP-NanamiNeural' })).status, 400);
    const preflight = await fetch(base + '/speech', { method: 'OPTIONS', headers: { Origin: 'https://fobeetsai.github.io' } });
    assert.equal(preflight.status, 204);
    assert.equal(preflight.headers.get('Access-Control-Allow-Origin'), 'https://fobeetsai.github.io');
    console.log('PASS relay origin, request bounds, voice allowlist, private file protection and Chrome CORS');
}
main().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => child.kill());
