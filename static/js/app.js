/**
 * 日文閱讀助手 (Japanese Reading Assistant) - 前端核心互動邏輯
 * 仿 句解霸 (en998) 閱讀拆解理念・深度聯動《絵でわかる日本語》941文法
 */

// 全域狀態管理
const state = {
    analyzedData: null,
    currentSentenceIdx: 0,
    rubyMode: 'show', // 'show' | 'hide' | 'mask'
    enableWordColors: true,
    enableGrammar: true,
    enableTranslation: true,
    fontSizeLevel: 0, // -2 to +4
    theme: 'light',
    notebook: {
        words: [],
        grammars: []
    },
    sampleArticles: []
};

// DOM 元素快取
const dom = {
    // Header
    btnRubyShow: document.getElementById('btnRubyShow'),
    btnRubyHide: document.getElementById('btnRubyHide'),
    btnRubyMask: document.getElementById('btnRubyMask'),
    btnToggleWordColors: document.getElementById('btnToggleWordColors'),
    btnToggleGrammar: document.getElementById('btnToggleGrammar'),
    btnToggleTranslation: document.getElementById('btnToggleTranslation'),
    btnOpenNotebook: document.getElementById('btnOpenNotebook'),
    notebookCount: document.getElementById('notebookCount'),
    btnThemeToggle: document.getElementById('btnThemeToggle'),
    themeIcon: document.getElementById('themeIcon'),

    // Input
    inputCard: document.getElementById('inputCard'),
    tabPasteBtn: document.getElementById('tabPasteBtn'),
    tabUrlBtn: document.getElementById('tabUrlBtn'),
    panelPaste: document.getElementById('panelPaste'),
    panelUrl: document.getElementById('panelUrl'),
    articleInput: document.getElementById('articleInput'),
    urlInput: document.getElementById('urlInput'),
    btnFetchUrl: document.getElementById('btnFetchUrl'),
    btnClearInput: document.getElementById('btnClearInput'),
    sampleButtonsList: document.getElementById('sampleButtonsList'),
    inputCharCount: document.getElementById('inputCharCount'),
    chkAutoTranslate: document.getElementById('chkAutoTranslate'),
    btnStartReading: document.getElementById('btnStartReading'),
    loadingState: document.getElementById('loadingState'),

    // Reader Deck
    readerDeck: document.getElementById('readerDeck'),
    readerArticleTitle: document.getElementById('readerArticleTitle'),
    articleStatsBadges: document.getElementById('articleStatsBadges'),
    articleContentBox: document.getElementById('articleContentBox'),
    btnFontDecr: document.getElementById('btnFontDecr'),
    btnFontIncr: document.getElementById('btnFontIncr'),
    btnNewArticle: document.getElementById('btnNewArticle'),

    // Analyzer Column (Right)
    currentSentenceBadge: document.getElementById('currentSentenceBadge'),
    selectedSentenceJp: document.getElementById('selectedSentenceJp'),
    selectedSentenceZh: document.getElementById('selectedSentenceZh'),
    sentenceGrammarCount: document.getElementById('sentenceGrammarCount'),
    sentenceGrammarsList: document.getElementById('sentenceGrammarsList'),
    sentenceWordCount: document.getElementById('sentenceWordCount'),
    sentenceWordsTbody: document.getElementById('sentenceWordsTbody'),
    btnPlaySentenceAudio: document.getElementById('btnPlaySentenceAudio'),
    btnPrevSentence: document.getElementById('btnPrevSentence'),
    btnNextSentence: document.getElementById('btnNextSentence'),

    // Word Popover
    wordPopover: document.getElementById('wordPopover'),
    popoverWordSurface: document.getElementById('popoverWordSurface'),
    popoverWordLevel: document.getElementById('popoverWordLevel'),
    popoverWordKana: document.getElementById('popoverWordKana'),
    popoverWordPos: document.getElementById('popoverWordPos'),
    popoverWordMeaning: document.getElementById('popoverWordMeaning'),
    btnPlayWordAudio: document.getElementById('btnPlayWordAudio'),
    btnAddWordToNotebook: document.getElementById('btnAddWordToNotebook'),

    // Grammar Drawer
    grammarDrawerOverlay: document.getElementById('grammarDrawerOverlay'),
    drawerGrammarLevel: document.getElementById('drawerGrammarLevel'),
    drawerGrammarTitle: document.getElementById('drawerGrammarTitle'),
    drawerGrammarExternalLink: document.getElementById('drawerGrammarExternalLink'),
    btnDrawerFav: document.getElementById('btnDrawerFav'),
    drawerGrammarBody: document.getElementById('drawerGrammarBody'),

    // Notebook Modal
    notebookModal: document.getElementById('notebookModal'),
    nbWordCount: document.getElementById('nbWordCount'),
    nbGrammarCount: document.getElementById('nbGrammarCount'),
    tabNotebookWordsBtn: document.getElementById('tabNotebookWordsBtn'),
    tabNotebookGrammarsBtn: document.getElementById('tabNotebookGrammarsBtn'),
    notebookListArea: document.getElementById('notebookListArea'),
    btnExportNotebook: document.getElementById('btnExportNotebook'),
    btnClearNotebook: document.getElementById('btnClearNotebook'),

    // Toast
    toast: document.getElementById('toast'),
    toastMsg: document.getElementById('toastMsg')
};

