# -*- coding: utf-8 -*-
"""
日文閱讀助手 - 單一靜態網頁 (Standalone HTML) 產生器
將所有 CSS、JS 邏輯、8,138 筆 JLPT 單字庫與 941 條《絵でわかる日本語》文法庫
完整封裝至單一 HTML 檔案中，可直接雙擊在瀏覽器開啟，或直接上傳部署至 GitHub Pages！
"""

import os
import json
import re

def build():
    print("[1/4] 載入 941 條文法資料庫...")
    with open("grammar_data.json", "r", encoding="utf-8") as f:
        grammar_data = json.load(f)

    print("[2/4] 載入並壓縮 JLPT 單字庫...")
    with open("jlpt_vocab_all.json", "r", encoding="utf-8") as f:
        raw_vocab = json.load(f)

    # 壓縮為精簡字典: { word: [level, reading] }
    compact_vocab = {}
    for word, entries in raw_vocab.items():
        if entries and isinstance(entries, list):
            lvl = entries[0].get("level", 0)
            reading = entries[0].get("reading", "")
            compact_vocab[word] = [lvl, reading]

    grammar_json_str = json.dumps(grammar_data, ensure_ascii=False, separators=(',', ':'))
    vocab_json_str = json.dumps(compact_vocab, ensure_ascii=False, separators=(',', ':'))

    print("[3/4] 載入樣式表與基礎版型...")
    with open("static/css/style.css", "r", encoding="utf-8") as f:
        css_content = f.read()

    html_template = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>日文閱讀助手 (Japanese Reading Assistant) | 仿句解霸・941條文法聯動</title>
    <!-- Google Fonts & Font Awesome -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700;900&family=Noto+Sans+TC:wght@400;500;600;700;900&family=Noto+Serif+JP:wght@500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
{css_content}
    </style>
