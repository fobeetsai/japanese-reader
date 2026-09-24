import os, sys, re, json
sys.stdout.reconfigure(encoding='utf-8')

MASTER_PATH = r"C:\Users\fobee\我的雲端硬碟\Antigravity Apps\Ai agent\master.html"
NOVEL_PATH = r"C:\Users\fobee\我的雲端硬碟\Antigravity Apps\Ai agent\novel.html"
ALIAS_PATH = r"C:\Users\fobee\我的雲端硬碟\Antigravity Apps\Ai agent\小說閱讀.html"

print("[1/5] 讀取 master.html 核心資源...")
with open(MASTER_PATH, "r", encoding="utf-8") as f:
    master_html = f.read()

# 提取核心 CSS (FontAwesome, Google Fonts 等)
head_match = re.search(r"<head>(.*?)</head>", master_html, re.DOTALL)
head_content = head_match.group(1) if head_match else ""

# 提取外部字型與 CSS 引用
external_css = re.findall(r'<link\s+[^>]*rel=["\']stylesheet["\'][^>]*>', head_content)
external_css_str = "\n    ".join(external_css)

# 提取 master.html 內置的 JS 代碼區塊
scripts = list(re.finditer(r'<script(?:\s+[^>]*)?>(.*?)</script>', master_html, re.DOTALL))
db_script = scripts[0].group(1).strip()        # GRAMMAR_DATA, JLPT_VOCAB, KANJI_COMPACT, PARTICLE_DATA
nlp_script = scripts[1].group(1).strip()       # Tokenizer, morphological analysis, grammar pattern matcher
core_ui_script = scripts[2].group(1).strip()   # Core UI state, helpers, word popover, particle logic, notebook logic

print("[2/5] 設計小說閱讀專用響應式樣式...")

novel_css = """
/* ==========================================================================
   小說閱讀器 (Novel Master) 專屬版型與樣式
   ========================================================================== */

:root {
    --novel-bg: #fcf8f2;
    --novel-text: #2c2724;
    --novel-card-bg: rgba(255, 255, 255, 0.95);
    --novel-border: #e6ded3;
    --novel-accent: #2563eb;
    --novel-accent-hover: #1d4ed8;
    --novel-font-size: 1.28rem;
    --novel-line-height: 2.3;
    --karaoke-active-bg: #fef08a;
    --karaoke-active-border: #eab308;
    --karaoke-token-highlight: #fde047;
}

body.novel-body {
    background-color: var(--novel-bg);
    color: var(--novel-text);
    font-family: "Noto Serif JP", "Hiragino Mincho ProN", "Yu Mincho", "Source Han Serif", serif;
    margin: 0;
    padding: 0;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    overflow-x: hidden;
}

/* 頂部固定沉浸式導覽列 */
.novel-navbar {
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(255, 255, 255, 0.96);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--novel-border);
    padding: 8px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
    flex-wrap: wrap;
    gap: 8px;
}

.novel-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1.15rem;
    font-weight: 700;
    color: #1e293b;
    text-decoration: none;
}

.novel-brand i {
    color: #b45309;
    font-size: 1.35rem;
}

.novel-toolbar-group {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}

.novel-tool-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 8px;
    font-size: 0.88rem;
    font-weight: 600;
    background: #fff;
    border: 1px solid var(--novel-border);
    color: #334155;
    cursor: pointer;
    transition: all 0.18s ease;
    user-select: none;
}

.novel-tool-btn:hover {
    background: #f1f5f9;
    border-color: #cbd5e1;
    color: #0f172a;
}

.novel-tool-btn.primary {
    background: #2563eb;
    color: #ffffff;
    border-color: #1d4ed8;
}

.novel-tool-btn.primary:hover {
    background: #1d4ed8;
}

.novel-tool-btn.success {
    background: #059669;
    color: #ffffff;
    border-color: #047857;
}

.novel-tool-btn.success:hover {
    background: #047857;
}

.novel-tool-btn.warning {
    background: #d97706;
    color: #ffffff;
    border-color: #b45309;
}

.novel-tool-btn.active {
    background: #e0e7ff;
    color: #3730a3;
    border-color: #818cf8;
}

.novel-badge {
    background: #fef3c7;
    color: #92400e;
    font-size: 0.75rem;
    padding: 2px 7px;
    border-radius: 9999px;
    font-weight: 700;
    margin-left: 4px;
}

/* 主閱讀容器 */
.novel-main-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    max-width: 1040px;
    width: 100%;
    margin: 0 auto;
    padding: 24px 20px 140px 20px;
    box-sizing: border-box;
}

/* 小說內容卡片 */
.novel-reader-card {
    background: var(--novel-card-bg);
    border-radius: 14px;
    border: 1px solid var(--novel-border);
    box-shadow: 0 4px 24px rgba(44, 39, 36, 0.05);
    padding: 36px 44px;
    min-height: 60vh;
    position: relative;
    transition: all 0.25s ease;
}

@media (max-width: 768px) {
    .novel-reader-card {
        padding: 20px 16px;
    }
}

/* 直排 (縱書) 閱讀模式 */
.novel-reader-card.vertical-mode {
    writing-mode: vertical-rl;
    text-orientation: upright;
    overflow-x: auto;
    overflow-y: hidden;
    height: 72vh;
    padding: 30px 40px;
    white-space: normal;
}

.novel-reader-card.vertical-mode ruby rt {
    font-size: 0.52em;
    user-select: none;
}

/* 句子行排版與卡拉OK高亮 */
.sentence-row {
    position: relative;
    padding: 8px 12px;
    margin-bottom: 10px;
    border-radius: 8px;
    line-height: var(--novel-line-height);
    font-size: var(--novel-font-size);
    transition: background-color 0.22s ease, box-shadow 0.22s ease;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.novel-reader-card.vertical-mode .sentence-row {
    margin-bottom: 0;
    margin-left: 14px;
    padding: 10px 8px;
    flex-direction: row;
}

.sentence-row:hover {
    background-color: rgba(0, 0, 0, 0.025);
}

.sentence-row.karaoke-active-sentence {
    background-color: var(--karaoke-active-bg) !important;
    border-left: 4px solid var(--karaoke-active-border);
    box-shadow: 0 2px 14px rgba(234, 179, 8, 0.18);
}

.novel-reader-card.vertical-mode .sentence-row.karaoke-active-sentence {
    border-left: none;
    border-top: 4px solid var(--karaoke-active-border);
}

.sentence-content {
    cursor: pointer;
    word-break: break-word;
    font-family: inherit;
}

/* 句子行工具按鈕 (播放、收藏、文法) */
.sentence-actions-bar {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-top: 4px;
    opacity: 0.55;
    transition: opacity 0.2s;
}

.sentence-row:hover .sentence-actions-bar,
.sentence-row.karaoke-active-sentence .sentence-actions-bar {
    opacity: 1;
}

.sentence-btn-mini {
    background: transparent;
    border: none;
    padding: 3px 6px;
    border-radius: 4px;
    font-size: 0.85rem;
    color: #64748b;
    cursor: pointer;
    transition: all 0.15s;
}

.sentence-btn-mini:hover {
    background: rgba(0, 0, 0, 0.06);
    color: #0f172a;
}

.sentence-star-btn {
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 0.95rem;
    color: #94a3b8;
    transition: transform 0.15s, color 0.15s;
}

.sentence-star-btn:hover {
    transform: scale(1.2);
    color: #f59e0b;
}

.sentence-star-btn.is-fav {
    color: #f59e0b;
}

/* 文法高亮與點擊卡片彈出 */
.novel-grammar-highlight {
    background-color: rgba(59, 130, 246, 0.14);
    border-bottom: 2px solid #3b82f6;
    border-radius: 3px;
    padding: 1px 3px;
    cursor: pointer;
    transition: all 0.18s;
}

.novel-grammar-highlight:hover {
    background-color: rgba(59, 130, 246, 0.28);
    border-bottom-color: #1d4ed8;
}

.novel-grammar-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.74rem;
    background: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
    padding: 2px 7px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    margin-right: 6px;
    user-select: none;
    vertical-align: middle;
}

.novel-grammar-badge:hover {
    background: #dbeafe;
    border-color: #93c5fd;
}

/* 底部全功能懸浮朗讀控制列 */
.novel-floating-audio-bar {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    width: 92%;
    max-width: 860px;
    background: rgba(255, 255, 255, 0.98);
    backdrop-filter: blur(14px);
    border: 1px solid var(--novel-border);
    border-radius: 18px;
    padding: 10px 18px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    z-index: 999;
    flex-wrap: wrap;
    transition: all 0.3s ease;
}

.audio-controls-left {
    display: flex;
    align-items: center;
    gap: 8px;
}

.audio-btn-circle {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    border: none;
    background: #2563eb;
    color: #fff;
    font-size: 1.15rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    transition: transform 0.15s, background-color 0.15s;
}

.audio-btn-circle:hover {
    transform: scale(1.06);
    background: #1d4ed8;
}

.audio-btn-square {
    width: 34px;
    height: 34px;
    border-radius: 8px;
    border: 1px solid var(--novel-border);
    background: #fff;
    color: #475569;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.15s;
}

.audio-btn-square:hover {
    background: #f1f5f9;
    color: #0f172a;
}

.audio-status-info {
    font-size: 0.88rem;
    color: #334155;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
}

.audio-controls-right {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}

/* 翻頁底導航 */
.novel-pagination-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
    margin-top: 24px;
    font-size: 0.95rem;
    color: #475569;
}

.novel-page-btn {
    padding: 8px 16px;
    border-radius: 8px;
    border: 1px solid var(--novel-border);
    background: #fff;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
}

.novel-page-btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
}

.novel-page-btn:not(:disabled):hover {
    background: #f1f5f9;
}

/* 模態框與通用抽屜樣式 */
.novel-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(4px);
    z-index: 1000;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 16px;
}

.novel-modal-overlay.open {
    display: flex;
}

.novel-modal-box {
    background: #ffffff;
    border-radius: 16px;
    width: 100%;
    max-width: 680px;
    max-height: 88vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
    overflow: hidden;
}

.novel-modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 22px;
    border-bottom: 1px solid #e2e8f0;
    background: #f8fafc;
}

.novel-modal-header h3 {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 700;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 8px;
}

.novel-modal-close-btn {
    background: transparent;
    border: none;
    font-size: 1.25rem;
    color: #64748b;
    cursor: pointer;
    border-radius: 6px;
    padding: 4px 8px;
}

.novel-modal-close-btn:hover {
    background: #e2e8f0;
    color: #0f172a;
}

.novel-modal-body {
    padding: 20px 24px;
    overflow-y: auto;
    flex: 1;
}

/* Toast 提示條 (保證支援 icon 與 msg) */
.toast {
    position: fixed;
    bottom: 84px;
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    background: rgba(15, 23, 42, 0.92);
    color: #ffffff;
    padding: 10px 22px;
    border-radius: 9999px;
    font-size: 0.92rem;
    font-weight: 500;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25);
    opacity: 0;
    visibility: hidden;
    transition: all 0.25s ease;
    z-index: 10000;
    pointer-events: none;
    display: flex;
    align-items: center;
    gap: 8px;
}

.toast.show {
    opacity: 1;
    visibility: visible;
    transform: translateX(-50%) translateY(0);
}
"""