// ==========================================================================
// 初始化與事件監聽
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
    loadSavedSettings();
    loadNotebook();
    setupEventListeners();
    fetchSampleArticles();
});

function loadSavedSettings() {
    // 讀音模式
    const savedRuby = localStorage.getItem('japanese_reader_ruby_mode') || 'show';
    setRubyMode(savedRuby);

    // 主題
    const savedTheme = localStorage.getItem('japanese_reader_theme') || 'light';
    setTheme(savedTheme);

    // 單字顏色
    const savedWordColors = localStorage.getItem('japanese_reader_word_colors') !== 'false';
    setWordColors(savedWordColors);

    // 文型標註
    const savedGrammar = localStorage.getItem('japanese_reader_grammar') !== 'false';
    setGrammarHighlight(savedGrammar);

    // 逐句翻譯
    const savedTrans = localStorage.getItem('japanese_reader_trans') !== 'false';
    setTranslationDisplay(savedTrans);
}

function setupEventListeners() {
    // 假名模式切換
    dom.btnRubyShow.addEventListener('click', () => setRubyMode('show'));
    dom.btnRubyHide.addEventListener('click', () => setRubyMode('hide'));
    dom.btnRubyMask.addEventListener('click', () => setRubyMode('mask'));

    // 單字色彩切換
    dom.btnToggleWordColors.addEventListener('click', () => setWordColors(!state.enableWordColors));

    // 文型開關
    dom.btnToggleGrammar.addEventListener('click', () => setGrammarHighlight(!state.enableGrammar));

    // 翻譯開關
    dom.btnToggleTranslation.addEventListener('click', () => setTranslationDisplay(!state.enableTranslation));

    // 主題切換
    dom.btnThemeToggle.addEventListener('click', () => setTheme(state.theme === 'light' ? 'dark' : 'light'));

    // 字數計算
    dom.articleInput.addEventListener('input', () => {
        const len = dom.articleInput.value.length;
        dom.inputCharCount.textContent = `已輸入 ${len} 字`;
    });

    // 清空輸入
    dom.btnClearInput.addEventListener('click', () => {
        dom.articleInput.value = '';
        dom.inputCharCount.textContent = '已輸入 0 字';
        dom.articleInput.focus();
    });

    // 網址擷取
    dom.btnFetchUrl.addEventListener('click', handleFetchUrl);

    // 開始閱讀按鈕
    dom.btnStartReading.addEventListener('click', handleStartReading);

    // 字體縮放
    dom.btnFontIncr.addEventListener('click', () => changeFontSize(1));
    dom.btnFontDecr.addEventListener('click', () => changeFontSize(-1));

    // 更換文章
    dom.btnNewArticle.addEventListener('click', () => {
        dom.inputCard.style.display = 'flex';
        dom.inputCard.scrollIntoView({ behavior: 'smooth' });
    });

    // 句子導航按鈕
    dom.btnPrevSentence.addEventListener('click', () => navigateSentence(-1));
    dom.btnNextSentence.addEventListener('click', () => navigateSentence(1));

    // 鍵盤左右鍵導航句子
    document.addEventListener('keydown', (e) => {
        if (state.analyzedData && dom.readerDeck.style.display !== 'none') {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.key === 'ArrowLeft') navigateSentence(-1);
            if (e.key === 'ArrowRight') navigateSentence(1);
            if (e.key === 'Escape') {
                closeWordPopover();
                closeGrammarDrawer();
                closeNotebookModal();
            }
        }
    });

    // 句子語音朗讀
    dom.btnPlaySentenceAudio.addEventListener('click', () => {
        if (!state.analyzedData) return;
        const currentSentence = state.analyzedData.sentences[state.currentSentenceIdx];
        if (currentSentence) {
            speakJapanese(currentSentence.text);
        }
    });

    // 單字彈跳卡語音
    dom.btnPlayWordAudio.addEventListener('click', () => {
        const text = dom.popoverWordSurface.textContent;
        if (text) speakJapanese(text);
    });

    // 筆記本開關
    dom.btnOpenNotebook.addEventListener('click', openNotebookModal);
    dom.btnExportNotebook.addEventListener('click', exportNotebook);
    dom.btnClearNotebook.addEventListener('click', clearNotebook);

    // 點擊外部關閉單字彈跳卡
    document.addEventListener('click', (e) => {
        if (dom.wordPopover.style.display !== 'none' &&
            !dom.wordPopover.contains(e.target) &&
            !e.target.closest('.word-token')) {
            closeWordPopover();
        }
    });
}

