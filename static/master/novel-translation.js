(function (root) {
    'use strict';
    const jobs = new WeakMap();
    let mode = 'show';
    try { mode = localStorage.getItem('novel_translation_mode') || 'show'; } catch (_) {}
    if (!['show', 'mask', 'hide'].includes(mode)) mode = 'show';
    const current = () => root.novelState?.pagesCache[root.novelState.currentPageIndex];
    function ensure(page, retry = false, update) {
        if (!page?.analyzed) return Promise.resolve([]);
        if (jobs.has(page)) return jobs.get(page);
        const job = root.ReaderTranslation.fill(page.analyzed.sentences, update, retry);
        jobs.set(page, job);
        job.finally(() => jobs.delete(page));
        return job;
    }
    function draw(page) {
        if (current() !== page) return;
        const panel = document.getElementById('novelTranslationPanel');
        panel.hidden = mode === 'hide';
        if (panel.hidden) return;
        const list = document.getElementById('novelTranslationList');
        list.replaceChildren();
        const sentences = page.analyzed.sentences;
        for (const [index, sentence] of sentences.entries()) {
            const row = document.createElement('div'); row.className = 'novel-translation-row';
            const jp = document.createElement('p'); jp.lang = 'ja'; jp.textContent = sentence.text; row.append(jp);
            const zh = document.createElement('button'); zh.type = 'button'; zh.className = 'novel-translation-text'; zh.lang = 'zh-Hant';
            let revealed = mode === 'show';
            const paint = () => {
                zh.textContent = !sentence.translation ? (jobs.has(page) ? '翻譯中…' : '暫無譯文，請按「重試翻譯」。') : revealed ? sentence.translation : '中文已遮蔽，點擊顯示';
                zh.classList.toggle('is-masked', !!sentence.translation && !revealed);
                zh.setAttribute('aria-label', `第 ${index + 1} 句中文：${!sentence.translation ? zh.textContent : revealed ? sentence.translation + '（點擊遮蔽）' : '已遮蔽，點擊顯示'}`);
                zh.setAttribute('aria-expanded', String(revealed && !!sentence.translation));
                zh.disabled = !sentence.translation;
            };
            zh.onclick = () => { revealed = !revealed; paint(); }; paint(); row.append(zh); list.append(row);
        }
        const translated = sentences.filter(s => s.translation).length;
        document.getElementById('btnRetryNovelTranslation').disabled = jobs.has(page);
        document.getElementById('novelTranslationStatus').textContent = `${jobs.has(page) ? '翻譯中' : translated < sentences.length ? '部分譯文暫不可用' : '翻譯完成'}：${translated} / ${sentences.length} 句。${!jobs.has(page) && translated < sentences.length ? '可按重試翻譯。' : 'Google 機器翻譯，請與日文原文核對。'}`;
    }
    async function render(retry = false) {
        const page = current();
        if (!page?.analyzed) return;
        const panel = document.getElementById('novelTranslationPanel'); panel.hidden = mode === 'hide';
        if (panel.hidden && !retry) return;
        const job = ensure(page, retry, () => draw(page));
        draw(page);
        await job;
        draw(page);
    }
    function install() {
        const select = document.getElementById('novelTranslationMode'); select.value = mode;
        select.onchange = () => {
            mode = select.value;
            try { localStorage.setItem('novel_translation_mode', mode); } catch (_) {}
            render();
        };
        document.getElementById('btnRetryNovelTranslation').onclick = async () => {
            await render(true);
            root.syncNovelLearningPage?.();
        };
    }
    root.NovelTranslation = { install, render, ensure };
})(window);
