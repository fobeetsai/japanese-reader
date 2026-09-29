const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

for (const page of ['novel.html', '小說閱讀.html']) {
    const html = fs.readFileSync(path.join(__dirname, '..', page), 'utf8');
    const audioStart = html.indexOf('window.NovelAudio = {');
    const audioEnd = html.indexOf('// 全域相容 speakJapanese', audioStart);
    const grammarStart = html.indexOf('window.showNovelGrammarCard = function');
    const grammarEnd = html.indexOf('window.closeNovelGrammarModal = function', grammarStart);
    assert.ok(audioStart > 0 && audioEnd > audioStart && grammarStart > 0 && grammarEnd > grammarStart);

    const nodes = new Map();
    function node(id) {
        if (!nodes.has(id)) nodes.set(id, { style: {}, classList: { add() {}, remove() {} }, textContent: '', innerHTML: '' });
        return nodes.get(id);
    }
    node('novelVoiceSelect').value = 'nanami';
    const audios = [];
    class FakeAudio {
        constructor(url) { this.url = url; this.paused = true; audios.push(this); }
        play() { this.paused = false; return Promise.resolve(); }
        pause() { this.paused = true; }
    }
    const context = vm.createContext({
        window: { novelState: { repeatCount: 1 }, speechSynthesis: { getVoices: () => [{ name: 'Japanese Desktop', lang: 'ja-JP' }], cancel() {} } },
        document: { getElementById: node, querySelectorAll: () => [], querySelector: () => null },
        Audio: FakeAudio,
        GRAMMAR_DATA: [{ id: 42, title: '〜ながら', level: 'N3', form: '動詞ます形＋ながら', meaningZh: '一邊……一邊……', example: '歩きながら話す。' }],
        escapeHtml: value => String(value), escapeJsString: value => String(value),
        showToast() {}, setTimeout: fn => fn()
    });
    vm.runInContext(html.slice(audioStart, audioEnd), context, { filename: page + ':audio' });
    vm.runInContext(html.slice(grammarStart, grammarEnd), context, { filename: page + ':grammar' });

    context.window.showNovelGrammarCard(42);
    assert.equal(node('novelGrammarModal').style.display, 'flex');
    assert.equal(node('novelGrammarTitle').textContent, '〜ながら');
    assert.match(node('novelGrammarBody').innerHTML, /一邊……一邊……/);

    const engine = context.window.NovelAudio;
    assert.equal(engine.getVoiceConfig('nanami').voice, null, 'desktop voice must not masquerade as Nanami');
    assert.equal(engine.getVoiceConfig('keita').voice, null, 'desktop voice must not masquerade as Keita');
    assert.equal(engine.cloudChunks('あ'.repeat(400)).join(''), 'あ'.repeat(400), 'cloud speech must not truncate long sentences');
    let finished = 0;
    engine.speakSentence('海岸へ行って泳いだ。', null, () => { finished++; }, 1);
    assert.equal(audios.length, 1);
    assert.match(node('novelVoiceStatus').textContent, /雲端/);
    engine.pause();
    assert.equal(audios[0].paused, true);
    engine.resume();
    assert.equal(audios[0].paused, false);
    audios[0].onended();
    assert.equal(finished, 1);
    assert.equal(engine.status, 'idle');
    engine.speakSentence('時間を守る。', null, () => { finished++; }, 1);
    const last = audios.at(-1);
    engine.stop(false);
    assert.equal(last.paused, true);
    last.onended();
    assert.equal(finished, 1, 'stopped audio must not advance the reader');
    context.window.novelState.currentPageIndex = 1;
    context.window.novelState.pagesCache = { 1: { analyzed: { sentences: [
        { text: '一文目。' }, { text: '二文目。' }
    ] } } };
    engine.playWholePage();
    audios.at(-1).onended();
    assert.equal(engine.currentSentenceIdx, 1, 'whole-page reading must advance to the second sentence');
    audios.at(-1).onended();
    assert.equal(engine.status, 'idle', 'whole-page reading must finish');
    console.log(`PASS ${page} grammar card and natural/cloud audio fallback`);
}
