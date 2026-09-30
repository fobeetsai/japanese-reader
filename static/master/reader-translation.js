(function (root) {
    'use strict';
    const cache = new Map(), pending = new Map();
    function seed(entries) {
        for (const item of entries || []) if (typeof item.text === 'string' && typeof item.translation === 'string' && item.translation.trim()) cache.set(item.text.trim(), item.translation);
    }
    async function translate(value) {
        const text = String(value || '').trim();
        if (!text) return '';
        if (cache.has(text)) return cache.get(text);
        if (pending.has(text)) return pending.get(text);
        const job = (async () => {
            const controller = new AbortController();
            const timer = setTimeout(() => controller.abort(), 12000);
            try {
                const url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=ja&tl=zh-TW&dt=t&q=' + encodeURIComponent(text);
                const response = await fetch(url, { signal: controller.signal });
                if (!response.ok) return '';
                const data = await response.json();
                const result = Array.isArray(data?.[0]) ? data[0].map(row => typeof row?.[0] === 'string' ? row[0] : '').join('').trim() : '';
                if (result) cache.set(text, result);
                return result;
            } catch (_) { return ''; }
            finally { clearTimeout(timer); }
        })();
        pending.set(text, job);
        try { return await job; } finally { pending.delete(text); }
    }
    async function fill(sentences, onUpdate = () => {}, retry = false) {
        let cursor = 0;
        await Promise.all(Array.from({ length: Math.min(3, sentences.length) }, async () => {
            while (cursor < sentences.length) {
                const sentence = sentences[cursor++];
                if (!sentence.translation && (!sentence.translationAttempted || retry)) {
                    sentence.translationAttempted = true;
                    sentence.translation = await translate(sentence.text);
                }
                onUpdate();
            }
        }));
        return sentences;
    }
    const api = { seed, translate, fill };
    root.ReaderTranslation = api;
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
