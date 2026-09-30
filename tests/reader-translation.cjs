const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const Reader = require('../static/master/reader-translation.js');
(async () => {
    let calls = 0, active = 0, maximum = 0;
    global.fetch = async url => {
        calls++; maximum = Math.max(maximum, ++active);
        await new Promise(resolve => setImmediate(resolve)); active--;
        const text = new URL(url).searchParams.get('q');
        return { ok: true, json: async () => [[[`中文:${text}`]]] };
    };
    const together = await Promise.all([Reader.translate('同じ文。'), Reader.translate('同じ文。')]);
    assert.deepEqual(together, ['中文:同じ文。','中文:同じ文。']); assert.equal(calls, 1);
    await Reader.translate('同じ文。'); assert.equal(calls, 1);
    const sentences = Array.from({ length: 8 }, (_, i) => ({ text: `文${i}。` }));
    await Reader.fill(sentences); assert.equal(maximum, 3); assert.ok(sentences.every(s => s.translation));
    global.fetch = async () => ({ ok: false });
    const failed = [{ text: '失敗を再試行。' }];
    await Reader.fill(failed); assert.equal(failed[0].translation, '');
    global.fetch = async () => ({ ok: true, json: async () => [[['重試成功']]] });
    await Reader.fill(failed); assert.equal(failed[0].translation, '', 'failed requests should not retry on every render');
    await Reader.fill(failed, () => {}, true); assert.equal(failed[0].translation, '重試成功');
    const timed = vm.createContext({ AbortController, setTimeout: fn => setImmediate(fn), clearTimeout: clearImmediate,
        fetch: (_, {signal}) => new Promise((_, reject) => signal.addEventListener('abort', () => reject(new Error('timeout')))) });
    vm.runInContext(fs.readFileSync('static/master/reader-translation.js','utf8'),timed);
    assert.equal(await timed.ReaderTranslation.translate('時間制限。'), '', 'a stalled translator must settle so the reading bridge can continue');

    // A delayed older bridge import must not replace a newer page or its Chinese text.
    const html = fs.readFileSync('master.html','utf8');
    const start = html.indexOf('        let novelLoadGeneration = 0;');
    const end = html.indexOf('        function renderReaderView()', start);
    const waiting = new Map(), state = {}, selected = [];
    const dom = { articleInput: {}, readerArticleTitle: {}, inputCharCount: {}, chkAutoTranslate: {} };
    const context = vm.createContext({ window: { ReaderTranslation: Reader, switchMasterView() {} }, dom, state, TRANSLATE_CACHE: new Map(),
        clientAnalyzeText: text => new Promise(resolve => waiting.set(text, resolve)), renderReaderView() {}, selectSentence: index => selected.push(index), openNotebookModal() {} });
    vm.runInContext(html.slice(start,end),context);
    const old = context.window.loadNovelPageIntoMaster({ title:'old', text:'旧。', translations:[{text:'旧。',translation:'舊頁'}] });
    const recent = context.window.loadNovelPageIntoMaster({ title:'new', text:'新。', translations:[{text:'新。',translation:'新頁'}] });
    waiting.get('新。')({ sentences:[{text:'新。'}] }); await recent;
    waiting.get('旧。')({ sentences:[{text:'旧。'}] }); await old;
    assert.equal(dom.readerArticleTitle.textContent,'new'); assert.equal(state.analyzedData.sentences[0].translation,'新頁');
    assert.equal(dom.chkAutoTranslate.checked,true); assert.equal(selected.length,1);
    console.log('PASS translation deduplication, concurrency, failure retry and stale iframe page rejection');
})().catch(e => { console.error(e); process.exitCode=1; });
