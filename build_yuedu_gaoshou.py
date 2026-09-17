# -*- coding: utf-8 -*-
"""
閱讀高手 (Reading Master) - 全方位終極日語學習工作台產生器
整合：
1. 句解霸文章深度解析 (941 條《絵でわかる日本語》文法庫、助詞與文型階層自測、代用換句話說、整句深度分析器)
2. Trancy 沉浸雙語閱讀 (中日對照卡片流、全顯/遮日/遮中/雙遮、小字假名注音、單句深度拆解連動)
3. 跟讀與聽力特訓 (隨讀變色 Karaoke 高亮、微軟 Edge 自然語音七海/圭太、無段語速、影子跟讀錄音對比、聽寫填空)
4. 單字與文法複習中心 (JLPT N1-N5 單字分級色彩著色、生詞本、星號收藏句、941文法抽認卡、Anki單字翻牌自測)
"""

import os
import json
import re

def build():
    root = os.path.dirname(os.path.abspath(__file__))
    print("[1/5] 讀取核心資料庫 (941條文法、JLPT單字、漢字字典、助詞)...")

    with open(os.path.join(root, "grammar_data.json"), "r", encoding="utf-8") as f:
        grammar_data = json.load(f)

    with open(os.path.join(root, "jlpt_vocab_all.json"), "r", encoding="utf-8") as f:
        raw_vocab = json.load(f)

    compact_vocab = {}
    for word, entries in raw_vocab.items():
        if entries and isinstance(entries, list):
            lvl = entries[0].get("level", 0)
            reading = entries[0].get("reading", "")
            compact_vocab[word] = [lvl, reading]

    supplemental_vocab = {
        'みる': [5, 'みる'], 'いる': [5, 'いる'], 'おる': [3, 'おる'], 'くる': [5, 'くる'],
        'おく': [4, 'おく'], 'ゆく': [4, 'ゆく'], 'ない': [5, 'ない'], 'ほしい': [5, 'ほしい'],
        'たい': [5, 'たい'], 'そうだ': [4, 'そうだ'], 'ようだ': [4, 'ようだ'], 'らしい': [4, 'らしい'],
        'わけ': [3, 'わけ'], 'もの': [4, 'もの'], 'ため': [4, 'ため'], 'よう': [4, 'よう'],
        'ところ': [4, 'ところ'], 'とおり': [4, 'とおり'], 'どおり': [4, 'どおり'], 'はず': [4, 'はず'],
        'つもり': [4, 'つもり'], 'こと': [5, 'こと'], 'ほう': [5, 'ほう'], 'とき': [5, 'とき']
    }
    for k, v in supplemental_vocab.items():
        if k not in compact_vocab:
            compact_vocab[k] = v

    with open(os.path.join(root, "kanji_compact.json"), "r", encoding="utf-8") as f:
        kanji_compact_str = f.read()

    with open(os.path.join(root, "particle_data.json"), "r", encoding="utf-8") as f:
        particle_data = json.load(f)

    from analyzer import SPECIAL_GRAMMAR_PATTERNS, COMPOUND_PARTICLES, ADVERBIAL_PARTICLES, CONJUNCTIVE_PARTICLES, CASE_PARTICLES

    grammar_json_str = json.dumps(grammar_data, ensure_ascii=False, separators=(',', ':'))
    vocab_json_str = json.dumps(compact_vocab, ensure_ascii=False, separators=(',', ':'))
    particle_json_str = json.dumps(particle_data, ensure_ascii=False, separators=(',', ':'))
    special_grammar_json = json.dumps(SPECIAL_GRAMMAR_PATTERNS, ensure_ascii=False, separators=(',', ':'))
    compound_particles_json = json.dumps(COMPOUND_PARTICLES, ensure_ascii=False, separators=(',', ':'))
    adverbial_particles_json = json.dumps(ADVERBIAL_PARTICLES, ensure_ascii=False, separators=(',', ':'))
    conjunctive_particles_json = json.dumps(CONJUNCTIVE_PARTICLES, ensure_ascii=False, separators=(',', ':'))
    case_particles_json = json.dumps(CASE_PARTICLES, ensure_ascii=False, separators=(',', ':'))

    print("[2/5] 讀取並整合樣式表...")
    with open(os.path.join(root, "static", "css", "style.css"), "r", encoding="utf-8") as f:
        reader_css = f.read()

    print("[3/5] 讀取 index.html 核心代碼並注入全方位工作台擴展...")
    with open(os.path.join(root, "index.html"), "r", encoding="utf-8") as f:
        base_html = f.read()

    # 1. 更改頁面標題與品牌
    updated_html = base_html.replace(
        "<title>日文閱讀助手 (Japanese Reading Assistant) | 仿句解霸・941條文法聯動</title>",
        "<title>閱讀高手 (Reading Master) | 句解霸・941條文法・沉浸雙語・跟讀聽力・單字大成</title>"
    )

    # 2. 注入自定義全方位工作台樣式
    master_css = """
/* ==========================================================================
   閱讀高手 (Reading Master) 全方位工作台專屬樣式
   ========================================================================== */

/* 頂部工作台模式切換導航 */
.master-nav-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(15, 23, 42, 0.06);
    padding: 4px;
    border-radius: 12px;
    margin-left: 14px;
}
[data-theme="dark"] .master-nav-wrap {
    background: rgba(255, 255, 255, 0.08);
}
.master-tab-btn {
    border: none;
    background: transparent;
    padding: 8px 14px;
    border-radius: 8px;
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--text-muted);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s ease;
    white-space: nowrap;
}
.master-tab-btn:hover {
    color: var(--primary);
    background: rgba(99, 102, 241, 0.1);
}
.master-tab-btn.active {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

/* 核心四大視圖面板 */
.master-view-pane {
    display: none;
    animation: fadeInPane 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}
.master-view-pane.active {
    display: block;
}
@keyframes fadeInPane {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}

/* 沉浸雙語卡片流樣式 */
.trancy-stream-container {
    max-width: 1060px;
    margin: 0 auto;
    padding-bottom: 90px;
}
.trancy-stream-toolbar {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 12px 18px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    box-shadow: var(--shadow-sm);
}
.trancy-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 18px 22px;
    margin-bottom: 14px;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
    position: relative;
}
.trancy-card:hover {
    border-color: #6366f1;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.15);
}
.trancy-card.active-playing {
    border-color: #8b5cf6;
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.4), 0 8px 24px rgba(139, 92, 246, 0.2);
    background: linear-gradient(180deg, var(--bg-card), rgba(99, 102, 241, 0.03));
}
.trancy-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}
.trancy-idx-tag {
    font-size: 0.75rem;
    font-weight: 800;
    color: #6366f1;
    background: rgba(99, 102, 241, 0.12);
    padding: 2px 8px;
    border-radius: 9999px;
}
.trancy-card-actions {
    display: flex;
    align-items: center;
    gap: 6px;
}
.trancy-btn-action {
    background: var(--bg-sub);
    border: 1px solid var(--border-color);
    color: var(--text-main);
    padding: 5px 10px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    transition: all 0.15s;
}
.trancy-btn-action:hover {
    background: #6366f1;
    color: #ffffff;
    border-color: #6366f1;
}
.trancy-btn-action.btn-deep-analyze {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.15));
    border-color: rgba(99, 102, 241, 0.35);
    color: #6366f1;
    font-weight: 700;
}
.trancy-btn-action.btn-deep-analyze:hover {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff;
}
.trancy-card-jp {
    font-family: var(--font-jp);
    font-size: 1.25rem;
    line-height: 2.3;
    margin-bottom: 8px;
    color: var(--text-main);
}
.trancy-card-zh {
    font-size: 1.02rem;
    color: var(--text-muted);
    line-height: 1.7;
    border-top: 1px dashed var(--border-color);
    padding-top: 8px;
}

/* 雙向遮蔽效果 */
.mask-active-jp .trancy-card-jp {
    filter: blur(7px);
    opacity: 0.3;
    user-select: none;
    transition: filter 0.2s, opacity 0.2s;
    cursor: pointer;
}
.mask-active-jp .trancy-card:hover .trancy-card-jp,
.mask-active-jp .trancy-card.revealed .trancy-card-jp {
    filter: none;
    opacity: 1;
}
.mask-active-zh .trancy-card-zh {
    filter: blur(7px);
    opacity: 0.3;
    user-select: none;
    transition: filter 0.2s, opacity 0.2s;
    cursor: pointer;
}
.mask-active-zh .trancy-card:hover .trancy-card-zh,
.mask-active-zh .trancy-card.revealed .trancy-card-zh {
    filter: none;
    opacity: 1;
}

/* KARAOKE 卡拉OK 隨讀變色高亮 */
.jp-token.karaoke-active, .karaoke-active {
    background: #fef08a !important;
    color: #1e1b4b !important;
    box-shadow: 0 0 14px rgba(250, 204, 21, 0.9), 0 0 0 1px rgba(234, 179, 8, 0.7) !important;
    transform: scale(1.08);
    font-weight: 700;
    border-radius: 4px;
    z-index: 5;
}
.jp-token.karaoke-active rt {
    color: #1e1b4b !important;
    font-weight: 700;
    filter: none !important;
}
.jp-token.karaoke-passed, .karaoke-passed {
    color: #818cf8;
    background: rgba(99, 102, 241, 0.1);
}

/* 跟讀與影子訓練專用樣式 */
.shadowing-master-card {
    max-width: 900px;
    margin: 0 auto 30px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 28px;
    box-shadow: var(--shadow-md);
    text-align: center;
}
.shadowing-display-box {
    background: var(--bg-sub);
    border-radius: var(--radius-md);
    padding: 24px;
    margin-bottom: 24px;
}
.shadowing-jp-large {
    font-family: var(--font-jp);
    font-size: 1.65rem;
    line-height: 2.2;
    margin-bottom: 12px;
}
.shadowing-zh-hint {
    font-size: 1.15rem;
    color: var(--text-muted);
}
.shadowing-controls {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}
.btn-mic-record {
    width: 68px;
    height: 68px;
    border-radius: 9999px;
    border: none;
    background: linear-gradient(135deg, #ef4444, #f43f5e);
    color: #fff;
    font-size: 1.6rem;
    cursor: pointer;
    box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}
.btn-mic-record:hover {
    transform: scale(1.08);
}
.btn-mic-record.recording {
    animation: micPulse 1.2s infinite;
    background: #dc2626;
}
@keyframes micPulse {
    0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
    70% { transform: scale(1.1); box-shadow: 0 0 0 16px rgba(239, 68, 68, 0); }
    100% { transform: scale(1); }
}

/* 底部全域語音播放器底列 */
.master-audio-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    background: rgba(15, 23, 42, 0.94);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-top: 1px solid rgba(99, 102, 241, 0.35);
    padding: 10px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.4);
    color: #f8fafc;
}
.audio-bar-left {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 240px;
}
.audio-bar-center {
    display: flex;
    align-items: center;
    gap: 14px;
    flex: 1;
    justify-content: center;
    max-width: 600px;
}
.audio-bar-right {
    display: flex;
    align-items: center;
    gap: 14px;
}
.btn-player-round {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: none;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff;
    font-size: 1.15rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
    transition: all 0.15s;
}
.btn-player-round:hover {
    transform: scale(1.08);
}
.btn-player-icon {
    background: transparent;
    border: none;
    color: #94a3b8;
    font-size: 1.1rem;
    cursor: pointer;
    padding: 6px;
    border-radius: 6px;
    transition: all 0.15s;
}
.btn-player-icon:hover {
    color: #fff;
    background: rgba(255, 255, 255, 0.1);
}
.btn-player-icon.active {
    color: #818cf8;
}
.audio-voice-select {
    background: #1e293b;
    border: 1px solid rgba(99, 102, 241, 0.4);
    color: #f8fafc;
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 0.82rem;
    outline: none;
}
"""

    # 注入 CSS
    updated_html = updated_html.replace("</style>", master_css + "\n</style>")

    # 3. 注入頂部品牌與四大模式切換導航
    old_brand_html = """            <div class="header-brand-wrap">
                <div class="brand-logo">
                    <i class="fa-solid fa-book-open-reader"></i>
                </div>
                <div class="brand-info">
                    <div class="brand-title">
                        <h1>日文閱讀助手</h1>
                        <span class="version-tag">v2.1 漢字全假名・單字複習版</span>
                    </div>
                    <p class="brand-subtitle">
                        仿句解霸閱讀拆解・深度聯動 
                        <a href="https://fobeetsai.github.io/japanese-grammar/" target="_blank" rel="noopener noreferrer" class="grammar-link">
                            <i class="fa-solid fa-graduation-cap"></i>《絵でわかる日本語》941條文法庫
                        </a>
                    </p>
                </div>
            </div>"""

    new_brand_html = """            <div class="header-brand-wrap">
                <div class="brand-logo" style="background: linear-gradient(135deg, #6366f1, #a855f7); box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);">
                    <i class="fa-solid fa-crown" style="color: #ffd700;"></i>
                </div>
                <div class="brand-info">
                    <div class="brand-title">
                        <h1 style="background: linear-gradient(135deg, #4f46e5, #9333ea); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900;">閱讀高手</h1>
                        <span class="version-tag" style="background: linear-gradient(135deg, #f59e0b, #ef4444); color: #fff; font-weight: 800;">全方位大成版</span>
                    </div>
                    <p class="brand-subtitle">
                        941條文法 ✦ JLPT單字 ✦ 句解霸拆解 ✦ 沉浸雙語 ✦ 隨讀變色 ✦ 影子跟讀
                    </p>
                </div>

                <!-- 核心四大模式導航頁籤 -->
                <nav class="master-nav-wrap" role="tablist">
                    <button class="master-tab-btn active" data-view="deep" id="tabModeDeep" title="句解霸風格：整句拆解、941文法抽屜、助詞與換句話說">
                        <i class="fa-solid fa-microscope"></i> 文章深度解析
                    </button>
                    <button class="master-tab-btn" data-view="trancy" id="tabModeTrancy" title="Trancy 風格：雙語字幕對照、全顯/遮日/遮中/雙遮、小字假名注音">
                        <i class="fa-solid fa-closed-captioning"></i> 沉浸雙語閱讀
                    </button>
                    <button class="master-tab-btn" data-view="shadowing" id="tabModeShadowing" title="影子跟讀與口語特訓：原聲隨讀變色、麥克風錄音對比、聽寫填空">
                        <i class="fa-solid fa-microphone-lines"></i> 跟讀聽力特訓
                    </button>
                    <button class="master-tab-btn" data-view="review" id="tabModeReview" title="SRS 單字與文法抽認卡、生詞本、星號收藏句">
                        <i class="fa-solid fa-layer-group"></i> 單字文法複習
                    </button>
                </nav>
            </div>"""

    updated_html = updated_html.replace(old_brand_html, new_brand_html)

    # 4. 注入主區域中的另外三大視圖面板
    view_trancy_html = """
        <!-- ==========================================================================
             VIEW 2: TRANCY 沉浸雙語閱讀 (BILINGUAL DUAL STREAM)
             ========================================================================== -->
        <section class="master-view-pane" id="paneTrancy">
            <div class="trancy-stream-container">
                <div class="trancy-stream-toolbar">
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <span style="font-size: 0.85rem; font-weight: 700; color: var(--text-muted);"><i class="fa-solid fa-eye-slash"></i> 雙向遮蔽:</span>
                        <div class="btn-group" id="trancyMaskGroup">
                            <button class="pill-btn active" data-tmask="all">全顯</button>
                            <button class="pill-btn" data-tmask="mask-jp" title="遮蔽日文原文（懸停或點擊解開）">遮日</button>
                            <button class="pill-btn" data-tmask="mask-zh" title="遮蔽中文譯文（懸停或點擊解開）">遮中</button>
                            <button class="pill-btn" data-tmask="mask-both" title="雙向全遮（盲聽特訓）">雙遮</button>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <button class="btn-action-pill" id="btnTrancyPlayAll" style="background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff; font-weight: 700; border: none;">
                            <i class="fa-solid fa-play"></i> 全篇卡拉OK朗讀
                        </button>
                        <button class="btn-action-pill" id="btnTrancyReverseAll" title="一鍵反轉所有遮蔽">
                            <i class="fa-solid fa-arrows-rotate"></i> 反轉遮蔽
                        </button>
                    </div>
                </div>

                <!-- Dual Sentences Stream -->
                <div id="trancySentencesStream">
                    <!-- Injected dynamically -->
                </div>
            </div>
        </section>

        <!-- ==========================================================================
             VIEW 3: 跟讀與聽力特訓 (SHADOWING & DICTATION)
             ========================================================================== -->
        <section class="master-view-pane" id="paneShadowing">
            <div class="shadowing-master-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <span class="badge-jlpt badge-n2" id="shadowingIndexBadge">第 1 句 / 共 0 句</span>
                    <div style="display: flex; gap: 8px;">
                        <button class="tool-btn" id="btnShadowPrev"><i class="fa-solid fa-backward-step"></i> 上一句</button>
                        <button class="tool-btn" id="btnShadowNext">下一句 <i class="fa-solid fa-forward-step"></i></button>
                    </div>
                </div>

                <div class="shadowing-display-box">
                    <div class="shadowing-jp-large" id="shadowingJpDisplay">
                        <!-- Target Sentence Injected -->
                    </div>
                    <div class="shadowing-zh-hint" id="shadowingZhDisplay">
                        <!-- Chinese Translation Injected -->
                    </div>
                </div>

                <!-- Controls -->
                <div class="shadowing-controls">
                    <button class="btn-primary-action" id="btnShadowListen" style="background: linear-gradient(135deg, #6366f1, #8b5cf6); font-size: 1rem;">
                        <i class="fa-solid fa-volume-high"></i> 聆聽原聲 (伴隨變色)
                    </button>
                    <button class="btn-mic-record" id="btnShadowMic" title="點擊開始錄音，再次點擊結束">
                        <i class="fa-solid fa-microphone"></i>
                    </button>
                    <button class="btn-primary-action" id="btnShadowPlayRec" style="background: #10b981; font-size: 1rem; display: none;">
                        <i class="fa-solid fa-play"></i> 回放我的錄音
                    </button>
                </div>
                <div id="shadowRecTimer" style="font-size: 0.9rem; color: #ef4444; font-weight: 700; display: none;">
                    ● 正在錄音中...
                </div>

                <!-- 聽打填空特訓模組 -->
                <div style="margin-top: 36px; padding-top: 24px; border-top: 1px dashed var(--border-color);">
                    <h3 style="font-size: 1.15rem; margin-bottom: 12px; color: var(--text-main);"><i class="fa-solid fa-keyboard"></i> 聽打克漏字挑戰</h3>
                    <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 14px;">聽取發音後，在輸入框中打出正確日語句子，檢驗假名與聽力：</p>
                    <div style="display: flex; gap: 10px; justify-content: center; max-width: 600px; margin: 0 auto;">
                        <input type="text" id="dictationInput" placeholder="請在此輸入聽到的日語句子..." style="flex: 1; padding: 10px 14px; border: 2px solid var(--border-color); border-radius: 8px; font-family: var(--font-jp); font-size: 1.05rem; outline: none;">
                        <button class="tool-btn btn-quiz-accent" id="btnCheckDictation">驗證答案</button>
                    </div>
                    <div id="dictationFeedback" style="margin-top: 10px; font-size: 0.92rem; font-weight: 700;"></div>
                </div>
            </div>
        </section>

        <!-- ==========================================================================
             VIEW 4: 單字與文法複習中心 (REVIEW CENTER)
             ========================================================================== -->
        <section class="master-view-pane" id="paneReview">
            <div style="max-width: 1060px; margin: 0 auto; padding-bottom: 90px;">
                <div class="trancy-stream-toolbar">
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <span style="font-weight: 800; font-size: 1.05rem; color: var(--text-main);"><i class="fa-solid fa-book-bookmark text-amber-500"></i> 我的學習複習庫</span>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button class="pill-btn active" id="btnSubTabStarred">⭐ 收藏句 (<span id="revStarredCount">0</span>)</button>
                        <button class="pill-btn" id="btnSubTabVocab">📖 標記生詞 (<span id="revVocabCount">0</span>)</button>
                        <button class="pill-btn" id="btnSubTabGrammar">🎴 941 文法卡片</button>
                    </div>
                </div>

                <div id="reviewContainer">
                    <!-- Injected dynamically -->
                </div>
            </div>
        </section>
    """

    # 將 readerDeck 包裝為 View 1
    updated_html = updated_html.replace(
        '<section class="reader-deck" id="readerDeck" style="display: none;">',
        '<div class="master-view-pane active" id="paneDeep">\n<section class="reader-deck" id="readerDeck" style="display: none;">'
    )
    # 在 </main> 之前閉合 paneDeep 並插入另外三電視圖
    updated_html = updated_html.replace(
        '</main>',
        '</div><!-- end paneDeep -->\n' + view_trancy_html + '\n</main>'
    )

    # 5. 注入底部全域語音控制欄
    audio_bar_html = """
    <!-- 底部微軟 Edge 自然人聲與卡拉OK高亮控制底列 -->
    <div class="master-audio-bar" id="masterAudioBar">
        <div class="audio-bar-left">
            <button class="btn-player-round" id="btnGlobalPlay" title="播放 / 暫停 (Space)">
                <i class="fa-solid fa-play" id="globalPlayIcon"></i>
            </button>
            <div>
                <div style="font-size: 0.88rem; font-weight: 700; color: #fff;" id="playerStatusTitle">語音發音就緒</div>
                <div style="font-size: 0.72rem; color: #94a3b8;" id="playerStatusSnippet">點選任意句子或單字即可發音</div>
            </div>
        </div>

        <div class="audio-bar-center">
            <button class="btn-player-icon" id="btnGlobalPrev" title="上一句 (J)"><i class="fa-solid fa-backward-step"></i></button>
            <button class="btn-player-icon" id="btnGlobalLoop" title="循環朗讀當前句子"><i class="fa-solid fa-repeat"></i></button>
            <button class="btn-player-icon active" id="btnGlobalAutoNext" title="朗讀完畢自動連播下一句"><i class="fa-solid fa-forward"></i></button>
            <button class="btn-player-icon" id="btnGlobalNext" title="下一句 (K)"><i class="fa-solid fa-forward-step"></i></button>
        </div>

        <div class="audio-bar-right">
            <!-- 語音引擎選單 -->
            <select class="audio-voice-select" id="globalVoiceSelect" title="選取自然真人發音引擎">
                <option value="nanami">🌸 微軟 Nanami (七海・自然女聲)</option>
                <option value="keita">👦 微軟 Keita (圭太・自然男聲)</option>
                <option value="google-hd">☁️ Google 真人高音質 (Cloud HD)</option>
                <option value="default">🌐 瀏覽器日語 (系統)</option>
            </select>

            <!-- 無段語速 -->
            <div style="display: flex; align-items: center; gap: 6px;">
                <span style="font-size: 0.78rem; color: #cbd5e1;" id="globalRateLabel">1.0x</span>
                <input type="range" id="globalRateSlider" min="0.5" max="2.0" step="0.05" value="1.0" style="width: 75px; accent-color: #6366f1; cursor: pointer;">
            </div>
        </div>
    </div>
    """

    updated_html = updated_html.replace('</body>', audio_bar_html + '\n</body>')

    # 6. 注入微軟 Edge 自然語音引擎 + 卡拉OK隨讀變色 + 視圖切換之 JavaScript 代碼
    master_js = """
    // ==========================================================================
    // 閱讀高手 (Reading Master) 全方位工作台互動控制器
    // ==========================================================================
    (function() {
        'use strict';

        const masterState = {
            activeView: 'deep', // 'deep', 'trancy', 'shadowing', 'review'
            trancyMask: 'all',
            currentAudio: null,
            currentSentenceIdx: 0,
            isPlaying: false,
            isLoop: false,
            isAutoPlay: true,
            playbackRate: 1.0,
            voice: 'nanami',
            starredSentences: JSON.parse(localStorage.getItem('master_starred_sentences') || '[]'),
            customVocab: JSON.parse(localStorage.getItem('master_custom_vocab') || '[]'),
            mediaRecorder: null,
            audioChunks: [],
            recordedBlobUrl: null
        };

        // --- 視圖模式切換 ---
        function switchMasterView(viewId) {
            masterState.activeView = viewId;
            document.querySelectorAll('.master-tab-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.view === viewId);
            });
            document.querySelectorAll('.master-view-pane').forEach(p => p.classList.remove('active'));

            if (viewId === 'deep') {
                const pane = document.getElementById('paneDeep');
                if (pane) pane.classList.add('active');
            } else if (viewId === 'trancy') {
                const pane = document.getElementById('paneTrancy');
                if (pane) pane.classList.add('active');
                renderTrancyStream();
            } else if (viewId === 'shadowing') {
                const pane = document.getElementById('paneShadowing');
                if (pane) pane.classList.add('active');
                updateShadowingCard(masterState.currentSentenceIdx);
            } else if (viewId === 'review') {
                const pane = document.getElementById('paneReview');
                if (pane) pane.classList.add('active');
                renderReviewNotebook('starred');
            }
        }

        document.querySelectorAll('.master-tab-btn').forEach(btn => {
            btn.addEventListener('click', () => switchMasterView(btn.dataset.view));
        });

        // --- 自然真人語音引擎 (Edge Neural Voices + Google Cloud HD + Stepless Rate) ---
        function speakWithKaraoke(text, containerEl, onEnd) {
            if (!text) return;
            const cleanText = text.replace(/<[^>]+>/g, '').trim();

            if (masterState.currentAudio) {
                masterState.currentAudio.pause();
                masterState.currentAudio = null;
            }
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
            }
            clearKaraokeHighlights();

            // 準備欲高亮之單字 tokens
            let tokens = [];
            if (containerEl) {
                tokens = Array.from(containerEl.querySelectorAll('.jp-token, .trancy-karaoke-word, .word-token'));
            }

            const voiceChoice = masterState.voice;
            const rate = masterState.playbackRate;

            updatePlayerBarStatus(true, cleanText);

            // 方案 A: 若在 Edge 瀏覽器原生包含微軟自然語音
            if (voiceChoice !== 'google-hd' && 'speechSynthesis' in window) {
                const voices = window.speechSynthesis.getVoices();
                let matchedVoice = voices.find(v => {
                    const isJa = v.lang.startsWith('ja') || v.lang.includes('JP');
                    if (voiceChoice === 'nanami') return isJa && (v.name.includes('Nanami') || (v.name.includes('Natural') && !v.name.includes('Keita')));
                    if (voiceChoice === 'keita') return isJa && v.name.includes('Keita');
                    return isJa && !v.name.includes('Desktop') && !v.name.includes('Haruka');
                });

                if (matchedVoice) {
                    const u = new SpeechSynthesisUtterance(cleanText);
                    u.voice = matchedVoice;
                    u.lang = 'ja-JP';
                    u.rate = rate;

                    if (tokens.length > 0) {
                        u.onboundary = (e) => {
                            const charIdx = e.charIndex || 0;
                            let acc = 0;
                            let activeIdx = 0;
                            for (let i = 0; i < tokens.length; i++) {
                                const w = tokens[i].dataset.word || tokens[i].innerText || '';
                                acc += Math.max(1, w.length);
                                if (acc > charIdx) { activeIdx = i; break; }
                            }
                            applyTokenHighlight(tokens, activeIdx);
                        };
                    }

                    u.onend = () => {
                        updatePlayerBarStatus(false);
                        setTimeout(clearKaraokeHighlights, 400);
                        if (onEnd) onEnd();
                    };
                    u.onerror = () => {
                        updatePlayerBarStatus(false);
                        clearKaraokeHighlights();
                    };
                    window.speechSynthesis.speak(u);
                    return;
                }
            }

            // 方案 B: Google Cloud HD 原汁原味自然真人聲音
            const audioUrl = `https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=ja&q=${encodeURIComponent(cleanText.slice(0, 180))}`;
            const audio = new Audio(audioUrl);
            masterState.currentAudio = audio;
            audio.playbackRate = rate;

            if (tokens.length > 0) {
                const lengths = tokens.map(t => Math.max(1, (t.dataset.word || t.innerText || '').length));
                const totalLen = lengths.reduce((a, b) => a + b, 0);
                const cumulative = [];
                let sum = 0;
                for (const l of lengths) { sum += l; cumulative.push(sum / totalLen); }

                const interval = setInterval(() => {
                    if (!audio || audio.paused || audio.ended) {
                        clearInterval(interval);
                        return;
                    }
                    const dur = (audio.duration && !isNaN(audio.duration)) ? audio.duration : (totalLen * 0.28 / rate);
                    const ratio = Math.min(0.999, (audio.currentTime || 0) / dur);
                    let activeIdx = 0;
                    for (let i = 0; i < cumulative.length; i++) {
                        if (ratio <= cumulative[i]) { activeIdx = i; break; }
                    }
                    applyTokenHighlight(tokens, activeIdx);
                }, 35);
            }

            audio.onended = () => {
                updatePlayerBarStatus(false);
                masterState.currentAudio = null;
                setTimeout(clearKaraokeHighlights, 400);
                if (onEnd) onEnd();
            };
            audio.onerror = () => {
                updatePlayerBarStatus(false);
                clearKaraokeHighlights();
            };
            audio.play().catch(() => updatePlayerBarStatus(false));
        }

        function applyTokenHighlight(tokens, activeIdx) {
            tokens.forEach((t, i) => {
                if (i === activeIdx) {
                    t.classList.add('karaoke-active');
                    t.classList.remove('karaoke-passed');
                } else if (i < activeIdx) {
                    t.classList.remove('karaoke-active');
                    t.classList.add('karaoke-passed');
                } else {
                    t.classList.remove('karaoke-active', 'karaoke-passed');
                }
            });
        }

        function clearKaraokeHighlights() {
            document.querySelectorAll('.karaoke-active').forEach(el => el.classList.remove('karaoke-active'));
            document.querySelectorAll('.karaoke-passed').forEach(el => el.classList.remove('karaoke-passed'));
        }

        function updatePlayerBarStatus(playing, snippet = '') {
            masterState.isPlaying = playing;
            const icon = document.getElementById('globalPlayIcon');
            const title = document.getElementById('playerStatusTitle');
            const snipEl = document.getElementById('playerStatusSnippet');
            if (icon) icon.className = playing ? 'fa-solid fa-pause' : 'fa-solid fa-play';
            if (title) title.textContent = playing ? '正在流暢朗讀...' : '語音發音就緒';
            if (snipEl && snippet) snipEl.textContent = snippet.slice(0, 35) + (snippet.length > 35 ? '...' : '');
        }

        // --- 全域覆寫 speakJapanese 函式 ---
        window.speakJapanese = function(text, targetEl = null) {
            speakWithKaraoke(text, targetEl);
        };

        // --- 渲染 Trancy 沉浸雙語流 (View 2) ---
        function renderTrancyStream() {
            const stream = document.getElementById('trancySentencesStream');
            if (!stream) return;
            if (!state.sentences || state.sentences.length === 0) {
                stream.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">尚未加載文章，請先在「文章深度解析」貼上文章或選取範例文摘。</div>';
                return;
            }

            stream.innerHTML = '';
            state.sentences.forEach((s, idx) => {
                const card = document.createElement('div');
                card.className = `trancy-card ${getTrancyMaskClass()}`;
                card.id = `trancy-card-${idx}`;
                card.dataset.index = idx;

                const isStarred = masterState.starredSentences.some(st => st.text === s.text);

                card.innerHTML = `
                    <div class="trancy-card-header">
                        <span class="trancy-idx-tag">#${idx + 1}</span>
                        <div class="trancy-card-actions">
                            <button class="trancy-btn-action trancy-play-btn" data-idx="${idx}" title="自然語音播放 (伴隨變色)">
                                <i class="fa-solid fa-volume-high"></i> 朗讀
                            </button>
                            <button class="trancy-btn-action btn-deep-analyze" data-idx="${idx}" title="一鍵跳轉句解霸深度解析 (941文法與助詞)">
                                <i class="fa-solid fa-microscope"></i> 深度解析
                            </button>
                            <button class="trancy-btn-action ${isStarred ? 'active-star' : ''}" data-idx="${idx}" id="btnStarCard-${idx}" title="收藏此句">
                                <i class="fa-solid fa-star" style="${isStarred ? 'color:#fbbf24;' : ''}"></i>
                            </button>
                            <button class="trancy-btn-action trancy-copy-btn" data-idx="${idx}" title="複製雙語內容">
                                <i class="fa-solid fa-copy"></i>
                            </button>
                        </div>
                    </div>
                    <div class="trancy-card-jp">
                        ${s.rubyHtml || s.text}
                    </div>
                    <div class="trancy-card-zh">
                        ${s.translation || '(正在獲取翻譯...)'}
                    </div>
                `;

                // 點擊深度解析按鈕 -> 無縫切換至 View 1 並展開句解霸分析器
                const deepBtn = card.querySelector('.btn-deep-analyze');
                deepBtn.onclick = (e) => {
                    e.stopPropagation();
                    switchMasterView('deep');
                    setTimeout(() => {
                        selectSentence(idx);
                        const targetRow = document.getElementById(`sent-${idx}`);
                        if (targetRow) targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 80);
                };

                // 朗讀按鈕
                const playBtn = card.querySelector('.trancy-play-btn');
                playBtn.onclick = (e) => {
                    e.stopPropagation();
                    playSentenceAt(idx);
                };

                // 收藏按鈕
                const starBtn = card.querySelector(`#btnStarCard-${idx}`);
                starBtn.onclick = (e) => {
                    e.stopPropagation();
                    toggleStarSentence(s);
                    const nowStarred = masterState.starredSentences.some(st => st.text === s.text);
                    starBtn.innerHTML = `<i class="fa-solid fa-star" style="${nowStarred ? 'color:#fbbf24;' : ''}"></i>`;
                };

                // 複製按鈕
                const copyBtn = card.querySelector('.trancy-copy-btn');
                copyBtn.onclick = (e) => {
                    e.stopPropagation();
                    navigator.clipboard.writeText(`${s.text}\\n${s.translation || ''}`).then(() => {
                        showToast('已複製雙語內容！');
                    });
                };

                // 點擊卡片解開遮蔽
                card.onclick = () => card.classList.toggle('revealed');

                stream.appendChild(card);
            });
        }

        function getTrancyMaskClass() {
            if (masterState.trancyMask === 'mask-jp') return 'mask-active-jp';
            if (masterState.trancyMask === 'mask-zh') return 'mask-active-zh';
            if (masterState.trancyMask === 'mask-both') return 'mask-active-jp mask-active-zh';
            return '';
        }

        // 雙語遮蔽按鈕切換
        document.querySelectorAll('#trancyMaskGroup button').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('#trancyMaskGroup button').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                masterState.trancyMask = btn.dataset.tmask;
                renderTrancyStream();
            });
        });

        const btnRevAll = document.getElementById('btnTrancyReverseAll');
        if (btnRevAll) {
            btnRevAll.onclick = () => {
                document.querySelectorAll('.trancy-card').forEach(c => c.classList.toggle('revealed'));
            };
        }

        // --- 播放第 idx 句 ---
        function playSentenceAt(idx) {
            if (!state.sentences || idx < 0 || idx >= state.sentences.length) return;
            masterState.currentSentenceIdx = idx;

            // 高亮 Trancy 卡片
            document.querySelectorAll('.trancy-card').forEach((c, i) => {
                c.classList.toggle('active-playing', i === idx);
            });

            // 句解霸高亮
            selectSentence(idx);

            const s = state.sentences[idx];
            let activeContainer = document.querySelector(`#trancy-card-${idx} .trancy-card-jp`) || document.getElementById(`sent-${idx}`);
            if (masterState.activeView === 'shadowing') {
                activeContainer = document.getElementById('shadowingJpDisplay');
            }

            speakWithKaraoke(s.text, activeContainer, () => {
                if (masterState.isLoop) {
                    setTimeout(() => playSentenceAt(idx), 600);
                } else if (masterState.isAutoPlay) {
                    if (idx + 1 < state.sentences.length) {
                        setTimeout(() => playSentenceAt(idx + 1), 750);
                    } else {
                        showToast('已完成全篇朗讀！');
                    }
                }
            });
        }

        // --- 影子跟讀與口語錄音 (View 3) ---
        function updateShadowingCard(idx) {
            if (!state.sentences || state.sentences.length === 0) return;
            const s = state.sentences[idx] || state.sentences[0];
            masterState.currentSentenceIdx = idx;

            const badge = document.getElementById('shadowingIndexBadge');
            const jpDisplay = document.getElementById('shadowingJpDisplay');
            const zhDisplay = document.getElementById('shadowingZhDisplay');
            if (badge) badge.textContent = `第 ${idx + 1} 句 / 共 ${state.sentences.length} 句`;
            if (jpDisplay) jpDisplay.innerHTML = s.rubyHtml || s.text;
            if (zhDisplay) zhDisplay.textContent = s.translation || '(無中文翻譯)';

            const dictInput = document.getElementById('dictationInput');
            if (dictInput) { dictInput.value = ''; dictInput.style.borderColor = 'var(--border-color)'; }
            const dictFeed = document.getElementById('dictationFeedback');
            if (dictFeed) dictFeed.innerHTML = '';
        }

        document.getElementById('btnShadowPrev')?.addEventListener('click', () => {
            if (masterState.currentSentenceIdx > 0) updateShadowingCard(masterState.currentSentenceIdx - 1);
        });
        document.getElementById('btnShadowNext')?.addEventListener('click', () => {
            if (state.sentences && masterState.currentSentenceIdx + 1 < state.sentences.length) {
                updateShadowingCard(masterState.currentSentenceIdx + 1);
            }
        });
        document.getElementById('btnShadowListen')?.addEventListener('click', () => {
            const s = state.sentences[masterState.currentSentenceIdx];
            if (s) speakWithKaraoke(s.text, document.getElementById('shadowingJpDisplay'));
        });

        // 麥克風錄音
        const micBtn = document.getElementById('btnShadowMic');
        const playRecBtn = document.getElementById('btnShadowPlayRec');
        const recTimer = document.getElementById('shadowRecTimer');

        if (micBtn && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            micBtn.onclick = async () => {
                if (masterState.mediaRecorder && masterState.mediaRecorder.state === 'recording') {
                    masterState.mediaRecorder.stop();
                    micBtn.classList.remove('recording');
                    if (recTimer) recTimer.style.display = 'none';
                } else {
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        masterState.audioChunks = [];
                        masterState.mediaRecorder = new MediaRecorder(stream);
                        masterState.mediaRecorder.ondataavailable = (e) => masterState.audioChunks.push(e.data);
                        masterState.mediaRecorder.onstop = () => {
                            const blob = new Blob(masterState.audioChunks, { type: 'audio/webm' });
                            masterState.recordedBlobUrl = URL.createObjectURL(blob);
                            if (playRecBtn) {
                                playRecBtn.style.display = 'inline-flex';
                                playRecBtn.onclick = () => {
                                    const audio = new Audio(masterState.recordedBlobUrl);
                                    audio.play();
                                };
                            }
                            showToast('錄音完成！點擊綠色按鈕回放對比');
                        };
                        masterState.mediaRecorder.start();
                        micBtn.classList.add('recording');
                        if (recTimer) recTimer.style.display = 'block';
                    } catch (err) {
                        showToast('無法取得麥克風權限：' + err.message);
                    }
                }
            };
        }

        // 聽打填空驗證
        document.getElementById('btnCheckDictation')?.addEventListener('click', () => {
            const input = document.getElementById('dictationInput');
            const feedback = document.getElementById('dictationFeedback');
            const s = state.sentences[masterState.currentSentenceIdx];
            if (!input || !s) return;

            const cleanUser = input.value.trim().replace(/[\\s、。！？,.!?]/g, '');
            const cleanTarget = s.text.trim().replace(/[\\s、。！？,.!?]/g, '');

            if (cleanUser === cleanTarget) {
                input.style.borderColor = '#10b981';
                feedback.innerHTML = '<span style="color:#10b981;">🎉 完全正確！聽力與假名拼寫完全過關！</span>';
            } else {
                input.style.borderColor = '#ef4444';
                feedback.innerHTML = `<span style="color:#ef4444;">❌ 答案未完全對應，標準句子：${s.text}</span>`;
            }
        });

        // --- 收藏句子與生詞庫 (View 4) ---
        function toggleStarSentence(s) {
            const idx = masterState.starredSentences.findIndex(st => st.text === s.text);
            if (idx >= 0) {
                masterState.starredSentences.splice(idx, 1);
                showToast('已自收藏庫移除');
            } else {
                masterState.starredSentences.push({
                    text: s.text,
                    translation: s.translation || '',
                    date: new Date().toLocaleDateString()
                });
                showToast('已收藏至複習庫 ⭐');
            }
            localStorage.setItem('master_starred_sentences', JSON.stringify(masterState.starredSentences));
            updateReviewCounters();
        }

        function updateReviewCounters() {
            const starCountEl = document.getElementById('revStarredCount');
            const vocabCountEl = document.getElementById('revVocabCount');
            if (starCountEl) starCountEl.textContent = masterState.starredSentences.length;
            if (vocabCountEl) vocabCountEl.textContent = masterState.customVocab.length;
        }

        function renderReviewNotebook(subTab = 'starred') {
            updateReviewCounters();
            const container = document.getElementById('reviewContainer');
            if (!container) return;

            if (subTab === 'starred') {
                if (masterState.starredSentences.length === 0) {
                    container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">尚未收藏句子，在閱讀或雙語模式點擊 ⭐ 即可收藏！</div>';
                    return;
                }
                let html = '<div style="display:flex;flex-direction:column;gap:12px;">';
                masterState.starredSentences.forEach((st, i) => {
                    html += `
                        <div class="trancy-card" style="margin-bottom:0;">
                            <div class="trancy-card-header">
                                <span class="trancy-idx-tag">#${i + 1} (${st.date})</span>
                                <div>
                                    <button class="trancy-btn-action" onclick="window.speakJapanese('${st.text.replace(/'/g, "\\\\'")}');"><i class="fa-solid fa-volume-high"></i></button>
                                </div>
                            </div>
                            <div class="trancy-card-jp" style="font-size:1.15rem;">${st.text}</div>
                            <div class="trancy-card-zh">${st.translation}</div>
                        </div>
                    `;
                });
                html += '</div>';
                container.innerHTML = html;
            }
        }

        // --- 全域音頻播放欄控制事件 ---
        document.getElementById('btnGlobalPlay')?.addEventListener('click', () => {
            if (masterState.isPlaying) {
                if (masterState.currentAudio) masterState.currentAudio.pause();
                if ('speechSynthesis' in window) window.speechSynthesis.cancel();
                updatePlayerBarStatus(false);
            } else {
                playSentenceAt(masterState.currentSentenceIdx);
            }
        });

        document.getElementById('btnGlobalPrev')?.addEventListener('click', () => {
            if (masterState.currentSentenceIdx > 0) playSentenceAt(masterState.currentSentenceIdx - 1);
        });
        document.getElementById('btnGlobalNext')?.addEventListener('click', () => {
            if (state.sentences && masterState.currentSentenceIdx + 1 < state.sentences.length) {
                playSentenceAt(masterState.currentSentenceIdx + 1);
            }
        });
        document.getElementById('btnGlobalLoop')?.addEventListener('click', (e) => {
            masterState.isLoop = !masterState.isLoop;
            e.currentTarget.classList.toggle('active', masterState.isLoop);
            showToast(masterState.isLoop ? '已開啟單句循環' : '已關閉單句循環');
        });
        document.getElementById('btnGlobalAutoNext')?.addEventListener('click', (e) => {
            masterState.isAutoPlay = !masterState.isAutoPlay;
            e.currentTarget.classList.toggle('active', masterState.isAutoPlay);
            showToast(masterState.isAutoPlay ? '已開啟自動連播' : '已關閉自動連播');
        });

        document.getElementById('globalVoiceSelect')?.addEventListener('change', (e) => {
            masterState.voice = e.target.value;
            localStorage.setItem('master_voice', masterState.voice);
        });

        document.getElementById('globalRateSlider')?.addEventListener('input', (e) => {
            masterState.playbackRate = parseFloat(e.target.value);
            const lbl = document.getElementById('globalRateLabel');
            if (lbl) lbl.textContent = masterState.playbackRate.toFixed(2) + 'x';
            if (masterState.currentAudio) masterState.currentAudio.playbackRate = masterState.playbackRate;
        });

        // 監聽句子解析完成事件，自動同步至四大視圖
        const origRenderArticle = window.renderArticle;
        window.renderArticle = function() {
            if (typeof origRenderArticle === 'function') {
                origRenderArticle.apply(this, arguments);
            }
            // 同步渲染 Trancy 雙語
            renderTrancyStream();
            // 同步跟讀目標
            updateShadowingCard(0);
        };

        // 鍵盤快速鍵 (Space 播放, J 上一句, K 下一句)
        document.addEventListener('keydown', (e) => {
            if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;
            if (e.code === 'Space') {
                e.preventDefault();
                document.getElementById('btnGlobalPlay')?.click();
            } else if (e.key === 'j' || e.key === 'J') {
                document.getElementById('btnGlobalPrev')?.click();
            } else if (e.key === 'k' || e.key === 'K') {
                document.getElementById('btnGlobalNext')?.click();
            }
        });

    })();
    """

    # 注入 JS 到 </body> 前
    updated_html = updated_html.replace('</script>\n</body>', '</script>\n<script>\n' + master_js + '\n</script>\n</body>')

    out_file = os.path.join(root, "閱讀高手.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(updated_html)

    size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f"[OK] 成功產出獨立全方位大成 APP：{out_file} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    build()