// ==========================================================================
// 核心設定切換函式
// ==========================================================================
function setRubyMode(mode) {
    state.rubyMode = mode;
    localStorage.setItem('japanese_reader_ruby_mode', mode);
    document.body.setAttribute('data-ruby-mode', mode);

    dom.btnRubyShow.classList.toggle('active', mode === 'show');
    dom.btnRubyHide.classList.toggle('active', mode === 'hide');
    dom.btnRubyMask.classList.toggle('active', mode === 'mask');

    if (mode === 'mask') {
        showToast('已開啟【遮蔽測驗模式】：假名讀音已遮蔽，滑鼠懸浮或點擊時揭示');
    } else if (mode === 'hide') {
        showToast('已隱藏假名讀音');
    } else {
        showToast('已顯示假名讀音');
    }
}

function setWordColors(enable) {
    state.enableWordColors = enable;
    localStorage.setItem('japanese_reader_word_colors', enable);
    document.body.classList.toggle('enable-word-colors', enable);
    dom.btnToggleWordColors.classList.toggle('active', enable);
}

function setGrammarHighlight(enable) {
    state.enableGrammar = enable;
    localStorage.setItem('japanese_reader_grammar', enable);
    document.body.classList.toggle('enable-grammar', enable);
    dom.btnToggleGrammar.classList.toggle('active', enable);
}

function setTranslationDisplay(enable) {
    state.enableTranslation = enable;
    localStorage.setItem('japanese_reader_trans', enable);
    document.body.classList.toggle('enable-translation', enable);
    dom.btnToggleTranslation.classList.toggle('active', enable);
}

function setTheme(theme) {
    state.theme = theme;
    localStorage.setItem('japanese_reader_theme', theme);
    document.body.setAttribute('data-theme', theme);
    if (theme === 'dark') {
        dom.themeIcon.className = 'fa-solid fa-sun text-yellow-300';
    } else {
        dom.themeIcon.className = 'fa-solid fa-moon';
    }
}

function changeFontSize(delta) {
    state.fontSizeLevel = Math.max(-2, Math.min(4, state.fontSizeLevel + delta));
    const sizes = ['1.05rem', '1.15rem', '1.28rem', '1.45rem', '1.65rem', '1.85rem', '2.05rem'];
    const newSize = sizes[state.fontSizeLevel + 2];
    document.documentElement.style.setProperty('--reader-font-size', newSize);
}

// ==========================================================================
// 範例載入與分頁切換
// ==========================================================================
function switchInputTab(tab) {
    if (tab === 'paste') {
        dom.tabPasteBtn.classList.add('active');
        dom.tabUrlBtn.classList.remove('active');
        dom.panelPaste.classList.add('active');
        dom.panelUrl.classList.remove('active');
    } else {
        dom.tabUrlBtn.classList.add('active');
        dom.tabPasteBtn.classList.remove('active');
        dom.panelUrl.classList.add('active');
        dom.panelPaste.classList.remove('active');
    }
}

async function fetchSampleArticles() {
    try {
        const res = await fetch('/api/examples');
        if (!res.ok) return;
        state.sampleArticles = await res.json();
        renderSampleButtons();
    } catch (e) {
        console.error('獲取範例失敗:', e);
    }
}

function renderSampleButtons() {
    dom.sampleButtonsList.innerHTML = '';
    state.sampleArticles.forEach((article) => {
        const btn = document.createElement('button');
        btn.className = 'sample-btn';
        btn.innerHTML = `<i class="fa-solid fa-file-lines"></i> ${article.title.split('】')[0]}】`;
        btn.title = `${article.title} (${article.level})`;
        btn.onclick = () => {
            switchInputTab('paste');
            dom.articleInput.value = article.content;
            dom.inputCharCount.textContent = `已輸入 ${article.content.length} 字`;
            showToast(`已載入「${article.title}」`);
        };
        dom.sampleButtonsList.appendChild(btn);
    });
}

// ==========================================================================
// 網址正文抓取
// ==========================================================================
async function handleFetchUrl() {
    const url = dom.urlInput.value.trim();
    if (!url) {
        showToast('請先輸入有效的日文網址');
        dom.urlInput.focus();
        return;
    }

    dom.btnFetchUrl.disabled = true;
    dom.btnFetchUrl.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 正在抓取正文...';

    try {
        const res = await fetch('/api/extract-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '抓取失敗');
        }

        const data = await res.json();
        switchInputTab('paste');
        dom.articleInput.value = data.content;
        dom.inputCharCount.textContent = `已輸入 ${data.content.length} 字`;
        dom.readerArticleTitle.textContent = data.title;
        showToast(`已成功抓取正文「${data.title}」！`);
    } catch (err) {
        showToast(`網址抓取失敗: ${err.message}`);
    } finally {
        dom.btnFetchUrl.disabled = false;
        dom.btnFetchUrl.innerHTML = '<i class="fa-solid fa-cloud-arrow-down"></i> 一鍵抓取網頁正文';
    }
}