</head>
<body data-theme="light">

    <!-- Top Navigation Header -->
    <header class="app-header">
        <div class="header-container">
            <div class="header-brand-wrap">
                <div class="brand-logo">
                    <i class="fa-solid fa-book-open-reader"></i>
                </div>
                <div class="brand-info">
                    <div class="brand-title">
                        <h1>日文閱讀助手</h1>
                        <span class="version-tag">v2.0 網頁獨立版 (GitHub Pages 直用)</span>
                    </div>
                    <p class="brand-subtitle">
                        仿句解霸閱讀拆解・深度聯動 
                        <a href="https://fobeetsai.github.io/japanese-grammar/" target="_blank" rel="noopener noreferrer" class="grammar-link">
                            <i class="fa-solid fa-graduation-cap"></i>《絵でわかる日本語》941條文法庫
                        </a>
                    </p>
                </div>
            </div>

            <!-- Reading Control Toolbar in Header -->
            <div class="header-toolbar">
                <!-- Furigana Mode Switch -->
                <div class="control-pill-group" title="振假名讀音顯示模式">
                    <span class="group-label"><i class="fa-solid fa-font"></i> 假名:</span>
                    <button class="pill-btn active" id="btnRubyShow" data-mode="show" title="顯示漢字上方平假名讀音">顯示</button>
                    <button class="pill-btn" id="btnRubyHide" data-mode="hide" title="完全隱藏假名讀音，訓練漢字直讀">隱藏</button>
                    <button class="pill-btn" id="btnRubyMask" data-mode="mask" title="【遮蔽測驗模式】讀音預設遮蔽，滑鼠懸浮或點擊時揭示">遮蔽自測</button>
                </div>

                <!-- Vocabulary Level Color Switch -->
                <div class="control-pill-group" title="JLPT 單字色彩標註開關">
                    <span class="group-label"><i class="fa-solid fa-palette"></i> 單字:</span>
                    <button class="pill-btn active" id="btnToggleWordColors" title="依 JLPT N1~N5 分顏色標示單字">分級著色</button>
                </div>

                <!-- Grammar Pattern Switch -->
                <div class="control-pill-group" title="941 條文法句型標註開關">
                    <span class="group-label"><i class="fa-solid fa-highlighter"></i> 文型:</span>
                    <button class="pill-btn active" id="btnToggleGrammar" title="高亮標註文章中符合《絵でわかる日本語》之文法">文法標註</button>
                </div>

                <!-- Translation Switch -->
                <div class="control-pill-group" title="中文對照翻譯開關">
                    <span class="group-label"><i class="fa-solid fa-language"></i> 翻譯:</span>
                    <button class="pill-btn active" id="btnToggleTranslation" title="全文顯示逐句繁體中文翻譯對照">逐句對照</button>
                </div>

                <!-- Action Buttons -->
                <div class="header-actions">
                    <button class="action-btn" id="btnOpenNotebook" title="我的生詞與文法筆記本">
                        <i class="fa-solid fa-star text-amber-400"></i>
                        <span>筆記本 (<strong id="notebookCount">0</strong>)</span>
                    </button>
                    <button class="action-btn icon-only" id="btnThemeToggle" title="切換深色/淺色模式">
                        <i class="fa-solid fa-moon" id="themeIcon"></i>
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Workspace Container -->
    <main class="app-main">

        <!-- Input Section (Collapsible) -->
        <section class="input-card" id="inputCard">
            <div class="input-tabs-bar">
                <div class="tab-buttons">
                    <button class="tab-btn active" id="tabPasteBtn" onclick="switchInputTab('paste')">
                        <i class="fa-solid fa-paste"></i> 貼附日文文章
                    </button>
                    <button class="tab-btn" id="tabUrlBtn" onclick="switchInputTab('url')">
                        <i class="fa-solid fa-link"></i> 輸入網址抓取
                    </button>
                </div>

                <div class="sample-chips-wrap">
                    <span class="sample-label"><i class="fa-solid fa-wand-magic-sparkles"></i> 載入精選範例文摘：</span>
                    <div class="sample-buttons" id="sampleButtonsList">
                        <!-- Injected dynamically -->
                    </div>
                </div>
            </div>

            <!-- Tab 1: Paste Text -->
            <div class="tab-panel active" id="panelPaste">
                <div class="textarea-wrap">
                    <textarea id="articleInput" class="article-textarea" rows="6" placeholder="請在此貼上欲閱讀之日文文章、章節、NHK 新聞或小說段落...&#10;點擊下方「開始閱讀與智慧解析」即可全自動生成漢字假名、JLPT 著色、文型標註與繁中對照！"></textarea>
                    <button class="clear-input-btn" id="btnClearInput" title="清空內容">
                        <i class="fa-solid fa-trash-can"></i> 清空
                    </button>
                </div>
            </div>

            <!-- Tab 2: URL Extractor -->
            <div class="tab-panel" id="panelUrl">
                <div class="url-input-wrap">
                    <div class="url-input-box">
                        <i class="fa-solid fa-globe url-icon"></i>
                        <input type="text" id="urlInput" class="url-input" placeholder="請輸入日文新聞或文章網址 (例如：https://www3.nhk.or.jp/news/easy/...)">
                        <button class="btn-fetch-url" id="btnFetchUrl">
                            <i class="fa-solid fa-cloud-arrow-down"></i> 一鍵抓取網頁正文
                        </button>
                    </div>
                    <div class="url-hint">
                        <i class="fa-solid fa-circle-info"></i> 獨立網頁版透過 CORS 代理即時讀取日文網頁正文，並自動過濾導航與廣告。
                    </div>
                </div>
            </div>

            <!-- Input Bottom Actions -->
            <div class="input-actions-bar">
                <div class="input-stats-preview" id="inputCharCount">
                    已輸入 0 字
                </div>
                <div class="action-buttons-wrap">
                    <label class="checkbox-label" title="解析時自動獲取精準繁體中文逐句翻譯">
                        <input type="checkbox" id="chkAutoTranslate" checked>
                        <span>自動生成中文翻譯</span>
                    </label>
                    <button class="btn-primary-action" id="btnStartReading">
                        <i class="fa-solid fa-bolt-lightning"></i> 開始閱讀與智慧解析
                    </button>
                </div>
            </div>
        </section>

        <!-- Loading Overlay -->
        <div class="loading-state" id="loadingState" style="display: none;">
            <div class="spinner"></div>
            <div class="loading-text">
                <h3>正在進行日語形態素分詞、941文型比對與翻譯...</h3>
                <p>純前端極速運算中，請稍候片刻</p>
            </div>
        </div>

        <!-- Reader Workspace (Two-Column Layout: Article Deck & Sentence Inspector) -->
        <section class="reader-deck" id="readerDeck" style="display: none;">

            <!-- Left / Main Column: Article Reading Flow -->
            <div class="article-column">
                
                <!-- Article Meta Header -->
                <div class="article-meta-card">
                    <div class="article-title-wrap">
                        <h2 id="readerArticleTitle">日文文章閱讀</h2>
                        <div class="article-badges" id="articleStatsBadges">
                            <!-- Stats Badges injected dynamically -->
                        </div>
                    </div>

                    <!-- JLPT Level Legend & Color Toggle Filters -->
                    <div class="jlpt-legend-bar">
                        <span class="legend-title"><i class="fa-solid fa-layer-group"></i> 單字分級色彩：</span>
                        <div class="legend-chips">
                            <span class="badge-jlpt badge-n1"><i class="fa-solid fa-circle"></i> N1 高級</span>
                            <span class="badge-jlpt badge-n2"><i class="fa-solid fa-circle"></i> N2 中高</span>
                            <span class="badge-jlpt badge-n3"><i class="fa-solid fa-circle"></i> N3 中級</span>
                            <span class="badge-jlpt badge-n4"><i class="fa-solid fa-circle"></i> N4 初中</span>
                            <span class="badge-jlpt badge-n5"><i class="fa-solid fa-circle"></i> N5 基礎</span>
                            <span class="badge-grammar-legend"><i class="fa-solid fa-bookmark"></i> 941文型</span>
                        </div>

                        <div class="reader-text-tools">
                            <button class="tool-btn" id="btnFontDecr" title="縮小字體"><i class="fa-solid fa-minus"></i> A</button>
                            <button class="tool-btn" id="btnFontIncr" title="放大字體"><i class="fa-solid fa-plus"></i> A</button>
                            <button class="tool-btn" id="btnNewArticle" title="更換文章 / 重新輸入"><i class="fa-solid fa-pen-to-square"></i> 換文章</button>
                        </div>
                    </div>
                </div>

                <!-- Article Content Container -->
                <div class="article-content-box" id="articleContentBox">
                    <!-- Sentences injected dynamically -->
                </div>

            </div>

            <!-- Right Column: Sentence & Grammar Deep Analyzer (句解霸核心功能) -->
            <aside class="analyzer-column">
                <div class="analyzer-sticky-card">
                    
                    <div class="analyzer-header">
                        <div class="analyzer-title">
                            <i class="fa-solid fa-magnifying-glass-chart text-primary"></i>
                            <h3>整句深度分析器</h3>
                        </div>
                        <span class="sentence-index-badge" id="currentSentenceBadge">第 1 句</span>
                    </div>

                    <div class="analyzer-body" id="analyzerBody">
                        
                        <!-- Selected Sentence Display & Audio -->
                        <div class="analyzer-section">
                            <div class="section-label">
                                <span><i class="fa-solid fa-quote-left"></i> 本句原文 (附假名)</span>
                                <button class="btn-audio" id="btnPlaySentenceAudio" title="朗讀本句 (高品質日語發音)">
                                    <i class="fa-solid fa-volume-high"></i> 播放發音
                                </button>
                            </div>
                            <div class="selected-sentence-text" id="selectedSentenceJp">
                                點擊左側文章中任意句子，此處將即時展開整句結構、單字詞性與 941 文法精解！
                            </div>
                        </div>

                        <!-- Sentence Translation -->
                        <div class="analyzer-section">
                            <div class="section-label">
                                <span><i class="fa-solid fa-language"></i> 繁體中文翻譯</span>
                            </div>
                            <div class="selected-sentence-trans" id="selectedSentenceZh">
                                暫無翻譯
                            </div>
                        </div>

                        <!-- Matched Grammars in this sentence -->
                        <div class="analyzer-section">
                            <div class="section-label">
                                <span><i class="fa-solid fa-book-bookmark text-primary"></i> 命中《絵でわかる日本語》文法句型 (<strong id="sentenceGrammarCount">0</strong>)</span>
                            </div>
                            <div class="matched-grammars-list" id="sentenceGrammarsList">
                                <div class="empty-hint">本句未偵測到特殊 941 文法句型</div>
                            </div>
                        </div>

                        <!-- Word Token Breakdown in this sentence -->
                        <div class="analyzer-section">
                            <div class="section-label">
                                <span><i class="fa-solid fa-table-list"></i> 本句單字與詞性拆解 (<strong id="sentenceWordCount">0</strong>)</span>
                            </div>
                            <div class="words-table-wrap">
                                <table class="words-breakdown-table">
                                    <thead>
                                        <tr>
                                            <th style="min-width:75px;">單字 (辭書形)</th>
                                            <th style="min-width:65px;">讀音</th>
                                            <th style="min-width:85px;">文型／詞性</th>
                                            <th style="min-width:55px;">級數</th>
                                            <th style="min-width:90px;">中文翻譯</th>
                                            <th style="text-align:center;width:40px;">收藏</th>
                                        </tr>
                                    </thead>
                                    <tbody id="sentenceWordsTbody">
                                        <!-- Injected dynamically -->
                                    </tbody>
                                </table>
                            </div>
                        </div>

                    </div>

                    <!-- Sentence Navigation Buttons -->
                    <div class="analyzer-footer">
                        <button class="btn-nav" id="btnPrevSentence" title="上一句 (快捷鍵 ←)">
                            <i class="fa-solid fa-chevron-left"></i> 上一句
                        </button>
                        <button class="btn-nav" id="btnNextSentence" title="下一句 (快捷鍵 →)">
                            下一句 <i class="fa-solid fa-chevron-right"></i>
                        </button>
                    </div>

                </div>
            </aside>

        </section>

    </main>

    <!-- Floating Word Dictionary Popover (點擊單字浮出) -->
    <div class="word-popover" id="wordPopover" style="display: none;">
        <button class="popover-close-btn" onclick="closeWordPopover()"><i class="fa-solid fa-xmark"></i></button>
        <div class="popover-header">
            <div class="popover-word-title" id="popoverWordSurface">単語</div>
            <span class="badge-jlpt" id="popoverWordLevel">N5</span>
        </div>
        <div class="popover-reading-row">
            <span class="popover-kana" id="popoverWordKana">たんご</span>
            <button class="btn-audio-mini" id="btnPlayWordAudio" title="發音"><i class="fa-solid fa-volume-high"></i></button>
            <span class="popover-pos" id="popoverWordPos">名詞</span>
        </div>
        <div class="popover-meaning-box" id="popoverWordMeaning">
            <div class="meaning-spinner"><i class="fa-solid fa-spinner fa-spin"></i> 正在查詢中文釋義...</div>
        </div>
        <div class="popover-footer">
            <button class="btn-popover-action" id="btnAddWordToNotebook">
                <i class="fa-regular fa-star"></i> 存入生詞本
            </button>
        </div>
    </div>

    <!-- Grammar Detail Drawer Modal (點擊文法卡片開啟完整精解) -->
    <div class="drawer-overlay" id="grammarDrawerOverlay">
        <div class="drawer-container">
            <div class="drawer-header">
                <div class="drawer-header-left">
                    <span class="badge-jlpt" id="drawerGrammarLevel">N2</span>
                    <h3 id="drawerGrammarTitle">文法名稱</h3>
                </div>
                <div class="drawer-header-actions">
                    <button class="btn-drawer-action" id="btnDrawerFav" title="收藏此文法"><i class="fa-regular fa-star"></i></button>
                    <a id="drawerGrammarExternalLink" href="#" target="_blank" class="btn-drawer-action" title="前往原站專題查看"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>
                    <button class="btn-drawer-action" onclick="closeGrammarDrawer()"><i class="fa-solid fa-xmark"></i></button>
                </div>
            </div>
            <div class="drawer-body" id="drawerGrammarBody">
                <!-- Dynamically injected grammar details -->
            </div>
        </div>
    </div>

    <!-- Notebook / Favorites Modal (生詞本與文法筆記) -->
    <div class="modal-overlay" id="notebookModal">
        <div class="modal-container">
            <div class="modal-header">
                <h3><i class="fa-solid fa-bookmark text-amber-400"></i> 我的日語學習筆記本</h3>
                <button class="modal-close-btn" onclick="closeNotebookModal()"><i class="fa-solid fa-xmark"></i></button>
            </div>
            
            <div class="notebook-tabs">
                <button class="notebook-tab-btn active" id="tabNotebookWordsBtn" onclick="switchNotebookTab('words')">
                    收藏單字 (<span id="nbWordCount">0</span>)
                </button>
                <button class="notebook-tab-btn" id="tabNotebookGrammarsBtn" onclick="switchNotebookTab('grammars')">
                    收藏文型 (<span id="nbGrammarCount">0</span>)
                </button>
            </div>

            <div class="notebook-list-area" id="notebookListArea">
                <!-- Injected dynamically -->
            </div>

            <div class="modal-footer">
                <button class="btn-secondary" id="btnExportNotebook">
                    <i class="fa-solid fa-download"></i> 匯出學習筆記 (.txt)
                </button>
                <button class="btn-danger-outline" id="btnClearNotebook">
                    <i class="fa-solid fa-trash-can"></i> 清空全部
                </button>
            </div>
        </div>
    </div>

    <!-- Toast Notification -->
    <div class="toast" id="toast">
        <i class="fa-solid fa-circle-check text-green-400"></i>
        <span id="toastMsg">通知訊息</span>
    </div>

    <!-- ==========================================================================
         內建 941 條文法資料庫與 JLPT 單字庫
         ========================================================================== -->
    <script>
        // 941 條《絵でわかる日本語》文法庫
        const GRAMMAR_DATA = {grammar_json_str};

        // 8,138 筆 JLPT 單字精簡庫：{{ word: [level_number, reading_hiragana] }}
        const JLPT_VOCAB = {vocab_json_str};

        // 精選範例文摘
        const SAMPLE_ARTICLES = [
            {{
                "id": "nhk_ai_news",
                "title": "【時事科技】AI技術の進化と私たちの生活 (NHK 風格新聞)",
                "level": "N3 ~ N2",
                "content": "日本では、AI（人工知能）を使った新しいサービスが次々と始まっています。\\n病院では、医師が診察する時にAIを使って、病気を見つける手助けをしています。\\nまた、外国人の観光客が増えているため、ホテルや駅では自動で翻訳するロボットが活躍しています。\\n専門家は「これからは生活のあらゆる場面でAIが使われる一方、正しい情報をどう見分けるかが大切になる」と話しています。\\n新しい技術を恐れることなく、上手に付き合っていくことが求められています。"
            }},
            {{
                "id": "jlpt_n2_essay",
                "title": "【JLPT N2/N1 讀解】便利さと心の豊かさ（多項文法精選論說文）",
                "level": "N2 ~ N1",
                "content": "科学技術の急速な発展に伴い、私たちの生活は便利になる一方である。\\nしかし、いくら生活が便利になったからといっても、人間の心が豊かになったとは言えないのではないだろうか。\\n現代人は利便性を追求するあまり、自然との触れ合いや人との絆を忘れがちである。\\n１時間悩んだあげく、余計な物を買ってしまう消費者心理も問題視されている。\\n豊かな社会を築くためには、物質的な豊かさのみならず、心のゆとりを大切にする姿勢こそが欠かせないものにほかならない。"
            }},
            {{
                "id": "momotaro_story",
                "title": "【經典故事】桃太郎（基礎讀物與初中階文型）",
                "level": "N5 ~ N3",
                "content": "むかしむかし、ある所に、おじいさんとおばあさんが住んでいました。\\nおじいさんは山へ柴刈りに、おばあさんは川へ洗濯に行きました。\\nおばあさんが川で洗濯をしていると、川上から大きな桃が、どんぶらこ、どんぶらこと流れてきました。\\n「おや、これは大きな桃だこと。家に持って帰って、おじいさんと一緒に食べよう」とおばあさんは桃を拾い上げて、家に持ち帰りました。\\n夕方、おじいさんが山から帰ってきて、桃を割ってみると、中から元気な男の子が生まれました。\\n二人は大喜びで、男の子に「桃太郎」と名付けました。"
            }}
        ];
    </script>

    <!-- ==========================================================================
         純前端分詞、振假名生成、941文型匹配與 Google 翻譯引擎
         ========================================================================== -->
    <script>
        // 假名字元區間
        const KANJI_REGEX = /[\\u4e00-\\u9faf]/;
        const KANA_REGEX = /[\\u3040-\\u309f\\u30a0-\\u30ff]/;
        const PUNCT_REGEX = /[。！？!?\\n]/;

        // 片假名轉平假名
        function kataToHira(str) {{
            if (!str) return '';
            return str.replace(/[\\u30a1-\\u30f6]/g, c => String.fromCharCode(c.charCodeAt(0) - 0x60));
        }}

        // 產生標準 Ruby 振假名標籤
        function createRubyHtml(surface, readingHira) {{
            if (!readingHira || !KANJI_REGEX.test(surface)) return surface;
            
            // 全漢字情況
            if (/^[\\u4e00-\\u9faf]+$/.test(surface)) {{
                return `<ruby>${{surface}}<rt>${{readingHira}}</rt></ruby>`;
            }}

            // 尋找共同送假名後綴
            let sLen = 0;
            while (sLen < surface.length && sLen < readingHira.length &&
                   surface[surface.length - 1 - sLen] === readingHira[readingHira.length - 1 - sLen]) {{
                sLen++;
            }}

            // 尋找前綴假名
            let pLen = 0;
            while (pLen < (surface.length - sLen) && pLen < (readingHira.length - sLen) &&
                   surface[pLen] === readingHira[pLen]) {{
                pLen++;
            }}

            const prefix = surface.substring(0, pLen);
            const kanji = surface.substring(pLen, surface.length - sLen);
            const suffix = sLen > 0 ? surface.substring(surface.length - sLen) : '';
            const rKanji = readingHira.substring(pLen, readingHira.length - sLen);

            if (kanji && rKanji) {{
                return `${{prefix}}<ruby>${{kanji}}<rt>${{rKanji}}</rt></ruby>${{suffix}}`;
            }}
            return `<ruby>${{surface}}<rt>${{readingHira}}</rt></ruby>`;
        }}

        // 編譯 941 條文法搜尋索引
        let COMPILED_GRAMMAR_PATTERNS = [];
        function initGrammarPatterns() {{
            COMPILED_GRAMMAR_PATTERNS = [];
            GRAMMAR_DATA.forEach(g => {{
                const raw = (g.title || '').trim();
                const key = raw.replace(/^[〜~・\\s]+/, '');
                const subTitles = key.split(/[・／/]/);

                const variants = [];
                subTitles.forEach(sub => {{
                    const cleaned = sub.replace(/[①②③④⑤⑥⑦⑧⑨⑩]/g, '');
                    const mOpt = cleaned.match(/（([にはでとがをも]+)）|\\(([にはでとがをも]+)\\)/);
                    if (mOpt) {{
                        const pt = mOpt[1] || mOpt[2];
                        const base = cleaned.replace(/（[^\\)にはでとがをも]+）|\\([^\\)にはでとがをも]+\\)/g, '');
                        variants.push(base.replace(/（[にはでとがをも]+）|\\([にはでとがをも]+\\)/g, pt));
                        variants.push(base.replace(/（[にはでとがをも]+）|\\([にはでとがをも]+\\)/g, ''));
                    }} else {{
                        variants.push(cleaned.replace(/（.*?）|\\(.*?\\)/g, ''));
                    }}
                }});

                variants.forEach(cand => {{
                    let c = cand.replace(/^[〜~・\\s]+/, '').replace(/[〜~・\\s]+$/, '');
                    c = c.replace(/[の\\s]*[NAV]$/, '').trim();
                    if (c.length >= 2) {{
                        COMPILED_GRAMMAR_PATTERNS.push({{
                            pattern: c,
                            data: g
                        }});
                    }}
                }});
            }});

            // 優先長詞匹配 (Longest Match First)
            COMPILED_GRAMMAR_PATTERNS.sort((a, b) => b.pattern.length - a.pattern.length);
        }}

        // 句子中搜尋 941 文法
        function findSentenceGrammars(sentenceText) {{
            const found = [];
            const matchedSpans = [];

            for (let i = 0; i < COMPILED_GRAMMAR_PATTERNS.length; i++) {{
                const pInfo = COMPILED_GRAMMAR_PATTERNS[i];
                const pat = pInfo.pattern;
                const g = pInfo.data;

                let startIdx = 0;
                while (true) {{
                    const pos = sentenceText.indexOf(pat, startIdx);
                    if (pos === -1) break;
                    const endPos = pos + pat.length;

                    // 避免「ちゃ」誤判於「ちゃんと」中
                    if ((pat === 'ちゃ' || pat === 'じゃ') && endPos < sentenceText.length &&
                        (sentenceText[endPos] === 'ん' || sentenceText[endPos] === 'ン')) {{
                        startIdx = pos + 1;
                        continue;
                    }}

                    // 避免重疊
                    const isOverlap = matchedSpans.some(([s, e]) => s <= pos && endPos <= e);
                    if (!isOverlap) {{
                        matchedSpans.push([pos, endPos]);
                        found.push({{
                            id: g.id,
                            title: g.title,
                            clean_title: g.clean_title,
                            level: g.level,
                            category: g.category,
                            form: g.form,
                            meaningZh: g.meaningZh,
                            meaningJa: g.meaningJa,
                            example: g.example,
                            exampleRuby: g.exampleRuby,
                            translation: g.translation,
                            note: g.note,
                            sourceUrl: g.sourceUrl,
                            matched_text: pat,
                            start: pos,
                            end: endPos
                        }});
                    }}
                    startIdx = pos + 1;
                }}
            }}

            found.sort((a, b) => a.start - b.start);
            return found;
        }}

        // 純前端日語最大正向分詞 (Max-Match Tokenizer against JLPT_VOCAB)
        function tokenizeSentence(text) {{
            const tokens = [];
            let i = 0;
            const MAX_WORD_LEN = 10;

            while (i < text.length) {{
                let matched = false;

                // 嘗試由長至短在 JLPT_VOCAB 中比對
                const limit = Math.min(MAX_WORD_LEN, text.length - i);
                for (let len = limit; len >= 2; len--) {{
                    const sub = text.substring(i, i + len);
                    if (JLPT_VOCAB[sub]) {{
                        const [lvlNum, reading] = JLPT_VOCAB[sub];
                        const readingHira = kataToHira(reading);
                        const hasKanji = KANJI_REGEX.test(sub);
                        tokens.push({{
                            surface: sub,
                            base_form: sub,
                            reading: readingHira,
                            jlpt: lvlNum ? `N${{lvlNum}}` : null,
                            is_kanji: hasKanji,
                            ruby_html: hasKanji ? createRubyHtml(sub, readingHira) : sub,
                            pos: '單字'
                        }});
                        i += len;
                        matched = true;
                        break;
                    }}
                }}

                if (matched) continue;

                // 若未在單字庫匹配，判斷字元類型區塊
                const char = text[i];

                // 漢字區塊
                if (KANJI_REGEX.test(char)) {{
                    let kanjiRun = char;
                    let j = i + 1;
                    while (j < text.length && KANJI_REGEX.test(text[j])) {{
                        kanjiRun += text[j];
                        j++;
                    }}
                    // 查核全詞
                    const vocabEntry = JLPT_VOCAB[kanjiRun];
                    const lvl = vocabEntry ? `N${{vocabEntry[0]}}` : null;
                    const rHira = vocabEntry ? kataToHira(vocabEntry[1]) : '';
                    tokens.push({{
                        surface: kanjiRun,
                        base_form: kanjiRun,
                        reading: rHira,
                        jlpt: lvl,
                        is_kanji: true,
                        ruby_html: rHira ? createRubyHtml(kanjiRun, rHira) : kanjiRun,
                        pos: '漢字詞'
                    }});
                    i = j;
                    continue;
                }}

                // 片假名外來語區塊
                if (/[\\u30a0-\\u30ff]/.test(char)) {{
                    let kataRun = char;
                    let j = i + 1;
                    while (j < text.length && /[\\u30a0-\\u30ffー]/.test(text[j])) {{
                        kataRun += text[j];
                        j++;
                    }}
                    tokens.push({{
                        surface: kataRun,
                        base_form: kataRun,
                        reading: kataToHira(kataRun),
                        jlpt: JLPT_VOCAB[kataRun] ? `N${{JLPT_VOCAB[kataRun][0]}}` : null,
                        is_kanji: false,
                        ruby_html: kataRun,
                        pos: '外來語'
                    }});
                    i = j;
                    continue;
                }}

                // 標點符號或單個平假名/英數
                tokens.push({{
                    surface: char,
                    base_form: char,
                    reading: char,
                    jlpt: null,
                    is_kanji: false,
                    ruby_html: char,
                    pos: '符號/助詞'
                }});
                i++;
            }}

            return tokens;
        }}

        // 線上 Google Translate 免費端點 (具備即時 CORS 支援)
        const TRANSLATE_CACHE = new Map();
        async function translateJaToZh(text) {{
            const trimmed = text.trim();
            if (!trimmed) return '';
            if (TRANSLATE_CACHE.has(trimmed)) return TRANSLATE_CACHE.get(trimmed);

            try {{
                const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=ja&tl=zh-TW&dt=t&q=${{encodeURIComponent(trimmed)}}`;
                const res = await fetch(url);
                if (!res.ok) throw new Error('API Error');
                const data = await res.json();
                let trans = '';
                if (data && data[0]) {{
                    trans = data[0].map(item => item[0]).filter(Boolean).join('');
                }}
                TRANSLATE_CACHE.set(trimmed, trans);
                return trans;
            }} catch (e) {{
                console.warn('翻譯連線超時或受阻:', e);
                return '';
            }}
        }}

        // 分句器
        function splitArticleSentences(text) {{
            const lines = text.split(/\\r?\\n/);
            const sentences = [];
            lines.forEach(line => {{
                const trimmed = line.trim();
                if (!trimmed) return;
                const parts = trimmed.split(/([。！？!?]+)/);
                for (let i = 0; i < parts.length; i += 2) {{
                    const s = parts[i] || '';
                    const p = parts[i + 1] || '';
                    const combined = (s + p).trim();
                    if (combined) sentences.push(combined);
                }}
            }});
            return sentences;
        }}

        // 全篇綜合解析
        async function clientAnalyzeText(text, autoTranslate = true) {{
            const sentencesRaw = splitArticleSentences(text);
            const analyzedSentences = [];
            const jlptCounts = {{ N1: 0, N2: 0, N3: 0, N4: 0, N5: 0, Other: 0 }};
            let totalWords = 0;
            const matchedGrammarSet = new Set();

            for (let sIdx = 0; sIdx < sentencesRaw.length; sIdx++) {{
                const sText = sentencesRaw[sIdx];
                const words = tokenizeSentence(sText);
                const grammars = findSentenceGrammars(sText);

                words.forEach(w => {{
                    if (w.jlpt && jlptCounts[w.jlpt] !== undefined) {{
                        jlptCounts[w.jlpt]++;
                    }} else if (w.is_kanji || w.pos === '外來語') {{
                        jlptCounts.Other++;
                    }}
                    totalWords++;
                }});

                grammars.forEach(g => matchedGrammarSet.add(g.id));

                let translation = '';
                if (autoTranslate) {{
                    translation = await translateJaToZh(sText);
                }}

                analyzedSentences.push({{
                    sentence_id: sIdx,
                    text: sText,
                    words: words,
                    grammars: grammars,
                    translation: translation
                }});
            }}

            return {{
                sentences: analyzedSentences,
                stats: {{
                    sentence_count: analyzedSentences.length,
                    word_count: totalWords,
                    grammar_count: matchedGrammarSet.size,
                    jlpt_distribution: jlptCounts
                }}
            }};
        }}
    </script>

    <!-- ==========================================================================
         前端互動與介面控制器
         ========================================================================== -->
    <script>
        // 全域狀態
        const state = {{
            analyzedData: null,
            currentSentenceIdx: 0,
            rubyMode: 'show',
            enableWordColors: true,
            enableGrammar: true,
            enableTranslation: true,
            fontSizeLevel: 0,
            theme: 'light',
            notebook: {{ words: [], grammars: [] }}
        }};

        // DOM 元素快取
        const dom = {{
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

            readerDeck: document.getElementById('readerDeck'),
            readerArticleTitle: document.getElementById('readerArticleTitle'),
            articleStatsBadges: document.getElementById('articleStatsBadges'),
            articleContentBox: document.getElementById('articleContentBox'),
            btnFontDecr: document.getElementById('btnFontDecr'),
            btnFontIncr: document.getElementById('btnFontIncr'),
            btnNewArticle: document.getElementById('btnNewArticle'),

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

            wordPopover: document.getElementById('wordPopover'),
            popoverWordSurface: document.getElementById('popoverWordSurface'),
            popoverWordLevel: document.getElementById('popoverWordLevel'),
            popoverWordKana: document.getElementById('popoverWordKana'),
            popoverWordPos: document.getElementById('popoverWordPos'),
            popoverWordMeaning: document.getElementById('popoverWordMeaning'),
            btnPlayWordAudio: document.getElementById('btnPlayWordAudio'),
            btnAddWordToNotebook: document.getElementById('btnAddWordToNotebook'),

            grammarDrawerOverlay: document.getElementById('grammarDrawerOverlay'),
            drawerGrammarLevel: document.getElementById('drawerGrammarLevel'),
            drawerGrammarTitle: document.getElementById('drawerGrammarTitle'),
            drawerGrammarExternalLink: document.getElementById('drawerGrammarExternalLink'),
            btnDrawerFav: document.getElementById('btnDrawerFav'),
            drawerGrammarBody: document.getElementById('drawerGrammarBody'),

            notebookModal: document.getElementById('notebookModal'),
            nbWordCount: document.getElementById('nbWordCount'),
            nbGrammarCount: document.getElementById('nbGrammarCount'),
            tabNotebookWordsBtn: document.getElementById('tabNotebookWordsBtn'),
            tabNotebookGrammarsBtn: document.getElementById('tabNotebookGrammarsBtn'),
            notebookListArea: document.getElementById('notebookListArea'),
            btnExportNotebook: document.getElementById('btnExportNotebook'),
            btnClearNotebook: document.getElementById('btnClearNotebook'),

            toast: document.getElementById('toast'),
            toastMsg: document.getElementById('toastMsg')
        }};

        document.addEventListener('DOMContentLoaded', () => {{
            initGrammarPatterns();
            loadSavedSettings();
            loadNotebook();
            setupEventListeners();
            renderSampleButtons();
        }});

        function loadSavedSettings() {{
            const savedRuby = localStorage.getItem('japanese_reader_ruby_mode') || 'show';
            setRubyMode(savedRuby);
            const savedTheme = localStorage.getItem('japanese_reader_theme') || 'light';
            setTheme(savedTheme);
            const savedWordColors = localStorage.getItem('japanese_reader_word_colors') !== 'false';
            setWordColors(savedWordColors);
            const savedGrammar = localStorage.getItem('japanese_reader_grammar') !== 'false';
            setGrammarHighlight(savedGrammar);
            const savedTrans = localStorage.getItem('japanese_reader_trans') !== 'false';
            setTranslationDisplay(savedTrans);
        }}

        function setupEventListeners() {{
            dom.btnRubyShow.addEventListener('click', () => setRubyMode('show'));
            dom.btnRubyHide.addEventListener('click', () => setRubyMode('hide'));
            dom.btnRubyMask.addEventListener('click', () => setRubyMode('mask'));

            dom.btnToggleWordColors.addEventListener('click', () => setWordColors(!state.enableWordColors));
            dom.btnToggleGrammar.addEventListener('click', () => setGrammarHighlight(!state.enableGrammar));
            dom.btnToggleTranslation.addEventListener('click', () => setTranslationDisplay(!state.enableTranslation));
            dom.btnThemeToggle.addEventListener('click', () => setTheme(state.theme === 'light' ? 'dark' : 'light'));

            dom.articleInput.addEventListener('input', () => {{
                dom.inputCharCount.textContent = `已輸入 ${{dom.articleInput.value.length}} 字`;
            }});

            dom.btnClearInput.addEventListener('click', () => {{
                dom.articleInput.value = '';
                dom.inputCharCount.textContent = '已輸入 0 字';
                dom.articleInput.focus();
            }});

            dom.btnFetchUrl.addEventListener('click', handleFetchUrlClient);
            dom.btnStartReading.addEventListener('click', handleStartReadingClient);

            dom.btnFontIncr.addEventListener('click', () => changeFontSize(1));
            dom.btnFontDecr.addEventListener('click', () => changeFontSize(-1));

            dom.btnNewArticle.addEventListener('click', () => {{
                dom.inputCard.style.display = 'flex';
                dom.inputCard.scrollIntoView({{ behavior: 'smooth' }});
            }});

            dom.btnPrevSentence.addEventListener('click', () => navigateSentence(-1));
            dom.btnNextSentence.addEventListener('click', () => navigateSentence(1));

            document.addEventListener('keydown', (e) => {{
                if (state.analyzedData && dom.readerDeck.style.display !== 'none') {{
                    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
                    if (e.key === 'ArrowLeft') navigateSentence(-1);
                    if (e.key === 'ArrowRight') navigateSentence(1);
                    if (e.key === 'Escape') {{
                        closeWordPopover();
                        closeGrammarDrawer();
                        closeNotebookModal();
                    }}
                }}
            }});

            dom.btnPlaySentenceAudio.addEventListener('click', () => {{
                if (!state.analyzedData) return;
                const s = state.analyzedData.sentences[state.currentSentenceIdx];
                if (s) speakJapanese(s.text);
            }});

            dom.btnPlayWordAudio.addEventListener('click', () => {{
                const text = dom.popoverWordSurface.textContent;
                if (text) speakJapanese(text);
            }});

            dom.btnOpenNotebook.addEventListener('click', openNotebookModal);
            dom.btnExportNotebook.addEventListener('click', exportNotebook);
            dom.btnClearNotebook.addEventListener('click', clearNotebook);

            document.addEventListener('click', (e) => {{
                if (dom.wordPopover.style.display !== 'none' &&
                    !dom.wordPopover.contains(e.target) &&
                    !e.target.closest('.word-token')) {{
                    closeWordPopover();
                }}
            }});
        }}

        function setRubyMode(mode) {{
            state.rubyMode = mode;
            localStorage.setItem('japanese_reader_ruby_mode', mode);
            document.body.setAttribute('data-ruby-mode', mode);
            dom.btnRubyShow.classList.toggle('active', mode === 'show');
            dom.btnRubyHide.classList.toggle('active', mode === 'hide');
            dom.btnRubyMask.classList.toggle('active', mode === 'mask');
            if (mode === 'mask') showToast('已開啟【遮蔽自測模式】：假名已遮蔽，滑鼠移過或點擊即可揭示讀音！');
        }}

        function setWordColors(enable) {{
            state.enableWordColors = enable;
            localStorage.setItem('japanese_reader_word_colors', enable);
            document.body.classList.toggle('enable-word-colors', enable);
            dom.btnToggleWordColors.classList.toggle('active', enable);
        }}

        function setGrammarHighlight(enable) {{
            state.enableGrammar = enable;
            localStorage.setItem('japanese_reader_grammar', enable);
            document.body.classList.toggle('enable-grammar', enable);
            dom.btnToggleGrammar.classList.toggle('active', enable);
        }}

        function setTranslationDisplay(enable) {{
            state.enableTranslation = enable;
            localStorage.setItem('japanese_reader_trans', enable);
            document.body.classList.toggle('enable-translation', enable);
            dom.btnToggleTranslation.classList.toggle('active', enable);
        }}

        function setTheme(theme) {{
            state.theme = theme;
            localStorage.setItem('japanese_reader_theme', theme);
            document.body.setAttribute('data-theme', theme);
            dom.themeIcon.className = theme === 'dark' ? 'fa-solid fa-sun text-yellow-300' : 'fa-solid fa-moon';
        }}

        function changeFontSize(delta) {{
            state.fontSizeLevel = Math.max(-2, Math.min(4, state.fontSizeLevel + delta));
            const sizes = ['1.05rem', '1.15rem', '1.28rem', '1.45rem', '1.65rem', '1.85rem', '2.05rem'];
            document.documentElement.style.setProperty('--reader-font-size', sizes[state.fontSizeLevel + 2]);
        }}

        function switchInputTab(tab) {{
            dom.tabPasteBtn.classList.toggle('active', tab === 'paste');
            dom.tabUrlBtn.classList.toggle('active', tab === 'url');
            dom.panelPaste.classList.toggle('active', tab === 'paste');
            dom.panelUrl.classList.toggle('active', tab === 'url');
        }}

        function renderSampleButtons() {{
            dom.sampleButtonsList.innerHTML = '';
            SAMPLE_ARTICLES.forEach(a => {{
                const btn = document.createElement('button');
                btn.className = 'sample-btn';
                btn.innerHTML = `<i class="fa-solid fa-file-lines"></i> ${{a.title.split('】')[0]}}】`;
                btn.onclick = () => {{
                    switchInputTab('paste');
                    dom.articleInput.value = a.content;
                    dom.inputCharCount.textContent = `已輸入 ${{a.content.length}} 字`;
                    showToast(`已載入「${{a.title}}」`);
                }};
                dom.sampleButtonsList.appendChild(btn);
            }});
        }}

        // 純前端網址正文抓取（透過 CORS Proxy）
        async function handleFetchUrlClient() {{
            let url = dom.urlInput.value.trim();
            if (!url) {{
                showToast('請輸入有效的日文網址');
                dom.urlInput.focus();
                return;
            }}
            if (!url.startsWith('http://') && !url.startsWith('https://')) {{
                url = 'https://' + url;
            }}

            dom.btnFetchUrl.disabled = true;
            dom.btnFetchUrl.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 正在抓取正文...';

            try {{
                // 優先使用代理服務
                const proxyUrl = `https://api.allorigins.win/raw?url=${{encodeURIComponent(url)}}`;
                const res = await fetch(proxyUrl);
                if (!res.ok) throw new Error('連線失敗');
                const html = await res.text();

                // 使用 DOMParser 萃取純文字
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');

                // 移除干擾元素
                doc.querySelectorAll('script, style, nav, header, footer, aside, noscript, iframe').forEach(el => el.remove());

                const title = doc.title || '網頁文章';
                let text = '';
                const mainEl = doc.querySelector('article, main, .article-body, #content, .content, body');
                if (mainEl) {{
                    const pList = Array.from(mainEl.querySelectorAll('p, h1, h2, h3, li'))
                        .map(p => p.textContent.trim())
                        .filter(t => t.length > 8);
                    text = pList.join('\\n\\n');
                }}

                if (!text) {{
                    text = doc.body.innerText.split('\\n').map(l => l.trim()).filter(l => l.length > 8).join('\\n\\n');
                }}

                switchInputTab('paste');
                dom.articleInput.value = text;
                dom.inputCharCount.textContent = `已輸入 ${{text.length}} 字`;
                dom.readerArticleTitle.textContent = title;
                showToast(`已抓取「${{title}}」！`);
            }} catch (err) {{
                showToast(`網址抓取受限，請直接複製網頁文字並貼上閱讀`);
            }} finally {{
                dom.btnFetchUrl.disabled = false;
                dom.btnFetchUrl.innerHTML = '<i class="fa-solid fa-cloud-arrow-down"></i> 一鍵抓取網頁正文';
            }}
        }}

        // 開始閱讀與智慧解析
        async function handleStartReadingClient() {{
            const text = dom.articleInput.value.trim();
            if (!text) {{
                showToast('請先貼上日文文章！');
                dom.articleInput.focus();
                return;
            }}

            dom.loadingState.style.display = 'flex';
            dom.readerDeck.style.display = 'none';

            try {{
                // 執行純前端解析器
                const res = await clientAnalyzeText(text, dom.chkAutoTranslate.checked);
                state.analyzedData = res;
                state.currentSentenceIdx = 0;

                renderReaderView();
                showToast('文章解析完成！');
                dom.readerDeck.scrollIntoView({{ behavior: 'smooth' }});
            }} catch (err) {{
                showToast(`解析出錯: ${{err.message}}`);
            }} finally {{
                dom.loadingState.style.display = 'none';
            }}
        }}

        function renderReaderView() {{
            const data = state.analyzedData;
            if (!data) return;

            dom.readerDeck.style.display = 'grid';
            const stats = data.stats;
            dom.articleStatsBadges.innerHTML = `
                <span class="meta-chip"><i class="fa-solid fa-paragraph"></i> 句子：<strong>${{stats.sentence_count}}</strong></span>
                <span class="meta-chip"><i class="fa-solid fa-spell-check"></i> 詞彙：<strong>${{stats.word_count}}</strong></span>
                <span class="meta-chip"><i class="fa-solid fa-book-bookmark"></i> 命中941文型：<strong>${{stats.grammar_count}}</strong> 條</span>
            `;

            dom.articleContentBox.innerHTML = '';

            data.sentences.forEach((s, sIdx) => {{
                const row = document.createElement('div');
                row.className = `sentence-row ${{sIdx === 0 ? 'active' : ''}}`;
                row.dataset.sentenceIdx = sIdx;
                row.addEventListener('click', () => selectSentence(sIdx));

                const jpWrap = document.createElement('div');
                jpWrap.className = 'sentence-jp-text';
                renderSentenceTokens(jpWrap, s, sIdx);
                row.appendChild(jpWrap);

                if (s.translation) {{
                    const transRow = document.createElement('div');
                    transRow.className = 'sentence-trans-row';
                    transRow.innerHTML = `
                        <span class="trans-tag">繁中</span>
                        <span class="trans-text">${{s.translation}}</span>
                    `;
                    row.appendChild(transRow);
                }}

                dom.articleContentBox.appendChild(row);
            }});

            selectSentence(0);
        }}

        function renderSentenceTokens(container, sentence, sIdx) {{
            const words = sentence.words;
            const grammars = sentence.grammars || [];

            let charOffset = 0;
            const wordOffsets = [];
            words.forEach(w => {{
                const start = charOffset;
                const end = start + w.surface.length;
                wordOffsets.push({{ start, end, word: w }});
                charOffset = end;
            }});

            words.forEach((w, wIdx) => {{
                const tokenSpan = document.createElement('span');
                tokenSpan.className = `word-token ${{w.jlpt ? `jlpt-${{w.jlpt}}` : ''}}`;
                tokenSpan.innerHTML = w.ruby_html;
                tokenSpan.dataset.surface = w.surface;
                tokenSpan.dataset.baseForm = w.base_form;
                tokenSpan.dataset.reading = w.reading;
                tokenSpan.dataset.pos = w.pos;
                tokenSpan.dataset.jlpt = w.jlpt || '';
                tokenSpan.dataset.sentenceIdx = sIdx;
                tokenSpan.dataset.wordIdx = wIdx;

                tokenSpan.addEventListener('click', (e) => {{
                    e.stopPropagation();
                    if (state.rubyMode === 'mask') {{
                        tokenSpan.classList.toggle('revealed');
                    }}
                    showWordPopover(tokenSpan, w, e);
                }});

                const curOffset = wordOffsets[wIdx];
                const matchedGrammar = grammars.find(g => 
                    (curOffset.start >= g.start && curOffset.start < g.end) ||
                    (curOffset.end > g.start && curOffset.end <= g.end)
                );

                if (matchedGrammar) {{
                    tokenSpan.classList.add('grammar-highlight');
                    tokenSpan.title = `【941文型】${{matchedGrammar.title}} (${{matchedGrammar.level || '文型'}})`;
                    tokenSpan.dataset.grammarId = matchedGrammar.id;

                    const isLastOfGrammar = (wIdx === words.length - 1) || (wordOffsets[wIdx + 1].start >= matchedGrammar.end);
                    if (isLastOfGrammar) {{
                        const miniBadge = document.createElement('span');
                        miniBadge.className = 'grammar-mini-badge';
                        miniBadge.textContent = matchedGrammar.level ? `${{matchedGrammar.level}}` : '文型';
                        miniBadge.onclick = (e) => {{
                            e.stopPropagation();
                            openGrammarDrawer(matchedGrammar);
                        }};
                        tokenSpan.appendChild(miniBadge);
                    }}
                }}

                container.appendChild(tokenSpan);
            }});
        }}

        function selectSentence(idx) {{
            if (!state.analyzedData || !state.analyzedData.sentences[idx]) return;
            state.currentSentenceIdx = idx;
            const sentence = state.analyzedData.sentences[idx];
            const total = state.analyzedData.sentences.length;

            document.querySelectorAll('.sentence-row').forEach(r => r.classList.remove('active'));
            const activeRow = document.querySelector(`.sentence-row[data-sentence-idx="${{idx}}"]`);
            if (activeRow) activeRow.classList.add('active');

            dom.currentSentenceBadge.textContent = `第 ${{idx + 1}} 句 / 共 ${{total}} 句`;
            dom.selectedSentenceJp.innerHTML = sentence.words.map(w => w.ruby_html).join('');
            dom.selectedSentenceZh.textContent = sentence.translation || '暫無翻譯';

            renderSentenceGrammars(sentence.grammars || []);
            renderSentenceWordsTable(sentence.words, sentence.grammars || []);

            dom.btnPrevSentence.disabled = (idx === 0);
            dom.btnNextSentence.disabled = (idx === total - 1);
        }}

        function navigateSentence(delta) {{
            if (!state.analyzedData) return;
            const newIdx = state.currentSentenceIdx + delta;
            if (newIdx >= 0 && newIdx < state.analyzedData.sentences.length) {{
                selectSentence(newIdx);
                const target = document.querySelector(`.sentence-row[data-sentence-idx="${{newIdx}}"]`);
                if (target) target.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
            }}
        }}

        function renderSentenceGrammars(grammars) {{
            dom.sentenceGrammarCount.textContent = grammars.length;
            dom.sentenceGrammarsList.innerHTML = '';
            if (grammars.length === 0) {{
                dom.sentenceGrammarsList.innerHTML = '<div class="empty-hint">本句未偵測到特殊 941 文法句型</div>';
                return;
            }}
            grammars.forEach(g => {{
                const card = document.createElement('div');
                card.className = 'grammar-item-card';
                card.innerHTML = `
                    <div class="grammar-card-top">
                        <div class="grammar-card-title">${{escapeHtml(g.title)}}</div>
                        <span class="badge-jlpt badge-${{(g.level || 'n2').toLowerCase().replace('~', '_')}}">${{g.level || 'JLPT'}}</span>
                    </div>
                    ${{g.form ? `<div class="grammar-form-box"><strong>接續：</strong>${{escapeHtml(g.form)}}</div>` : ''}}
                    <div class="grammar-meaning-box">${{escapeHtml(g.meaningZh || '暫無解析')}}</div>
                    ${{g.exampleRuby ? `<div class="grammar-example-box"><strong>例句：</strong>${{g.exampleRuby}}<br><span style="color:var(--text-muted);font-size:0.84rem;">${{escapeHtml(g.translation || '')}}</span></div>` : ''}}
                    <div class="grammar-card-actions">
                        <button class="btn-grammar-detail" onclick="openGrammarDrawerById(${{g.id}})">
                            <i class="fa-solid fa-book-open"></i> 查看完整詳解
                        </button>
                    </div>
                `;
                dom.sentenceGrammarsList.appendChild(card);
            }});
        }}

        function renderSentenceWordsTable(words, grammars = []) {{
            dom.sentenceWordCount.textContent = words.length;
            dom.sentenceWordsTbody.innerHTML = '';

            words.forEach((w, wIdx) => {{
                const isFav = state.notebook.words.some(item => item.surface === w.surface);

                // 判斷是否命中 941 文型
                const matchedGrammar = grammars.find(g => 
                    (g.title && g.title.includes(w.surface)) || 
                    (g.matched_text && g.matched_text.includes(w.surface)) ||
                    (w.base_form && g.title && g.title.includes(w.base_form))
                );

                let posBadge = '';
                if (matchedGrammar) {{
                    posBadge = `<span class="badge-grammar-legend" style="font-size:0.75rem;"><i class="fa-solid fa-bookmark"></i> 文型 [${{matchedGrammar.level || '句型'}}]</span>`;
                }} else {{
                    let posName = w.pos || '單字';
                    if (posName.includes('動詞')) posName = '動詞';
                    else if (posName.includes('形容詞')) posName = '形容詞';
                    else if (posName.includes('副詞')) posName = '副詞';
                    else if (posName.includes('名詞')) posName = '名詞';
                    else if (posName.includes('助詞')) posName = '助詞';
                    else if (posName.includes('助動詞')) posName = '助動詞';
                    else if (posName.includes('接續') || posName.includes('接続')) posName = '接續詞';
                    else if (posName.includes('外來') || posName.includes('カタカナ')) posName = '外來語';
                    else if (posName.includes('連體') || posName.includes('連体')) posName = '連體詞';
                    else if (posName.includes('記號') || posName.includes('符號')) posName = '符號';
                    posBadge = `<span style="font-size:0.82rem;color:var(--text-muted);font-weight:600;">${{posName}}</span>`;
                }}

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${{escapeHtml(w.base_form || w.surface)}}</strong></td>
                    <td style="color:#e11d48;font-weight:700;">${{escapeHtml(w.reading || '-')}}</td>
                    <td>${{posBadge}}</td>
                    <td>${{w.jlpt ? `<span class="badge-jlpt badge-${{w.jlpt.toLowerCase()}}">${{w.jlpt}}</span>` : '<span style="color:var(--text-muted);">-</span>'}}</td>
                    <td style="color:var(--text-main);font-size:0.88rem;" id="word-trans-cell-${{wIdx}}">
                        <span style="color:var(--text-muted);font-size:0.78rem;"><i class="fa-solid fa-spinner fa-spin"></i> 翻譯中</span>
                    </td>
                    <td style="text-align:center;">
                        <button class="btn-fav-word ${{isFav ? 'active' : ''}}" title="加入生詞本" onclick="toggleWordNotebook('${{escapeHtml(w.surface)}}', '${{escapeHtml(w.base_form)}}', '${{escapeHtml(w.reading)}}', '${{escapeHtml(w.jlpt || '')}}', '${{escapeHtml(w.pos || '')}}')">
                            <i class="fa-solid fa-star"></i>
                        </button>
                    </td>
                `;
                dom.sentenceWordsTbody.appendChild(tr);

                // 異步翻譯單字中文
                const termToQuery = w.base_form || w.surface;
                translateJaToZh(termToQuery).then(trans => {{
                    const cell = document.getElementById(`word-trans-cell-${{wIdx}}`);
                    if (cell) {{
                        cell.innerHTML = `<strong>${{escapeHtml(trans || '-')}}</strong>`;
                        w.translation = trans;
                    }}
                }}).catch(() => {{
                    const cell = document.getElementById(`word-trans-cell-${{wIdx}}`);
                    if (cell) cell.textContent = '-';
                }});
            }});
        }}

        async function showWordPopover(targetElem, word, event) {{
            const rect = targetElem.getBoundingClientRect();
            dom.popoverWordSurface.textContent = word.surface;
            dom.popoverWordKana.textContent = word.reading || word.surface;
            dom.popoverWordPos.textContent = word.pos || '單字';

            if (word.jlpt) {{
                dom.popoverWordLevel.textContent = word.jlpt;
                dom.popoverWordLevel.className = `badge-jlpt badge-${{word.jlpt.toLowerCase()}}`;
                dom.popoverWordLevel.style.display = 'inline-flex';
            }} else {{
                dom.popoverWordLevel.style.display = 'none';
            }}

            const isFav = state.notebook.words.some(item => item.surface === word.surface);
            dom.btnAddWordToNotebook.innerHTML = isFav 
                ? '<i class="fa-solid fa-star text-amber-400"></i> 已在生詞本中'
                : '<i class="fa-regular fa-star"></i> 存入生詞本';

            dom.btnAddWordToNotebook.onclick = () => {{
                toggleWordNotebook(word.surface, word.base_form, word.reading, word.jlpt, word.pos);
                const nowFav = state.notebook.words.some(item => item.surface === word.surface);
                dom.btnAddWordToNotebook.innerHTML = nowFav 
                    ? '<i class="fa-solid fa-star text-amber-400"></i> 已在生詞本中'
                    : '<i class="fa-regular fa-star"></i> 存入生詞本';
            }};

            dom.wordPopover.style.display = 'flex';
            const popoverWidth = 290;
            let left = rect.left + window.scrollX - (popoverWidth / 2) + (rect.width / 2);
            let top = rect.bottom + window.scrollY + 8;
            if (left < 10) left = 10;
            if (left + popoverWidth > window.innerWidth - 10) left = window.innerWidth - popoverWidth - 10;

            dom.wordPopover.style.left = `${{left}}px`;
            dom.wordPopover.style.top = `${{top}}px`;

            dom.popoverWordMeaning.innerHTML = '<div class="meaning-spinner"><i class="fa-solid fa-spinner fa-spin"></i> 正在查詢釋義...</div>';
            const trans = await translateJaToZh(word.base_form || word.surface);
            dom.popoverWordMeaning.innerHTML = `<strong>中文釋義：</strong>${{escapeHtml(trans || '暫無釋義')}}`;
        }}

        function closeWordPopover() {{
            dom.wordPopover.style.display = 'none';
        }}

        function openGrammarDrawerById(id) {{
            const g = GRAMMAR_DATA.find(item => item.id === id);
            if (g) openGrammarDrawer(g);
        }}

        function openGrammarDrawer(g) {{
            dom.drawerGrammarTitle.textContent = g.title;
            dom.drawerGrammarLevel.textContent = g.level || 'JLPT';
            dom.drawerGrammarLevel.className = `badge-jlpt badge-${{(g.level || 'n2').toLowerCase().replace('~', '_')}}`;
            dom.drawerGrammarExternalLink.href = g.sourceUrl || `https://fobeetsai.github.io/japanese-grammar/`;

            const isFav = state.notebook.grammars.some(item => item.id === g.id);
            dom.btnDrawerFav.innerHTML = isFav 
                ? '<i class="fa-solid fa-star text-amber-400"></i>' 
                : '<i class="fa-regular fa-star"></i>';
            dom.btnDrawerFav.onclick = () => {{
                toggleGrammarNotebook(g);
                const nowFav = state.notebook.grammars.some(item => item.id === g.id);
                dom.btnDrawerFav.innerHTML = nowFav 
                    ? '<i class="fa-solid fa-star text-amber-400"></i>' 
                    : '<i class="fa-regular fa-star"></i>';
            }};

            dom.drawerGrammarBody.innerHTML = `
                <div class="drawer-box">
                    <div class="drawer-label"><i class="fa-solid fa-link"></i> 接續規則 (Connection Form)</div>
                    <div style="font-weight:700;color:var(--primary);font-size:1.05rem;">${{escapeHtml(g.form || '無特殊接續限制')}}</div>
                </div>

                <div class="drawer-box">
                    <div class="drawer-label"><i class="fa-solid fa-circle-question"></i> 中文深度精解 (Meaning ZH)</div>
                    <div style="font-size:1.05rem;line-height:1.7;">${{escapeHtml(g.meaningZh || '暫無解析')}}</div>
                    ${{g.meaningJa ? `<div style="font-size:0.9rem;color:var(--text-muted);margin-top:0.5rem;border-top:1px dashed var(--border-color);padding-top:0.5rem;">日語說明：${{escapeHtml(g.meaningJa)}}</div>` : ''}}
                </div>

                <div class="drawer-box">
                    <div class="drawer-label"><i class="fa-solid fa-quote-left"></i> 精選例文與振假名 (Example Sentence)</div>
                    <div style="font-size:1.25rem;font-weight:700;font-family:var(--font-jp);line-height:1.8;">${{g.exampleRuby || escapeHtml(g.example || '')}}</div>
                    <div style="font-size:1.02rem;color:var(--text-muted);margin-top:0.65rem;border-top:1px dashed var(--border-color);padding-top:0.65rem;">
                        <strong>例句翻譯：</strong>${{escapeHtml(g.translation || '暫無翻譯')}}
                    </div>
                </div>

                ${{g.note ? `
                <div class="drawer-box" style="border-left:4px solid #f59e0b;">
                    <div class="drawer-label" style="color:#b45309;"><i class="fa-solid fa-lightbulb"></i> 重點學習提示 (Key Note)</div>
                    <div style="font-size:0.95rem;color:var(--text-main);">${{escapeHtml(g.note)}}</div>
                </div>
                ` : ''}}
            `;

            dom.grammarDrawerOverlay.classList.add('open');
        }}

        function closeGrammarDrawer() {{
            dom.grammarDrawerOverlay.classList.remove('open');
        }}

        function loadNotebook() {{
            try {{
                const s = localStorage.getItem('japanese_reader_notebook');
                if (s) state.notebook = JSON.parse(s);
            }} catch (e) {{
                state.notebook = {{ words: [], grammars: [] }};
            }}
            updateNotebookHeaderCount();
        }}

        function saveNotebook() {{
            localStorage.setItem('japanese_reader_notebook', JSON.stringify(state.notebook));
            updateNotebookHeaderCount();
        }}

        function updateNotebookHeaderCount() {{
            const total = state.notebook.words.length + state.notebook.grammars.length;
            dom.notebookCount.textContent = total;
            dom.nbWordCount.textContent = state.notebook.words.length;
            dom.nbGrammarCount.textContent = state.notebook.grammars.length;
        }}

        function toggleWordNotebook(surface, baseForm, reading, jlpt, pos) {{
            const idx = state.notebook.words.findIndex(w => w.surface === surface);
            if (idx > -1) {{
                state.notebook.words.splice(idx, 1);
                showToast(`已移除「${{surface}}」`);
            }} else {{
                state.notebook.words.push({{
                    surface,
                    baseForm: baseForm || surface,
                    reading,
                    jlpt,
                    pos,
                    addedAt: new Date().toLocaleDateString()
                }});
                showToast(`已存入生詞本「${{surface}}」！`);
            }}
            saveNotebook();
            if (state.analyzedData) {{
                const s = state.analyzedData.sentences[state.currentSentenceIdx];
                renderSentenceWordsTable(s.words, s.grammars || []);
            }}
        }}

        function toggleGrammarNotebook(g) {{
            const idx = state.notebook.grammars.findIndex(item => item.id === g.id);
            if (idx > -1) {{
                state.notebook.grammars.splice(idx, 1);
                showToast(`已自收藏移除「${{g.title}}」`);
            }} else {{
                state.notebook.grammars.push({{
                    id: g.id,
                    title: g.title,
                    level: g.level,
                    meaningZh: g.meaningZh,
                    addedAt: new Date().toLocaleDateString()
                }});
                showToast(`已收藏文型「${{g.title}}」！`);
            }}
            saveNotebook();
        }}

        function openNotebookModal() {{
            dom.notebookModal.classList.add('open');
            switchNotebookTab('words');
        }}

        function closeNotebookModal() {{
            dom.notebookModal.classList.remove('open');
        }}

        function switchNotebookTab(tab) {{
            dom.tabNotebookWordsBtn.classList.toggle('active', tab === 'words');
            dom.tabNotebookGrammarsBtn.classList.toggle('active', tab === 'grammars');
            dom.notebookListArea.innerHTML = '';

            if (tab === 'words') {{
                if (state.notebook.words.length === 0) {{
                    dom.notebookListArea.innerHTML = '<div class="empty-hint" style="text-align:center;padding:2rem;">生詞本目前為空</div>';
                    return;
                }}
                state.notebook.words.forEach((w, idx) => {{
                    const item = document.createElement('div');
                    item.className = 'notebook-item';
                    item.innerHTML = `
                        <div>
                            <strong style="font-size:1.15rem;font-family:var(--font-jp);">${{escapeHtml(w.surface)}}</strong>
                            <span style="color:#e11d48;margin-left:0.5rem;font-weight:700;">${{escapeHtml(w.reading || '')}}</span>
                            ${{w.jlpt ? `<span class="badge-jlpt badge-${{w.jlpt.toLowerCase()}}" style="margin-left:0.4rem;">${{w.jlpt}}</span>` : ''}}
                            <div style="font-size:0.8rem;color:var(--text-muted);">${{escapeHtml(w.pos || '')}}</div>
                        </div>
                        <button class="btn-del-item" onclick="removeWordFromNotebook(${{idx}})" title="刪除"><i class="fa-solid fa-trash-can"></i></button>
                    `;
                    dom.notebookListArea.appendChild(item);
                }});
            }} else {{
                if (state.notebook.grammars.length === 0) {{
                    dom.notebookListArea.innerHTML = '<div class="empty-hint" style="text-align:center;padding:2rem;">文法筆記目前為空</div>';
                    return;
                }}
                state.notebook.grammars.forEach((g, idx) => {{
                    const item = document.createElement('div');
                    item.className = 'notebook-item';
                    item.innerHTML = `
                        <div>
                            <strong style="font-size:1.15rem;font-family:var(--font-jp);color:var(--primary);">${{escapeHtml(g.title)}}</strong>
                            ${{g.level ? `<span class="badge-jlpt badge-${{g.level.toLowerCase().replace('~', '_')}}" style="margin-left:0.4rem;">${{g.level}}</span>` : ''}}
                            <div style="font-size:0.88rem;margin-top:0.25rem;">${{escapeHtml(g.meaningZh || '')}}</div>
                        </div>
                        <button class="btn-del-item" onclick="removeGrammarFromNotebook(${{idx}})" title="刪除"><i class="fa-solid fa-trash-can"></i></button>
                    `;
                    dom.notebookListArea.appendChild(item);
                }});
            }}
        }}

        function removeWordFromNotebook(idx) {{
            state.notebook.words.splice(idx, 1);
            saveNotebook();
            switchNotebookTab('words');
        }}

        function removeGrammarFromNotebook(idx) {{
            state.notebook.grammars.splice(idx, 1);
            saveNotebook();
            switchNotebookTab('grammars');
        }}

        function clearNotebook() {{
            if (!confirm('確定要清空所有收藏嗎？')) return;
            state.notebook = {{ words: [], grammars: [] }};
            saveNotebook();
            switchNotebookTab('words');
            showToast('已清空筆記本');
        }}

        function exportNotebook() {{
            let content = "=== 日文閱讀助手・學習筆記本 ===\\n\\n";
            content += "【生詞本】\\n";
            state.notebook.words.forEach((w, i) => {{
                content += `${{i + 1}}. ${{w.surface}} [${{w.reading}}] (${{w.jlpt || 'Other'}})\\n`;
            }});
            content += "\\n【文法句型筆記】\\n";
            state.notebook.grammars.forEach((g, i) => {{
                content += `${{i + 1}}. ${{g.title}} [${{g.level || 'JLPT'}}]\\n   ${{g.meaningZh}}\\n`;
            }});

            const blob = new Blob([content], {{ type: 'text/plain;charset=utf-8' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `日文閱讀筆記_${{new Date().toISOString().slice(0, 10)}}.txt`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('已匯出學習筆記！');
        }}

        function speakJapanese(text) {{
            if (!('speechSynthesis' in window)) {{
                showToast('您的瀏覽器不支援語音朗讀');
                return;
            }}
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(text);
            u.lang = 'ja-JP';
            u.rate = 0.95;
            const voices = window.speechSynthesis.getVoices();
            const jaVoice = voices.find(v => v.lang.startsWith('ja'));
            if (jaVoice) u.voice = jaVoice;
            window.speechSynthesis.speak(u);
        }}

        let toastTimer = null;
        function showToast(msg) {{
            dom.toastMsg.textContent = msg;
            dom.toast.classList.add('show');
            clearTimeout(toastTimer);
            toastTimer = setTimeout(() => dom.toast.classList.remove('show'), 2800);
        }}

        function escapeHtml(str) {{
            if (!str) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }}
    </script>
</body>
</html>
"""

    print("[4/4] 寫入獨立網頁檔案...")
    # 輸出到 index.html (用於直接上傳 GitHub Pages)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

    # 輸出到 japanese_reader.html
    with open("japanese_reader.html", "w", encoding="utf-8") as f:
        f.write(html_template)

    # 同時覆蓋 static/index.html，讓本地伺服器與靜態部署皆可立即使用
    with open("static/index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

    size_kb = os.path.getsize("index.html") / 1024
    print(f"[OK] 產出完成！index.html, japanese_reader.html, static/index.html 已更新，檔案大小：{size_kb:.1f} KB")

if __name__ == "__main__":
    build()