print("[3/5] 整合 HTML 模板與功能抽屜組件...")

# 提取 master.html 內置的 notebookModal
nb_modal_match = re.search(r'<div class="modal-overlay" id="notebookModal">.*?</div>\s*</div>\s*</div>', master_html, re.DOTALL)
notebook_modal_html = nb_modal_match.group(0) if nb_modal_match else ""

novel_body_html = f"""
    <!-- 頂部小說閱讀器導覽列 -->
    <header class="novel-navbar">
        <div class="novel-toolbar-group">
            <a href="novel.html" class="novel-brand">
                <i class="fa-solid fa-book-open"></i>
                <span id="novelTitleText">小說沉浸閱讀</span>
            </a>
            <span class="badge-jlpt" id="novelPageBadge" style="font-size: 0.8rem; padding: 3px 8px;">第 1 頁</span>
        </div>

        <!-- 核心功能控制按鈕群 -->
        <div class="novel-toolbar-group">
            <!-- 朗讀本頁 (整頁連播) 按鈕 -->
            <button class="novel-tool-btn primary" id="btnPlayWholePage" title="從本頁第 1 句連續朗讀至頁尾">
                <i class="fa-solid fa-play" id="mainPlayIcon"></i> <span id="mainPlayBtnText">朗讀本頁</span>
            </button>
            <button class="novel-tool-btn" id="btnStopPageAudio" title="停止朗讀" style="display: none;">
                <i class="fa-solid fa-stop text-rose-500"></i> 停止
            </button>

            <!-- 聲音角色選擇 (Nanami 溫潤女聲 / Keita 沉穩男聲) -->
            <select id="novelVoiceSelect" class="novel-tool-btn" style="padding: 5px 8px; font-weight: 600;" title="切換微軟自然真人語音">
                <option value="nanami" selected>🌸 七海 Nanami (微軟自然女聲)</option>
                <option value="keita">🎙️ 圭太 Keita (微軟自然男聲)</option>
            </select>

            <!-- 重複次數選擇 (1次、2次、3次、5次、循環) -->
            <select id="novelRepeatCountSelect" class="novel-tool-btn" style="padding: 5px 8px; font-weight: 600;" title="設定每句朗讀重複次數">
                <option value="1">朗讀 1 次</option>
                <option value="2">重複 2 次</option>
                <option value="3" selected>重複 3 次 (精聽)</option>
                <option value="5">重複 5 次 (複讀)</option>
                <option value="999">🔂 單句循環</option>
            </select>

            <!-- 生詞本抽屜開啟按鈕 -->
            <button class="novel-tool-btn" id="btnOpenNotebook" onclick="openNotebookModal()" title="開啟生詞本">
                <i class="fa-solid fa-bookmark text-amber-500"></i> 生詞本 <span class="novel-badge" id="savedWordsCountBadge">0</span>
            </button>

            <!-- 收藏句子抽屜開啟按鈕 -->
            <button class="novel-tool-btn" id="btnOpenSavedSentences" onclick="openSavedSentencesModal()" title="查看已收藏的日語句子">
                <i class="fa-solid fa-star text-amber-500"></i> 收藏句子 <span class="novel-badge" id="savedSentencesCountBadge">0</span>
            </button>

            <!-- 拍照 / 圖片 OCR 辨識按鈕 -->
            <button class="novel-tool-btn" id="btnOpenOcrModal" onclick="openOcrModal()" title="拍照或上傳書頁截圖進行日語 OCR 分析">
                <i class="fa-solid fa-camera text-indigo-600"></i> 拍照/OCR
            </button>

            <!-- 檔案匯入 (PDF / EPUB / TXT / DOCX) -->
            <button class="novel-tool-btn" onclick="openFilePickerModal()" title="匯入書籍檔案並自選頁數">
                <i class="fa-solid fa-file-arrow-up text-emerald-600"></i> 匯入小說
            </button>

            <!-- 縱橫排版切換 -->
            <button class="novel-tool-btn" id="btnToggleWritingMode" onclick="toggleWritingMode()" title="切換日文直排 (縱書) / 現代橫排 (橫書)">
                <i class="fa-solid fa-arrows-split-up-and-left"></i> <span id="writingModeText">直排縱書</span>
            </button>

            <!-- 假名標註切換 -->
            <select id="novelFuriganaSelect" class="novel-tool-btn" onchange="changeFuriganaMode(this.value)" title="漢字讀音標註模式">
                <option value="all" selected>全漢字振假名</option>
                <option value="hard">僅難字/N1-N3標註</option>
                <option value="none">純日文(懸停查音)</option>
            </select>

            <!-- 字體大小調整 -->
            <button class="novel-tool-btn" onclick="adjustNovelFontSize(-1)" title="縮小字級">A-</button>
            <button class="novel-tool-btn" onclick="adjustNovelFontSize(1)" title="放大字級">A+</button>
        </div>
    </header>

    <!-- 小說閱讀主內容區 -->
    <main class="novel-main-container">
        <!-- 書籍標題與進度 -->
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; padding: 0 6px;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #475569;" id="novelBookTitle">
                夏目漱石《心》(こころ)
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 0.9rem; color: #64748b;" id="novelPageIndicator">第 1 頁 / 共 1 頁</span>
            </div>
        </div>

        <!-- 小說本文容器 -->
        <div class="novel-reader-card" id="novelContentCard">
            <!-- 句子動態渲染區 -->
            <div id="novelSentencesList"></div>
        </div>

        <!-- 底部翻頁欄 -->
        <div class="novel-pagination-bar">
            <button class="novel-page-btn" id="btnPrevPage" onclick="navigateNovelPage(-1)">
                <i class="fa-solid fa-chevron-left"></i> 上一頁
            </button>
            <span id="novelPaginationText" style="font-weight: 600;">第 1 頁</span>
            <button class="novel-page-btn" id="btnNextPage" onclick="navigateNovelPage(1)">
                下一頁 <i class="fa-solid fa-chevron-right"></i>
            </button>
        </div>
    </main>

    <!-- 底部懸浮朗讀控制列 -->
    <div class="novel-floating-audio-bar" id="floatingAudioBar">
        <div class="audio-controls-left">
            <button class="audio-btn-circle" id="floatingPlayBtn" onclick="toggleFloatingPlay()" title="播放 / 暫停">
                <i class="fa-solid fa-play" id="floatingPlayIcon"></i>
            </button>
            <button class="audio-btn-square" onclick="NovelAudio.prevSentence()" title="上一句">
                <i class="fa-solid fa-backward-step"></i>
            </button>
            <button class="audio-btn-square" onclick="NovelAudio.nextSentence()" title="下一句">
                <i class="fa-solid fa-forward-step"></i>
            </button>
            <button class="audio-btn-square" onclick="NovelAudio.stop()" title="停止播放">
                <i class="fa-solid fa-stop text-rose-500"></i>
            </button>

            <div class="audio-status-info">
                <span id="audioModeBadge" class="badge-jlpt" style="background: #e0f2fe; color: #0369a1;">整頁朗讀</span>
                <span id="audioCurrentSentenceText" style="max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">準備朗讀</span>
            </div>
        </div>

        <div class="audio-controls-right">
            <span style="font-size: 0.85rem; color: #64748b;" id="audioProgressCounter">句 1 / 1</span>
            <button class="audio-btn-square" id="floatingFavoriteBtn" onclick="toggleCurrentPlayingSentenceFav()" title="收藏當前朗讀句子">
                <i class="fa-regular fa-star text-amber-500" id="floatingFavStar"></i>
            </button>
        </div>
    </div>

    <!-- 單字 Popover (點擊單字浮出) -->
    <div class="word-popover" id="wordPopover" style="display: none;">
        <button class="popover-close-btn" onclick="closeWordPopover()"><i class="fa-solid fa-xmark"></i></button>
        <div class="popover-header">
            <div class="popover-word-title" id="popoverWordSurface">単語</div>
            <span class="badge-jlpt" id="popoverWordLevel">N5</span>
        </div>
        <div class="popover-reading-row">
            <span class="popover-kana" id="popoverWordKana">たんご</span>
            <button class="btn-audio-mini" id="btnPlayWordAudio" title="真人語音發音"><i class="fa-solid fa-volume-high"></i></button>
            <span class="popover-pos" id="popoverWordPos">名詞</span>
        </div>
        <div class="popover-meaning-box" id="popoverWordMeaning">
            <div class="meaning-spinner"><i class="fa-solid fa-spinner fa-spin"></i> 正在查詢中文釋義...</div>
        </div>
        <div class="popover-footer" style="padding: 10px 14px; border-top: 1px solid var(--novel-border); display: flex; justify-content: flex-end;">
            <button class="novel-tool-btn" id="btnAddWordToNotebook" style="font-size: 0.85rem; padding: 5px 12px; background: #fffbeb; border-color: #fde68a; color: #b45309;">
                <i class="fa-regular fa-star"></i> 存入生詞本
            </button>
        </div>
    </div>

    <!-- 941 文法專屬彈出卡片 (點擊文法直接彈出，附帶連動按鈕) -->
    <div class="novel-modal-overlay" id="novelGrammarModal">
        <div class="novel-modal-box" style="max-width: 620px;">
            <div class="novel-modal-header" style="background: #eff6ff;">
                <h3 id="modalGrammarTitle"><i class="fa-solid fa-book-bookmark text-blue-600"></i> 文法解析</h3>
                <button class="novel-modal-close-btn" onclick="closeNovelGrammarModal()"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="novel-modal-body" id="modalGrammarBody">
                <!-- 動態注入接續、中文、日語解析、例文 -->
            </div>
        </div>
    </div>

    <!-- 句子收藏庫 Modal (查看、播放、刪除、匯出) -->
    <div class="novel-modal-overlay" id="savedSentencesModal">
        <div class="novel-modal-box" style="max-width: 720px;">
            <div class="novel-modal-header">
                <h3><i class="fa-solid fa-star text-amber-500"></i> 我的收藏句子庫 (<span id="savedModalTotalCount">0</span>)</h3>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <button class="novel-tool-btn" onclick="exportSavedSentences()" style="font-size: 0.8rem; padding: 4px 10px;">
                        <i class="fa-solid fa-file-export"></i> 匯出清單
                    </button>
                    <button class="novel-modal-close-btn" onclick="closeSavedSentencesModal()"><i class="fa-solid fa-xmark"></i></button>
                </div>
            </div>
            <div class="novel-modal-body" id="savedSentencesList" style="max-height: 68vh;">
                <!-- 動態載入收藏句子 -->
            </div>
        </div>
    </div>

    <!-- 拍照 / 圖片 OCR 辨識 Modal -->
    <div class="novel-modal-overlay" id="ocrModal">
        <div class="novel-modal-box" style="max-width: 660px;">
            <div class="novel-modal-header">
                <h3><i class="fa-solid fa-camera text-indigo-600"></i> 拍照 / 圖片日語 OCR 辨識</h3>
                <button class="novel-modal-close-btn" onclick="closeOcrModal()"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="novel-modal-body">
                <div style="background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 16px;">
                    <i class="fa-solid fa-cloud-arrow-up" style="font-size: 2.4rem; color: #64748b; margin-bottom: 10px;"></i>
                    <div style="font-weight: 600; color: #334155; margin-bottom: 6px;">拍照上傳或貼上書籍截圖 (Ctrl + V)</div>
                    <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 14px;">支援拍攝紙本書頁、日語小說、漫畫台詞與講義截圖</div>
                    
                    <div style="display: flex; justify-content: center; gap: 10px; flex-wrap: wrap;">
                        <label class="novel-tool-btn primary" style="cursor: pointer;">
                            <i class="fa-solid fa-camera"></i> 啟動相機拍照
                            <input type="file" id="cameraInput" accept="image/*" capture="environment" style="display: none;" onchange="handleImageFileSelect(event)">
                        </label>
                        <label class="novel-tool-btn" style="cursor: pointer;">
                            <i class="fa-solid fa-image"></i> 選取相簿圖片
                            <input type="file" id="imageInput" accept="image/*" style="display: none;" onchange="handleImageFileSelect(event)">
                        </label>
                    </div>
                </div>

                <!-- 辨識選項 (直排/橫排引擎切換) -->
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; padding: 8px 12px; background: #f1f5f9; border-radius: 8px;">
                    <span style="font-size: 0.88rem; font-weight: 600; color: #475569;">辨識方向模式：</span>
                    <div style="display: flex; gap: 8px;">
                        <label style="font-size: 0.85rem; cursor: pointer;">
                            <input type="radio" name="ocrDirection" value="jpn_vert" checked> 日文直排 (小說縱書)
                        </label>
                        <label style="font-size: 0.85rem; cursor: pointer; margin-left: 10px;">
                            <input type="radio" name="ocrDirection" value="jpn"> 日文橫排 (一般排版)
                        </label>
                    </div>
                </div>

                <!-- 預覽與進度 -->
                <div id="ocrPreviewArea" style="display: none; margin-bottom: 12px; text-align: center;">
                    <img id="ocrImagePreview" src="" style="max-height: 220px; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: 0 4px 10px rgba(0,0,0,0.06);">
                    <div id="ocrStatusText" style="margin-top: 8px; font-weight: 600; color: #2563eb; font-size: 0.9rem;"></div>
                </div>

                <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 14px;">
                    <button class="novel-tool-btn" onclick="closeOcrModal()">取消</button>
                    <button class="novel-tool-btn success" id="btnStartOcrRecognize" onclick="runOcrRecognition()" style="display: none;">
                        <i class="fa-solid fa-wand-magic-sparkles"></i> 開始 OCR 分析
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- 檔案匯入 Modal (支援 PDF 自選頁數、EPUB、TXT、DOCX) -->
    <div class="novel-modal-overlay" id="filePickerModal">
        <div class="novel-modal-box" style="max-width: 600px;">
            <div class="novel-modal-header">
                <h3><i class="fa-solid fa-file-import text-emerald-600"></i> 匯入小說檔案</h3>
                <button class="novel-modal-close-btn" onclick="closeFilePickerModal()"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="novel-modal-body">
                <div style="background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 16px;">
                    <i class="fa-solid fa-book" style="font-size: 2.2rem; color: #059669; margin-bottom: 8px;"></i>
                    <div style="font-weight: 600; color: #334155; margin-bottom: 4px;">選擇 PDF、EPUB、TXT、DOCX 或 MD 檔案</div>
                    <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 12px;">PDF 支援自選頁碼範圍，避免一次載入整本過重</div>
                    <label class="novel-tool-btn success" style="cursor: pointer;">
                        <i class="fa-solid fa-folder-open"></i> 瀏覽本機檔案
                        <input type="file" id="novelFileInput" accept=".pdf,.epub,.txt,.docx,.md" style="display: none;" onchange="handleNovelFileSelect(event)">
                    </label>
                </div>

                <!-- PDF 頁碼設定區 (偵測為 PDF 時顯現) -->
                <div id="pdfPageRangeBox" style="display: none; background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 10px; padding: 14px; margin-bottom: 16px;">
                    <div style="font-weight: 700; color: #065f46; margin-bottom: 8px; font-size: 0.95rem;">
                        <i class="fa-solid fa-file-pdf"></i> PDF 頁數設定 (總頁數：<span id="pdfTotalPagesDisplay">0</span> 頁)
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                        <label style="font-size: 0.88rem; color: #047857;">起始頁：
                            <input type="number" id="pdfStartPage" min="1" value="1" style="width: 70px; padding: 4px 8px; border-radius: 6px; border: 1px solid #6ee7b7;">
                        </label>
                        <label style="font-size: 0.88rem; color: #047857;">結束頁：
                            <input type="number" id="pdfEndPage" min="1" value="10" style="width: 70px; padding: 4px 8px; border-radius: 6px; border: 1px solid #6ee7b7;">
                        </label>
                        <span style="font-size: 0.8rem; color: #059669;">(建議單次載入 10~20 頁以達最佳流暢度)</span>
                    </div>
                </div>

                <div style="display: flex; justify-content: flex-end; gap: 10px;">
                    <button class="novel-tool-btn" onclick="closeFilePickerModal()">取消</button>
                    <button class="novel-tool-btn primary" id="btnConfirmLoadFile" onclick="confirmLoadFile()" style="display: none;">
                        <i class="fa-solid fa-check"></i> 確認載入開始閱讀
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- 引入 master.html 原生之生詞本 Modal (支援單字、文型、批次與 Anki) -->
    {notebook_modal_html}

    <!-- 浮動 Toast 提示條 (包含 toastMsg 容器，確保不報錯) -->
    <div id="toast" class="toast">
        <i class="fa-solid fa-circle-check text-emerald-400"></i>
        <span id="toastMsg">提示訊息</span>
    </div>
"""