// ==========================================================================
// 開始閱讀與智慧解析
// ==========================================================================
async function handleStartReading() {
    const text = dom.articleInput.value.trim();
    if (!text) {
        showToast('請先輸入或貼上日文文章！');
        dom.articleInput.focus();
        return;
    }

    dom.loadingState.style.display = 'flex';
    dom.readerDeck.style.display = 'none';

    try {
        const res = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                auto_translate: dom.chkAutoTranslate.checked
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '解析失敗');
        }

        state.analyzedData = await res.json();
        state.currentSentenceIdx = 0;

        renderReaderView();
        showToast('文章解析完成！');

        // 平滑滾動至閱讀區
        dom.readerDeck.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
        showToast(`解析出錯: ${err.message}`);
    } finally {
        dom.loadingState.style.display = 'none';
    }
}

// ==========================================================================
// 渲染閱讀器主視圖
// ==========================================================================
function renderReaderView() {
    const data = state.analyzedData;
    if (!data) return;

    dom.readerDeck.style.display = 'grid';

    // 1. 渲染文章統計徽章
    const stats = data.stats;
    dom.articleStatsBadges.innerHTML = `
        <span class="meta-chip"><i class="fa-solid fa-paragraph"></i> 句子：<strong>${stats.sentence_count}</strong></span>
        <span class="meta-chip"><i class="fa-solid fa-spell-check"></i> 詞彙：<strong>${stats.word_count}</strong></span>
        <span class="meta-chip"><i class="fa-solid fa-book-bookmark"></i> 命中941文型：<strong>${stats.grammar_count}</strong> 條</span>
    `;

    // 2. 渲染左側文章主體
    dom.articleContentBox.innerHTML = '';

    data.sentences.forEach((s, sIdx) => {
        const row = document.createElement('div');
        row.className = `sentence-row ${sIdx === 0 ? 'active' : ''}`;
        row.dataset.sentenceIdx = sIdx;

        // 點擊句子切換選中狀態並觸發整句深度分析
        row.addEventListener('click', (e) => {
            // 若點擊的是單字且非遮蔽模式，由單字點擊事件處理
            selectSentence(sIdx);
        });

        // 句子日文原文組合
        const jpWrap = document.createElement('div');
        jpWrap.className = 'sentence-jp-text';

        // 處理文法與單字跨距標註
        renderSentenceTokens(jpWrap, s, sIdx);
        row.appendChild(jpWrap);

        // 逐句中文翻譯
        if (s.translation) {
            const transRow = document.createElement('div');
            transRow.className = 'sentence-trans-row';
            transRow.innerHTML = `
                <span class="trans-tag">繁中</span>
                <span class="trans-text">${s.translation}</span>
            `;
            row.appendChild(transRow);
        }

        dom.articleContentBox.appendChild(row);
    });

    // 3. 預設選取第一句並啟動深度分析
    selectSentence(0);
}

/**
 * 組合單字與文法標籤
 */
function renderSentenceTokens(container, sentence, sIdx) {
    const words = sentence.words;
    const grammars = sentence.grammars || [];

    // 建立字元位置到文法的映射
    let charOffset = 0;
    const wordOffsets = [];
    words.forEach((w) => {
        const start = charOffset;
        const end = start + w.surface.length;
        wordOffsets.push({ start, end, word: w });
        charOffset = end;
    });

    // 渲染每個單字 Token
    words.forEach((w, wIdx) => {
        const tokenSpan = document.createElement('span');
        tokenSpan.className = `word-token ${w.jlpt ? `jlpt-${w.jlpt}` : ''}`;
        tokenSpan.innerHTML = w.ruby_html;
        tokenSpan.dataset.surface = w.surface;
        tokenSpan.dataset.baseForm = w.base_form;
        tokenSpan.dataset.reading = w.reading;
        tokenSpan.dataset.pos = w.pos;
        tokenSpan.dataset.jlpt = w.jlpt || '';
        tokenSpan.dataset.sentenceIdx = sIdx;
        tokenSpan.dataset.wordIdx = wIdx;

        // 遮蔽模式下點擊揭示此單字讀音
        tokenSpan.addEventListener('click', (e) => {
            e.stopPropagation();
            if (state.rubyMode === 'mask') {
                tokenSpan.classList.toggle('revealed');
            }
            showWordPopover(tokenSpan, w, e);
        });

        // 檢查此單字是否落在某個命中文法區間內
        const curOffset = wordOffsets[wIdx];
        const matchedGrammar = grammars.find(g => 
            (curOffset.start >= g.start && curOffset.start < g.end) ||
            (curOffset.end > g.start && curOffset.end <= g.end)
        );

        if (matchedGrammar) {
            tokenSpan.classList.add('grammar-highlight');
            tokenSpan.title = `【941文型】${matchedGrammar.title} (${matchedGrammar.level || '文型'})`;
            tokenSpan.dataset.grammarId = matchedGrammar.id;

            // 若為此文型匹配區間的最後一個單字，插入微型標籤
            const isLastOfGrammar = (wIdx === words.length - 1) || (wordOffsets[wIdx + 1].start >= matchedGrammar.end);
            if (isLastOfGrammar) {
                const miniBadge = document.createElement('span');
                miniBadge.className = 'grammar-mini-badge';
                miniBadge.textContent = matchedGrammar.level ? `${matchedGrammar.level}` : '文型';
                miniBadge.onclick = (e) => {
                    e.stopPropagation();
                    openGrammarDrawer(matchedGrammar);
                };
                tokenSpan.appendChild(miniBadge);
            }
        }

        container.appendChild(tokenSpan);
    });
}

