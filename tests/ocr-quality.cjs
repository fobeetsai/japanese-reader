// Real OCR regression; requires tesseract.js@5.1.1 and @napi-rs/canvas.
// OCR_ENGINE_MODULE/OCR_CANVAS_MODULE can point to external test dependencies.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const drawing = require(process.env.OCR_CANVAS_MODULE || '@napi-rs/canvas');
const engine = require(process.env.OCR_ENGINE_MODULE || 'tesseract.js');
global.Image = class extends drawing.Image { get naturalWidth() { return this.width; } get naturalHeight() { return this.height; } };
global.document = { createElement: type => { assert.equal(type, 'canvas'); return drawing.createCanvas(1, 1); } };
const cachePath = process.env.OCR_CACHE_PATH || process.cwd();
global.Tesseract = { createWorker: async (lang, oem, options) => {
    const worker = await engine.createWorker(lang, oem, { ...options, cachePath });
    const original = worker.recognize;
    worker.recognize = (image, ...args) => original(image.toBuffer ? image.toBuffer('image/png') : image, ...args);
    return worker;
} };
const OCR = require('../static/master/novel-ocr.js');
const compact = s => String(s).replace(/\s/g, '');
function cer(actual, expected) {
    actual = compact(actual); expected = compact(expected);
    let prev = Array.from({ length: expected.length + 1 }, (_, i) => i);
    for (let i = 1; i <= actual.length; i++) {
        const next = [i];
        for (let j = 1; j <= expected.length; j++) next[j] = Math.min(next[j - 1] + 1, prev[j] + 1, prev[j - 1] + (actual[i - 1] === expected[j - 1] ? 0 : 1));
        prev = next;
    }
    return +(prev[expected.length] / expected.length).toFixed(4);
}
const cases = [
    { name: 'vertical', mode: 'vertical', expected: '日本語の文章を読みます。図面の内容を確認します。工事の安全を守ります。' },
    { name: 'table', mode: 'table', rows: [['項目','数量','単位'],['鉄筋','120','本'],['型枠','350','枚'],['安全確認','2','回']] },
    { name: 'figure', mode: 'auto', labels: ['作業の順序','計画','施工','確認','計画を立ててから施工を始めます。','作業後に品質を確認します。'] }
];
(async () => {
    const records = [];
    for (const c of cases) {
        const file = path.join(__dirname, 'fixtures', `ocr-${c.name}.png`);
        const old = await engine.createWorker(c.mode === 'vertical' ? 'jpn_vert' : 'jpn', 1, { cachePath });
        let baseline;
        try { baseline = (await old.recognize(file)).data.text; } finally { await old.terminate(); }
        const prepared = await OCR.prepareImage(file, { enhance: true });
        const current = await OCR.recognize(prepared, { mode: c.mode, language: 'japanese' });
        const record = { case: c.name, baseline, current };
        if (c.expected) { record.oldCER = cer(baseline, c.expected); record.newCER = cer(current.text, c.expected); record.pass = record.newCER < .1; }
        if (c.rows) { record.correctCells = current.rows.flat().filter((s, i) => compact(s) === compact(c.rows.flat()[i] || '')).length; record.totalCells = 12; record.pass = record.correctCells === 12; }
        if (c.labels) { record.labelsFound = c.labels.filter(s => current.text.split(/\n+/).map(compact).includes(compact(s))); record.pass = record.labelsFound.length === c.labels.length; }
        records.push(record); console.log(JSON.stringify(record, null, 2));
    }
    if (process.argv[2]) fs.writeFileSync(process.argv[2], JSON.stringify(records, null, 2));
    assert.ok(records.every(r => r.pass), 'One or more OCR quality gates failed.');
})().catch(e => { console.error(e); process.exitCode = 1; });
