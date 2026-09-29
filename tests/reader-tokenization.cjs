const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ReaderReading = require('../static/master/reading-accuracy.js');

for (const page of ['master.html', 'novel.html']) {
    const html = fs.readFileSync(path.join(__dirname, '..', page), 'utf8');
    const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)].map(match => match[1]);
    const data = scripts.find(script => script.includes('const KANJI_DICT'));
    const analyzer = scripts.find(script => script.includes('function tokenizeSentence'));
    assert.ok(data && analyzer, page);
    const context = vm.createContext({
        window: { ReaderReading },
        document: { getElementById: () => null, addEventListener: () => {}, querySelectorAll: () => [] },
        localStorage: { getItem: () => null, setItem: () => {} },
        matchMedia: () => ({ matches: false }),
        console,
        escapeHtml: value => String(value),
        setTimeout: () => 0,
        fetch: async () => { throw new Error('network disabled during test'); }
    });
    vm.runInContext(data, context, { filename: page + ':data' });
    vm.runInContext(analyzer, context, { filename: page + ':analyzer' });
    function tokens(sentence) {
        return vm.runInContext(`tokenizeSentence(${JSON.stringify(sentence)})`, context);
    }
    for (const [sentence, expected] of [
        ['海岸へ行って泳いだ。', 'いって'],
        ['学校へ行った。', 'いった'],
        ['会議を行った。', 'おこなった']
    ]) {
        const token = tokens(sentence).find(item => item.surface === '行って' || item.surface === '行った');
        assert.ok(token, `${page}: missing 行 token in ${sentence}`);
        assert.equal(token.reading, expected, `${page}: ${sentence}`);
    }
    vm.runInContext('initGrammarPatterns()', context);
    const falseCitation = vm.runInContext('findSentenceGrammars("海岸へ行って泳いだ。", tokenizeSentence("海岸へ行って泳いだ。"))', context);
    assert.ok(!falseCitation.some(item => item.title.includes('引用')), `${page}: 行って is not a quotation`);
    const realCitation = vm.runInContext('findSentenceGrammars("明日行くって。", tokenizeSentence("明日行くって。"))', context);
    assert.ok(realCitation.some(item => item.title.includes('引用')), `${page}: 行くって remains a quotation`);
    const kunHtml = vm.runInContext('getKanjiReadingsHtml("行って", "いって")', context);
    assert.match(kunHtml, /和語型・訓讀/);
    assert.match(kunHtml, /【訓讀】/);
    assert.match(kunHtml, /コウ, ギョウ, アン/);
    const onHtml = vm.runInContext('getKanjiReadingsHtml("時間", "じかん")', context);
    assert.match(onHtml, /漢語型・音讀/);
    assert.match(onHtml, /【音讀】/);
    assert.match(onHtml, /ジ/);
    console.log(`PASS ${page} contextual 行く/行う readings`);
}