// ==========================================================================
// 句子切換與整句深度分析器 (句解霸核心功能)
// ==========================================================================
function selectSentence(idx) {
    if (!state.analyzedData || !state.analyzedData.sentences[idx]) return;

    state.currentSentenceIdx = idx;
    const sentence = state.analyzedData.sentences[idx];
    const total = state.analyzedData.sentences.length;

    // 更新左側行選中樣式
    document.querySelectorAll('.sentence-row').forEach(row => row.classList.remove('active'));
    const activeRow = document.querySelector(`.sentence-row[data-sentence-idx="${idx}"]`);
    if (activeRow) {
        activeRow.classList.add('active');
    }

    // 更新右側整句分析器
    dom.currentSentenceBadge.textContent = `第 ${idx + 1} 句 / 共 ${total} 句`;

    // 1. 本句原文（組合所有單字的 ruby）
    const rubyHtml = sentence.words.map(w => w.ruby_html).join('');
    dom.selectedSentenceJp.innerHTML = rubyHtml;

    // 2. 本句中文翻譯
    dom.selectedSentenceZh.textContent = sentence.translation || '暫無翻譯';

    // 3. 本句命中的 941 文法清單
    renderSentenceGrammars(sentence.grammars || []);

    // 4. 本句單字拆解表格
    renderSentenceWordsTable(sentence.words);

    // 5. 更新上一句/下一句按鈕狀態
    dom.btnPrevSentence.disabled = (idx === 0);
    dom.btnNextSentence.disabled = (idx === total - 1);
}

