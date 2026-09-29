/* Context-aware reading labels shared by Reading Master and Novel Reader. */
(function (root, factory) {
    const api = factory();
    root.ReaderReading = api;
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
    const isKanji = char => /[\u3400-\u9fff]/.test(char);
    const toHiragana = text => String(text || '').replace(/[\u30a1-\u30f6]/g, char => String.fromCharCode(char.charCodeAt(0) - 0x60));
    const toKatakana = text => String(text || '').replace(/[\u3041-\u3096]/g, char => String.fromCharCode(char.charCodeAt(0) + 0x60));
    const listReadings = text => String(text || '').split(/[,、]/).map(item => toHiragana(item.trim().replace(/\(.*?\)/g, '').replace(/[-－]/g, ''))).filter(Boolean);
    const voiced = {
        か: 'が', き: 'ぎ', く: 'ぐ', け: 'げ', こ: 'ご',
        さ: 'ざ', し: 'じ', す: 'ず', せ: 'ぜ', そ: 'ぞ',
        た: 'だ', ち: 'ぢ', つ: 'づ', て: 'で', と: 'ど',
        は: 'ば', ひ: 'び', ふ: 'ぶ', へ: 'べ', ほ: 'ぼ'
    };

    function variants(reading) {
        const result = [reading];
        if (voiced[reading[0]]) result.push(voiced[reading[0]] + reading.slice(1));
        if (reading[0] === 'は') result.push('ぱ' + reading.slice(1));
        if (/[くちつ]$/.test(reading)) result.push(reading.slice(0, -1) + 'っ');
        return [...new Set(result)];
    }

    // Match the complete surface and the complete pronunciation. A partial
    // substring match cannot establish whether an individual kanji is on/kun.
    function classifyWord(word, reading, dictionary, jukujikun = {}) {
        const surface = String(word || '');
        const spoken = toHiragana(reading).trim();
        if (!surface || !spoken || !dictionary) return [];
        const kanjiCount = [...surface].filter(isKanji).length;
        if (!kanjiCount) return [];

        if (jukujikun[surface] === spoken) {
            return [...surface].map((char, index) => isKanji(char) ? { index, char, type: 'jukuji', reading: spoken } : null).filter(Boolean);
        }

        const containsKana = /[\u3040-\u30ff]/.test(surface);
        const memo = new Map();
        function solve(surfaceIndex, readingIndex) {
            const key = surfaceIndex + ':' + readingIndex;
            if (memo.has(key)) return memo.get(key);
            if (surfaceIndex === surface.length) return readingIndex === spoken.length ? { score: 0, parts: [] } : null;
            const char = surface[surfaceIndex];
            if (!isKanji(char)) {
                const kana = toHiragana(char);
                const next = spoken.startsWith(kana, readingIndex) ? solve(surfaceIndex + 1, readingIndex + kana.length) : null;
                memo.set(key, next);
                return next;
            }
            const entry = dictionary[char];
            if (!entry) { memo.set(key, null); return null; }
            let best = null;
            for (const [type, source] of [['on', entry[2]], ['kun', entry[3]]]) {
                for (const base of listReadings(source)) {
                    for (const actual of variants(base)) {
                        if (!spoken.startsWith(actual, readingIndex)) continue;
                        const next = solve(surfaceIndex + 1, readingIndex + actual.length);
                        if (!next) continue;
                        const preference = containsKana ? (type === 'kun' ? 2 : 0) : (type === 'on' ? 1 : 0);
                        const option = {
                            score: next.score + preference + actual.length / 100,
                            parts: [{ index: surfaceIndex, char, type, reading: actual }, ...next.parts]
                        };
                        if (!best || option.score > best.score) best = option;
                    }
                }
            }
            memo.set(key, best);
            return best;
        }
        const found = solve(0, 0);
        if (found) return found.parts;
        return [...surface].map((char, index) => isKanji(char) ? { index, char, type: 'unknown', reading: '' } : null).filter(Boolean);
    }

    function wordKind(parts) {
        const types = new Set(parts.map(part => part.type));
        if (!parts.length || types.has('unknown')) return '讀法待確認';
        if (types.has('jukuji')) return '熟字訓（整詞讀法）';
        if (types.size > 1) return '音訓混讀';
        return types.has('on') ? '漢語型・音讀' : '和語型・訓讀';
    }

    // 行く (いく) and 行う (おこなう) share 行った/行って. The object
    // particle points to 行う; a destination particle points to 行く.
    function resolveAmbiguousBase(surface, sentence, start) {
        if (surface !== '行った' && surface !== '行って') return null;
        const before = String(sentence || '').slice(Math.max(0, start - 16), start);
        if (/(?:を|が)(?:\s*)$/.test(before) && !/[へに](?:\s*)$/.test(before)) return '行う';
        return '行く';
    }

    return { classifyWord, wordKind, resolveAmbiguousBase, toHiragana, toKatakana };
});