print("[4/5] 編寫高穩定度小說閱讀器核心腳本 (Edge Natural TTS + 941 文法 + 收藏 + 朗讀整頁)...")

novel_script = """
        // ==========================================================================
        // 小說閱讀狀態管理器 (Novel Reader State)
        // ==========================================================================
        window.novelState = {
            currentBook: {
                title: "夏目漱石《心》(こころ)",
                totalPages: 1,
                pages: []
            },
            currentPageIndex: 0,
            fontSize: 1.28,
            writingMode: 'horizontal', // 'horizontal' | 'vertical'
            furiganaMode: 'all',       // 'all' | 'hard' | 'none'
            repeatCount: 3,
            selectedVoice: 'nanami',   // 'nanami' | 'keita'
            currentSentenceIndex: 0
        };

        // 安全 Toast 提示函數 (徹底修復 TypeError 崩潰問題)
        function showToast(msg) {
            const t = document.getElementById('toast');
            if (!t) return;
            const m = document.getElementById('toastMsg') || t;
            m.textContent = msg;
            t.classList.add('show');
            if (window.toastTimer) clearTimeout(window.toastTimer);
            window.toastTimer = setTimeout(() => t.classList.remove('show'), 2800);
        }

        // ==========================================================================
        // 微軟自然真人語音引擎 (NovelAudio) - 七海 Nanami & 圭太 Keita
        // ==========================================================================
        window.NovelAudio = {
            status: 'idle', // 'idle' | 'playing' | 'paused'
            playbackScope: 'whole_page', // 'whole_page' | 'sentence'
            currentUtterance: null,
            activeSentenceEl: null,
            pageSentenceQueue: [],
            currentQueueIdx: 0,
            repeatLeft: 1,

            // 解析語音參數 (支援 Nanami 自然女聲 與 Keita 自然男聲)
            getVoiceConfig(voicePref) {
                const voices = (window.speechSynthesis && window.speechSynthesis.getVoices()) || [];
                const jaVoices = voices.filter(v => v.lang && (v.lang.startsWith('ja') || v.lang.includes('JP')));
                const naturalVoices = jaVoices.filter(v => 
                    !v.name.includes('Desktop') && !v.name.includes('Haruka') && (/Natural|Online/i.test(v.name))
                );

                if (voicePref === 'keita') {
                    // 尋找原生男聲 (Keita, Daichi, Naoki 等)
                    const maleVoice = jaVoices.find(v => /Keita|圭太|Daichi|大地|Naoki|直樹|Takumi|拓海|Kenji/i.test(v.name));
                    if (maleVoice) {
                        return { voice: maleVoice, pitch: 1.0, rate: 0.95, isMale: true };
                    }
                    // 若系統未安裝 Keita，調用自然真音並降調至男聲共振頻率 (pitch 0.72)
                    const baseVoice = naturalVoices[0] || jaVoices[0] || null;
                    return { voice: baseVoice, pitch: 0.72, rate: 0.92, isMale: true };
                } else {
                    // Nanami 甜美自然女聲
                    const femaleVoice = naturalVoices.find(v => /Nanami|七海/i.test(v.name)) || naturalVoices[0] || jaVoices[0] || null;
                    return { voice: femaleVoice, pitch: 1.0, rate: 0.95, isMale: false };
                }
            },

            // 單字發音 (點擊單字浮動卡片中的 🔊 按鈕時觸發)
            speakWord(text) {
                if (!text) return;
                const clean = text.replace(/<[^>]+>/g, '').trim();
                const voicePref = document.getElementById('novelVoiceSelect')?.value || window.novelState.selectedVoice || 'nanami';
                const cfg = this.getVoiceConfig(voicePref);

                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                    const u = new SpeechSynthesisUtterance(clean);
                    if (cfg.voice) u.voice = cfg.voice;
                    u.lang = 'ja-JP';
                    u.pitch = cfg.pitch;
                    u.rate = cfg.rate;
                    window.speechSynthesis.speak(u);
                    return;
                }

                // Fallback: Google 雲端真人發音
                const audioUrl = 'https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=ja&q=' + encodeURIComponent(clean);
                const a = new Audio(audioUrl);
                a.playbackRate = cfg.isMale ? 0.88 : 0.95;
                a.play().catch(() => {});
            },

            // 朗讀指定句子 (含即時高亮與重複次數處理)
            speakSentence(text, containerEl, onFinish, customRepeatCount = null) {
                if (!text) {
                    if (onFinish) onFinish();
                    return;
                }
                const cleanText = text.replace(/<[^>]+>/g, '').trim();
                const totalRepeats = customRepeatCount !== null ? customRepeatCount : (window.novelState.repeatCount || 1);
                this.repeatLeft = totalRepeats;

                // 移除舊的句子高亮
                document.querySelectorAll('.karaoke-active-sentence').forEach(el => el.classList.remove('karaoke-active-sentence'));
                if (containerEl) {
                    containerEl.classList.add('karaoke-active-sentence');
                    this.activeSentenceEl = containerEl;
                    // 自動平滑捲動到當前句子
                    if (window.novelState.writingMode === 'vertical') {
                        containerEl.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
                    } else {
                        containerEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }

                const playOnce = () => {
                    if (this.status === 'idle') return;

                    const voicePref = document.getElementById('novelVoiceSelect')?.value || window.novelState.selectedVoice || 'nanami';
                    const cfg = this.getVoiceConfig(voicePref);

                    if ('speechSynthesis' in window) {
                        window.speechSynthesis.cancel();
                        const u = new SpeechSynthesisUtterance(cleanText);
                        if (cfg.voice) u.voice = cfg.voice;
                        u.lang = 'ja-JP';
                        u.pitch = cfg.pitch;
                        u.rate = cfg.rate;

                        u.onend = () => {
                            this.repeatLeft--;
                            if (this.repeatLeft > 0 && this.status === 'playing') {
                                showToast(`🔁 正在重複朗讀 (剩餘 ${this.repeatLeft} 次)...`);
                                setTimeout(playOnce, 320);
                            } else {
                                if (onFinish) onFinish();
                            }
                        };

                        u.onerror = () => {
                            if (onFinish) onFinish();
                        };

                        this.currentUtterance = u;
                        this.updateUIState('playing');
                        window.speechSynthesis.speak(u);
                    } else {
                        // Fallback Audio
                        const audioUrl = 'https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=ja&q=' + encodeURIComponent(cleanText.slice(0, 180));
                        const a = new Audio(audioUrl);
                        a.playbackRate = cfg.isMale ? 0.88 : 0.95;
                        a.onended = () => {
                            this.repeatLeft--;
                            if (this.repeatLeft > 0 && this.status === 'playing') {
                                setTimeout(playOnce, 320);
                            } else {
                                if (onFinish) onFinish();
                            }
                        };
                        a.onerror = () => { if (onFinish) onFinish(); };
                        this.updateUIState('playing');
                        a.play().catch(() => { if (onFinish) onFinish(); });
                    }
                };

                this.status = 'playing';
                playOnce();
            },

            // 朗讀整頁核心流程 (從第 startIdx 句連播至本頁結束)
            playWholePage(startIdx = 0) {
                const book = window.novelState.currentBook;
                const page = book.pages && book.pages[window.novelState.currentPageIndex];
                if (!page || !page.sentences || page.sentences.length === 0) {
                    showToast('本頁尚無可供朗讀之日語句子！');
                    return;
                }

                this.playbackScope = 'whole_page';
                this.pageSentenceQueue = page.sentences;
                this.currentQueueIdx = startIdx >= 0 && startIdx < page.sentences.length ? startIdx : 0;
                this.status = 'playing';
                this.updateUIState('playing');

                const playNext = () => {
                    if (this.status === 'idle') return;
                    if (this.currentQueueIdx >= this.pageSentenceQueue.length) {
                        this.stop(false);
                        showToast('🎉 本頁已朗讀完畢！');
                        return;
                    }

                    const s = this.pageSentenceQueue[this.currentQueueIdx];
                    window.novelState.currentSentenceIndex = this.currentQueueIdx;
                    this.updateProgressBadge();

                    const sRow = document.querySelector(`.sentence-row[data-sentence-idx="${this.currentQueueIdx}"]`);
                    this.speakSentence(s.text, sRow, () => {
                        this.currentQueueIdx++;
                        playNext();
                    });
                };

                playNext();
            },

            pause() {
                if ('speechSynthesis' in window && window.speechSynthesis.speaking) {
                    window.speechSynthesis.pause();
                }
                this.status = 'paused';
                this.updateUIState('paused');
                showToast('⏸️ 朗讀已暫停');
            },

            resume() {
                if ('speechSynthesis' in window && window.speechSynthesis.paused) {
                    window.speechSynthesis.resume();
                }
                this.status = 'playing';
                this.updateUIState('playing');
                showToast('▶️ 繼續朗讀');
            },

            stop(notify = true) {
                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                }
                this.status = 'idle';
                this.currentUtterance = null;
                document.querySelectorAll('.karaoke-active-sentence').forEach(el => el.classList.remove('karaoke-active-sentence'));
                this.updateUIState('idle');
                if (notify) showToast('⏹️ 已停止朗讀');
            },

            nextSentence() {
                if (this.playbackScope === 'whole_page' && this.pageSentenceQueue.length > 0) {
                    this.currentQueueIdx = Math.min(this.pageSentenceQueue.length - 1, this.currentQueueIdx + 1);
                    this.playWholePage(this.currentQueueIdx);
                }
            },

            prevSentence() {
                if (this.playbackScope === 'whole_page' && this.pageSentenceQueue.length > 0) {
                    this.currentQueueIdx = Math.max(0, this.currentQueueIdx - 1);
                    this.playWholePage(this.currentQueueIdx);
                }
            },

            updateProgressBadge() {
                const total = this.pageSentenceQueue.length || 1;
                const cur = (this.currentQueueIdx || 0) + 1;
                const counter = document.getElementById('audioProgressCounter');
                if (counter) counter.textContent = `句 ${cur} / ${total}`;

                const sObj = this.pageSentenceQueue[this.currentQueueIdx];
                const textEl = document.getElementById('audioCurrentSentenceText');
                if (textEl && sObj) {
                    textEl.textContent = sObj.text;
                }

                // 更新懸浮欄的收藏星號狀態
                if (sObj) {
                    const isFav = getSavedSentences().some(item => item.text === sObj.text);
                    const starIcon = document.getElementById('floatingFavStar');
                    if (starIcon) {
                        starIcon.className = `fa-${isFav ? 'solid' : 'regular'} fa-star text-amber-500`;
                    }
                }
            },

            updateUIState(st) {
                const mainBtn = document.getElementById('btnPlayWholePage');
                const mainIcon = document.getElementById('mainPlayIcon');
                const mainText = document.getElementById('mainPlayBtnText');
                const stopBtn = document.getElementById('btnStopPageAudio');

                const floatIcon = document.getElementById('floatingPlayIcon');
                const modeBadge = document.getElementById('audioModeBadge');

                if (st === 'playing') {
                    if (mainBtn) mainBtn.className = 'novel-tool-btn warning';
                    if (mainIcon) mainIcon.className = 'fa-solid fa-pause';
                    if (mainText) mainText.textContent = '暫停朗讀';
                    if (stopBtn) stopBtn.style.display = 'inline-flex';

                    if (floatIcon) floatIcon.className = 'fa-solid fa-pause';
                    if (modeBadge) modeBadge.textContent = this.playbackScope === 'whole_page' ? '整頁連續朗讀' : '單句朗讀';
                } else if (st === 'paused') {
                    if (mainBtn) mainBtn.className = 'novel-tool-btn primary';
                    if (mainIcon) mainIcon.className = 'fa-solid fa-play';
                    if (mainText) mainText.textContent = '繼續朗讀';
                    if (stopBtn) stopBtn.style.display = 'inline-flex';

                    if (floatIcon) floatIcon.className = 'fa-solid fa-play';
                } else {
                    if (mainBtn) mainBtn.className = 'novel-tool-btn primary';
                    if (mainIcon) mainIcon.className = 'fa-solid fa-play';
                    if (mainText) mainText.textContent = '朗讀本頁';
                    if (stopBtn) stopBtn.style.display = 'none';

                    if (floatIcon) floatIcon.className = 'fa-solid fa-play';
                }
            }
        };

        // 全域 speakJapanese 轉發至 NovelAudio.speakWord
        window.speakJapanese = function(text) {
            window.NovelAudio.speakWord(text);
        };

        // ==========================================================================
        // 句子收藏庫管理 (Sentence Favorite Storage)
        // ==========================================================================
        function getSavedSentences() {
            try {
                return JSON.parse(localStorage.getItem('novel_saved_sentences') || '[]');
            } catch (e) {
                return [];
            }
        }

        function toggleFavoriteSentence(text, pageNum, bookTitle) {
            let list = getSavedSentences();
            const idx = list.findIndex(item => item.text === text);
            let isNowFav = false;

            if (idx >= 0) {
                list.splice(idx, 1);
                isNowFav = false;
                showToast('已自收藏庫移除。');
            } else {
                list.unshift({
                    id: Date.now(),
                    text: text,
                    pageNum: pageNum || (window.novelState.currentPageIndex + 1),
                    bookTitle: bookTitle || window.novelState.currentBook.title,
                    time: new Date().toLocaleDateString()
                });
                isNowFav = true;
                showToast('⭐ 已成功存入句子收藏庫！');
            }

            // 確保第一時間持久化至 LocalStorage
            try {
                localStorage.setItem('novel_saved_sentences', JSON.stringify(list));
            } catch (err) {
                console.error('LocalStorage save error:', err);
            }

            updateSavedSentencesCountBadge();
            renderSavedSentencesList();
            return isNowFav;
        }

        function updateSavedSentencesCountBadge() {
            const list = getSavedSentences();
            const b = document.getElementById('savedSentencesCountBadge');
            if (b) b.textContent = list.length;
            const mb = document.getElementById('savedModalTotalCount');
            if (mb) mb.textContent = list.length;
        }

        function openSavedSentencesModal() {
            renderSavedSentencesList();
            const m = document.getElementById('savedSentencesModal');
            if (m) m.classList.add('open');
        }

        function closeSavedSentencesModal() {
            const m = document.getElementById('savedSentencesModal');
            if (m) m.classList.remove('open');
        }

        function renderSavedSentencesList() {
            const list = getSavedSentences();
            const container = document.getElementById('savedSentencesList');
            if (!container) return;

            if (list.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 40px 10px; color: #94a3b8;">
                        <i class="fa-regular fa-star" style="font-size: 2.8rem; margin-bottom: 12px; color: #cbd5e1;"></i>
                        <div style="font-size: 1.05rem; font-weight: 600; color: #64748b;">目前尚無收藏的句子</div>
                        <div style="font-size: 0.85rem; margin-top: 6px;">在閱讀時點擊句子旁的 ⭐ 即可立即加入！</div>
                    </div>
                `;
                return;
            }

            container.innerHTML = list.map((item, idx) => `
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; margin-bottom: 10px; display: flex; flex-direction: column; gap: 8px;">
                    <div style="font-size: 1.15rem; font-family: var(--font-jp); line-height: 1.8; color: #1e293b;">
                        ${item.text}
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.8rem; color: #64748b; border-top: 1px dashed #e2e8f0; padding-top: 6px;">
                        <span><i class="fa-solid fa-bookmark text-amber-500"></i> ${escapeHtml(item.bookTitle)} (第 ${item.pageNum} 頁) · ${item.time}</span>
                        <div style="display: flex; gap: 8px;">
                            <button class="novel-tool-btn" onclick="NovelAudio.speakWord('${escapeJsString(item.text)}')" style="padding: 3px 8px; font-size: 0.78rem;">
                                <i class="fa-solid fa-volume-high"></i> 朗讀
                            </button>
                            <button class="novel-tool-btn" onclick="copyToClipboard('${escapeJsString(item.text)}')" style="padding: 3px 8px; font-size: 0.78rem;">
                                <i class="fa-regular fa-copy"></i> 複製
                            </button>
                            <button class="novel-tool-btn" onclick="deleteSavedSentence(${item.id})" style="padding: 3px 8px; font-size: 0.78rem; color: #ef4444;">
                                <i class="fa-solid fa-trash"></i> 刪除
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        window.deleteSavedSentence = function(id) {
            let list = getSavedSentences();
            list = list.filter(item => item.id !== id);
            localStorage.setItem('novel_saved_sentences', JSON.stringify(list));
            updateSavedSentencesCountBadge();
            renderSavedSentencesList();
            showToast('已刪除收藏句子。');
        };

        window.exportSavedSentences = function() {
            const list = getSavedSentences();
            if (list.length === 0) {
                showToast('目前無收藏句子可匯出。');
                return;
            }
            const content = list.map((item, i) => `${i+1}. [${item.bookTitle} P.${item.pageNum}]\\n${item.text}\\n`).join('\\n');
            const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `日語小說收藏句子_${new Date().toISOString().slice(0,10)}.txt`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('已成功匯出句子文字檔！');
        };

        window.toggleCurrentPlayingSentenceFav = function() {
            const queue = window.NovelAudio.pageSentenceQueue;
            const idx = window.NovelAudio.currentQueueIdx;
            const sObj = queue && queue[idx];
            if (!sObj) return;

            const isFav = toggleFavoriteSentence(sObj.text, window.novelState.currentPageIndex + 1, window.novelState.currentBook.title);
            const starIcon = document.getElementById('floatingFavStar');
            if (starIcon) {
                starIcon.className = `fa-${isFav ? 'solid' : 'regular'} fa-star text-amber-500`;
            }
            // 同步頁面上該句的星號
            const row = document.querySelector(`.sentence-row[data-sentence-idx="${idx}"]`);
            if (row) {
                const sBtn = row.querySelector('.sentence-star-btn');
                if (sBtn) {
                    sBtn.className = `sentence-star-btn ${isFav ? 'is-fav' : ''}`;
                    sBtn.innerHTML = `<i class="fa-${isFav ? 'solid' : 'regular'} fa-star"></i>`;
                }
            }
        };

        // ==========================================================================
        // 941 文法彈出卡片 (Grammar Popup Detail Modal)
        // ==========================================================================
        window.showNovelGrammarCard = function(grammarId) {
            const g = (window.GRAMMAR_DATA || []).find(item => item.id === grammarId);
            if (!g) {
                showToast('查無該條 941 文法之詳細資料。');
                return;
            }

            const titleEl = document.getElementById('modalGrammarTitle');
            if (titleEl) {
                titleEl.innerHTML = `<i class="fa-solid fa-book-bookmark text-blue-600"></i> ${escapeHtml(g.title)} <span class="badge-jlpt badge-${(g.level || 'n2').toLowerCase()}" style="margin-left: 8px;">${g.level || 'JLPT'}</span>`;
            }

            const bodyEl = document.getElementById('modalGrammarBody');
            if (bodyEl) {
                bodyEl.innerHTML = `
                    <div style="background: #f8fafc; border-radius: 10px; padding: 14px; margin-bottom: 12px; border-left: 4px solid #2563eb;">
                        <div style="font-size: 0.85rem; font-weight: 700; color: #64748b; margin-bottom: 4px;">接續規則 (Connection Form)</div>
                        <div style="font-weight: 700; color: #1e40af; font-size: 1.05rem;">${escapeHtml(g.form || '無特殊接續限制')}</div>
                    </div>

                    <div style="background: #f8fafc; border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-size: 0.85rem; font-weight: 700; color: #64748b; margin-bottom: 4px;">中文深度解析</div>
                        <div style="font-size: 1.02rem; line-height: 1.7; color: #1e293b;">${escapeHtml(g.meaningZh || g.meaning || '暫無中文說明')}</div>
                        ${g.meaningJa ? `<div style="font-size: 0.88rem; color: #64748b; margin-top: 8px; border-top: 1px dashed #cbd5e1; padding-top: 6px;">日語說明：${escapeHtml(g.meaningJa)}</div>` : ''}
                    </div>

                    <div style="background: #fdfbf7; border: 1px solid #fde68a; border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-size: 0.85rem; font-weight: 700; color: #b45309; margin-bottom: 6px;">精選例文與振假名 (點擊朗讀)</div>
                        <div style="font-size: 1.22rem; font-family: var(--font-jp); line-height: 2.2; cursor: pointer;" onclick="NovelAudio.speakWord('${escapeJsString((g.example || '').replace(/<[^>]+>/g, ''))}')">
                            ${g.exampleRuby || escapeHtml(g.example || '')}
                        </div>
                        <div style="font-size: 0.95rem; color: #475569; margin-top: 6px; border-top: 1px dashed #fcd34d; padding-top: 6px;">
                            <strong>譯文：</strong>${escapeHtml(g.translation || '暫無翻譯')}
                        </div>
                    </div>

                    ${g.note ? `
                    <div style="background: #fffbeb; border-radius: 10px; padding: 12px; margin-bottom: 12px; font-size: 0.9rem; color: #92400e;">
                        <strong>💡 記憶要點：</strong>${escapeHtml(g.note)}
                    </div>
                    ` : ''}

                    <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 14px; border-top: 1px solid #e2e8f0; padding-top: 12px;">
                        <a href="https://fobeetsai.github.io/japanese-grammar/?id=${g.id}" target="_blank" class="novel-tool-btn primary" style="text-decoration: none;">
                            <i class="fa-solid fa-arrow-up-right-from-square"></i> 在 941 文法庫中開啟深度抽屜
                        </a>
                        <button class="novel-tool-btn" onclick="closeNovelGrammarModal()">關閉</button>
                    </div>
                `;
            }

            const m = document.getElementById('novelGrammarModal');
            if (m) m.classList.add('open');
        };

        window.closeNovelGrammarModal = function() {
            const m = document.getElementById('novelGrammarModal');
            if (m) m.classList.remove('open');
        };

        // ==========================================================================
        // 渲染小說句子核心 (整合 941 文法高亮與單字點擊發音、收藏)
        // ==========================================================================
        function renderNovelPage(pageIdx) {
            const book = window.novelState.currentBook;
            if (!book.pages || book.pages.length === 0) return;

            if (pageIdx < 0) pageIdx = 0;
            if (pageIdx >= book.pages.length) pageIdx = book.pages.length - 1;
            window.novelState.currentPageIndex = pageIdx;

            const page = book.pages[pageIdx];
            const listEl = document.getElementById('novelSentencesList');
            if (!listEl) return;

            // 更新頁碼指示
            const badge = document.getElementById('novelPageBadge');
            if (badge) badge.textContent = `第 ${pageIdx + 1} 頁`;
            const indicator = document.getElementById('novelPageIndicator');
            if (indicator) indicator.textContent = `第 ${pageIdx + 1} 頁 / 共 ${book.pages.length} 頁`;
            const paginationText = document.getElementById('novelPaginationText');
            if (paginationText) paginationText.textContent = `第 ${pageIdx + 1} / ${book.pages.length} 頁`;

            const prevBtn = document.getElementById('btnPrevPage');
            const nextBtn = document.getElementById('btnNextPage');
            if (prevBtn) prevBtn.disabled = pageIdx <= 0;
            if (nextBtn) nextBtn.disabled = pageIdx >= book.pages.length - 1;

            const savedList = getSavedSentences();

            listEl.innerHTML = page.sentences.map((s, sIdx) => {
                const isFav = savedList.some(item => item.text === s.text);
                const hasGrammars = s.grammars && s.grammars.length > 0;

                const grammarBadgesHtml = hasGrammars ? s.grammars.map(g => `
                    <span class="novel-grammar-badge" onclick="event.stopPropagation(); showNovelGrammarCard(${g.id})" title="點擊查看【${escapeHtml(g.title)}】文法解析">
                        <i class="fa-solid fa-tag"></i> ${escapeHtml(g.title)}
                    </span>
                `).join('') : '';

                return `
                    <div class="sentence-row" data-sentence-idx="${sIdx}">
                        <div class="sentence-content" id="s_content_${sIdx}">
                            <!-- tokens generated -->
                        </div>
                        <div class="sentence-actions-bar">
                            <button class="sentence-btn-mini" onclick="playSingleSentenceAt(${sIdx})" title="朗讀此句">
                                <i class="fa-solid fa-play"></i> 朗讀
                            </button>
                            <button class="sentence-star-btn ${isFav ? 'is-fav' : ''}" onclick="toggleSentenceFavAt(${sIdx}, event)" title="收藏句子">
                                <i class="fa-${isFav ? 'solid' : 'regular'} fa-star"></i>
                            </button>
                            ${grammarBadgesHtml}
                        </div>
                    </div>
                `;
            }).join('');

            // 為每一句注入 Word Tokens 與點擊事件
            page.sentences.forEach((s, sIdx) => {
                const container = document.getElementById(`s_content_${sIdx}`);
                if (container) {
                    renderTokensIntoContainer(container, s);
                }
            });

            // 重設朗讀整頁隊列為當前頁
            window.NovelAudio.pageSentenceQueue = page.sentences;
            window.NovelAudio.currentQueueIdx = 0;
            window.NovelAudio.updateProgressBadge();
        }

        function renderTokensIntoContainer(container, sentenceObj) {
            container.innerHTML = '';
            const words = sentenceObj.words || [];

            words.forEach(w => {
                const tokenSpan = document.createElement('span');
                tokenSpan.className = 'token';

                if (w.jlpt) {
                    tokenSpan.classList.add(`vocab-${w.jlpt.toLowerCase()}`);
                }

                // 振假名處理 (遵循全假名/難字假名/純日文模式)
                const mode = window.novelState.furiganaMode;
                const showFurigana = mode === 'all' || (mode === 'hard' && w.jlpt && ['N1','N2','N3'].includes(w.jlpt));

                if (w.reading && w.reading !== w.surface && showFurigana && /[\u4e00-\u9faf]/.test(w.surface)) {
                    tokenSpan.innerHTML = `<ruby>${escapeHtml(w.surface)}<rt>${escapeHtml(w.reading)}</rt></ruby>`;
                } else {
                    tokenSpan.textContent = w.surface;
                }

                // 檢查該 token 是否屬於 941 文法片段
                const matchingGrammar = (sentenceObj.grammars || []).find(g => {
                    return sentenceObj.text.includes(g.title) && (w.surface.includes(g.title) || g.title.includes(w.surface));
                });

                if (matchingGrammar) {
                    tokenSpan.classList.add('novel-grammar-highlight');
                    tokenSpan.title = `941 文法: ${matchingGrammar.title} (點擊開啟卡片)`;
                    tokenSpan.addEventListener('click', (e) => {
                        e.stopPropagation();
                        showNovelGrammarCard(matchingGrammar.id);
                    });
                } else {
                    tokenSpan.addEventListener('click', (e) => {
                        e.stopPropagation();
                        showNovelWordPopover(tokenSpan, w, e);
                    });
                }

                container.appendChild(tokenSpan);
            });
        }

        // ==========================================================================
        // 單字浮動 Popover 與 生詞本 (Word Popover & Vocabulary Notebook)
        // ==========================================================================
        async function showNovelWordPopover(targetElem, word, event) {
            const popover = document.getElementById('wordPopover');
            if (!popover) return;

            const rect = targetElem.getBoundingClientRect();
            document.getElementById('popoverWordSurface').textContent = word.surface;
            document.getElementById('popoverWordKana').textContent = word.reading || word.surface;
            document.getElementById('popoverWordPos').textContent = word.pos || '單字';

            const lvlBadge = document.getElementById('popoverWordLevel');
            if (word.jlpt) {
                lvlBadge.textContent = word.jlpt;
                lvlBadge.className = `badge-jlpt badge-${word.jlpt.toLowerCase()}`;
                lvlBadge.style.display = 'inline-flex';
            } else {
                lvlBadge.style.display = 'none';
            }

            // 綁定發音按鈕 (採用真人自然真音)
            const audioBtn = document.getElementById('btnPlayWordAudio');
            if (audioBtn) {
                audioBtn.onclick = (e) => {
                    e.stopPropagation();
                    window.NovelAudio.speakWord(word.surface || word.reading);
                };
            }

            // 綁定存入生詞本按鈕
            const addBtn = document.getElementById('btnAddWordToNotebook');
            if (addBtn) {
                const isFav = isWordInNotebook(word.surface);
                addBtn.innerHTML = isFav 
                    ? '<i class="fa-solid fa-star text-amber-500"></i> 已在生詞本中'
                    : '<i class="fa-regular fa-star"></i> 存入生詞本';

                addBtn.onclick = (e) => {
                    e.stopPropagation();
                    const nowFav = toggleNovelWordNotebook(word);
                    addBtn.innerHTML = nowFav 
                        ? '<i class="fa-solid fa-star text-amber-500"></i> 已在生詞本中'
                        : '<i class="fa-regular fa-star"></i> 存入生詞本';
                };
            }

            // 顯示與定位
            popover.style.display = 'flex';
            const popoverWidth = 290;
            let left = rect.left + window.scrollX - (popoverWidth / 2) + (rect.width / 2);
            let top = rect.bottom + window.scrollY + 8;
            if (left < 10) left = 10;
            if (left + popoverWidth > window.innerWidth - 10) left = window.innerWidth - popoverWidth - 10;

            popover.style.left = `${left}px`;
            popover.style.top = `${top}px`;

            // 即時查詢中文釋義
            const meaningBox = document.getElementById('popoverWordMeaning');
            meaningBox.innerHTML = '<div class="meaning-spinner"><i class="fa-solid fa-spinner fa-spin"></i> 正在查詢釋義...</div>';
            
            let trans = '暫無釋義';
            if (typeof translateJaToZh === 'function') {
                trans = await translateJaToZh(word.base_form || word.surface);
            }
            const kBox = (typeof getKanjiReadingsHtml === 'function') ? getKanjiReadingsHtml(word.base_form || word.surface, word.reading) : '';
            meaningBox.innerHTML = `<strong>中文釋義：</strong>${escapeHtml(trans || '暫無釋義')}${kBox ? `<div style="margin-top:8px;border-top:1px dashed var(--novel-border);padding-top:6px;"><div style="font-size:0.75rem;font-weight:700;color:#64748b;margin-bottom:4px;">漢字音訓對照：</div>${kBox}</div>` : ''}`;
        }

        function closeWordPopover() {
            const p = document.getElementById('wordPopover');
            if (p) p.style.display = 'none';
        }

        function isWordInNotebook(surface) {
            try {
                const nb = JSON.parse(localStorage.getItem('yuedu_gaoshou_notebook') || '{}');
                const words = nb.words || [];
                return words.some(w => w.surface === surface);
            } catch (e) {
                return false;
            }
        }

        function toggleNovelWordNotebook(word) {
            let nb = {};
            try {
                nb = JSON.parse(localStorage.getItem('yuedu_gaoshou_notebook') || '{"words":[],"grammars":[],"articles":[]}');
            } catch (e) {
                nb = { words: [], grammars: [], articles: [] };
            }
            if (!nb.words) nb.words = [];

            const idx = nb.words.findIndex(w => w.surface === word.surface);
            let isNowIn = false;

            if (idx > -1) {
                nb.words.splice(idx, 1);
                isNowIn = false;
                showToast(`已自生詞本移除「${word.surface}」`);
            } else {
                nb.words.unshift({
                    surface: word.surface,
                    baseForm: word.base_form || word.surface,
                    reading: word.reading || word.surface,
                    jlpt: word.jlpt || '',
                    pos: word.pos || '單字',
                    addedAt: new Date().toLocaleDateString()
                });
                isNowIn = true;
                showToast(`⭐ 已存入生詞本「${word.surface}」！`);
            }

            try {
                localStorage.setItem('yuedu_gaoshou_notebook', JSON.stringify(nb));
            } catch (err) {
                console.error(err);
            }

            // 同步記憶體 state
            if (window.state && window.state.notebook) {
                window.state.notebook = nb;
            }

            updateNotebookBadges();
            return isNowIn;
        }

        function updateNotebookBadges() {
            try {
                const nb = JSON.parse(localStorage.getItem('yuedu_gaoshou_notebook') || '{}');
                const wordCount = (nb.words && nb.words.length) || 0;
                const b = document.getElementById('savedWordsCountBadge');
                if (b) b.textContent = wordCount;
                const nbW = document.getElementById('nbWordCount');
                if (nbW) nbW.textContent = wordCount;
            } catch (e) {}
        }

        // ==========================================================================
        // 閱讀器操作動作 (播放、翻頁、直橫排、字體縮放)
        // ==========================================================================
        window.playSingleSentenceAt = function(sIdx) {
            const page = window.novelState.currentBook.pages[window.novelState.currentPageIndex];
            if (!page || !page.sentences[sIdx]) return;
            const s = page.sentences[sIdx];
            window.NovelAudio.playbackScope = 'sentence';
            window.NovelAudio.currentQueueIdx = sIdx;
            window.NovelAudio.updateProgressBadge();

            const row = document.querySelector(`.sentence-row[data-sentence-idx="${sIdx}"]`);
            window.NovelAudio.speakSentence(s.text, row, () => {
                row.classList.remove('karaoke-active-sentence');
            });
        };

        window.toggleSentenceFavAt = function(sIdx, event) {
            if (event) event.stopPropagation();
            const page = window.novelState.currentBook.pages[window.novelState.currentPageIndex];
            if (!page || !page.sentences[sIdx]) return;
            const s = page.sentences[sIdx];

            const isFav = toggleFavoriteSentence(s.text, window.novelState.currentPageIndex + 1, window.novelState.currentBook.title);
            const row = document.querySelector(`.sentence-row[data-sentence-idx="${sIdx}"]`);
            if (row) {
                const starBtn = row.querySelector('.sentence-star-btn');
                if (starBtn) {
                    starBtn.className = `sentence-star-btn ${isFav ? 'is-fav' : ''}`;
                    starBtn.innerHTML = `<i class="fa-${isFav ? 'solid' : 'regular'} fa-star"></i>`;
                }
            }
        };

        window.toggleFloatingPlay = function() {
            if (window.NovelAudio.status === 'playing') {
                window.NovelAudio.pause();
            } else if (window.NovelAudio.status === 'paused') {
                window.NovelAudio.resume();
            } else {
                window.NovelAudio.playWholePage();
            }
        };

        window.navigateNovelPage = function(delta) {
            window.NovelAudio.stop(false);
            const book = window.novelState.currentBook;
            const newIdx = window.novelState.currentPageIndex + delta;
            if (newIdx >= 0 && newIdx < book.pages.length) {
                renderNovelPage(newIdx);
                const card = document.getElementById('novelContentCard');
                if (card) {
                    card.scrollTop = 0;
                    card.scrollLeft = 0;
                }
            }
        };

        window.toggleWritingMode = function() {
            const card = document.getElementById('novelContentCard');
            const btnText = document.getElementById('writingModeText');
            if (window.novelState.writingMode === 'horizontal') {
                window.novelState.writingMode = 'vertical';
                card.classList.add('vertical-mode');
                if (btnText) btnText.textContent = '現代橫排';
                showToast('已切換為【日文直排 (縱書)】模式');
            } else {
                window.novelState.writingMode = 'horizontal';
                card.classList.remove('vertical-mode');
                if (btnText) btnText.textContent = '直排縱書';
                showToast('已切換為【現代橫排 (橫書)】模式');
            }
        };

        window.changeFuriganaMode = function(mode) {
            window.novelState.furiganaMode = mode;
            renderNovelPage(window.novelState.currentPageIndex);
            if (mode === 'all') {
                showToast('已開啟【全部漢字振假名】');
            } else if (mode === 'hard') {
                showToast('已開啟【僅難字/N1-N3標註】(進階沉浸)');
            } else {
                showToast('已開啟【純日文閱讀 (懸停查讀音)】');
            }
        };

        window.adjustNovelFontSize = function(delta) {
            let cur = window.novelState.fontSize;
            cur += delta * 0.12;
            if (cur < 0.9) cur = 0.9;
            if (cur > 2.0) cur = 2.0;
            window.novelState.fontSize = cur;
            document.documentElement.style.setProperty('--novel-font-size', `${cur.toFixed(2)}rem`);
            showToast(`字級已調整為：${cur.toFixed(2)}rem`);
        };

        // ==========================================================================
        // 拍照 / 圖片 OCR 辨識引擎 (Tesseract.js 日語直排與橫排)
        // ==========================================================================
        let selectedOcrImageFile = null;

        function openOcrModal() {
            const m = document.getElementById('ocrModal');
            if (m) m.classList.add('open');
        }

        function closeOcrModal() {
            const m = document.getElementById('ocrModal');
            if (m) m.classList.remove('open');
        }

        function handleImageFileSelect(event) {
            const file = event.target.files && event.target.files[0];
            if (!file) return;
            selectedOcrImageFile = file;

            const reader = new FileReader();
            reader.onload = (e) => {
                const previewImg = document.getElementById('ocrImagePreview');
                const previewArea = document.getElementById('ocrPreviewArea');
                const startBtn = document.getElementById('btnStartOcrRecognize');
                if (previewImg) previewImg.src = e.target.result;
                if (previewArea) previewArea.style.display = 'block';
                if (startBtn) startBtn.style.display = 'inline-flex';
                showToast('圖片已載入，請點擊「開始 OCR 分析」！');
            };
            reader.readAsDataURL(file);
        }

        // 支援鍵盤直接 Ctrl + V 貼上截圖
        window.addEventListener('paste', (e) => {
            const items = (e.clipboardData || e.originalEvent.clipboardData).items;
            for (let item of items) {
                if (item.kind === 'file' && item.type.startsWith('image/')) {
                    const blob = item.getAsFile();
                    selectedOcrImageFile = blob;
                    const reader = new FileReader();
                    reader.onload = (evt) => {
                        openOcrModal();
                        const previewImg = document.getElementById('ocrImagePreview');
                        const previewArea = document.getElementById('ocrPreviewArea');
                        const startBtn = document.getElementById('btnStartOcrRecognize');
                        if (previewImg) previewImg.src = evt.target.result;
                        if (previewArea) previewArea.style.display = 'block';
                        if (startBtn) startBtn.style.display = 'inline-flex';
                        showToast('已偵測到剪貼簿截圖，可直接進行 OCR 分析！');
                    };
                    reader.readAsDataURL(blob);
                    break;
                }
            }
        });

        async function runOcrRecognition() {
            if (!selectedOcrImageFile) return;

            const directionRadios = document.getElementsByName('ocrDirection');
            let lang = 'jpn_vert';
            for (let r of directionRadios) {
                if (r.checked) { lang = r.value; break; }
            }

            const statusText = document.getElementById('ocrStatusText');
            if (statusText) statusText.textContent = '正在初始化 OCR 辨識模型...';
            showToast('正在辨識書頁日文文字，請稍候...');

            try {
                if (typeof Tesseract === 'undefined') {
                    throw new Error('Tesseract OCR 組件正在載入，請稍候再試。');
                }

                const worker = await Tesseract.createWorker(lang);
                if (statusText) statusText.textContent = '正在進行高精準光學字元辨識...';

                const ret = await worker.recognize(selectedOcrImageFile);
                await worker.terminate();

                const text = ret.data.text.trim();
                if (!text) {
                    throw new Error('未在圖片中偵測到清晰文字，請更換光線充足之圖片重試。');
                }

                // 辨識成功，將文字載入為新書頁
                loadRawTextIntoNovel(text, '📸 拍照書頁辨識');
                closeOcrModal();
                showToast('🎉 書頁辨識完成！已自動載入並完成 941 文法與假名解析！');
            } catch (err) {
                if (statusText) statusText.textContent = `辨識出錯：${err.message}`;
                showToast(`辨識失敗：${err.message}`);
            }
        }

        // ==========================================================================
        // 檔案匯入 (PDF 自選頁碼、EPUB、TXT、DOCX)
        // ==========================================================================
        let selectedNovelFile = null;
        let loadedPdfDoc = null;

        function openFilePickerModal() {
            const m = document.getElementById('filePickerModal');
            if (m) m.classList.add('open');
        }

        function closeFilePickerModal() {
            const m = document.getElementById('filePickerModal');
            if (m) m.classList.remove('open');
        }

        async function handleNovelFileSelect(event) {
            const file = event.target.files && event.target.files[0];
            if (!file) return;
            selectedNovelFile = file;

            const name = file.name.toLowerCase();
            const pdfBox = document.getElementById('pdfPageRangeBox');
            const confirmBtn = document.getElementById('btnConfirmLoadFile');

            if (name.endsWith('.pdf')) {
                showToast(`正在讀取 PDF 架構：${file.name}...`);
                const arrayBuffer = await file.arrayBuffer();
                loadedPdfDoc = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
                const total = loadedPdfDoc.numPages;
                document.getElementById('pdfTotalPagesDisplay').textContent = total;
                document.getElementById('pdfStartPage').value = 1;
                document.getElementById('pdfEndPage').value = Math.min(10, total);
                document.getElementById('pdfEndPage').max = total;
                if (pdfBox) pdfBox.style.display = 'block';
                if (confirmBtn) confirmBtn.style.display = 'inline-flex';
                showToast(`PDF 總共 ${total} 頁，請自選要讀取的頁數範圍！`);
            } else {
                if (pdfBox) pdfBox.style.display = 'none';
                if (confirmBtn) confirmBtn.style.display = 'inline-flex';
                showToast(`已選取檔案：${file.name}，請點擊確認載入！`);
            }
        }

        async function confirmLoadFile() {
            if (!selectedNovelFile) return;
            const name = selectedNovelFile.name.toLowerCase();

            try {
                if (name.endsWith('.pdf') && loadedPdfDoc) {
                    const startPage = parseInt(document.getElementById('pdfStartPage').value, 10) || 1;
                    const endPage = parseInt(document.getElementById('pdfEndPage').value, 10) || loadedPdfDoc.numPages;
                    
                    showToast(`正在提取第 ${startPage} 至 ${endPage} 頁文字...`);
                    let fullText = '';
                    for (let p = startPage; p <= endPage; p++) {
                        const page = await loadedPdfDoc.getPage(p);
                        const textContent = await page.getTextContent();
                        const pageStr = textContent.items.map(item => item.str).join('');
                        fullText += `\\n\\n--- 第 ${p} 頁 ---\\n\\n` + pageStr;
                    }
                    loadRawTextIntoNovel(fullText, `${selectedNovelFile.name} (P.${startPage}-${endPage})`);
                } else if (name.endsWith('.epub')) {
                    showToast('正在解析 EPUB 電子書...');
                    const arrayBuffer = await selectedNovelFile.arrayBuffer();
                    const book = ePub(arrayBuffer);
                    await book.ready;
                    let fullText = '';
                    const spine = book.spine;
                    const maxSections = Math.min(15, spine.length);
                    for (let i = 0; i < maxSections; i++) {
                        const section = spine.get(i);
                        const doc = await section.load(book.load.bind(book));
                        fullText += '\\n\\n' + (doc.body ? doc.body.innerText : '');
                    }
                    loadRawTextIntoNovel(fullText, selectedNovelFile.name);
                } else if (name.endsWith('.docx')) {
                    showToast('正在解析 Word DOCX 文件...');
                    const arrayBuffer = await selectedNovelFile.arrayBuffer();
                    const result = await mammoth.extractRawText({ arrayBuffer });
                    loadRawTextIntoNovel(result.value, selectedNovelFile.name);
                } else {
                    // TXT / MD
                    const text = await selectedNovelFile.text();
                    loadRawTextIntoNovel(text, selectedNovelFile.name);
                }

                closeFilePickerModal();
                showToast('🎉 小說載入成功！已完成全書分頁與文法解析！');
            } catch (err) {
                showToast(`載入失敗：${err.message}`);
            }
        }

        // 將原始字串分頁並進行日文形態素分析與 941 文法配對
        function loadRawTextIntoNovel(rawText, title) {
            window.NovelAudio.stop(false);
            const bookTitleEl = document.getElementById('novelBookTitle');
            const titleTextEl = document.getElementById('novelTitleText');
            if (bookTitleEl) bookTitleEl.textContent = title;
            if (titleTextEl) titleTextEl.textContent = title.slice(0, 18);

            // 分割為頁面 (每頁約 1500~2000 字元，避免瀏覽器卡頓)
            const cleanText = rawText.replace(/\\r\\n/g, '\\n').trim();
            const paragraphs = cleanText.split(/\\n+/).filter(p => p.trim());

            const pages = [];
            let curPageText = '';
            for (let p of paragraphs) {
                if (curPageText.length + p.length > 1600 && curPageText.length > 500) {
                    pages.push(curPageText);
                    curPageText = p;
                } else {
                    curPageText += (curPageText ? '\\n' : '') + p;
                }
            }
            if (curPageText) pages.push(curPageText);
            if (pages.length === 0) pages.push("本文尚無內容。");

            // 對每一頁進行形態素分析與文法提取
            const analyzedPages = pages.map((pageText, pIdx) => {
                const analyzed = analyzeJapaneseText(pageText);
                return {
                    pageNumber: pIdx + 1,
                    text: pageText,
                    sentences: analyzed.sentences
                };
            });

            window.novelState.currentBook = {
                title: title,
                totalPages: analyzedPages.length,
                pages: analyzedPages
            };

            renderNovelPage(0);
        }

        // ==========================================================================
        // 初始載入與預設名著範例
        // ==========================================================================
        const SAMPLE_KOKORO_TEXT = `私はその人を常に先生と呼んでいた。だからここでもただ先生と書くだけで本名は打ち明けない。これは世間を憚かる遠慮というよりも、その方が私にとって自然だからである。私はその人の記憶を呼び起すごとに、すぐ「先生」といいたくなる。筆を執っても心持は同じ事である。よそよそしい頭文字などはとても使う気にならない。
私が先生と知り合いになったのは鎌倉である。その時私はまだ若々しい書生であった。暑中休暇を利用して友達から海へ泳ぎに行こうという端書を受け取ったので、私は多少の金を工面して出掛ける事にした。私は金の工面に二三日を費やした。ところが私が鎌倉に着いて三日と経たないうちに、私を呼び寄せた友達は、急に国元から帰れという電報を受け取った。電報には母が病気だからと断ってあったけれども友達はそれを信じなかった。友達はかねてから国元にある親たちに肯んじない婚姻を強ひられていた。彼は現代の習慣からいうと結婚するにはあまり年が若過ぎた。それに肝心の当人が気に入らなかった。それで夏休みにわざわざ遠くへ逃げて来たのである。彼は電報を見せて私にどうしようと相談した。私にはどうしていいか分らなかった。けれども彼がもし本当に病気なら、帰るべきであると考えた。彼は結局帰る事になった。一人取り残された私は、毎日海岸へ行って泳いだ。
その海岸で、私はふとしたきっかけから先生と出会ったのである。先生は毎日決まった時間に海へ入り、静かに砂浜を歩いて宿へ帰って行った。私はその物静かな風貌に惹かれ、いつしか先生の後を追うようにして言葉を交わすようになった。`;

        document.addEventListener('DOMContentLoaded', () => {
            // 綁定頂部控制列事件
            document.getElementById('btnPlayWholePage').onclick = () => {
                if (window.NovelAudio.status === 'playing') {
                    window.NovelAudio.pause();
                } else if (window.NovelAudio.status === 'paused') {
                    window.NovelAudio.resume();
                } else {
                    window.NovelAudio.playWholePage();
                }
            };

            document.getElementById('btnStopPageAudio').onclick = () => {
                window.NovelAudio.stop();
            };

            document.getElementById('novelVoiceSelect').onchange = (e) => {
                window.novelState.selectedVoice = e.target.value;
                showToast(`已切換聲音為：${e.target.options[e.target.selectedIndex].text}`);
            };

            document.getElementById('novelRepeatCountSelect').onchange = (e) => {
                window.novelState.repeatCount = parseInt(e.target.value, 10);
                showToast(`已設定每句朗讀重複 ${e.target.options[e.target.selectedIndex].text}`);
            };

            // 快捷鍵監聽 (空白鍵播放/暫停，左右方向鍵翻頁)
            window.addEventListener('keydown', (e) => {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
                if (e.code === 'Space') {
                    e.preventDefault();
                    document.getElementById('btnPlayWholePage')?.click();
                } else if (e.code === 'ArrowLeft') {
                    navigateNovelPage(-1);
                } else if (e.code === 'ArrowRight') {
                    navigateNovelPage(1);
                }
            });

            // 關閉浮動卡片監聽
            document.addEventListener('click', (e) => {
                if (!e.target.closest('#wordPopover') && !e.target.closest('.token')) {
                    closeWordPopover();
                }
            });

            // 初始化預設經典小說《心》
            loadRawTextIntoNovel(SAMPLE_KOKORO_TEXT, "夏目漱石《心》(こころ)");
            updateSavedSentencesCountBadge();
            updateNotebookBadges();
        });

        // 輔助跳脫函數
        function escapeHtml(str) {
            if (!str) return '';
            return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }
        function escapeJsString(str) {
            if (!str) return '';
            return String(str).replace(/\\\\/g, '\\\\\\\\').replace(/'/g, "\\\\'").replace(/"/g, '\\\\"').replace(/\\n/g, ' ');
        }
        function copyToClipboard(str) {
            navigator.clipboard.writeText(str).then(() => showToast('已成功複製到剪貼簿！'));
        }
"""

