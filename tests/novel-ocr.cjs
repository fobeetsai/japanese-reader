const assert = require('node:assert/strict');
const { cleanText, layoutOptions, detectGrid } = require('../static/master/novel-ocr.js');
assert.equal(cleanText('日 本 語 の 文章 を 読み ます 。\nSteel beam  120 kN'), '日本語の文章を読みます。\nSteel beam  120 kN');
assert.equal(layoutOptions('vertical').psm, '5');
assert.equal(layoutOptions('vertical').languages, 'jpn_vert');
assert.equal(layoutOptions('figure').psm, '11');
assert.match(layoutOptions('auto', 'mixed').languages, /chi_tra/);
const w = 400, h = 320, data = new Uint8ClampedArray(w * h * 4).fill(255);
function pixel(x, y, value = 0) { const i = (y * w + x) * 4; data[i] = data[i + 1] = data[i + 2] = value; }
assert.equal(detectGrid(data, w, h), null);
for (const y of [40, 120, 200, 280]) for (let x = 20; x <= 380; x++) for (let d = 0; d < 2; d++) pixel(x, y + d);
for (const x of [20, 140, 260, 380]) for (let y = 40; y <= 280; y++) for (let d = 0; d < 2; d++) pixel(x + d, y);
const grid = detectGrid(data, w, h);
assert.equal(grid.rows, 3); assert.equal(grid.cols, 3); assert.equal(grid.cells.length, 9);
assert.deepEqual(grid.cells.map(c => [c.row, c.col]), [[0,0],[0,1],[0,2],[1,0],[1,1],[1,2],[2,0],[2,1],[2,2]]);
// Merged/partial grid must not silently assign guessed cell boundaries.
for (let y = 125; y < 195; y++) for (let d = 0; d < 2; d++) pixel(140 + d, y, 255);
assert.equal(detectGrid(data, w, h), null);
console.log('PASS OCR layout, Japanese spacing, table cell coordinates and merged-grid rejection');
