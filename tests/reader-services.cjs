const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const S = require('../static/master/reader-services.js');

async function main() {
    const original = '安全基準を遵守しています。機械を使用しました。しかし、現在は購入しないことにしました。品質を確認してください。圧縮強度30 MPa、JIS A 5308、養生7日。';
    const outputs = ['n2_to_n3', 'n3_to_n4', 'easy_jp'].map(level => S.simplify(original, level));
    assert.ok(outputs.every(result => result.changed));
    assert.equal(new Set(outputs.map(result => result.simplifiedText)).size, 3);
    assert.match(outputs[0].simplifiedText, /守っています/);
    assert.match(outputs[1].simplifiedText, /使いました/);
    assert.match(outputs[2].simplifiedText, /買わない/);
    assert.match(outputs[2].simplifiedText, /確かめてください/);
    assert.deepEqual(S.facts(outputs[2].simplifiedText), S.facts(original));
    assert.equal(S.simplify('未確認事項と使用率を調べた。', 'easy_jp').simplifiedText, '未確認事項と使用率を調べた。');
    assert.equal(S.simplify('今日は学校へ行きます。', 'easy_jp').changed, false);
    assert.equal(S.simplify('猫です。犬です。', 'easy_jp').changed, false, 'formatting alone is not simplification');
    assert.equal(S.simplify('機械を使用していました。', 'easy_jp').simplifiedText, '機械を使っていました。');
    assert.equal(S.simplify('道具を購入しませんでした。', 'easy_jp').simplifiedText, '道具を買いませんでした。');
    assert.equal(S.simplify('可能とは限らない。', 'easy_jp').simplifiedText, '可能とは限らない。');
    const transformer = '変流器は、電流の大きさを変換するための装置で、大電流が流れる電路の計測や、保護継電器を動作させるために使う。低圧・高圧の大電流をそのまま計測しようとすると、測定機器の絶縁を…';
    const technical = S.simplify(transformer, 'n2_to_n3');
    assert.ok(technical.changed);
    assert.match(technical.simplifiedText, /変えるための装置です。\n/);
    assert.match(technical.simplifiedText, /計測（測ること）に使います。\nまた、保護継電器を動かすためにも使います。/);
    assert.match(technical.simplifiedText, /そのまま測ろうとすると/);
    assert.ok(technical.simplifiedText.endsWith('測定機器の絶縁を…'));
    assert.equal(technical.sentenceSplitCount, 2);
    assert.deepEqual(S.facts(technical.simplifiedText), S.facts(transformer));
    assert.equal(S.simplify(technical.simplifiedText, 'n2_to_n3').changed, false);
    assert.deepEqual(S.facts(S.simplify(transformer + transformer, 'easy_jp').simplifiedText), S.facts(transformer + transformer));
    assert.equal(S.simplify('この装置で、電流を測る。', 'n2_to_n3').simplifiedText, 'この装置で、電流を測る。');
    assert.match(S.simplify('信号を変換しない。装置を動作させない。電圧を測定しませんでした。', 'n2_to_n3').simplifiedText, /変えない。\n装置を動かさない。\n電圧を測りませんでした。/);
    assert.equal(S.audioChunks('あ'.repeat(5000)).join(''), 'あ'.repeat(5000));
    assert.equal(S.xml('A&B < > " \''), 'A&amp;B &lt; &gt; &quot; &apos;');

    const desktop = { name: 'Microsoft Haruka - Japanese', lang: 'ja-JP' };
    const neural = { name: 'Microsoft Nanami Online (Natural) - Japanese', lang: 'ja-JP' };
    const male = { name: 'Microsoft Keita Online (Natural) - Japanese', lang: 'ja-JP' };
    assert.equal(S.selectNatural([desktop], desktop.name), null);
    assert.equal(S.selectNatural([desktop, neural], desktop.name), neural);
    assert.equal(S.selectNatural([neural, male], male.name), male);
    assert.equal(S.isNatural({ name: neural.name, lang: 'en-US' }), false);
    assert.equal(S.isNatural({ name: 'Google 日本語', lang: 'ja-JP' }), false);

    let sent, options;
    global.fetch = async (url, config) => {
        sent = url; options = config;
        return { ok: true, json: async () => ({ candidates: [{ finishReason: 'STOP', content: { parts: [{ text: JSON.stringify({ text: '機械を使いました。30 MPa。', changes: [{ original: '使用しました', target: '使いました' }] }) }] } }] }) };
    };
    const rewritten = await S.rewrite('機械を使用しました。30 MPa。', 'easy_jp', 'fixture-only-key');
    assert.match(rewritten.simplifiedText, /使いました/);
    assert.ok(!sent.includes('fixture-only-key'));
    assert.equal(options.headers['x-goog-api-key'], 'fixture-only-key');
    assert.match(JSON.parse(options.body).systemInstruction.parts[0].text, /N4〜N5/);
    await assert.rejects(S.rewrite('原文', 'easy_jp', ''), /沒有內建 AI 通道/);
    global.fetch = async () => ({ ok: false, status: 429 });
    await assert.rejects(S.rewrite('原文', 'easy_jp', 'fixture'), /429/);
    for (const [text, finishReason, error] of [['機械を使いました。20 MPa。', 'STOP', /數值/], ['原文。', 'MAX_TOKENS', /未完成/], ['原文。', 'STOP', /相同/]]) {
        global.fetch = async () => ({ ok: true, json: async () => ({ candidates: [{ finishReason, content: { parts: [{ text: JSON.stringify({ text, changes: [] }) }] } }] }) });
        await assert.rejects(S.rewrite(text.includes('MPa') ? '機械を使用しました。30 MPa。' : '原文。', 'easy_jp', 'fixture'), error);
    }

    const audio = [], spoken = [], statuses = [];
    class FakeAudio {
        constructor(url) { this.url = url; audio.push(this); }
        play() { queueMicrotask(() => this.onended?.()); return Promise.resolve(); }
        pause() { this.paused = true; }
    }
    const env = {
        URL: { createObjectURL: () => 'blob:test', revokeObjectURL() {} },
        Audio: FakeAudio, setTimeout, clearTimeout,
        speechSynthesis: { getVoices: () => [desktop, neural], cancel() {}, speak(u) { spoken.push(u); queueMicrotask(() => u.onend?.()); } },
        SpeechSynthesisUtterance: class { constructor(text) { this.text = text; } },
        fetch: async (url, config) => { sent = url; options = config; return { ok: true, blob: async () => new Blob(['mp3 fixture']) }; }
    };
    const speech = S.createSpeech(env);
    await speech.speak('あ'.repeat(3500), { provider: 'edge', preferred: desktop.name }, s => statuses.push(s));
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(spoken.map(u => u.text).join(''), 'あ'.repeat(3500));
    assert.ok(spoken.every(u => u.voice === neural));
    await speech.speak('A&B、自然な日文です。', { provider: 'azure', key: 'fixture-only-key', region: 'eastasia', voice: 'ja-JP-NanamiNeural' }, s => statuses.push(s));
    assert.equal(sent, 'https://eastasia.tts.speech.microsoft.com/cognitiveservices/v1');
    assert.match(options.body, /NanamiNeural/);
    assert.match(options.body, /A&amp;B/);
    assert.equal(audio.length, 1);
    assert.equal(statuses.at(-1), '微軟自然人聲播放完成');
    await speech.speak('日文', { provider: 'azure', key: '', region: '', voice: 'ja-JP-NanamiNeural' }, s => statuses.push(s));
    assert.match(statuses.at(-1), /請先/);
    env.speechSynthesis.getVoices = () => [desktop];
    env.setTimeout = fn => setTimeout(fn, 0);
    await speech.speak('日文', { provider: 'edge' }, s => statuses.push(s));
    assert.match(statuses.at(-1), /HTTPS 與支援 WebSocket/);
    assert.equal(spoken.length, 3, 'no desktop fallback is spoken');

    // With no native natural voice, Edge must synthesize over WebSocket, not return a no-voice message.
    let socket;
    env.crypto = require('node:crypto').webcrypto;
    env.Blob = Blob;
    env.setTimeout = setTimeout;
    env.WebSocket = class {
        constructor(url) { socket = this; this.url = url; this.messages = []; queueMicrotask(() => this.onopen?.()); }
        send(message) {
            this.messages.push(message);
            if (!message.includes('Path:ssml')) return;
            queueMicrotask(() => {
                const header = new TextEncoder().encode('Content-Type:audio/mpeg\r\nPath:audio\r\n');
                const payload = new Uint8Array(2 + header.length + 4);
                payload[0] = header.length >> 8; payload[1] = header.length & 255;
                payload.set(header, 2); payload.set([1, 2, 3, 4], 2 + header.length);
                this.onmessage?.({ data: payload.buffer });
                this.onmessage?.({ data: 'Path:turn.end\r\n' });
            });
        }
        close() { this.closed = true; }
    };
    await speech.speak('A&B、こんにちは。', { provider: 'edge', voice: 'ja-JP-KeitaNeural' }, s => statuses.push(s));
    assert.equal(new URL(socket.url).hostname, 'speech.platform.bing.com');
    assert.match(socket.messages[1], /KeitaNeural/);
    assert.match(socket.messages[1], /A&amp;B/);
    assert.equal(audio.length, 2, 'cloud audio works without natural voices in getVoices');
    assert.equal(statuses.at(-1), '微軟自然人聲播放完成');
    assert.ok(socket.closed);
    env.WebSocket = class { constructor() { socket = this; } close() { this.closed = true; } };
    const controller = new AbortController();
    const pending = S.edgeAudio(env, 'こんにちは。', 'ja-JP-NanamiNeural', controller.signal);
    await new Promise(resolve => setImmediate(resolve)); controller.abort();
    await assert.rejects(pending, /已停止/);
    assert.ok(socket.closed);

    // Real reader controller: an older AI reply cannot overwrite edited input or a newer target.
    const html = fs.readFileSync('index.html', 'utf8');
    const start = html.indexOf('// 降維處理狀態'), end = html.indexOf('// 精選範例文摘', start);
    const nodes = new Map();
    const node = id => {
        if (!nodes.has(id)) {
            const classes = new Set();
            nodes.set(id, { value: '', style: {}, textContent: '', innerHTML: '',
                classList: { toggle() {}, add: value => classes.add(value), remove: value => classes.delete(value), contains: value => classes.has(value) } });
        }
        return nodes.get(id);
    };
    node('simplifyLevelSelect').value = 'easy_jp';
    const storage = new Map(), waiting = [];
    const service = { ...S, rewrite: text => new Promise(resolve => waiting.push({ text, resolve })) };
    const context = vm.createContext({ ReaderServices: service, AbortController, showToast() {}, escapeHtml: value => value,
        document: { getElementById: node, querySelectorAll: () => [] },
        localStorage: { getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value) },
        state: { analyzedData: null }, dom: { articleInput: node('articleInput'), inputCharCount: node('inputCharCount') } });
    vm.runInContext(html.slice(start, end), context);
    node('articleInput').value = original;
    await context.directSimplifyInputArticle();
    assert.equal(node('articleInput').value, outputs[2].simplifiedText);
    await context.directSimplifyInputArticle();
    context.revertOriginalInputArticle();
    assert.equal(node('articleInput').value, original, 'repeated simplification retains the first original');
    node('articleInput').value = transformer;
    await context.directSimplifyInputArticle();
    context.openSimplifyModal(false);
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(node('origTextDisplay').textContent, transformer, 'comparison retains source after shortcut');
    assert.equal(node('simplifiedTextarea').value, technical.simplifiedText);
    context.closeSimplifyModal();
    context.syncSimplifyEngine('ai');
    const old = context.directSimplifyInputArticle();
    node('articleInput').value = '新しい文章。';
    const newer = context.directSimplifyInputArticle();
    waiting[1].resolve({ simplifiedText: '新しい文。', changes: [], changed: true, engine: 'ai' });
    await newer;
    waiting[0].resolve({ simplifiedText: '旧文。', changes: [], changed: true, engine: 'ai' });
    await old;
    assert.equal(node('articleInput').value, '新しい文。');
    context.syncSimplifyEngine('rule');
    context.openSimplifyModal(false);
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(node('simplifyModal').style.display, 'flex');
    assert.equal(node('simplifyModal').classList.contains('open'), true, 'modal needs open state for opacity and pointer events');
    context.closeSimplifyModal();
    assert.equal(node('simplifyModal').classList.contains('open'), false);
    // Existing PWA blocks paid AI elsewhere; only this reader's explicit key/header is permitted.
    const listeners = {}, requests = [];
    let clientUrl = 'https://example.com/japanese-reader/index.html';
    const worker = vm.createContext({ URL, Response, Request, Promise,
        self: { registration: { scope: 'https://example.com/japanese-reader/' },
            clients: { get: async () => ({ url: clientUrl }) }, addEventListener: (name, handler) => listeners[name] = handler },
        fetch: async request => { requests.push(request); return new Response('fixture'); } });
    vm.runInContext(fs.readFileSync('sw.js', 'utf8'), worker);
    async function callWorker(url, headers) {
        let result;
        listeners.fetch({ clientId: 'test', request: new Request(url, { method: 'POST', headers }), respondWith: value => result = value });
        return await result;
    }
    const endpoint = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent';
    assert.equal((await callWorker(endpoint, { 'x-goog-api-key': 'fixture' })).status, 200);
    assert.equal(requests.length, 1);
    clientUrl = 'https://example.com/japanese-reader/master.html';
    assert.equal((await callWorker(endpoint, { 'x-goog-api-key': 'fixture' })).status, 410);
    clientUrl = 'https://example.com/japanese-reader/index.html';
    assert.equal((await callWorker(endpoint + '?key=old-path', {})).status, 410);
    assert.equal(requests.length, 1);
    console.log('PASS three levels, verb inflection, preserved facts, original recovery, stale rewrite rejection, AI errors, strict natural voice selection, Azure audio and long speech');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
