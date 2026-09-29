const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const reading = require('../static/master/reading-accuracy.js');

const source = fs.readFileSync(path.join(__dirname, '../master.html'), 'utf8');
const start = source.indexOf('const KANJI_DICT = ');
assert.ok(start >= 0);
const jsonStart = source.indexOf('{', start);
const jsonEnd = source.indexOf('};', jsonStart) + 1;
const dictionary = JSON.parse(source.slice(jsonStart, jsonEnd));

function expect(word, spoken, types, kind) {
    const parts = reading.classifyWord(word, spoken, dictionary);
    assert.deepEqual(parts.map(part => part.type), types, `${word} (${spoken})`);
    assert.equal(reading.wordKind(parts), kind, word);
}

expect('行って', 'いって', ['kun'], '和語型・訓讀');
expect('行った', 'おこなった', ['kun'], '和語型・訓讀');
expect('時間', 'じかん', ['on', 'on'], '漢語型・音讀');
expect('手紙', 'てがみ', ['kun', 'kun'], '和語型・訓讀');
expect('施工', 'しこう', ['on', 'on'], '漢語型・音讀');
expect('時間', 'ざざざ', ['unknown', 'unknown'], '讀法待確認');
assert.equal(reading.wordKind(reading.classifyWord('今日', 'きょう', dictionary, { 今日: 'きょう' })), '熟字訓（整詞讀法）');
assert.equal(reading.resolveAmbiguousBase('行って', '海岸へ行って泳いだ', 3), '行く');
assert.equal(reading.resolveAmbiguousBase('行った', '会議を行った', 3), '行う');
assert.equal(reading.toKatakana('こう, ぎょう'), 'コウ, ギョウ');
assert.equal(reading.toHiragana('カン, ケン'), 'かん, けん');
console.log('PASS reading classification and context cases');