function navigateSentence(delta) {
    if (!state.analyzedData) return;
    const newIdx = state.currentSentenceIdx + delta;
    if (newIdx >= 0 && newIdx < state.analyzedData.sentences.length) {
        selectSentence(newIdx);
        // 平滑滾動到該句
        const targetRow = document.querySelector(`.sentence-row[data-sentence-idx="${newIdx}"]`);
        if (targetRow) {
            targetRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
}

/**
 * 渲染本句命中文法卡片清單
 */
function renderSentenceGrammars(grammars) {
    dom.sentenceGrammarCount.textContent = grammars.length;
    dom.sentenceGrammarsList.innerHTML = '';

    if (grammars.length === 0) {
        dom.sentenceGrammarsList.innerHTML = '<div class="empty-hint">本句未偵測到特殊 941 文法句型</div>';
        return;
    }

    grammars.forEach(g => {
        const card = document.createElement('div');
        card.className = 'grammar-item-card';
        card.innerHTML = `
            <div class="grammar-card-top">
                <div class="grammar-card-title">${escapeHtml(g.title)}</div>
                <span class="badge-jlpt badge-${(g.level || 'n2').toLowerCase().replace('~', '_')}">${g.level || 'JLPT'}</span>
            </div>
            ${g.form ? `<div class="grammar-form-box"><strong>接續：</strong>${escapeHtml(g.form)}</div>` : ''}
            <div class="grammar-meaning-box">${escapeHtml(g.meaningZh || '暫無中文詳解')}</div>
            ${g.exampleRuby ? `<div class="grammar-example-box"><strong>例句：</strong>${g.exampleRuby}<br><span style="color:var(--text-muted);font-size:0.84rem;">${escapeHtml(g.translation || '')}</span></div>` : ''}
            <div class="grammar-card-actions">
                <button class="btn-grammar-detail" onclick="openGrammarDrawerById(${g.id})">
                    <i class="fa-solid fa-book-open"></i> 查看完整詳解
                </button>
            </div>
        `;
        dom.sentenceGrammarsList.appendChild(card);
    });
}

/**
 * 渲染本句單字拆解表格
 */
function renderSentenceWordsTable(words) {
    dom.sentenceWordCount.textContent = words.length;
    dom.sentenceWordsTbody.innerHTML = '';

    words.forEach(w => {
        const isFav = state.notebook.words.some(item => item.surface === w.surface);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${escapeHtml(w.base_form || w.surface)}</strong></td>
            <td style="color:#e11d48;font-weight:700;">${escapeHtml(w.reading || '-')}</td>
            <td><span style="font-size:0.78rem;color:var(--text-muted);">${escapeHtml(w.pos || '-')}</span></td>
            <td>${w.jlpt ? `<span class="badge-jlpt badge-${w.jlpt.toLowerCase()}">${w.jlpt}</span>` : '<span style="color:var(--text-muted);">-</span>'}</td>
            <td style="text-align:center;">
                <button class="btn-fav-word ${isFav ? 'active' : ''}" title="加入生詞本" onclick="toggleWordNotebook('${escapeHtml(w.surface)}', '${escapeHtml(w.base_form)}', '${escapeHtml(w.reading)}', '${escapeHtml(w.jlpt || '')}', '${escapeHtml(w.pos || '')}')">
                    <i class="fa-solid fa-star"></i>
                </button>
            </td>
        `;
        dom.sentenceWordsTbody.appendChild(tr);
    });
}

// ==========================================================================
// 單字浮動字典卡片 (Word Popover)
// ==========================================================================
let currentPopoverWord = null;

async function showWordPopover(targetElem, word, event) {
    currentPopoverWord = word;
    const rect = targetElem.getBoundingClientRect();

    dom.popoverWordSurface.textContent = word.surface;
    dom.popoverWordKana.textContent = word.reading || word.surface;
    dom.popoverWordPos.textContent = word.pos || '單字';

    if (word.jlpt) {
        dom.popoverWordLevel.textContent = word.jlpt;
        dom.popoverWordLevel.className = `badge-jlpt badge-${word.jlpt.toLowerCase()}`;
        dom.popoverWordLevel.style.display = 'inline-flex';
    } else {
        dom.popoverWordLevel.style.display = 'none';
    }

    // 檢查是否已存入生詞本
    const isFav = state.notebook.words.some(item => item.surface === word.surface);
    dom.btnAddWordToNotebook.innerHTML = isFav 
        ? '<i class="fa-solid fa-star text-amber-400"></i> 已在生詞本中'
        : '<i class="fa-regular fa-star"></i> 存入生詞本';

    dom.btnAddWordToNotebook.onclick = () => {
        toggleWordNotebook(word.surface, word.base_form, word.reading, word.jlpt, word.pos);
        const nowFav = state.notebook.words.some(item => item.surface === word.surface);
        dom.btnAddWordToNotebook.innerHTML = nowFav 
            ? '<i class="fa-solid fa-star text-amber-400"></i> 已在生詞本中'
            : '<i class="fa-regular fa-star"></i> 存入生詞本';
    };

    // 定位卡片
    dom.wordPopover.style.display = 'flex';
    const popoverWidth = 290;
    let left = rect.left + window.scrollX - (popoverWidth / 2) + (rect.width / 2);
    let top = rect.bottom + window.scrollY + 8;

    if (left < 10) left = 10;
    if (left + popoverWidth > window.innerWidth - 10) left = window.innerWidth - popoverWidth - 10;

    dom.wordPopover.style.left = `${left}px`;
    dom.wordPopover.style.top = `${top}px`;

    // 查詢釋義
    dom.popoverWordMeaning.innerHTML = '<div class="meaning-spinner"><i class="fa-solid fa-spinner fa-spin"></i> 正在查詢釋義...</div>';
    try {
        const queryTerm = word.base_form || word.surface;
        const res = await fetch('/api/translate-word', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: queryTerm })
        });
        const data = await res.json();
        dom.popoverWordMeaning.innerHTML = `<strong>中文釋義：</strong>${escapeHtml(data.translation || '無相符翻譯')}`;
    } catch (e) {
        dom.popoverWordMeaning.textContent = '釋義查詢失敗';
    }
}

function closeWordPopover() {
    dom.wordPopover.style.display = 'none';
}

// ==========================================================================
// 文法詳細抽屜 (Grammar Drawer)
// ==========================================================================
async function openGrammarDrawerById(id) {
    try {
        const res = await fetch(`/api/grammar/${id}`);
        if (!res.ok) throw new Error('找不到文法');
        const g = await res.json();
        openGrammarDrawer(g);
    } catch (e) {
        showToast(`載入文法詳解失敗: ${e.message}`);
    }
}

function openGrammarDrawer(g) {
    dom.drawerGrammarTitle.textContent = g.title;
    dom.drawerGrammarLevel.textContent = g.level || 'JLPT';
    dom.drawerGrammarLevel.className = `badge-jlpt badge-${(g.level || 'n2').toLowerCase().replace('~', '_')}`;
    
    // 連結至使用者文法原站
    dom.drawerGrammarExternalLink.href = g.sourceUrl || `https://fobeetsai.github.io/japanese-grammar/`;

    // 檢查收藏狀態
    const isFav = state.notebook.grammars.some(item => item.id === g.id);
    dom.btnDrawerFav.innerHTML = isFav 
        ? '<i class="fa-solid fa-star text-amber-400"></i>' 
        : '<i class="fa-regular fa-star"></i>';
    dom.btnDrawerFav.onclick = () => {
        toggleGrammarNotebook(g);
        const nowFav = state.notebook.grammars.some(item => item.id === g.id);
        dom.btnDrawerFav.innerHTML = nowFav 
            ? '<i class="fa-solid fa-star text-amber-400"></i>' 
            : '<i class="fa-regular fa-star"></i>';
    };

    dom.drawerGrammarBody.innerHTML = `
        <div class="drawer-box">
            <div class="drawer-label"><i class="fa-solid fa-link"></i> 接續規則 (Connection Form)</div>
            <div style="font-weight:700;color:var(--primary);font-size:1.05rem;">${escapeHtml(g.form || '無特殊接續限制')}</div>
        </div>

        <div class="drawer-box">
            <div class="drawer-label"><i class="fa-solid fa-circle-question"></i> 中文深度精解 (Meaning ZH)</div>
            <div style="font-size:1.05rem;line-height:1.7;">${escapeHtml(g.meaningZh || '暫無解析')}</div>
            ${g.meaningJa ? `<div style="font-size:0.9rem;color:var(--text-muted);margin-top:0.5rem;border-top:1px dashed var(--border-color);padding-top:0.5rem;">日語說明：${escapeHtml(g.meaningJa)}</div>` : ''}
        </div>

        <div class="drawer-box">
            <div class="drawer-label"><i class="fa-solid fa-quote-left"></i> 精選例文與振假名 (Example Sentence)</div>
            <div style="font-size:1.25rem;font-weight:700;font-family:var(--font-jp);line-height:1.8;">${g.exampleRuby || escapeHtml(g.example || '')}</div>
            <div style="font-size:1.02rem;color:var(--text-muted);margin-top:0.65rem;border-top:1px dashed var(--border-color);padding-top:0.65rem;">
                <strong>例句翻譯：</strong>${escapeHtml(g.translation || '暫無翻譯')}
            </div>
        </div>

        ${g.note ? `
        <div class="drawer-box" style="border-left:4px solid #f59e0b;">
            <div class="drawer-label" style="color:#b45309;"><i class="fa-solid fa-lightbulb"></i> 重點學習提示 (Key Note)</div>
            <div style="font-size:0.95rem;color:var(--text-main);">${escapeHtml(g.note)}</div>
        </div>
        ` : ''}
    `;

    dom.grammarDrawerOverlay.classList.add('open');
}

function closeGrammarDrawer() {
    dom.grammarDrawerOverlay.classList.remove('open');
}

// ==========================================================================
// 筆記本 (單字與文法收藏)
// ==========================================================================
function loadNotebook() {
    try {
        const saved = localStorage.getItem('japanese_reader_notebook');
        if (saved) {
            state.notebook = JSON.parse(saved);
        }
    } catch (e) {
        state.notebook = { words: [], grammars: [] };
    }
    updateNotebookHeaderCount();
}

function saveNotebook() {
    localStorage.setItem('japanese_reader_notebook', JSON.stringify(state.notebook));
    updateNotebookHeaderCount();
}

function updateNotebookHeaderCount() {
    const total = state.notebook.words.length + state.notebook.grammars.length;
    dom.notebookCount.textContent = total;
    dom.nbWordCount.textContent = state.notebook.words.length;
    dom.nbGrammarCount.textContent = state.notebook.grammars.length;
}

function toggleWordNotebook(surface, baseForm, reading, jlpt, pos) {
    const idx = state.notebook.words.findIndex(w => w.surface === surface);
    if (idx > -1) {
        state.notebook.words.splice(idx, 1);
        showToast(`已自生詞本移除「${surface}」`);
    } else {
        state.notebook.words.push({
            surface,
            baseForm: baseForm || surface,
            reading,
            jlpt,
            pos,
            addedAt: new Date().toLocaleDateString()
        });
        showToast(`已成功加入生詞本「${surface}」！`);
    }
    saveNotebook();
    if (state.analyzedData) {
        renderSentenceWordsTable(state.analyzedData.sentences[state.currentSentenceIdx].words);
    }
}

function toggleGrammarNotebook(g) {
    const idx = state.notebook.grammars.findIndex(item => item.id === g.id);
    if (idx > -1) {
        state.notebook.grammars.splice(idx, 1);
        showToast(`已自收藏移除文型「${g.title}」`);
    } else {
        state.notebook.grammars.push({
            id: g.id,
            title: g.title,
            level: g.level,
            meaningZh: g.meaningZh,
            addedAt: new Date().toLocaleDateString()
        });
        showToast(`已成功收藏文型「${g.title}」！`);
    }
    saveNotebook();
}

function openNotebookModal() {
    dom.notebookModal.classList.add('open');
    switchNotebookTab('words');
}

function closeNotebookModal() {
    dom.notebookModal.classList.remove('open');
}

function switchNotebookTab(tab) {
    dom.tabNotebookWordsBtn.classList.toggle('active', tab === 'words');
    dom.tabNotebookGrammarsBtn.classList.toggle('active', tab === 'grammars');

    dom.notebookListArea.innerHTML = '';

    if (tab === 'words') {
        if (state.notebook.words.length === 0) {
            dom.notebookListArea.innerHTML = '<div class="empty-hint" style="text-align:center;padding:2rem;">生詞本目前為空，點擊閱讀區或分析表之星星即可加入！</div>';
            return;
        }
        state.notebook.words.forEach((w, idx) => {
            const item = document.createElement('div');
            item.className = 'notebook-item';
            item.innerHTML = `
                <div>
                    <strong style="font-size:1.15rem;font-family:var(--font-jp);">${escapeHtml(w.surface)}</strong>
                    <span style="color:#e11d48;margin-left:0.5rem;font-weight:700;">${escapeHtml(w.reading || '')}</span>
                    ${w.jlpt ? `<span class="badge-jlpt badge-${w.jlpt.toLowerCase()}" style="margin-left:0.4rem;">${w.jlpt}</span>` : ''}
                    <div style="font-size:0.8rem;color:var(--text-muted);">${escapeHtml(w.pos || '')} | 辭書形: ${escapeHtml(w.baseForm || '')}</div>
                </div>
                <button class="btn-del-item" onclick="removeWordFromNotebook(${idx})" title="刪除"><i class="fa-solid fa-trash-can"></i></button>
            `;
            dom.notebookListArea.appendChild(item);
        });
    } else {
        if (state.notebook.grammars.length === 0) {
            dom.notebookListArea.innerHTML = '<div class="empty-hint" style="text-align:center;padding:2rem;">文法筆記目前為空，點擊文型卡片之星星即可收藏！</div>';
            return;
        }
        state.notebook.grammars.forEach((g, idx) => {
            const item = document.createElement('div');
            item.className = 'notebook-item';
            item.innerHTML = `
                <div>
                    <strong style="font-size:1.15rem;font-family:var(--font-jp);color:var(--primary);">${escapeHtml(g.title)}</strong>
                    ${g.level ? `<span class="badge-jlpt badge-${g.level.toLowerCase().replace('~', '_')}" style="margin-left:0.4rem;">${g.level}</span>` : ''}
                    <div style="font-size:0.88rem;margin-top:0.25rem;">${escapeHtml(g.meaningZh || '')}</div>
                </div>
                <button class="btn-del-item" onclick="removeGrammarFromNotebook(${idx})" title="刪除"><i class="fa-solid fa-trash-can"></i></button>
            `;
            dom.notebookListArea.appendChild(item);
        });
    }
}

function removeWordFromNotebook(idx) {
    state.notebook.words.splice(idx, 1);
    saveNotebook();
    switchNotebookTab('words');
}

function removeGrammarFromNotebook(idx) {
    state.notebook.grammars.splice(idx, 1);
    saveNotebook();
    switchNotebookTab('grammars');
}

function clearNotebook() {
    if (!confirm('確定要清空所有收藏的生詞與文法嗎？')) return;
    state.notebook = { words: [], grammars: [] };
    saveNotebook();
    switchNotebookTab('words');
    showToast('已清空筆記本');
}

function exportNotebook() {
    let content = "=== 日文閱讀助手・學習筆記本 ===\n\n";
    content += "【生詞本】\n";
    state.notebook.words.forEach((w, i) => {
        content += `${i + 1}. ${w.surface} [${w.reading}] (${w.jlpt || 'Other'}) - ${w.pos}\n`;
    });
    content += "\n【文法句型筆記】\n";
    state.notebook.grammars.forEach((g, i) => {
        content += `${i + 1}. ${g.title} [${g.level || 'JLPT'}]\n   釋義：${g.meaningZh}\n`;
    });

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `日文閱讀筆記_${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('已匯出學習筆記檔案！');
}

// ==========================================================================
// 輔助工具函式
// ==========================================================================
function speakJapanese(text) {
    if (!('speechSynthesis' in window)) {
        showToast('您的瀏覽器不支援語音朗讀功能');
        return;
    }
    window.speechSynthesis.cancel(); // 停止先前的朗讀
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ja-JP';
    utterance.rate = 0.95; // 稍微放慢語速以利學習者聆聽

    // 嘗試尋找日語語音
    const voices = window.speechSynthesis.getVoices();
    const jaVoice = voices.find(v => v.lang.startsWith('ja'));
    if (jaVoice) utterance.voice = jaVoice;

    window.speechSynthesis.speak(utterance);
}

let toastTimer = null;
function showToast(msg) {
    dom.toastMsg.textContent = msg;
    dom.toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        dom.toast.classList.remove('show');
    }, 2800);
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