print("[5/5] 組裝完整 HTML 並寫入輸出檔案...")

full_novel_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="referrer" content="no-referrer">
    <title>日語小說沉浸閱讀 - 941文法連動與微軟真人自然朗讀</title>
    {external_css_str}
    <!-- Tesseract OCR 直排/橫排日語辨識 -->
    <script src="https://cdn.jsdelivr.net/npm/tesseract.js@4.1.1/dist/tesseract.min.js"></script>
    <!-- PDF.js 解析 -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script>pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';</script>
    <!-- ePub.js 電子書解析 -->
    <script src="https://cdn.jsdelivr.net/npm/epubjs/dist/epub.min.js"></script>
    <!-- Mammoth.js Word DOCX 解析 -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.6.0/mammoth.browser.min.js"></script>
    <style>
{novel_css}
    </style>
</head>
<body class="novel-body">
{novel_body_html}

    <!-- 1. 核心資料庫 (941條絵でわかる日本語文法庫、JLPT單字、漢字字典、助詞庫) -->
    <script>
{db_script}
    </script>

    <!-- 2. 日語自然語言處理器 (形態素分析、假名標註與文型比對) -->
    <script>
{nlp_script}
    </script>

    <!-- 3. 生詞本與複習核心邏輯 -->
    <script>
{core_ui_script}
    </script>

    <!-- 4. 小說沉浸閱讀器專屬全功能核心控制模組 -->
    <script>
{novel_script}
    </script>
</body>
</html>
"""

# 寫入 novel.html
with open(NOVEL_PATH, "w", encoding="utf-8") as f:
    f.write(full_novel_html)
print(f"[OK] 成功生成小說閱讀器：{NOVEL_PATH} ({os.path.getsize(NOVEL_PATH) / 1024 / 1024:.2f} MB)")

# 寫入 小說閱讀.html
with open(ALIAS_PATH, "w", encoding="utf-8") as f:
    f.write(full_novel_html)
print(f"[OK] 成功生成中文別名：{ALIAS_PATH}")
