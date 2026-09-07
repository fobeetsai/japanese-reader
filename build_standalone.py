# -*- coding: utf-8 -*-
"""
日文閱讀助手 - 單一靜態網頁 (Standalone HTML) 產生器
包含：
1. 100% 漢字假名全標註 (整合 JLPT 單字庫 + 12,559 漢字音訓辭典)
2. 假名防遮蔽與字型排版最佳化 (充足行距、字距與防裁切)
3. 單字翻牌抽卡複習功能 (Vocabulary Flashcard Review)
4. 單字拆解表格附「中文翻譯」與「文型／詞性」
5. 941 條《絵でわかる日本語》文法庫與詳細抽屜
"""

import os
import json
import re

def build():
    print("[1/5] 載入 941 條文法資料庫...")
    with open("grammar_data.json", "r", encoding="utf-8") as f:
        grammar_data = json.load(f)

    print("[2/5] 載入並壓縮 JLPT 單字庫與全漢字讀音字典...")
    with open("jlpt_vocab_all.json", "r", encoding="utf-8") as f:
        raw_vocab = json.load(f)

    compact_vocab = {}
    for word, entries in raw_vocab.items():
        if entries and isinstance(entries, list):
            lvl = entries[0].get("level", 0)
            reading = entries[0].get("reading", "")
            compact_vocab[word] = [lvl, reading]

    with open("kanji_compact.json", "r", encoding="utf-8") as f:
        kanji_compact_str = f.read()

    with open("particle_data.json", "r", encoding="utf-8") as f:
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

    print("[3/5] 載入並注入最佳化樣式表...")
    with open("static/css/style.css", "r", encoding="utf-8") as f:
        css_content = f.read()

    # 針對排版加強：降低漢字字體至 1.15rem，行距加大至 3.1，保證假名完全不被遮擋
    enhanced_css = css_content + """
/* ==========================================================================
   漢字假名防遮擋與單字複習專用樣式
   ========================================================================== */
:root {
    --reader-font-size: 1.16rem;
    --reader-line-height: 3.1;
}

.article-content-box {
    padding: 2.4rem 2rem 2rem !important;
    overflow: visible !important;
    line-height: 3.1 !important;
}

.sentence-row {
    padding: 0.95rem 1.15rem 0.75rem 1.15rem !important;
    margin-bottom: 0.85rem !important;
    overflow: visible !important;
}

.sentence-jp-text {
    display: block !important;
    line-height: 3.1 !important;
    overflow: visible !important;
}

ruby {
    ruby-position: over !important;
    ruby-align: center !important;
    display: inline-block !important;
    text-align: center !important;
    line-height: 1 !important;
    margin: 0 1.5px !important;
    vertical-align: baseline !important;
    overflow: visible !important;
}

ruby rt {
    font-size: 0.62em !important;
    line-height: 1.2 !important;
    color: #dc2626 !important;
    font-weight: 700 !important;
    font-family: var(--font-jp) !important;
    display: block !important;
    text-align: center !important;
    margin-bottom: 0.32em !important;
    letter-spacing: 0 !important;
    user-select: none !important;
    transform: translateY(-2px) !important;
}

.selected-sentence-text {
    line-height: 3.0 !important;
    padding-top: 1.35rem !important;
    overflow: visible !important;
}

/* ==========================================================================
   日文原文顯示模式 (顯示 / 遮蔽自測 - 中日雙向翻譯練習)
   ========================================================================== */
body[data-jp-mode="mask"] .sentence-jp-text,
body[data-jp-mode="mask"] #selectedSentenceJp {
    filter: blur(7px) !important;
    opacity: 0.22 !important;
    user-select: none !important;
    cursor: pointer !important;
    transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1) !important;
    background: #e2e8f0 !important;
    border-radius: 6px !important;
    padding: 0.2rem 0.5rem !important;
}

[data-theme="dark"] body[data-jp-mode="mask"] .sentence-jp-text,
[data-theme="dark"] body[data-jp-mode="mask"] #selectedSentenceJp {
    background: #334155 !important;
}

body[data-jp-mode="mask"] .sentence-row:hover .sentence-jp-text,
body[data-jp-mode="mask"] .sentence-jp-text:hover,
body[data-jp-mode="mask"] .sentence-jp-text.revealed,
body[data-jp-mode="mask"] #selectedSentenceJp:hover,
body[data-jp-mode="mask"] #selectedSentenceJp.revealed {
    filter: none !important;
    opacity: 1 !important;
    background: transparent !important;
    user-select: text !important;
}

/* ==========================================================================
   繁體中文翻譯顯示模式 (顯示 / 隱藏 / 遮蔽自測)
   ========================================================================== */
body[data-trans-mode="hide"] .sentence-trans-row,
body[data-trans-mode="hide"] #selectedSentenceZh,
body[data-trans-mode="hide"] .word-trans-val {
    display: none !important;
}

body[data-trans-mode="mask"] .trans-text,
body[data-trans-mode="mask"] #selectedSentenceZh,
body[data-trans-mode="mask"] .word-trans-val {
    filter: blur(5px) !important;
    opacity: 0.22 !important;
    background: #cbd5e1 !important;
    color: transparent !important;
    border-radius: 4px !important;
    user-select: none !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    display: inline-block !important;
    padding: 1px 6px !important;
}

[data-theme="dark"] body[data-trans-mode="mask"] .trans-text,
[data-theme="dark"] body[data-trans-mode="mask"] #selectedSentenceZh,
[data-theme="dark"] body[data-trans-mode="mask"] .word-trans-val {
    background: #475569 !important;
}

body[data-trans-mode="mask"] .sentence-trans-row:hover .trans-text,
body[data-trans-mode="mask"] .trans-text:hover,
body[data-trans-mode="mask"] .trans-text.revealed,
body[data-trans-mode="mask"] #selectedSentenceZh:hover,
body[data-trans-mode="mask"] #selectedSentenceZh.revealed,
body[data-trans-mode="mask"] .word-trans-val:hover,
body[data-trans-mode="mask"] .word-trans-val.revealed {
    filter: none !important;
    opacity: 1 !important;
    background: transparent !important;
    color: inherit !important;
    user-select: text !important;
}
/* ==========================================================================
   漢字音讀與訓讀欄樣式
   ========================================================================== */
.kanji-readings-box {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    font-size: 0.82rem;
    line-height: 1.35;
}

.kanji-reading-item {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.3rem;
    background: var(--bg-sub);
    padding: 0.18rem 0.45rem;
    border-radius: 4px;
    border: 1px solid var(--border-color);
}

.kanji-char-badge {
    font-family: var(--font-jp);
    font-size: 1.05rem;
    font-weight: 800;
    color: var(--text-main);
    margin-right: 0.2rem;
}

.badge-on {
    background: #dbeafe;
    color: #1e40af;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.05rem 0.3rem;
    border-radius: 3px;
    letter-spacing: 0.5px;
}

[data-theme="dark"] .badge-on {
    background: #1e3a8a;
    color: #93c5fd;
}

.badge-kun {
    background: #d1fae5;
    color: #065f46;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.05rem 0.3rem;
    border-radius: 3px;
    letter-spacing: 0.5px;
}

[data-theme="dark"] .badge-kun {
    background: #064e3b;
    color: #6ee7b7;
}

.reading-val-on {
    font-family: var(--font-jp);
    color: #2563eb;
    font-weight: 600;
    margin-right: 0.25rem;
}

[data-theme="dark"] .reading-val-on {
    color: #60a5fa;
}

.reading-val-kun {
    font-family: var(--font-jp);
    color: #059669;
    font-weight: 600;
}

[data-theme="dark"] .reading-val-kun {
    color: #34d399;
}

/* 單字複習專用樣式 */
.review-flashcard {
    background: var(--bg-sub);
    border: 2px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 2.2rem 1.5rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.25s ease;
    min-height: 270px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 0.85rem;
    box-shadow: var(--shadow-sm);
    user-select: none;
}

.review-flashcard:hover {
    border-color: var(--primary);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

.review-word-front {
    font-size: 2.6rem;
    font-weight: 900;
    font-family: var(--font-jp);
    color: var(--text-main);
}

.review-flip-hint {
    font-size: 0.86rem;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.review-back-content {
    display: none;
    flex-direction: column;
    align-items: center;
    gap: 0.65rem;
    width: 100%;
    animation: fadeIn 0.25s ease;
}

.review-back-content.revealed {
    display: flex;
}

.review-word-reading {
    font-size: 1.65rem;
    color: #dc2626;
    font-weight: 800;
    font-family: var(--font-jp);
}

.review-word-trans {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-main);
}

.review-progress-bar-wrap {
    height: 6px;
    background: var(--bg-sub);
    border-radius: 3px;
    overflow: hidden;
    margin-top: 0.5rem;
}

.review-progress-bar {
    height: 100%;
    background: var(--primary);
    transition: width 0.3s ease;
}

.review-progress-text {
    font-size: 0.82rem;
    color: var(--text-muted);
    text-align: center;
}

.review-actions-bar {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    flex-wrap: wrap;
    border-top: 1px solid var(--border-color);
    padding-top: 1rem;
}

.btn-review-action {
    padding: 0.55rem 1rem;
    border-radius: var(--radius-sm);
    font-size: 0.88rem;
    font-weight: 700;
    cursor: pointer;
    border: 1px solid var(--border-color);
    background: var(--bg-card);
    color: var(--text-main);
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    transition: all 0.2s ease;
}

.btn-review-action:hover {
    border-color: var(--primary);
    color: var(--primary);
}

.btn-review-flip {
    background: var(--primary);
    color: white;
    border-color: var(--primary);
}

.btn-review-flip:hover {
    background: var(--primary-hover);
    color: white;
}

/* ==========================================================================
   文法句型例句與振假名防遮擋、完整展開樣式
   ========================================================================== */
.grammar-example-box {
    background: var(--bg-sub) !important;
    border-left: 3.5px solid #10b981 !important;
    padding: 0.8rem 1rem !important;
    border-radius: 0 8px 8px 0 !important;
    font-size: 0.96rem !important;
    font-family: var(--font-jp) !important;
    line-height: 2.3 !important;
    overflow: visible !important;
    word-break: break-word !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}

.grammar-example-box .example-jp-line {
    font-size: 0.98rem !important;
    font-weight: 500 !important;
    color: var(--text-main) !important;
    line-height: 2.3 !important;
    overflow: visible !important;
}

.grammar-example-box .example-trans-line {
    display: block !important;
    margin-top: 0.45rem !important;
    font-size: 0.86rem !important;
    color: var(--text-muted) !important;
    line-height: 1.55 !important;
    border-top: 1px dashed var(--border-color);
    padding-top: 0.35rem;
}

.grammar-example-box ruby {
    line-height: 1 !important;
    display: inline-block !important;
    margin: 0 1px !important;
}

.grammar-example-box ruby rt {
    font-size: 0.62em !important;
    line-height: 1.1 !important;
    color: #dc2626 !important;
    font-weight: 700 !important;
    display: block !important;
    margin-bottom: 0.25em !important;
}

/* ==========================================================================
   整句深度分析器原文與例句 假名標示遮蔽與隱藏功能
   ========================================================================== */
body[data-ruby-mode="hide"] ruby rt {
    display: none !important;
}

body[data-ruby-mode="mask"] ruby rt {
    filter: blur(4.5px) !important;
    opacity: 0.15 !important;
    background: #94a3b8 !important;
    border-radius: 3px !important;
    color: transparent !important;
    user-select: none !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

[data-theme="dark"] body[data-ruby-mode="mask"] ruby rt {
    background: #64748b !important;
}

/* 滑鼠懸停或點擊切換揭示 (Hover or Click to Reveal) */
body[data-ruby-mode="mask"] ruby:hover rt,
body[data-ruby-mode="mask"] ruby.revealed rt,
body[data-ruby-mode="mask"] .word-token:hover ruby rt,
body[data-ruby-mode="mask"] .word-token.revealed ruby rt,
body[data-ruby-mode="mask"] .sentence-row:hover ruby rt,
body[data-ruby-mode="mask"] .sentence-row.revealed ruby rt,
body[data-ruby-mode="mask"] #selectedSentenceJp:hover ruby rt,
body[data-ruby-mode="mask"] #selectedSentenceJp.revealed ruby rt,
body[data-ruby-mode="mask"] .grammar-example-box:hover ruby rt,
body[data-ruby-mode="mask"] .grammar-example-box.revealed ruby rt,
body[data-ruby-mode="mask"] .grammar-item-card:hover .grammar-example-box ruby rt,
body[data-ruby-mode="mask"] .drawer-box:hover ruby rt,
body[data-ruby-mode="mask"] .drawer-box.revealed ruby rt {
    filter: none !important;
    opacity: 1 !important;
    background: transparent !important;
    color: #dc2626 !important;
    user-select: text !important;
}

[data-theme="dark"] body[data-ruby-mode="mask"] ruby:hover rt,
[data-theme="dark"] body[data-ruby-mode="mask"] ruby.revealed rt,
[data-theme="dark"] body[data-ruby-mode="mask"] .grammar-example-box:hover ruby rt,
[data-theme="dark"] body[data-ruby-mode="mask"] #selectedSentenceJp:hover ruby rt {
    color: #fb7185 !important;
}

/* ==========================================================================
   助詞與文型階層遮蔽自測 (Hierarchical Grammar Masking Mode) 專屬樣式
   ========================================================================== */
.grammar-elem-token {
    transition: background 0.15s ease, color 0.15s ease;
    border-radius: 4px;
    padding: 0 3px;
    cursor: pointer;
    position: relative;
}
.grammar-elem-token:hover {
    background: rgba(245, 158, 11, 0.18);
    color: #d97706;
}

/* 多分類遮蔽自測狀態 (全部遮蔽 / 格助詞 / 副助詞 / 複合助詞 / 文型句型 / 單句強制遮蔽) */
body[data-grammar-mode="mask-all"] .grammar-elem-token:not(.revealed),
body[data-grammar-mode="mask-case"] .grammar-elem-token[data-category="case"]:not(.revealed),
body[data-grammar-mode="mask-adverbial"] .grammar-elem-token[data-category="adverbial"]:not(.revealed),
body[data-grammar-mode="mask-compound"] .grammar-elem-token[data-category="compound"]:not(.revealed),
body[data-grammar-mode="mask-sentence"] .grammar-elem-token[data-category="sentence"]:not(.revealed),
body[data-grammar-mode="mask-conjunctive"] .grammar-elem-token[data-category="conjunctive"]:not(.revealed),
.grammar-elem-token.force-masked:not(.revealed) {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-width: 2.4rem !important;
    height: 1.7rem !important;
    margin: 0 3px !important;
    padding: 0 0.45rem !important;
    border-radius: 6px !important;
    color: transparent !important;
    font-size: 0.88em !important;
    position: relative !important;
    cursor: pointer !important;
    vertical-align: middle !important;
    user-select: none !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* 各分類色彩風格 (遮蔽狀態) */
body[data-grammar-mode^="mask"] .grammar-elem-token[data-category="case"]:not(.revealed),
.grammar-elem-token.force-masked[data-category="case"]:not(.revealed) {
    background: linear-gradient(135deg, #fef3c7, #fde68a) !important;
    border: 1.8px dashed #d97706 !important;
}
body[data-grammar-mode^="mask"] .grammar-elem-token[data-category="adverbial"]:not(.revealed),
.grammar-elem-token.force-masked[data-category="adverbial"]:not(.revealed) {
    background: linear-gradient(135deg, #ede9fe, #ddd6fe) !important;
    border: 1.8px dashed #7c3aed !important;
}
body[data-grammar-mode^="mask"] .grammar-elem-token[data-category="compound"]:not(.revealed),
.grammar-elem-token.force-masked[data-category="compound"]:not(.revealed) {
    background: linear-gradient(135deg, #d1fae5, #a7f3d0) !important;
    border: 1.8px dashed #059669 !important;
}
body[data-grammar-mode^="mask"] .grammar-elem-token[data-category="sentence"]:not(.revealed),
.grammar-elem-token.force-masked[data-category="sentence"]:not(.revealed) {
    background: linear-gradient(135deg, #ffe4e6, #fecdd3) !important;
    border: 1.8px dashed #e11d48 !important;
}
body[data-grammar-mode^="mask"] .grammar-elem-token[data-category="conjunctive"]:not(.revealed),
.grammar-elem-token.force-masked[data-category="conjunctive"]:not(.revealed) {
    background: linear-gradient(135deg, #e0f2fe, #bae6fd) !important;
    border: 1.8px dashed #0284c7 !important;
}

/* 遮蔽提示文字 (透過 data-mask-placeholder 動態設置) */
body[data-grammar-mode="mask-all"] .grammar-elem-token:not(.revealed)::before,
body[data-grammar-mode="mask-case"] .grammar-elem-token[data-category="case"]:not(.revealed)::before,
body[data-grammar-mode="mask-adverbial"] .grammar-elem-token[data-category="adverbial"]:not(.revealed)::before,
body[data-grammar-mode="mask-compound"] .grammar-elem-token[data-category="compound"]:not(.revealed)::before,
body[data-grammar-mode="mask-sentence"] .grammar-elem-token[data-category="sentence"]:not(.revealed)::before,
body[data-grammar-mode="mask-conjunctive"] .grammar-elem-token[data-category="conjunctive"]:not(.revealed)::before,
.grammar-elem-token.force-masked:not(.revealed)::before {
    content: attr(data-mask-placeholder) !important;
    position: absolute !important;
    left: 50% !important;
    top: 50% !important;
    transform: translate(-50%, -50%) !important;
    font-size: 0.72rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.5px !important;
    white-space: nowrap !important;
}

.grammar-elem-token[data-category="case"]::before { color: #b45309 !important; }
.grammar-elem-token[data-category="adverbial"]::before { color: #6d28d9 !important; }
.grammar-elem-token[data-category="compound"]::before { color: #047857 !important; }
.grammar-elem-token[data-category="sentence"]::before { color: #be123c !important; }
.grammar-elem-token[data-category="conjunctive"]::before { color: #0369a1 !important; }

/* 暗色主題適配 (遮蔽狀態) */
[data-theme="dark"] body[data-grammar-mode^="mask"] .grammar-elem-token[data-category="case"]:not(.revealed),
[data-theme="dark"] .grammar-elem-token.force-masked[data-category="case"]:not(.revealed) {
    background: linear-gradient(135deg, #78350f, #92400e) !important;
    border-color: #f59e0b !important;
}
[data-theme="dark"] body[data-grammar-mode^="mask"] .grammar-elem-token[data-category="adverbial"]:not(.revealed),
[data-theme="dark"] .grammar-elem-token.force-masked[data-category="adverbial"]:not(.revealed) {
    background: linear-gradient(135deg, #4c1d95, #5b21b6) !important;
    border-color: #a78bfa !important;
}
[data-theme="dark"] body[data-grammar-mode^="mask"] .grammar-elem-token[data-category="compound"]:not(.revealed),
[data-theme="dark"] .grammar-elem-token.force-masked[data-category="compound"]:not(.revealed) {
    background: linear-gradient(135deg, #064e3b, #065f46) !important;
    border-color: #34d399 !important;
}
[data-theme="dark"] body[data-grammar-mode^="mask"] .grammar-elem-token[data-category="sentence"]:not(.revealed),
[data-theme="dark"] .grammar-elem-token.force-masked[data-category="sentence"]:not(.revealed) {
    background: linear-gradient(135deg, #881337, #9f1239) !important;
    border-color: #fb7185 !important;
}
[data-theme="dark"] body[data-grammar-mode^="mask"] .grammar-elem-token[data-category="conjunctive"]:not(.revealed),
[data-theme="dark"] .grammar-elem-token.force-masked[data-category="conjunctive"]:not(.revealed) {
    background: linear-gradient(135deg, #0c4a6e, #075985) !important;
    border-color: #38bdf8 !important;
}

[data-theme="dark"] .grammar-elem-token[data-category="case"]::before { color: #fde68a !important; }
[data-theme="dark"] .grammar-elem-token[data-category="adverbial"]::before { color: #ddd6fe !important; }
[data-theme="dark"] .grammar-elem-token[data-category="compound"]::before { color: #a7f3d0 !important; }
[data-theme="dark"] .grammar-elem-token[data-category="sentence"]::before { color: #fecdd3 !important; }
[data-theme="dark"] .grammar-elem-token[data-category="conjunctive"]::before { color: #bae6fd !important; }

/* 懸浮揭示或點擊解開狀態 (文字恢復可見、綠色亮起) */
body[data-grammar-mode^="mask"] .grammar-elem-token:hover,
body[data-grammar-mode^="mask"] .grammar-elem-token.revealed,
.grammar-elem-token.force-masked:hover,
.grammar-elem-token.force-masked.revealed {
    display: inline-flex !important;
    background: #dcfce7 !important;
    border: 1.8px solid #16a34a !important;
    color: #15803d !important;
    font-weight: 800 !important;
    transform: scale(1.04) !important;
}

[data-theme="dark"] body[data-grammar-mode^="mask"] .grammar-elem-token:hover,
[data-theme="dark"] body[data-grammar-mode^="mask"] .grammar-elem-token.revealed,
[data-theme="dark"] .grammar-elem-token.force-masked:hover,
[data-theme="dark"] .grammar-elem-token.force-masked.revealed {
    background: #064e3b !important;
    border-color: #34d399 !important;
    color: #a7f3d0 !important;
}

body[data-grammar-mode^="mask"] .grammar-elem-token:hover::before,
body[data-grammar-mode^="mask"] .grammar-elem-token.revealed::before,
.grammar-elem-token.force-masked:hover::before,
.grammar-elem-token.force-masked.revealed::before {
    display: none !important;
}

/* 分類徽章 (Cat Badges) */
.cat-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.1rem 0.45rem;
    border-radius: 4px;
    letter-spacing: 0.5px;
    margin-left: 0.25rem;
}
.cat-badge-case { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
.cat-badge-adverbial { background: #ede9fe; color: #6d28d9; border: 1px solid #ddd6fe; }
.cat-badge-compound { background: #d1fae5; color: #047857; border: 1px solid #a7f3d0; }
.cat-badge-sentence { background: #ffe4e6; color: #be123c; border: 1px solid #fecdd3; }
.cat-badge-conjunctive { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }

[data-theme="dark"] .cat-badge-case { background: #78350f; color: #fde68a; border-color: #92400e; }
[data-theme="dark"] .cat-badge-adverbial { background: #4c1d95; color: #ddd6fe; border-color: #5b21b6; }
[data-theme="dark"] .cat-badge-compound { background: #064e3b; color: #a7f3d0; border-color: #065f46; }
[data-theme="dark"] .cat-badge-sentence { background: #881337; color: #fecdd3; border-color: #9f1239; }
[data-theme="dark"] .cat-badge-conjunctive { background: #0c4a6e; color: #bae6fd; border-color: #075985; }

/* ==========================================================================
   全篇助詞測驗挑戰彈窗樣式
   ========================================================================== */
.quiz-status-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
    font-size: 0.88rem;
    font-weight: 700;
}

.quiz-score-badge {
    color: #d97706;
    background: #fef3c7;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
}

[data-theme="dark"] .quiz-score-badge {
    background: #78350f;
    color: #fde68a;
}

.quiz-sentence-box {
    background: var(--bg-sub);
    border: 2px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 1.3rem 1.15rem;
    font-size: 1.2rem;
    font-family: var(--font-jp);
    line-height: 2.3;
    text-align: center;
    margin-bottom: 1rem;
    word-break: break-word;
}

.quiz-blank-slot {
    display: inline-block;
    min-width: 3.2rem;
    height: 2rem;
    line-height: 2rem;
    border-bottom: 3px solid #f59e0b;
    background: rgba(245, 158, 11, 0.14);
    color: #d97706;
    font-weight: 800;
    text-align: center;
    border-radius: 4px 4px 0 0;
    padding: 0 0.5rem;
    margin: 0 4px;
    vertical-align: middle;
}

.quiz-instruction {
    font-size: 0.86rem;
    color: var(--text-muted);
    margin-bottom: 0.6rem;
    text-align: center;
}

.quiz-options-container {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    margin-bottom: 1rem;
}

@media (max-width: 500px) {
    .quiz-options-container {
        grid-template-columns: 1fr;
    }
}

.btn-quiz-option {
    padding: 0.85rem 1rem;
    border-radius: var(--radius-md);
    border: 2px solid var(--border-color);
    background: var(--bg-card);
    color: var(--text-main);
    font-size: 1.15rem;
    font-weight: 700;
    font-family: var(--font-jp);
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.btn-quiz-option:hover {
    border-color: #f59e0b;
    background: #fef3c7;
    color: #b45309;
    transform: translateY(-1px);
}

[data-theme="dark"] .btn-quiz-option:hover {
    background: #78350f;
    color: #fde68a;
}

.btn-quiz-option.correct {
    border-color: #10b981 !important;
    background: #d1fae5 !important;
    color: #065f46 !important;
}

[data-theme="dark"] .btn-quiz-option.correct {
    background: #064e3b !important;
    color: #6ee7b7 !important;
}

.btn-quiz-option.wrong {
    border-color: #ef4444 !important;
    background: #fee2e2 !important;
    color: #991b1b !important;
}

.quiz-feedback-card {
    background: var(--bg-sub);
    border-radius: var(--radius-md);
    padding: 1rem 1.15rem;
    margin-top: 1rem;
    border-left: 4px solid #10b981;
    animation: fadeIn 0.25s ease;
}

.btn-quiz-accent {
    background: linear-gradient(135deg, #f59e0b, #d97706) !important;
    color: white !important;
    border: none !important;
    font-weight: 700 !important;
}
.btn-quiz-accent:hover {
    filter: brightness(1.1) !important;
}
"""

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
{enhanced_css}
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
                        <span class="version-tag">v2.1 漢字全假名・單字複習版</span>
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
                <!-- Japanese Original Mode Switch (中日雙向翻譯練習) -->
                <div class="control-pill-group" title="日文原文顯示模式 (中日雙向翻譯自測練習)">
                    <span class="group-label"><i class="fa-solid fa-file-lines"></i> 原文:</span>
                    <button class="pill-btn active" id="btnJpShow" data-mode="show" title="正常顯示日文原文">顯示</button>
                    <button class="pill-btn" id="btnJpMask" data-mode="mask" title="【中翻日練習模式】日文原文預設遮蔽模糊，看中文練習翻譯，游標移過或點擊揭示">遮蔽自測</button>
                </div>

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

                <!-- Particle Mode Switch (助詞遮蔽測驗) -->
                <!-- Particle & Grammar Masking Mode Switch (階層遮蔽自測) -->
                <!-- Particle & Grammar Masking Mode Switch (階層遮蔽自測) -->
                <div class="control-pill-group" title="助詞與文型階層遮蔽自測模式：可按格助詞、副助詞、複合助詞、文型句型進行單項或全文挖空自測">
                    <span class="group-label"><i class="fa-solid fa-shapes"></i> 語法自測:</span>
                    <button class="pill-btn active" id="btnGrammarShow" data-mode="show" title="正常顯示所有助詞與文型">顯示</button>
                    <button class="pill-btn" id="btnGrammarMaskAll" data-mode="mask-all" title="【全部遮蔽】遮蔽全文所有格助詞、副助詞、複合助詞與文型">全部遮蔽</button>
                    <button class="pill-btn" id="btnGrammarMaskCase" data-mode="mask-case" title="【格助詞遮蔽】僅遮蔽 が、を、に、で、へ、と 等格助詞">格助詞</button>
                    <button class="pill-btn" id="btnGrammarMaskAdverbial" data-mode="mask-adverbial" title="【副助詞遮蔽】僅遮蔽 は、も、ばかり、だけ、さえ 等副助詞與係助詞">副助詞</button>
                    <button class="pill-btn" id="btnGrammarMaskCompound" data-mode="mask-compound" title="【複合助詞遮蔽】僅遮蔽 について、に対して、として、に関して 等複合助詞">複合助詞</button>
                    <button class="pill-btn" id="btnGrammarMaskSentence" data-mode="mask-sentence" title="【文型句型遮蔽】僅遮蔽 ながらも、に伴い、あげく、一方だ 等單純文型句型">文型句型</button>
                    <button id="btnParticleShow" style="display:none;"></button>
                    <button id="btnParticleMask" style="display:none;"></button>
                </div>

                <!-- Translation Mode Switch -->
                <div class="control-pill-group" title="中文翻譯顯示模式">
                    <span class="group-label"><i class="fa-solid fa-language"></i> 翻譯:</span>
                    <button class="pill-btn active" id="btnTransShow" data-mode="show" title="全文顯示繁體中文翻譯對照">顯示</button>
                    <button class="pill-btn" id="btnTransHide" data-mode="hide" title="完全隱藏中文翻譯，專注日文沉浸閱讀">隱藏</button>
                    <button class="pill-btn" id="btnTransMask" data-mode="mask" title="【遮蔽測驗模式】中文預設遮蔽模糊，滑鼠懸浮或點擊即可揭示">遮蔽自測</button>
                </div>

                <!-- Action Buttons -->
                <div class="header-actions">
                    <button class="action-btn" id="btnOpenParticleQuizTop" title="開啟全篇日文助詞測驗挑戰與換句話說特訓">
                        <i class="fa-solid fa-puzzle-piece text-amber-500"></i>
                        <span>助詞特訓</span>
                    </button>
                    <button class="action-btn" id="btnWordReview" title="進入單字翻牌抽卡複習模式">
                        <i class="fa-solid fa-graduation-cap text-indigo-500"></i>
                        <span>單字複習</span>
                    </button>
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
                <h3>正在進行日語形態素分詞、全漢字假名標註與 941 文型比對...</h3>
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
                            <button class="tool-btn btn-quiz-accent" id="btnOpenParticleQuiz" title="針對當前文章/網頁，啟動全篇助詞測驗與換句話說挑戰">
                                <i class="fa-solid fa-puzzle-piece"></i> 助詞挑戰
                            </button>
                            <button class="tool-btn" id="btnFontDecr" title="縮小漢字字體 (利於觀看假名)"><i class="fa-solid fa-minus"></i> A</button>
                            <button class="tool-btn" id="btnFontIncr" title="放大漢字字體"><i class="fa-solid fa-plus"></i> A</button>
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
                            <div class="selected-sentence-text" id="selectedSentenceJp" onclick="this.classList.toggle('revealed')" title="點擊切換揭示/遮蔽">
                                點擊左側文章中任意句子，此處將即時展開整句結構、單字辭書形與 941 文法精解！
                            </div>
                        </div>

                        <!-- Sentence Translation -->
                        <div class="analyzer-section">
                            <div class="section-label">
                                <span><i class="fa-solid fa-language"></i> 繁體中文翻譯</span>
                            </div>
                            <div class="selected-sentence-trans" id="selectedSentenceZh" onclick="this.classList.toggle('revealed')" title="點擊切換揭示/遮蔽">
                                暫無翻譯
                            </div>
                        </div>

                        <!-- Particle Analysis & Paraphrase Lab (助詞運用與代用換句話說) -->
                        <div class="analyzer-section particle-analyzer-section">
                            <div class="section-label">
                                <span><i class="fa-solid fa-shapes text-amber-500"></i> 本句助詞運用與代用換句話說 (<strong id="sentenceParticleCount">0</strong>)</span>
                                <button class="btn-audio" id="btnMaskSentenceParticles" title="切換遮蔽本句所有助詞進行即時填空練習">
                                    <i class="fa-solid fa-eye-slash"></i> 遮蔽本句助詞
                                </button>
                            </div>
                            <div class="sentence-particles-list" id="sentenceParticlesList">
                                <div class="empty-hint">本句未偵測到特殊格助詞或副助詞</div>
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
                                <span><i class="fa-solid fa-table-list"></i> 本句單字拆解 (<strong id="sentenceWordCount">0</strong>)</span>
                            </div>
                            <div class="words-table-wrap">
                                <table class="words-breakdown-table">
                                    <thead>
                                        <tr>
                                            <th style="min-width:80px;">單字 (辭書形)</th>
                                            <th style="min-width:68px;">讀音</th>
                                            <th style="min-width:150px;">漢字 (音讀／訓讀)</th>
                                            <th style="min-width:52px;">級數</th>
                                            <th style="min-width:95px;">中文翻譯</th>
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

    <!-- Floating Particle Quick Quiz Popover (點擊助詞隨堂測驗與代用換句話說) -->
    <div class="particle-popover" id="particlePopover" style="display: none;">
        <button class="popover-close-btn" onclick="closeParticlePopover()"><i class="fa-solid fa-xmark"></i></button>
        <div class="popover-header">
            <div class="popover-word-title" id="popoverParticleTitle">助詞測驗</div>
            <span class="particle-role-badge" id="popoverParticleRole">格助詞</span>
        </div>
        <div class="popover-quiz-context" id="popoverParticleContext">
            <!-- 語境挖空 -->
        </div>
        <div class="popover-options-grid" id="popoverParticleOptions">
            <!-- 4選項按鈕 -->
        </div>
        <div id="popoverParticleFeedback" style="display:none; margin-top:0.6rem;">
            <!-- 回饋與解析 -->
        </div>
        <div id="popoverParticleSubstitutes" style="display:none; margin-top:0.6rem;">
            <!-- 代用文型推薦 -->
        </div>
    </div>

    <!-- Particle Quiz Challenge Modal (全篇助詞測驗挑戰與換句話說特訓) -->
    <!-- Particle & Grammar Quiz Challenge Modal (全篇助詞與文型階層特訓挑戰) -->
    <div class="modal-overlay" id="particleQuizModal">
        <div class="modal-container" style="max-width: 680px;">
            <div class="modal-header">
                <h3><i class="fa-solid fa-puzzle-piece text-amber-500"></i> 全篇助詞與文型階層特訓挑戰</h3>
                <button class="modal-close-btn" onclick="closeParticleQuizModal()"><i class="fa-solid fa-xmark"></i></button>
            </div>

            <!-- 分類篩選頁籤 (格助詞 / 副助詞 / 複合助詞 / 文型句型) -->
            <!-- 分類篩選頁籤 (格助詞 / 副助詞 / 複合助詞 / 文型句型) -->
            <div class="notebook-tabs" style="margin-bottom:0.75rem;">
                <button class="notebook-tab-btn active" id="btnQuizFilterAll" onclick="setQuizCategoryFilter('all')">全部 (<span id="quizCountAll">0</span>)</button>
                <button class="notebook-tab-btn" id="btnQuizFilterCase" onclick="setQuizCategoryFilter('case')">格助詞 (<span id="quizCountCase">0</span>)</button>
                <button class="notebook-tab-btn" id="btnQuizFilterAdverbial" onclick="setQuizCategoryFilter('adverbial')">副助詞 (<span id="quizCountAdverbial">0</span>)</button>
                <button class="notebook-tab-btn" id="btnQuizFilterCompound" onclick="setQuizCategoryFilter('compound')">複合助詞 (<span id="quizCountCompound">0</span>)</button>
                <button class="notebook-tab-btn" id="btnQuizFilterSentence" onclick="setQuizCategoryFilter('sentence')">文型句型 (<span id="quizCountSentence">0</span>)</button>
            </div>

            <div class="quiz-status-bar">
                <div class="quiz-counter" id="quizCounterText">第 1 / 10 題</div>
                <div class="quiz-score-badge" id="quizScoreText"><i class="fa-solid fa-award"></i> 答對：0 題</div>
            </div>

            <div class="review-progress-bar-wrap">
                <div class="review-progress-bar" id="quizProgressBar" style="width: 0%; background: #f59e0b;"></div>
            </div>

            <div class="quiz-question-card" id="quizQuestionCard">
                <div class="quiz-sentence-box" id="quizSentenceDisplay">
                    <!-- 挖空題目 -->
                </div>
                <div class="quiz-instruction">請依句意、語境與結構，點選最適合的語法：</div>
                <div class="quiz-options-container" id="quizOptionsContainer">
                    <!-- 選項 -->
                </div>
                <div class="quiz-feedback-card" id="quizFeedbackCard" style="display: none;">
                    <!-- 詳解與換句話說推薦 -->
                </div>
            </div>

            <div class="review-actions-bar">
                <button class="btn-review-action" id="btnQuizPrev" onclick="navQuiz(-1)" title="上一題 (←)">
                    <i class="fa-solid fa-chevron-left"></i> 上一題
                </button>
                <button class="btn-review-action" id="btnQuizReveal" onclick="revealCurrentQuizAnswer()" title="揭示答案與換句話說">
                    <i class="fa-solid fa-lightbulb"></i> 揭示解析
                </button>
                <button class="btn-review-action" id="btnQuizAudio" onclick="speakQuizSentence()" title="朗讀本句">
                    <i class="fa-solid fa-volume-high"></i> 發音
                </button>
                <button class="btn-review-action" id="btnQuizNext" onclick="navQuiz(1)" title="下一題 (→)">
                    下一題 <i class="fa-solid fa-chevron-right"></i>
                </button>
            </div>
        </div>
    </div>

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

    <!-- Vocabulary Review Flashcard Modal (單字翻牌抽卡複習) -->
    <div class="modal-overlay" id="reviewModal">
        <div class="modal-container" style="max-width: 620px;">
            <div class="modal-header">
                <h3><i class="fa-solid fa-graduation-cap text-indigo-500"></i> 單字翻牌抽卡複習</h3>
                <button class="modal-close-btn" onclick="closeReviewModal()"><i class="fa-solid fa-xmark"></i></button>
            </div>

            <div class="notebook-tabs">
                <button class="notebook-tab-btn active" id="tabReviewArticleBtn" onclick="switchReviewSource('article')">
                    本篇閱讀單字 (<span id="reviewArticleWordCount">0</span>)
                </button>
                <button class="notebook-tab-btn" id="tabReviewNotebookBtn" onclick="switchReviewSource('notebook')">
                    生詞本收藏 (<span id="reviewNotebookWordCount">0</span>)
                </button>
            </div>

            <div class="review-flashcard" id="reviewCard" onclick="flipReviewCard()">
                <span class="badge-jlpt" id="reviewCardLevel">N3</span>
                <div class="review-word-front" id="reviewCardWord">単語</div>
                <div class="review-flip-hint" id="reviewFlipHint">
                    <i class="fa-solid fa-hand-pointer"></i> 點擊卡片翻牌看讀音與中文
                </div>
                
                <div class="review-back-content" id="reviewBackContent">
                    <div class="review-word-reading" id="reviewCardReading">たんご</div>
                    <div class="review-word-trans" id="reviewCardTrans">單字釋義</div>
                </div>
            </div>

            <div class="review-progress-bar-wrap">
                <div class="review-progress-bar" id="reviewProgressBar" style="width: 0%;"></div>
            </div>
            <div class="review-progress-text" id="reviewProgressText">進度：0 / 0</div>

            <div class="review-actions-bar">
                <button class="btn-review-action" id="btnReviewPrev" onclick="navReview(-1)" title="上一張 (快速鍵 ←)">
                    <i class="fa-solid fa-chevron-left"></i> 上一張
                </button>
                <button class="btn-review-action btn-review-flip" onclick="flipReviewCard()" title="翻牌揭示 (空白鍵 Space)">
                    <i class="fa-solid fa-rotate"></i> 翻牌揭示
                </button>
                <button class="btn-review-action" id="btnReviewAudio" onclick="speakReviewCurrentWord()" title="播放發音">
                    <i class="fa-solid fa-volume-high"></i> 發音
                </button>
                <button class="btn-review-action" id="btnReviewNext" onclick="navReview(1)" title="下一張 (快速鍵 →)">
                    下一張 <i class="fa-solid fa-chevron-right"></i>
                </button>
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
         內建 941 條文法資料庫、8,138 JLPT 單字庫與 12,559 漢字全讀音字典
         ========================================================================== -->
    <script>
        // 941 條《絵でわかる日本語》文法庫
        const GRAMMAR_DATA = {grammar_json_str};

        // 24 組日文助詞代用與換句話說知識庫
        const PARTICLE_DATA = {particle_json_str};
                const CATEGORY_MAP = {{
            '格助詞': {{ code: 'case', name: '格助詞', placeholder: '？格助' }},
            '副助詞': {{ code: 'adverbial', name: '副助詞', placeholder: '？副助' }},
            '複合助詞': {{ code: 'compound', name: '複合助詞', placeholder: '？複合' }},
            '文型': {{ code: 'sentence', name: '文型句型', placeholder: '？文型' }},
            '接續助詞': {{ code: 'conjunctive', name: '接續助詞', placeholder: '？接續' }}
        }};

        const SPECIAL_GRAMMAR_PATTERNS = {special_grammar_json};
        const COMPOUND_PARTICLES = {compound_particles_json};
        const ADVERBIAL_PARTICLES = {adverbial_particles_json};
        const CONJUNCTIVE_PARTICLES = {conjunctive_particles_json};
        const CASE_PARTICLES = {case_particles_json};

        // 8,138 筆 JLPT 單字庫
        const JLPT_VOCAB = {vocab_json_str};

        // 12,559 漢字音訓全讀音字典: {{ "漢": ["オン (音)", "クン幹 (訓幹)", "クン全 (訓全)"] }}
        const KANJI_DICT = {kanji_compact_str};

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
         純前端形態素分詞、100% 漢字假名生成、941文型匹配與 Google 翻譯
         ========================================================================== -->
    <script>
        const KANJI_REGEX = /[\\u4e00-\\u9faf]/;
        const KANA_REGEX = /[\\u3040-\\u309f\\u30a0-\\u30ff]/;

        function kataToHira(str) {{
            if (!str) return '';
            return str.replace(/[\\u30a1-\\u30f6]/g, c => String.fromCharCode(c.charCodeAt(0) - 0x60));
        }}

        // 查詢單個漢字的讀音 (優先音讀或訓讀)
        function getSingleKanjiReading(char, isCompound = false) {{
            const entry = KANJI_DICT[char];
            if (!entry) return '';
            const [on, kunStem] = entry;
            if (isCompound) {{
                return on || kunStem || '';
            }}
            return kunStem || on || '';
        }}

        // 取得單字之漢字音讀與訓讀對照標籤
        function getKanjiReadingsHtml(word) {{
            if (!word) return '<span style="color:var(--text-muted);">-</span>';
            const kanjis = [];
            for (let i = 0; i < word.length; i++) {{
                const ch = word[i];
                if (KANJI_REGEX.test(ch) && !kanjis.includes(ch)) {{
                    kanjis.push(ch);
                }}
            }}
            if (kanjis.length === 0) {{
                return '<span style="color:var(--text-muted);font-size:0.8rem;">- (無漢字)</span>';
            }}
            let html = '<div class="kanji-readings-box">';
            kanjis.forEach(ch => {{
                const entry = KANJI_DICT[ch];
                if (entry) {{
                    const onStr = kataToHira(entry[2] || '-');
                    const kunStr = kataToHira(entry[3] || '-');
                    html += `
                        <div class="kanji-reading-item">
                            <span class="kanji-char-badge">${{ch}}</span>
                            <span class="badge-on">音</span><span class="reading-val-on">${{escapeHtml(onStr)}}</span>
                            <span class="badge-kun">訓</span><span class="reading-val-kun">${{escapeHtml(kunStr)}}</span>
                        </div>
                    `;
                }} else {{
                    html += `
                        <div class="kanji-reading-item">
                            <span class="kanji-char-badge">${{ch}}</span>
                            <span style="color:var(--text-muted);">-</span>
                        </div>
                    `;
                }}
            }});
            html += '</div>';
            return html;
        }}

        // 生成 Ruby HTML 標籤
        function createRubyHtml(surface, readingHira) {{
            if (!readingHira || !KANJI_REGEX.test(surface)) return surface;
            
            // 全漢字情況
            if (/^[\\u4e00-\\u9faf]+$/.test(surface)) {{
                return `<ruby>${{surface}}<rt>${{readingHira}}</rt></ruby>`;
            }}

            // 尋找尾部共同假名
            let sLen = 0;
            while (sLen < surface.length && sLen < readingHira.length &&
                   surface[surface.length - 1 - sLen] === readingHira[readingHira.length - 1 - sLen]) {{
                sLen++;
            }}

            // 尋找頭部共同假名
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

            COMPILED_GRAMMAR_PATTERNS.sort((a, b) => b.pattern.length - a.pattern.length);
        }}

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

                    if ((pat === 'ちゃ' || pat === 'じゃ') && endPos < sentenceText.length &&
                        (sentenceText[endPos] === 'ん' || sentenceText[endPos] === 'ン')) {{
                        startIdx = pos + 1;
                        continue;
                    }}

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

        // 動詞與形容詞活用還原到原型 (辭書形) 演算法
        function deinflectWord(word) {{
            if (!word || word.length < 2) return null;
            if (JLPT_VOCAB[word]) return word;

            const candidates = [];

            // 1. たい / たくない / たかった / たくなかった
            const taiForms = [
                ['たくなかった', 6], ['たかった', 4], ['たくない', 4], ['たい', 2]
            ];
            for (const [sfx, len] of taiForms) {{
                if (word.endsWith(sfx)) {{
                    const stem = word.slice(0, -len);
                    candidates.push(stem + 'る');
                    const iToU = {{'い':'う', 'き':'く', 'ぎ':'ぐ', 'し':'す', 'ち':'つ', 'に':'ぬ', 'び':'ぶ', 'み':'む', 'り':'る'}};
                    if (stem && iToU[stem.slice(-1)]) {{
                        candidates.push(stem.slice(0, -1) + iToU[stem.slice(-1)]);
                    }}
                    if (stem.endsWith('し')) {{
                        candidates.push(stem.slice(0, -1) + 'する');
                    }}
                    if (stem === '来' || stem === 'き') {{
                        candidates.push('来る');
                    }}
                }}
            }}

            // 2. ました / ません / ませんでした / ます
            const masuForms = [
                ['ませんでした', 6], ['ました', 3], ['ません', 3], ['ます', 2]
            ];
            for (const [sfx, len] of masuForms) {{
                if (word.endsWith(sfx)) {{
                    const stem = word.slice(0, -len);
                    candidates.push(stem + 'る');
                    const iToU = {{'い':'う', 'き':'く', 'ぎ':'ぐ', 'し':'す', 'ち':'つ', 'に':'ぬ', 'び':'ぶ', 'み':'む', 'り':'る'}};
                    if (stem && iToU[stem.slice(-1)]) {{
                        candidates.push(stem.slice(0, -1) + iToU[stem.slice(-1)]);
                    }}
                    if (stem.endsWith('し')) {{
                        candidates.push(stem.slice(0, -1) + 'する');
                    }}
                    if (stem === '来' || stem === 'き') {{
                        candidates.push('来る');
                    }}
                }}
            }}

            // 3. ている / ていた / ています / ていました / てる / てた
            const teiruForms = [
                ['ていました', 5], ['ています', 4], ['ていた', 3], ['ている', 3], ['てた', 2], ['てる', 2],
                ['でいました', 5], ['でいます', 4], ['でいた', 3], ['でいる', 3], ['でた', 2], ['でる', 2]
            ];
            for (const [sfx, len] of teiruForms) {{
                if (word.endsWith(sfx)) {{
                    const stem = word.slice(0, -len);
                    const aux = sfx.startsWith('て') ? 'て' : 'で';
                    const subRes = deinflectWord(stem + aux);
                    if (subRes) candidates.push(subRes);
                }}
            }}

            // 4. 促音便・イ音便・撥音便 (た / て / だ / で)
            if (word.endsWith('った') || word.endsWith('って')) {{
                const stem = word.slice(0, -2);
                candidates.push(stem + 'う', stem + 'つ', stem + 'る', stem + 'く');
            }}
            if (word.endsWith('いた') || word.endsWith('いて')) {{
                const stem = word.slice(0, -2);
                candidates.push(stem + 'く');
            }}
            if (word.endsWith('いだ') || word.endsWith('いで')) {{
                const stem = word.slice(0, -2);
                candidates.push(stem + 'ぐ');
            }}
            if (word.endsWith('した') || word.endsWith('して')) {{
                const stem = word.slice(0, -2);
                candidates.push(stem + 'す', stem + 'する');
            }}
            if (word.endsWith('んだ') || word.endsWith('んで')) {{
                const stem = word.slice(0, -2);
                candidates.push(stem + 'む', stem + 'ぶ', stem + 'ぬ');
            }}
            if (word.endsWith('た') || word.endsWith('て')) {{
                const stem = word.slice(0, -1);
                candidates.push(stem + 'る');
            }}

            // 5. 否定形 ない / なかった / なくて / ず
            const naiForms = [
                ['なかった', 4], ['なくて', 3], ['ない', 2], ['ず', 1]
            ];
            for (const [sfx, len] of naiForms) {{
                if (word.endsWith(sfx)) {{
                    const stem = word.slice(0, -len);
                    candidates.push(stem + 'る');
                    const aToU = {{'わ':'う', 'か':'く', 'が':'ぐ', 'さ':'す', 'た':'つ', 'な':'ぬ', 'ば':'ぶ', 'ま':'む', 'ら':'る'}};
                    if (stem && aToU[stem.slice(-1)]) {{
                        candidates.push(stem.slice(0, -1) + aToU[stem.slice(-1)]);
                    }}
                    if (stem.endsWith('し')) {{
                        candidates.push(stem.slice(0, -1) + 'する');
                    }}
                    if (stem === 'こ' || stem === '來' || stem === '来') {{
                        candidates.push('来る');
                    }}
                }}
            }}

            // 6. 受身・使役・可能形 (られる / させる / れる / せる)
            const passiveForms = [
                ['させられる', 5], ['される', 3], ['られる', 3], ['させる', 3], ['れる', 2], ['せる', 2]
            ];
            for (const [sfx, len] of passiveForms) {{
                if (word.endsWith(sfx)) {{
                    const stem = word.slice(0, -len);
                    candidates.push(stem + 'る');
                    const aToU = {{'わ':'う', 'か':'く', 'が':'ぐ', 'さ':'す', 'た':'つ', 'な':'ぬ', 'ば':'ぶ', 'ま':'む', 'ら':'る'}};
                    if (stem && aToU[stem.slice(-1)]) {{
                        candidates.push(stem.slice(0, -1) + aToU[stem.slice(-1)]);
                    }}
                    if (stem.endsWith('さ') || stem.endsWith('し')) {{
                        candidates.push(stem.slice(0, -1) + 'する');
                    }}
                }}
            }}

            // 7. 假定形 (ば)
            if (word.endsWith('ば')) {{
                const stem = word.slice(0, -1);
                if (stem.endsWith('れ')) {{
                    candidates.push(stem.slice(0, -1) + 'る');
                }}
                const eToU = {{'え':'う', 'け':'く', 'げ':'ぐ', 'せ':'す', 'て':'つ', 'ね':'ぬ', 'べ':'ぶ', 'め':'む', 'れ':'る'}};
                if (stem && eToU[stem.slice(-1)]) {{
                    candidates.push(stem.slice(0, -1) + eToU[stem.slice(-1)]);
                }}
                if (stem.endsWith('すれ')) {{
                    candidates.push(stem.slice(0, -2) + 'する');
                }}
            }}

            // 8. 意向形 (よう / おう)
            if (word.endsWith('よう')) {{
                candidates.push(word.slice(0, -2) + 'る');
            }}
            if (word.endsWith('う') && word.length >= 2) {{
                const stem = word.slice(0, -1);
                const oToU = {{'お':'う', 'こ':'く', 'ご':'ぐ', 'そ':'す', 'と':'つ', 'の':'ぬ', 'ぼ':'ぶ', 'も':'む', 'ろ':'る'}};
                if (stem && oToU[stem.slice(-1)]) {{
                    candidates.push(stem.slice(0, -1) + oToU[stem.slice(-1)]);
                }}
            }}

            // 9. 形容詞 (かった / くて / くない / くなかった / ければ)
            const adjForms = [
                ['くなかった', 5], ['ければ', 3], ['かった', 3], ['くない', 3], ['くて', 2]
            ];
            for (const [sfx, len] of adjForms) {{
                if (word.endsWith(sfx)) {{
                    const stem = word.slice(0, -len);
                    candidates.push(stem + 'い');
                }}
            }}

            // 10. 比對 JLPT 單字庫，命中即回傳原型！
            for (const c of candidates) {{
                if (JLPT_VOCAB[c]) {{
                    return c;
                }}
            }}

            return null;
        }}

        // 為動詞/形容詞活用形生成精準振假名
        function makeRubyHtmlForInflected(surface, baseWord, baseReading) {{
            if (!surface) return '';
            const hasKanji = KANJI_REGEX.test(surface);
            if (!hasKanji) return surface;

            let kanjiPrefixLen = 0;
            while (kanjiPrefixLen < surface.length && kanjiPrefixLen < baseWord.length &&
                   KANJI_REGEX.test(surface[kanjiPrefixLen]) && surface[kanjiPrefixLen] === baseWord[kanjiPrefixLen]) {{
                kanjiPrefixLen++;
            }}

            if (kanjiPrefixLen > 0) {{
                const kanjiPart = surface.slice(0, kanjiPrefixLen);
                const baseKanaSuffix = baseWord.slice(kanjiPrefixLen);
                const readingHira = kataToHira(baseReading);
                
                if (readingHira.endsWith(baseKanaSuffix)) {{
                    const kanjiReading = readingHira.slice(0, -baseKanaSuffix.length);
                    const surfaceSuffix = surface.slice(kanjiPrefixLen);
                    return `<ruby>${{kanjiPart}}<rt>${{kanjiReading}}</rt></ruby>${{surfaceSuffix}}`;
                }}
            }}

            let res = '';
            for (let k = 0; k < surface.length; k++) {{
                const ch = surface[k];
                if (KANJI_REGEX.test(ch)) {{
                    const r = getSingleKanjiReading(ch, false);
                    res += `<ruby>${{ch}}<rt>${{r || ''}}</rt></ruby>`;
                }} else {{
                    res += ch;
                }}
            }}
            return res;
        }}

        // 100% 保證所有漢字標示假名與動詞還原原型之分詞演算法
        function tokenizeSentence(text) {{
            // 階層分詞演算法：文型 -> 複合助詞 -> JLPT詞彙/動詞還原 -> 連續漢字 -> 片假名 -> 接續助詞/副助詞 -> 格助詞
            const spans = [];
            const textLen = text.length;

            function hasOverlap(start, end) {{
                return spans.some(s => !(end <= s.start || start >= s.end));
            }}

            // 1. 優先比對：941 特殊文型庫與單純句型 (Array of objects)
            if (typeof SPECIAL_GRAMMAR_PATTERNS !== 'undefined' && Array.isArray(SPECIAL_GRAMMAR_PATTERNS)) {{
                const specList = [...SPECIAL_GRAMMAR_PATTERNS].sort((a, b) => b.pattern.length - a.pattern.length);
                for (const item of specList) {{
                    const pat = item.pattern;
                    let idx = 0;
                    while (idx < textLen) {{
                        const pos = text.indexOf(pat, idx);
                        if (pos === -1) break;
                        const end = pos + pat.length;
                        if (!hasOverlap(pos, end)) {{
                            spans.push({{
                                start: pos,
                                end: end,
                                surface: pat,
                                type: '文型',
                                category: '文型',
                                meta: item,
                                grammar_id: item.grammar_id
                            }});
                        }}
                        idx = pos + 1;
                    }}
                }}
            }}

            // 2. 次優先比對：複合助詞 (Array of objects)
            if (typeof COMPOUND_PARTICLES !== 'undefined' && Array.isArray(COMPOUND_PARTICLES)) {{
                const compList = [...COMPOUND_PARTICLES].sort((a, b) => b.pattern.length - a.pattern.length);
                for (const item of compList) {{
                    const pat = item.pattern;
                    let idx = 0;
                    while (idx < textLen) {{
                        const pos = text.indexOf(pat, idx);
                        if (pos === -1) break;
                        const end = pos + pat.length;
                        if (!hasOverlap(pos, end)) {{
                            spans.push({{
                                start: pos,
                                end: end,
                                surface: pat,
                                type: '複合助詞',
                                category: '複合助詞',
                                meta: item,
                                grammar_id: item.grammar_id
                            }});
                        }}
                        idx = pos + 1;
                    }}
                }}
            }}

            // 排序保護區段
            spans.sort((a, b) => a.start - b.start);

            // 進行分詞組裝
            const tokens = [];
            let i = 0;
            const MAX_WORD_LEN = 8;

            while (i < textLen) {{
                // 檢查是否落在保護區間 (文型 / 複合助詞)
                const protectedSpan = spans.find(s => s.start === i);
                if (protectedSpan) {{
                    const s = protectedSpan.surface;
                    const cat = protectedSpan.category;
                    const meta = protectedSpan.meta || {{}};
                    const pData = (typeof PARTICLE_DATA !== 'undefined' && PARTICLE_DATA[s]) || {{}};
                    const placeholder = '？' + (cat === '複合助詞' ? '複合助' : cat);
                    tokens.push({{
                        surface: s,
                        base_form: s,
                        reading: s,
                        jlpt: meta.level || null,
                        is_kanji: false,
                        ruby_html: s,
                        pos: cat,
                        is_particle: true,
                        is_grammar_elem: true,
                        grammar_elem_info: {{
                            type: protectedSpan.type,
                            category: cat,
                            title: meta.title || pData.default_role || s,
                            role: meta.role || pData.default_role || cat,
                            desc: meta.desc || (pData.usages && pData.usages[0] && pData.usages[0].desc) || '',
                            grammar_id: protectedSpan.grammar_id,
                            mask_placeholder: placeholder,
                            distractors: meta.distractors || pData.distractors || ['は', 'が', 'を', 'に', 'で'],
                            pData: pData
                        }}
                    }});
                    i = protectedSpan.end;
                    continue;
                }}

                // 1. JLPT 單字庫長詞比對或動詞原型還原 (8 down to 2)
                let matched = false;
                const limit = Math.min(MAX_WORD_LEN, textLen - i);
                for (let len = limit; len >= 2; len--) {{
                    const sub = text.substring(i, i + len);

                    // A. 直接命中單字庫
                    if (JLPT_VOCAB && JLPT_VOCAB[sub]) {{
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
                            pos: '單字',
                            is_particle: false
                        }});
                        i += len;
                        matched = true;
                        break;
                    }}

                    // B. 動詞或形容詞活用形還原至原型
                    const baseWord = deinflectWord(sub);
                    if (baseWord && JLPT_VOCAB && JLPT_VOCAB[baseWord]) {{
                        const [lvlNum, baseReading] = JLPT_VOCAB[baseWord];
                        const baseReadingHira = kataToHira(baseReading);
                        const hasKanji = KANJI_REGEX.test(sub);
                        tokens.push({{
                            surface: sub,
                            base_form: baseWord,
                            reading: baseReadingHira,
                            jlpt: lvlNum ? `N${{lvlNum}}` : null,
                            is_kanji: hasKanji,
                            ruby_html: makeRubyHtmlForInflected(sub, baseWord, baseReading),
                            pos: baseWord.endsWith('い') ? '形容詞' : '動詞',
                            is_particle: false
                        }});
                        i += len;
                        matched = true;
                        break;
                    }}
                }}

                if (matched) continue;

                const char = text[i];

                // 2. 漢字區塊
                if (KANJI_REGEX.test(char)) {{
                    let kanjiRun = char;
                    let j = i + 1;
                    while (j < textLen && KANJI_REGEX.test(text[j])) {{
                        kanjiRun += text[j];
                        j++;
                    }}

                    if (JLPT_VOCAB && JLPT_VOCAB[kanjiRun]) {{
                        const [lvlNum, reading] = JLPT_VOCAB[kanjiRun];
                        const rHira = kataToHira(reading);
                        tokens.push({{
                            surface: kanjiRun,
                            base_form: kanjiRun,
                            reading: rHira,
                            jlpt: lvlNum ? `N${{lvlNum}}` : null,
                            is_kanji: true,
                            ruby_html: createRubyHtml(kanjiRun, rHira),
                            pos: '名詞'
                        }});
                        i = j;
                        continue;
                    }}

                    const isCompound = (kanjiRun.length > 1);
                    let rubyHtmlAcc = '';
                    let readingAcc = '';
                    for (let k = 0; k < kanjiRun.length; k++) {{
                        const kChar = kanjiRun[k];
                        const kReading = getSingleKanjiReading(kChar, isCompound);
                        if (kReading) {{
                            rubyHtmlAcc += `<ruby>${{kChar}}<rt>${{kReading}}</rt></ruby>`;
                            readingAcc += kReading;
                        }} else {{
                            rubyHtmlAcc += kChar;
                        }}
                    }}

                    tokens.push({{
                        surface: kanjiRun,
                        base_form: kanjiRun,
                        reading: readingAcc,
                        jlpt: null,
                        is_kanji: true,
                        ruby_html: rubyHtmlAcc,
                        pos: isCompound ? '名詞' : '單字'
                    }});
                    i = j;
                    continue;
                }}

                // 3. 片假名外來語
                if (/[\u30a0-\u30ff]/.test(char)) {{
                    let kataRun = char;
                    let j = i + 1;
                    while (j < textLen && /[\u30a0-\u30ffー]/.test(text[j])) {{
                        kataRun += text[j];
                        j++;
                    }}
                    tokens.push({{
                        surface: kataRun,
                        base_form: kataRun,
                        reading: kataToHira(kataRun),
                        jlpt: (JLPT_VOCAB && JLPT_VOCAB[kataRun]) ? `N${{JLPT_VOCAB[kataRun][0]}}` : null,
                        is_kanji: false,
                        ruby_html: kataRun,
                        pos: '外來語'
                    }});
                    i = j;
                    continue;
                }}

                // 3.5 常見助動詞與敬體詞尾 (避免 です、でした、である、ました 等被誤拆為助詞 で)
                const auxEndings = ['ではありません', 'ではない', 'ませんでした', 'でした', 'である', 'だった', 'ました', 'ません', 'です', 'ます'];
                let auxMatched = false;
                for (const aux of auxEndings) {{
                    if (text.startsWith(aux, i)) {{
                        tokens.push({{
                            surface: aux,
                            base_form: aux,
                            reading: aux,
                            jlpt: null,
                            is_kanji: false,
                            ruby_html: aux,
                            pos: '助動詞',
                            is_particle: false
                        }});
                        i += aux.length;
                        auxMatched = true;
                        break;
                    }}
                }}
                if (auxMatched) continue;

                // 4. 接續助詞 / 副助詞比對 (Array of objects)
                let pMatched = false;
                const checkGroups = [
                    [typeof CONJUNCTIVE_PARTICLES !== 'undefined' ? CONJUNCTIVE_PARTICLES : [], '接續助詞'],
                    [typeof ADVERBIAL_PARTICLES !== 'undefined' ? ADVERBIAL_PARTICLES : [], '副助詞']
                ];
                for (const [pList, catName] of checkGroups) {{
                    const sortedList = [...pList].sort((a, b) => b.pattern.length - a.pattern.length);
                    for (const item of sortedList) {{
                        const pk = item.pattern;
                        if (text.startsWith(pk, i)) {{
                            const pData = (typeof PARTICLE_DATA !== 'undefined' && PARTICLE_DATA[pk]) || {{}};
                            const placeholder = '？' + (catName === '接續助詞' ? '接續' : catName);
                            tokens.push({{
                                surface: pk,
                                base_form: pk,
                                reading: pk,
                                jlpt: item.level || null,
                                is_kanji: false,
                                ruby_html: pk,
                                pos: catName,
                                is_particle: true,
                                is_grammar_elem: true,
                                grammar_elem_info: {{
                                    type: catName,
                                    category: catName,
                                    title: item.title || pData.default_role || pk,
                                    role: item.role || pData.default_role || catName,
                                    desc: item.desc || (pData.usages && pData.usages[0] && pData.usages[0].desc) || '',
                                    grammar_id: item.grammar_id,
                                    mask_placeholder: placeholder,
                                    distractors: item.distractors || pData.distractors || ['は', 'が', 'を', 'に', 'で'],
                                    pData: pData
                                }}
                            }});
                            i += pk.length;
                            pMatched = true;
                            break;
                        }}
                    }}
                    if (pMatched) break;
                }}
                if (pMatched) continue;

                // 5. 格助詞比對 (が、を、に、で、へ、と、から、より、まで、の)
                const caseList = typeof CASE_PARTICLES !== 'undefined' ? [...CASE_PARTICLES].sort((a, b) => b.pattern.length - a.pattern.length) : [];
                let cMatched = false;
                for (const item of caseList) {{
                    const ck = item.pattern;
                    if (text.startsWith(ck, i)) {{
                        const pData = (typeof PARTICLE_DATA !== 'undefined' && PARTICLE_DATA[ck]) || {{}};
                        tokens.push({{
                            surface: ck,
                            base_form: ck,
                            reading: ck,
                            jlpt: null,
                            is_kanji: false,
                            ruby_html: ck,
                            pos: '格助詞',
                            is_particle: true,
                            is_grammar_elem: true,
                            grammar_elem_info: {{
                                type: '格助詞',
                                category: '格助詞',
                                title: item.title || pData.default_role || ck,
                                role: item.role || pData.default_role || '格助詞',
                                desc: item.desc || (pData.usages && pData.usages[0] && pData.usages[0].desc) || '',
                                grammar_id: null,
                                mask_placeholder: '？格助',
                                distractors: item.distractors || pData.distractors || ['は', 'が', 'を', 'に', 'で'],
                                pData: pData
                            }}
                        }});
                        i += ck.length;
                        cMatched = true;
                        break;
                    }}
                }}
                if (cMatched) continue;

                // 6. 一般標點與未知字元
                tokens.push({{
                    surface: char,
                    base_form: char,
                    reading: char,
                    jlpt: null,
                    is_kanji: false,
                    ruby_html: char,
                    pos: '符號',
                    is_particle: false
                }});
                i++;
            }}

            return tokens;
        }}

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
                return '';
            }}
        }}

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
         前端互動與單字複習抽卡控制器
         ========================================================================== -->
    <script>
        var toastTimer = null;
        const state = {{
            analyzedData: null,
            currentSentenceIdx: 0,
            rubyMode: 'show',
            transMode: 'show',
            jpMode: 'show',
            particleMode: 'show',
            grammarMode: 'show', // 'show' | 'mask-all' | 'mask-格助詞' | 'mask-副助詞' | 'mask-複合助詞' | 'mask-文型'
            enableWordColors: true,
            enableGrammar: true,
            fontSizeLevel: 0,
            theme: 'light',
            notebook: {{ words: [], grammars: [] }},
            review: {{
                source: 'article',
                words: [],
                currentIdx: 0,
                isFlipped: false
            }},
            quiz: {{
                items: [],
                currentIdx: 0,
                score: 0,
                answered: new Set()
            }}
        }};

        const dom = {{
            btnJpShow: document.getElementById('btnJpShow'),
            btnJpMask: document.getElementById('btnJpMask'),
            btnParticleShow: document.getElementById('btnParticleShow'),
            btnParticleMask: document.getElementById('btnParticleMask'),
            btnGrammarShow: document.getElementById('btnGrammarShow'),
            btnGrammarMaskAll: document.getElementById('btnGrammarMaskAll'),
            btnGrammarMaskCase: document.getElementById('btnGrammarMaskCase'),
            btnGrammarMaskAdverbial: document.getElementById('btnGrammarMaskAdverbial'),
            btnGrammarMaskCompound: document.getElementById('btnGrammarMaskCompound'),
            btnGrammarMaskSentence: document.getElementById('btnGrammarMaskSentence'),
            btnOpenParticleQuiz: document.getElementById('btnOpenParticleQuiz'),
            btnOpenParticleQuizTop: document.getElementById('btnOpenParticleQuizTop'),
            sentenceParticleCount: document.getElementById('sentenceParticleCount'),
            sentenceParticlesList: document.getElementById('sentenceParticlesList'),
            btnMaskSentenceParticles: document.getElementById('btnMaskSentenceParticles'),
            particlePopover: document.getElementById('particlePopover'),
            particleQuizModal: document.getElementById('particleQuizModal'),
            btnRubyShow: document.getElementById('btnRubyShow'),
            btnRubyHide: document.getElementById('btnRubyHide'),
            btnRubyMask: document.getElementById('btnRubyMask'),
            btnTransShow: document.getElementById('btnTransShow'),
            btnTransHide: document.getElementById('btnTransHide'),
            btnTransMask: document.getElementById('btnTransMask'),
            btnToggleWordColors: document.getElementById('btnToggleWordColors'),
            btnToggleGrammar: document.getElementById('btnToggleGrammar'),
            btnWordReview: document.getElementById('btnWordReview'),
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

            reviewModal: document.getElementById('reviewModal'),
            tabReviewArticleBtn: document.getElementById('tabReviewArticleBtn'),
            tabReviewNotebookBtn: document.getElementById('tabReviewNotebookBtn'),
            reviewArticleWordCount: document.getElementById('reviewArticleWordCount'),
            reviewNotebookWordCount: document.getElementById('reviewNotebookWordCount'),
            reviewCard: document.getElementById('reviewCard'),
            reviewCardLevel: document.getElementById('reviewCardLevel'),
            reviewCardWord: document.getElementById('reviewCardWord'),
            reviewFlipHint: document.getElementById('reviewFlipHint'),
            reviewBackContent: document.getElementById('reviewBackContent'),
            reviewCardReading: document.getElementById('reviewCardReading'),
            reviewCardTrans: document.getElementById('reviewCardTrans'),
            reviewProgressBar: document.getElementById('reviewProgressBar'),
            reviewProgressText: document.getElementById('reviewProgressText'),

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
            setRubyMode(savedRuby, true);
            const savedTheme = localStorage.getItem('japanese_reader_theme') || 'light';
            setTheme(savedTheme);
            const savedWordColors = localStorage.getItem('japanese_reader_word_colors') !== 'false';
            setWordColors(savedWordColors);
            const savedGrammar = localStorage.getItem('japanese_reader_grammar') !== 'false';
            setGrammarHighlight(savedGrammar);
            const savedTransMode = localStorage.getItem('japanese_reader_trans_mode') || 'show';
            setTransMode(savedTransMode);
            const savedJpMode = localStorage.getItem('japanese_reader_jp_mode') || 'show';
            setJpMode(savedJpMode);
            const savedGrammarMode = localStorage.getItem('japanese_reader_grammar_mode') || localStorage.getItem('japanese_reader_particle_mode') || 'show';
            setGrammarMode(savedGrammarMode, true);
        }}

        function setupEventListeners() {{
            dom.btnJpShow.addEventListener('click', () => setJpMode('show'));
            dom.btnJpMask.addEventListener('click', () => setJpMode('mask'));

            if (dom.btnParticleShow) dom.btnParticleShow.addEventListener('click', () => setParticleMode('show'));
            if (dom.btnParticleMask) dom.btnParticleMask.addEventListener('click', () => setParticleMode('mask'));
            if (dom.btnGrammarShow) dom.btnGrammarShow.addEventListener('click', () => setGrammarMode('show'));
            if (dom.btnGrammarMaskAll) dom.btnGrammarMaskAll.addEventListener('click', () => setGrammarMode('mask-all'));
            if (dom.btnGrammarMaskCase) dom.btnGrammarMaskCase.addEventListener('click', () => setGrammarMode('mask-case'));
            if (dom.btnGrammarMaskAdverbial) dom.btnGrammarMaskAdverbial.addEventListener('click', () => setGrammarMode('mask-adverbial'));
            if (dom.btnGrammarMaskCompound) dom.btnGrammarMaskCompound.addEventListener('click', () => setGrammarMode('mask-compound'));
            if (dom.btnGrammarMaskSentence) dom.btnGrammarMaskSentence.addEventListener('click', () => setGrammarMode('mask-sentence'));
            if (dom.btnOpenParticleQuiz) dom.btnOpenParticleQuiz.addEventListener('click', openParticleQuizModal);
            if (dom.btnOpenParticleQuizTop) dom.btnOpenParticleQuizTop.addEventListener('click', openParticleQuizModal);
            if (dom.btnMaskSentenceParticles) dom.btnMaskSentenceParticles.addEventListener('click', toggleMaskSentenceParticles);

            dom.btnRubyShow.addEventListener('click', () => setRubyMode('show'));
            dom.btnRubyHide.addEventListener('click', () => setRubyMode('hide'));
            dom.btnRubyMask.addEventListener('click', () => setRubyMode('mask'));

            dom.btnTransShow.addEventListener('click', () => setTransMode('show'));
            dom.btnTransHide.addEventListener('click', () => setTransMode('hide'));
            dom.btnTransMask.addEventListener('click', () => setTransMode('mask'));

            dom.btnToggleWordColors.addEventListener('click', () => setWordColors(!state.enableWordColors));
            dom.btnToggleGrammar.addEventListener('click', () => setGrammarHighlight(!state.enableGrammar));
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
                if (dom.reviewModal.classList.contains('open')) {{
                    if (e.key === ' ' || e.code === 'Space') {{
                        e.preventDefault();
                        flipReviewCard();
                    }} else if (e.key === 'ArrowLeft') {{
                        navReview(-1);
                    }} else if (e.key === 'ArrowRight') {{
                        navReview(1);
                    }} else if (e.key === 'v' || e.key === 'V') {{
                        speakReviewCurrentWord();
                    }} else if (e.key === 'Escape') {{
                        closeReviewModal();
                    }}
                    return;
                }}

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

            dom.btnWordReview.addEventListener('click', openReviewModal);
            dom.btnOpenNotebook.addEventListener('click', openNotebookModal);
            dom.btnExportNotebook.addEventListener('click', exportNotebook);
            dom.btnClearNotebook.addEventListener('click', clearNotebook);

            document.addEventListener('click', (e) => {{
                const r = e.target.closest('ruby');
                if (r && state.rubyMode === 'mask') {{
                    r.classList.toggle('revealed');
                }}
                if (dom.wordPopover.style.display !== 'none' &&
                    !dom.wordPopover.contains(e.target) &&
                    !e.target.closest('.word-token')) {{
                    closeWordPopover();
                }}
            }});
        }}

        function setJpMode(mode) {{
            state.jpMode = mode;
            localStorage.setItem('japanese_reader_jp_mode', mode);
            document.body.setAttribute('data-jp-mode', mode);
            dom.btnJpShow.classList.toggle('active', mode === 'show');
            dom.btnJpMask.classList.toggle('active', mode === 'mask');
            if (mode === 'mask') {{
                showToast('已開啟【中翻日自測模式】：日文原文已遮蔽，請看中文練習翻譯，滑鼠移過或點擊即可揭示！');
            }}
        }}

        function setParticleMode(mode, silent = false) {{
            setGrammarMode(mode === 'mask' ? 'mask-all' : 'show', silent);
        }}

        function setGrammarMode(mode, silent = false) {{
            state.grammarMode = mode;
            state.particleMode = (mode === 'show') ? 'show' : 'mask';
            localStorage.setItem('japanese_reader_grammar_mode', mode);
            localStorage.setItem('japanese_reader_particle_mode', (mode === 'show') ? 'show' : 'mask');
            document.body.setAttribute('data-grammar-mode', mode);
            document.body.setAttribute('data-particle-mode', (mode === 'show') ? 'show' : 'mask');

            // 移除已揭示狀態，切換模式時題目立即遮蔽
            document.querySelectorAll('.grammar-elem-token.revealed').forEach(el => el.classList.remove('revealed'));

            const btns = [
                ['show', dom.btnGrammarShow],
                ['mask-all', dom.btnGrammarMaskAll],
                ['mask-case', dom.btnGrammarMaskCase],
                ['mask-adverbial', dom.btnGrammarMaskAdverbial],
                ['mask-compound', dom.btnGrammarMaskCompound],
                ['mask-sentence', dom.btnGrammarMaskSentence]
            ];

            btns.forEach(([m, btn]) => {{
                if (btn) btn.classList.toggle('active', mode === m);
            }});

            const msgMap = {{
                'show': '已切換為助詞與文型【正常顯示】模式',
                'mask-all': '已開啟【全部遮蔽】自測：遮蔽全文所有格助詞、副助詞、複合助詞與文型！',
                'mask-case': '已開啟【格助詞遮蔽】自測：僅遮蔽全文格助詞 (が、を、に、で、へ、と等)！',
                'mask-adverbial': '已開啟【副助詞遮蔽】自測：僅遮蔽副助詞／係助詞 (は、も、ばかり、だけ、さえ等)！',
                'mask-compound': '已開啟【複合助詞遮蔽】自測：僅遮蔽複合助詞 (について、に対して、として等)！',
                'mask-sentence': '已開啟【文型句型遮蔽】自測：僅遮蔽單純文型句型 (ながらも、に伴い、あげく等)！'
            }};

            if (!silent) {{
                showToast(msgMap[mode] || `已切換自測模式: ${{mode}}`);
            }}
        }}

        function setRubyMode(mode, silent = false) {{
            state.rubyMode = mode;
            localStorage.setItem('japanese_reader_ruby_mode', mode);
            document.body.setAttribute('data-ruby-mode', mode);
            dom.btnRubyShow.classList.toggle('active', mode === 'show');
            dom.btnRubyHide.classList.toggle('active', mode === 'hide');
            dom.btnRubyMask.classList.toggle('active', mode === 'mask');
            if (mode === 'mask' && !silent) showToast('已開啟【遮蔽自測模式】：假名已遮蔽，滑鼠移過或點擊即可揭示讀音！');
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

        function setTransMode(mode) {{
            state.transMode = mode;
            localStorage.setItem('japanese_reader_trans_mode', mode);
            document.body.setAttribute('data-trans-mode', mode);
            dom.btnTransShow.classList.toggle('active', mode === 'show');
            dom.btnTransHide.classList.toggle('active', mode === 'hide');
            dom.btnTransMask.classList.toggle('active', mode === 'mask');
            if (mode === 'mask') {{
                showToast('已開啟【中文遮蔽自測模式】：中文翻譯已遮蔽，滑鼠移過或點擊即可揭示！');
            }}
        }}

        function setTheme(theme) {{
            state.theme = theme;
            localStorage.setItem('japanese_reader_theme', theme);
            document.body.setAttribute('data-theme', theme);
            dom.themeIcon.className = theme === 'dark' ? 'fa-solid fa-sun text-yellow-300' : 'fa-solid fa-moon';
        }}

        function changeFontSize(delta) {{
            state.fontSizeLevel = Math.max(-2, Math.min(4, state.fontSizeLevel + delta));
            const sizes = ['1.02rem', '1.08rem', '1.16rem', '1.28rem', '1.45rem', '1.65rem', '1.85rem'];
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
                const proxyUrl = `https://api.allorigins.win/raw?url=${{encodeURIComponent(url)}}`;
                const res = await fetch(proxyUrl);
                if (!res.ok) throw new Error('連線失敗');
                const html = await res.text();

                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');

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
                const res = await clientAnalyzeText(text, dom.chkAutoTranslate.checked);
                state.analyzedData = res;
                state.currentSentenceIdx = 0;

                renderReaderView();
                showToast('文章解析完成！100% 漢字假名已標註完畢');
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
                jpWrap.title = '點擊切換揭示/遮蔽';
                jpWrap.addEventListener('click', (e) => {{
                    if (state.jpMode === 'mask') {{
                        e.stopPropagation();
                        jpWrap.classList.toggle('revealed');
                    }}
                }});
                renderSentenceTokens(jpWrap, s, sIdx);
                row.appendChild(jpWrap);

                if (s.translation) {{
                    const transRow = document.createElement('div');
                    transRow.className = 'sentence-trans-row';
                    transRow.innerHTML = `
                        <span class="trans-tag">繁中</span>
                        <span class="trans-text" onclick="event.stopPropagation(); this.classList.toggle('revealed');" title="點擊切換揭示/遮蔽">${{s.translation}}</span>
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
                const isGrammarElem = Boolean(w.is_grammar_elem || w.is_particle || (PARTICLE_DATA && PARTICLE_DATA[w.surface]));
                const rawCategory = (w.grammar_elem_info && w.grammar_elem_info.category) || (PARTICLE_DATA && PARTICLE_DATA[w.surface] && PARTICLE_DATA[w.surface].category) || '格助詞';
                const catMeta = (typeof CATEGORY_MAP !== 'undefined' && CATEGORY_MAP[rawCategory]) ? CATEGORY_MAP[rawCategory] : {{ code: 'case', name: '格助詞', placeholder: '？格助' }};

                if (isGrammarElem) {{
                    tokenSpan.className = `word-token grammar-elem-token particle-token`;
                    tokenSpan.dataset.isGrammarElem = 'true';
                    tokenSpan.dataset.category = catMeta.code;
                    tokenSpan.dataset.categoryName = catMeta.name;
                    tokenSpan.dataset.maskPlaceholder = catMeta.placeholder;
                    tokenSpan.dataset.surface = w.surface;
                    tokenSpan.title = `【${{catMeta.name}}】${{w.surface}} (點擊進行自測與查看換句話說)`;
                }} else {{
                    tokenSpan.className = `word-token ${{w.jlpt ? `jlpt-${{w.jlpt}}` : ''}}`;
                }}

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
                    if (isGrammarElem) {{
                        tokenSpan.classList.add('revealed');
                        showParticleQuickPopover(tokenSpan, w, sIdx, wIdx, e);
                        return;
                    }}
                    showWordPopover(tokenSpan, w, e);
                }});

                // 檢查是否與 941 文法重疊標註
                const tokenStart = wordOffsets[wIdx].start;
                const tokenEnd = wordOffsets[wIdx].end;

                const hasGrammarMatch = grammars.some(g => {{
                    if (g.matches && Array.isArray(g.matches)) {{
                        return g.matches.some(m => tokenStart < m.end && tokenEnd > m.start);
                    }}
                    if (typeof g.start === 'number' && typeof g.end === 'number') {{
                        return tokenStart < g.end && tokenEnd > g.start;
                    }}
                    return false;
                }});

                if (hasGrammarMatch) {{
                    tokenSpan.classList.add('grammar-highlight');
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

            if (dom.currentSentenceBadge) dom.currentSentenceBadge.textContent = `第 ${{idx + 1}} 句 / 共 ${{total}} 句`;
            if (dom.selectedSentenceJp) dom.selectedSentenceJp.innerHTML = sentence.words.map(w => w.ruby_html).join('');
            if (dom.selectedSentenceZh) dom.selectedSentenceZh.textContent = sentence.translation || '暫無翻譯';

            renderSentenceGrammars(sentence.grammars || []);
            renderSentenceWordsTable(sentence.words, sentence.grammars || []);

            if (dom.btnPrevSentence) dom.btnPrevSentence.disabled = (idx === 0);
            if (dom.btnNextSentence) dom.btnNextSentence.disabled = (idx === total - 1);
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
                    ${{(g.exampleRuby || g.example) ? `
                        <div class="grammar-example-box" onclick="this.classList.toggle('revealed')" title="點擊切換假名揭示/遮蔽">
                            <div class="example-jp-line"><strong>例句：</strong>${{g.exampleRuby || escapeHtml(g.example)}}</div>
                            ${{g.translation ? `<div class="example-trans-line"><i class="fa-solid fa-language" style="margin-right:4px;"></i>${{escapeHtml(g.translation)}}</div>` : ''}}
                        </div>
                    ` : ''}}
                    <div class="grammar-card-actions">
                        <button class="btn-grammar-detail" onclick="openGrammarDrawerById(${{g.id}})">
                            <i class="fa-solid fa-book-open"></i> 查看完整詳解
                        </button>
                    </div>
                `;
                dom.sentenceGrammarsList.appendChild(card);
            }});
        }}

        const JAPANESE_PARTICLES = new Set([
            'は', 'が', 'を', 'に', 'で', 'と', 'も', 'へ', 'から', 'まで', 'より', 
            'ね', 'よ', 'か', 'な', 'の', 'ば', 'や', 'わ', 'ぜ', 'ぞ', 'し',
            'たり', 'だの', 'なり', 'ながら', 'つつ', 'ても', 'でも', 'のに', 'ので',
            'ばかり', 'だけ', 'ほど', 'くらい', 'ぐらい', 'など', 'なんぞ',
            'なんか', 'こそ', 'さえ', 'しか', 'ずつ', 'かしら', 'かな', 'て'
        ]);

        function renderSentenceWordsTable(words, grammars = []) {{
            // 1. 過濾純符號、純標點、純空白與助詞 (不分析助詞，專注核心實詞)
            const validWords = words.filter(w => {{
                const s = (w.surface || '').trim();
                if (!s) return false;
                if (/^[、。！？「」『』（）…—\\s.,!?]+$/.test(s)) return false;
                if (w.pos === '符號/助詞') return false;
                if (JAPANESE_PARTICLES.has(s)) return false;
                if (w.base_form && JAPANESE_PARTICLES.has(w.base_form)) return false;
                // 單一平假名且無漢字通常為助詞/感嘆詞
                if (/^[\\u3040-\\u309f]$/.test(s) && !KANJI_REGEX.test(s)) return false;
                return true;
            }});

            dom.sentenceWordCount.textContent = validWords.length;
            dom.sentenceWordsTbody.innerHTML = '';

            validWords.forEach((w, wIdx) => {{
                // 2. 動詞與形容詞還原為原型 (辭書形)
                const baseForm = deinflectWord(w.surface) || w.base_form || w.surface;
                let displayReading = w.reading || '-';
                let displayLevel = w.jlpt;

                if (JLPT_VOCAB[baseForm]) {{
                    const [lvlNum, r] = JLPT_VOCAB[baseForm];
                    displayReading = kataToHira(r);
                    if (lvlNum) displayLevel = `N${{lvlNum}}`;
                }}

                const isFav = state.notebook.words.some(item => item.surface === baseForm || item.surface === w.surface);
                const kanjiReadingsHtml = getKanjiReadingsHtml(baseForm);

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${{escapeHtml(baseForm)}}</strong></td>
                    <td style="color:#e11d48;font-weight:700;">${{escapeHtml(displayReading)}}</td>
                    <td>${{kanjiReadingsHtml}}</td>
                    <td>${{displayLevel ? `<span class="badge-jlpt badge-${{displayLevel.toLowerCase()}}">${{displayLevel}}</span>` : '<span style="color:var(--text-muted);">-</span>'}}</td>
                    <td style="color:var(--text-main);font-size:0.88rem;" id="word-trans-cell-${{wIdx}}">
                        <span class="word-trans-val" onclick="this.classList.toggle('revealed')" title="點擊切換揭示/遮蔽">
                            <span style="color:var(--text-muted);font-size:0.78rem;"><i class="fa-solid fa-spinner fa-spin"></i> 翻譯中</span>
                        </span>
                    </td>
                    <td style="text-align:center;">
                        <button class="btn-fav-word ${{isFav ? 'active' : ''}}" title="加入生詞本" onclick="toggleWordNotebook('${{escapeHtml(baseForm)}}', '${{escapeHtml(baseForm)}}', '${{escapeHtml(displayReading)}}', '${{escapeHtml(displayLevel || '')}}', '')">
                            <i class="fa-solid fa-star"></i>
                        </button>
                    </td>
                `;
                dom.sentenceWordsTbody.appendChild(tr);

                // 3. 確保使用原型查詢中文翻譯，取得精確字典釋義
                translateJaToZh(baseForm).then(trans => {{
                    const cell = document.getElementById(`word-trans-cell-${{wIdx}}`);
                    if (cell) {{
                        cell.innerHTML = `<span class="word-trans-val" onclick="this.classList.toggle('revealed')" title="點擊切換揭示/遮蔽"><strong>${{escapeHtml(trans || '-')}}</strong></span>`;
                        w.translation = trans;
                    }}
                }}).catch(() => {{
                    const cell = document.getElementById(`word-trans-cell-${{wIdx}}`);
                    if (cell) cell.innerHTML = `<span class="word-trans-val">-</span>`;
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

                <div class="drawer-box" onclick="this.classList.toggle('revealed')" title="點擊切換假名揭示/遮蔽" style="cursor:pointer;">
                    <div class="drawer-label"><i class="fa-solid fa-quote-left"></i> 精選例文與振假名 (Example Sentence)</div>
                    <div style="font-size:1.25rem;font-weight:700;font-family:var(--font-jp);line-height:2.4;overflow:visible;word-break:break-word;">${{g.exampleRuby || escapeHtml(g.example || '')}}</div>
                    <div style="font-size:1.02rem;color:var(--text-muted);margin-top:0.75rem;border-top:1px dashed var(--border-color);padding-top:0.75rem;line-height:1.6;">
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

        // ==========================================================================
        // 單字翻牌抽卡複習功能 (Vocabulary Flashcard Review)
        // ==========================================================================
        function openReviewModal() {{
            buildReviewWordList();
            if (state.review.words.length === 0) {{
                showToast('目前尚無可供複習之單字，請先解析文章或加入生詞本');
                return;
            }}
            state.review.currentIdx = 0;
            state.review.isFlipped = false;
            dom.reviewModal.classList.add('open');
            renderCurrentReviewCard();
        }}

        function closeReviewModal() {{
            dom.reviewModal.classList.remove('open');
        }}

        function buildReviewWordList() {{
            const list = [];
            const seen = new Set();

            if (state.review.source === 'article' && state.analyzedData) {{
                state.analyzedData.sentences.forEach(s => {{
                    s.words.forEach(w => {{
                        const key = w.base_form || w.surface;
                        if (key.length >= 2 && !seen.has(key) && w.pos !== '符號/助詞') {{
                            seen.add(key);
                            list.push({{
                                word: key,
                                reading: w.reading,
                                jlpt: w.jlpt,
                                pos: w.pos,
                                translation: w.translation || ''
                            }});
                        }}
                    }});
                }});
            }} else {{
                state.notebook.words.forEach(w => {{
                    if (!seen.has(w.surface)) {{
                        seen.add(w.surface);
                        list.push({{
                            word: w.surface,
                            reading: w.reading,
                            jlpt: w.jlpt,
                            pos: w.pos,
                            translation: w.translation || ''
                        }});
                    }}
                }});
            }}

            state.review.words = list;
            dom.reviewArticleWordCount.textContent = (state.analyzedData ? seen.size : 0);
            dom.reviewNotebookWordCount.textContent = state.notebook.words.length;
        }}

        function switchReviewSource(src) {{
            state.review.source = src;
            dom.tabReviewArticleBtn.classList.toggle('active', src === 'article');
            dom.tabReviewNotebookBtn.classList.toggle('active', src === 'notebook');
            buildReviewWordList();
            state.review.currentIdx = 0;
            state.review.isFlipped = false;
            renderCurrentReviewCard();
        }}

        async function renderCurrentReviewCard() {{
            const words = state.review.words;
            const total = words.length;

            if (total === 0) {{
                dom.reviewCardWord.textContent = '暫無單字';
                dom.reviewCardReading.textContent = '';
                dom.reviewCardTrans.textContent = '請先解析文章或將單字加入生詞本';
                dom.reviewProgressBar.style.width = '0%';
                dom.reviewProgressText.textContent = '進度：0 / 0';
                return;
            }}

            const idx = state.review.currentIdx;
            const item = words[idx];

            dom.reviewCardWord.textContent = item.word;
            dom.reviewCardReading.textContent = item.reading || item.word;

            if (item.jlpt) {{
                dom.reviewCardLevel.textContent = item.jlpt;
                dom.reviewCardLevel.className = `badge-jlpt badge-${{item.jlpt.toLowerCase()}}`;
                dom.reviewCardLevel.style.display = 'inline-flex';
            }} else {{
                dom.reviewCardLevel.style.display = 'none';
            }}

            // 揭示狀態處理
            state.review.isFlipped = false;
            dom.reviewBackContent.classList.remove('revealed');
            dom.reviewFlipHint.style.display = 'flex';

            // 異步填寫中文翻譯
            if (!item.translation) {{
                dom.reviewCardTrans.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 翻譯中...';
                translateJaToZh(item.word).then(tr => {{
                    item.translation = tr;
                    if (state.review.currentIdx === idx) {{
                        dom.reviewCardTrans.textContent = tr || '暫無翻譯';
                    }}
                }});
            }} else {{
                dom.reviewCardTrans.textContent = item.translation;
            }}

            // 更新進度條
            const percent = Math.round(((idx + 1) / total) * 100);
            dom.reviewProgressBar.style.width = `${{percent}}%`;
            dom.reviewProgressText.textContent = `第 ${{idx + 1}} / ${{total}} 個單字 (${{percent}}%)`;
        }}

        function flipReviewCard() {{
            state.review.isFlipped = !state.review.isFlipped;
            dom.reviewBackContent.classList.toggle('revealed', state.review.isFlipped);
            dom.reviewFlipHint.style.display = state.review.isFlipped ? 'none' : 'flex';
        }}

        function navReview(delta) {{
            const total = state.review.words.length;
            if (total === 0) return;
            state.review.currentIdx = (state.review.currentIdx + delta + total) % total;
            renderCurrentReviewCard();
        }}

        function speakReviewCurrentWord() {{
            const w = state.review.words[state.review.currentIdx];
            if (w) speakJapanese(w.word);
        }}

        // ==========================================================================
        // 筆記本 (單字與文法收藏)
        // ==========================================================================
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
            dom.reviewNotebookWordCount.textContent = state.notebook.words.length;
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

        // toastTimer is declared at the top of script
        function showToast(msg) {{
            dom.toastMsg.textContent = msg;
            dom.toast.classList.add('show');
            clearTimeout(toastTimer);
            toastTimer = setTimeout(() => dom.toast.classList.remove('show'), 2800);
        }}


        // ==========================================================================
        // 助詞深度解析、代用與換句話說核心引擎 (Particle & Paraphrase Engine)
        // ==========================================================================

        function getParticleData(pSurface) {{
            if (!window.PARTICLE_DATA) return null;
            return window.PARTICLE_DATA[pSurface] || null;
        }}

        function matchParticleUsage(pSurface, sentenceText) {{
            const pData = getParticleData(pSurface);
            if (!pData || !pData.usages || pData.usages.length === 0) return null;

            for (const u of pData.usages) {{
                if (u.context_clue && u.context_clue.some(c => sentenceText.includes(c))) {{
                    return u;
                }}
            }}
            return pData.usages[0];
        }}

        function generateParaphraseDemo(sentenceText, pSurface, subTitle) {{
            if (!sentenceText) return '';
            const s = sentenceText.trim();

            if (pSurface === 'で') {{
                if (s.includes('使って')) {{
                    return s.replace(/([^、。]*?)を使って/g, '<strong>【$1によって】</strong>');
                }}
                if (s.includes('では')) {{
                    return s.replace(/([^、。]*?)では/g, '<strong>【$1においては】</strong>');
                }}
                if (s.includes('で')) {{
                    return s.replace(/([^、。]*?)で/g, '<strong>【$1によって】</strong>');
                }}
            }} else if (pSurface === 'が') {{
                if (s.includes('が診察する時')) {{
                    return s.replace('が診察する時', '<strong>【の診察する時】</strong>（連體修飾節主語交代）');
                }}
                if (s.includes('が読んだ')) {{
                    return s.replace('が読んだ', '<strong>【の読んだ】</strong>（連體修飾節主語交代）');
                }}
                return s.replace(/([^\\s、。]{{1,6}})が([^\\s、。]{{2,8}}[する|した|る|た])/g, '<strong>$1【の】$2</strong>（連體修飾節「が」常代用為「の」）');
            }} else if (pSurface === 'に') {{
                if (s.includes('時に')) {{
                    return s.replace('時に', '<strong>【にあたって】</strong>');
                }}
                if (s.includes('行く') || s.includes('行きまし')) {{
                    return s.replace(/([^、。]*?)に(行[く|き])/g, '<strong>【$1へ$2】</strong>（方向助詞代用）');
                }}
            }} else if (pSurface === 'へ') {{
                return s.replace(/([^、。]*?)へ(行[く|き])/g, '<strong>【$1に$2】</strong>（歸著點助詞代用）');
            }} else if (pSurface === 'から') {{
                if (s.includes('ため')) {{
                    return s.replace('ため', '<strong>【によって】</strong>');
                }}
                return s.replace(/([^、。]*?)から/g, '<strong>【$1ので】</strong> 或 <strong>【$1ことから】</strong>');
            }} else if (pSurface === 'について') {{
                return s.replace(/([^、。]*?)について/g, '<strong>【$1に関して】</strong>');
            }} else if (pSurface === 'と') {{
                if (s.includes('一緒に') || s.includes('付き合っ')) {{
                    return s.replace(/([^、。]*?)と/g, '<strong>【$1とともに】</strong>');
                }}
            }} else if (pSurface === 'より') {{
                return s.replace(/([^、。]*?)より/g, '<strong>【$1に比べて】</strong>');
            }} else if (pSurface === 'だけ') {{
                return s.replace(/([^、。]*?)だけ/g, '<strong>【$1のみ】</strong>');
            }}

            return `可將句中「名詞＋${{pSurface}}」換句話說改寫為「名詞＋${{subTitle}}」！`;
        }}

        function renderSentenceParticles(sentence, sIdx) {{
            const listEl = dom.sentenceParticlesList;
            if (!listEl) return;
            listEl.innerHTML = '';

            const words = sentence.words || [];
            const sentenceText = sentence.text || '';

            // 抓取本句中所有語法單位（文型、複合助詞、副助詞、格助詞、接續助詞）
            const detectedParticles = [];
            words.forEach((w, wIdx) => {{
                const s = w.surface;
                const isGrammarElem = Boolean(w.is_grammar_elem || w.is_particle || (PARTICLE_DATA && PARTICLE_DATA[s]));
                if (isGrammarElem) {{
                    const prev = wIdx > 0 ? words[wIdx - 1].surface : '';
                    const next = wIdx + 1 < words.length ? words[wIdx + 1].surface : '';
                    const elInfo = w.grammar_elem_info || {{}};
                    const pData = getParticleData(s) || (elInfo.pData) || {{}};
                    detectedParticles.push({{
                        surface: s,
                        category: elInfo.category || pData.category || '助詞',
                        title: elInfo.title || pData.default_role || s,
                        grammar_id: elInfo.grammar_id || (pData.usages && pData.usages[0] && pData.usages[0].substitutes && pData.usages[0].substitutes[0] && pData.usages[0].substitutes[0].grammarId),
                        wordIdx: wIdx,
                        prevWord: prev,
                        nextWord: next,
                        pData: pData,
                        elInfo: elInfo
                    }});
                }}
            }});

            if (dom.sentenceParticleCount) {{
                dom.sentenceParticleCount.textContent = detectedParticles.length;
            }}

            if (detectedParticles.length === 0) {{
                listEl.innerHTML = '<div class="empty-hint">本句未偵測到特殊助詞或文型</div>';
                return;
            }}

            detectedParticles.forEach((pItem, idx) => {{
                const pSurface = pItem.surface;
                const pData = pItem.pData;
                const usage = matchParticleUsage(pSurface, sentenceText);

                const card = document.createElement('div');
                card.className = 'particle-item-card';

                const catName = pItem.category || (usage ? usage.role : '語法');
                const roleText = usage ? usage.role : (pItem.elInfo && pItem.elInfo.role ? pItem.elInfo.role : (pData ? pData.default_role : '語法功能'));
                const descText = usage ? usage.desc : (pItem.elInfo && pItem.elInfo.desc ? pItem.elInfo.desc : '在句中具有關鍵的語法聯繫與修飾功能。');
                const contextDisplay = `${{escapeHtml(pItem.prevWord)}}<strong>【${{escapeHtml(pSurface)}}】</strong>${{escapeHtml(pItem.nextWord)}}`;

                let substitutesHtml = '';
                if (usage && usage.substitutes && usage.substitutes.length > 0) {{
                    let subItemsHtml = '';
                    usage.substitutes.forEach(sub => {{
                        let gCardHtml = '';
                        if (sub.grammarId) {{
                            const gInfo = GRAMMAR_DATA.find(g => g.id === sub.grammarId);
                            if (gInfo) {{
                                gCardHtml = `
                                    <div style="margin-top:0.35rem; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:0.4rem;">
                                        <span style="font-size:0.82rem; color:var(--text-muted);">${{escapeHtml(gInfo.meaningZh || '')}}</span>
                                        <button class="btn-grammar-detail" style="padding:0.25rem 0.6rem; font-size:0.78rem;" onclick="openGrammarDrawerById(${{gInfo.id}})">
                                            <i class="fa-solid fa-book-open"></i> 查看 941 文法庫詳解
                                        </button>
                                    </div>
                                `;
                            }}
                        }}

                        const demoRewrite = generateParaphraseDemo(sentenceText, pSurface, sub.title);

                        subItemsHtml += `
                            <div class="substitute-item-card">
                                <div style="display:flex; align-items:center; gap:0.45rem; flex-wrap:wrap;">
                                    <span class="substitute-tag">${{escapeHtml(sub.type)}}</span>
                                    <strong style="color:var(--text-main); font-size:0.92rem; font-family:var(--font-jp);">${{escapeHtml(sub.title)}}</strong>
                                    <span class="badge-jlpt badge-${{(sub.level || 'n2').toLowerCase().replace('~','_')}}">${{escapeHtml(sub.level)}}</span>
                                </div>
                                <div style="font-size:0.83rem; color:var(--text-muted); margin-top:0.25rem;">
                                    ${{escapeHtml(sub.desc || '')}}
                                </div>
                                ${{demoRewrite ? `
                                    <div class="paraphrase-demo-box">
                                        <strong><i class="fa-solid fa-pen-nib"></i> 換句話說：</strong>
                                        <span>${{demoRewrite}}</span>
                                    </div>
                                ` : ''}}
                                ${{gCardHtml}}
                            </div>
                        `;
                    }});

                    substitutesHtml = `
                        <div class="particle-substitutes-wrap">
                            <div class="substitutes-title">
                                <i class="fa-solid fa-shuffle"></i> <strong>代用推薦與換句話說</strong>
                                <span style="font-size:0.78rem; font-weight:normal; color:var(--text-muted);">（可置換表達方式）</span>
                            </div>
                            ${{subItemsHtml}}
                        </div>
                    `;
                }}

                let grammarDrawerBtn = '';
                if (pItem.grammar_id) {{
                    grammarDrawerBtn = `<button class="btn-grammar-detail" style="padding:0.2rem 0.5rem;font-size:0.75rem;" onclick="openGrammarDrawerById(${{pItem.grammar_id}})">
                        <i class="fa-solid fa-book-open"></i> 941文型庫
                    </button>`;
                }}

                card.innerHTML = `
                    <div class="particle-item-header">
                        <div class="particle-title-wrap">
                            <span class="particle-main-badge">${{escapeHtml(pSurface)}}</span>
                            <span class="cat-badge cat-badge-${{catName}}">${{escapeHtml(catName)}}</span>
                            <span class="particle-context-chip">${{contextDisplay}}</span>
                        </div>
                        <div style="display:flex;align-items:center;gap:0.4rem;">
                            <span class="particle-role-badge">${{escapeHtml(roleText)}}</span>
                            ${{grammarDrawerBtn}}
                        </div>
                    </div>
                    <div class="particle-desc-text">${{escapeHtml(descText)}}</div>
                    ${{substitutesHtml}}
                `;

                listEl.appendChild(card);
            }});
        }}

        function toggleMaskSentenceParticles() {{
            const activeRow = document.querySelector(`.sentence-row[data-sentence-idx="${{state.currentSentenceIdx}}"]`);
            if (!activeRow) return;
            const particleTokens = activeRow.querySelectorAll('.grammar-elem-token, .particle-token');
            if (particleTokens.length === 0) {{
                showToast('本句無特殊助詞或文型');
                return;
            }}
            const isAnyMasked = Array.from(particleTokens).some(el => el.classList.contains('force-masked') && !el.classList.contains('revealed'));
            if (isAnyMasked) {{
                particleTokens.forEach(el => {{
                    el.classList.remove('force-masked');
                    el.classList.add('revealed');
                }});
                showToast('已揭示本句助詞與文型');
            }} else {{
                particleTokens.forEach(el => {{
                    el.classList.add('force-masked');
                    el.classList.remove('revealed');
                }});
                showToast('已遮蔽本句助詞與文型，請點擊進行隨堂自測！');
            }}
        }}

        function showParticleQuickPopover(targetEl, token, sIdx, wIdx, event) {{
            const popover = document.getElementById('particlePopover');
            if (!popover) return;

            const pSurface = token.surface;
            const pData = getParticleData(pSurface);
            const sentence = state.analyzedData ? state.analyzedData.sentences[sIdx] : null;
            const sentenceText = sentence ? sentence.text : '';
            const usage = matchParticleUsage(pSurface, sentenceText);

            const rawCat = (token.grammar_elem_info && token.grammar_elem_info.category) || (pData && pData.category) || '格助詞';
            const catMeta = (typeof CATEGORY_MAP !== 'undefined' && CATEGORY_MAP[rawCat]) ? CATEGORY_MAP[rawCat] : {{ code: 'case', name: '格助詞', placeholder: '？格助' }};

            document.getElementById('popoverParticleTitle').innerHTML = `${{escapeHtml(pSurface)}} <span class="cat-badge cat-badge-${{catMeta.code}}">${{escapeHtml(catMeta.name)}}</span>`;
            document.getElementById('popoverParticleRole').textContent = usage ? usage.role : (token.grammar_elem_info ? token.grammar_elem_info.role : '語法功能');

            // 語境預覽 (將助詞挖空)
            const words = sentence ? sentence.words : [];
            const prev = wIdx > 0 ? words[wIdx - 1].surface : '';
            const next = wIdx + 1 < words.length ? words[wIdx + 1].surface : '';
            document.getElementById('popoverParticleContext').innerHTML = `
                ${{escapeHtml(prev)}}<span class="quiz-blank-slot" style="min-width:2.4rem;height:1.6rem;line-height:1.6rem;">${{catMeta.placeholder}}</span>${{escapeHtml(next)}}
            `;

            // 4 個選項：正確答案 + 3 個干擾項
            const distractors = (token.grammar_elem_info && token.grammar_elem_info.distractors) || (pData && pData.distractors) || ['は', 'が', 'を', 'に', 'で'];
            const wrongChoices = distractors.filter(d => d !== pSurface).sort(() => Math.random() - 0.5).slice(0, 3);
            const allChoices = [pSurface, ...wrongChoices].sort(() => Math.random() - 0.5);

            const optionsGrid = document.getElementById('popoverParticleOptions');
            optionsGrid.innerHTML = '';
            const feedbackBox = document.getElementById('popoverParticleFeedback');
            const substitutesBox = document.getElementById('popoverParticleSubstitutes');
            feedbackBox.style.display = 'none';
            substitutesBox.style.display = 'none';

            allChoices.forEach(opt => {{
                const btn = document.createElement('button');
                btn.className = 'btn-popover-opt';
                btn.textContent = opt;
                btn.onclick = () => {{
                    optionsGrid.querySelectorAll('.btn-popover-opt').forEach(b => b.disabled = true);
                    if (opt === pSurface) {{
                        btn.classList.add('correct');
                        btn.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${{opt}} (正確！)`;
                        targetEl.classList.add('revealed');
                    }} else {{
                        btn.classList.add('wrong');
                        btn.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> ${{opt}}`;
                        optionsGrid.querySelectorAll('.btn-popover-opt').forEach(b => {{
                            if (b.textContent === pSurface) b.classList.add('correct');
                        }});
                    }}

                    feedbackBox.style.display = 'block';
                    feedbackBox.innerHTML = `
                        <div style="font-size:0.84rem; line-height:1.45; color:var(--text-main); background:var(--bg-sub); padding:0.5rem 0.7rem; border-radius:6px; border-left:3px solid #f59e0b;">
                            <strong>【語法解析】</strong>${{escapeHtml(usage ? usage.desc : (token.grammar_elem_info ? token.grammar_elem_info.desc : '日語重要助詞與文型。'))}}
                        </div>
                    `;

                    if (token.grammar_elem_info && token.grammar_elem_info.grammar_id) {{
                        feedbackBox.innerHTML += `
                            <div style="margin-top:0.4rem;">
                                <button class="btn-grammar-detail" style="padding:0.25rem 0.6rem; font-size:0.78rem;" onclick="closeParticlePopover(); openGrammarDrawerById(${{token.grammar_elem_info.grammar_id}})">
                                    <i class="fa-solid fa-book-open"></i> 查看 941 文型庫詳解
                                </button>
                            </div>
                        `;
                    }}

                    if (usage && usage.substitutes && usage.substitutes.length > 0) {{
                        substitutesBox.style.display = 'block';
                        const firstSub = usage.substitutes[0];
                        const demoRewrite = generateParaphraseDemo(sentenceText, pSurface, firstSub.title);
                        substitutesBox.innerHTML = `
                            <div style="font-size:0.83rem; background:rgba(16,185,129,0.1); border:1px solid #a7f3d0; padding:0.55rem 0.75rem; border-radius:6px; color:#047857;">
                                <strong><i class="fa-solid fa-lightbulb"></i> 換句話說代用：</strong>
                                <div>可換用 <strong>${{escapeHtml(firstSub.title)}}</strong> [${{escapeHtml(firstSub.level)}}]</div>
                                ${{firstSub.grammarId ? `
                                    <button class="btn-grammar-detail" style="margin-top:0.35rem; padding:0.2rem 0.5rem; font-size:0.76rem;" onclick="closeParticlePopover(); openGrammarDrawerById(${{firstSub.grammarId}})">
                                        <i class="fa-solid fa-book-open"></i> 查看 941 文法詳解
                                    </button>
                                ` : ''}}
                            </div>
                        `;
                    }}
                }};
                optionsGrid.appendChild(btn);
            }});

            // 計算定位
            const rect = targetEl.getBoundingClientRect();
            popover.style.display = 'block';
            let left = rect.left;
            let top = rect.bottom + 8;
            if (left + 320 > window.innerWidth) left = window.innerWidth - 335;
            if (left < 10) left = 10;
            if (top + 280 > window.innerHeight) top = rect.top - 290;
            popover.style.left = `${{left}}px`;
            popover.style.top = `${{top}}px`;
        }}

        function closeParticlePopover() {{
            const popover = document.getElementById('particlePopover');
            if (popover) popover.style.display = 'none';
        }}

        // ==========================================================================
        // 全篇助詞測驗挑戰彈窗 (Full-Article Particle Quiz Challenge)
        // ==========================================================================

        let currentQuizCategoryFilter = 'all';

        function collectArticleParticleQuizItems() {{
            if (!state.analyzedData || !state.analyzedData.sentences) return [];
            const items = [];

            state.analyzedData.sentences.forEach((sentence, sIdx) => {{
                const words = sentence.words || [];
                const sText = sentence.text || '';

                words.forEach((w, wIdx) => {{
                    const s = w.surface;
                    const isGrammarElem = Boolean(w.is_grammar_elem || w.is_particle || (PARTICLE_DATA && PARTICLE_DATA[s]));
                    if (isGrammarElem) {{
                        const elInfo = w.grammar_elem_info || {{}};
                        const pData = getParticleData(s) || (elInfo.pData) || {{}};
                        const rawCat = elInfo.category || pData.category || '格助詞';
                        const catMeta = (typeof CATEGORY_MAP !== 'undefined' && CATEGORY_MAP[rawCat]) ? CATEGORY_MAP[rawCat] : {{ code: 'case', name: '格助詞', placeholder: '？格助' }};
                        const usage = matchParticleUsage(s, sText);
                        const distractors = pData && pData.distractors ? pData.distractors : (elInfo.distractors || ['は', 'が', 'を', 'に', 'で']);
                        const wrongChoices = distractors.filter(d => d !== s).sort(() => Math.random() - 0.5).slice(0, 3);
                        const allChoices = [s, ...wrongChoices].sort(() => Math.random() - 0.5);

                        // 建立挖空句子 HTML
                        let maskedHtml = '';
                        words.forEach((mw, mi) => {{
                            if (mi === wIdx) {{
                                maskedHtml += `<span class="quiz-blank-slot" title="【${{catMeta.name}}】">${{catMeta.placeholder}}</span>`;
                            }} else {{
                                maskedHtml += escapeHtml(mw.surface);
                            }}
                        }});

                        items.push({{
                            particle: s,
                            categoryCode: catMeta.code,
                            categoryName: catMeta.name,
                            title: elInfo.title || pData.default_role || s,
                            grammar_id: elInfo.grammar_id,
                            sentenceIdx: sIdx,
                            wordIdx: wIdx,
                            sentenceText: sText,
                            maskedHtml: maskedHtml,
                            options: allChoices,
                            usage: usage,
                            pData: pData,
                            elInfo: elInfo
                        }});
                    }}
                }});
            }});

            return items;
        }}

        function updateQuizCategoryCounts(allItems) {{
            const counts = {{ 'all': allItems.length, 'case': 0, 'adverbial': 0, 'compound': 0, 'sentence': 0 }};
            allItems.forEach(it => {{
                if (counts[it.categoryCode] !== undefined) counts[it.categoryCode]++;
            }});
            const elAll = document.getElementById('quizCountAll'); if (elAll) elAll.textContent = counts['all'];
            const elCase = document.getElementById('quizCountCase'); if (elCase) elCase.textContent = counts['case'];
            const elAdv = document.getElementById('quizCountAdverbial'); if (elAdv) elAdv.textContent = counts['adverbial'];
            const elCmp = document.getElementById('quizCountCompound'); if (elCmp) elCmp.textContent = counts['compound'];
            const elSen = document.getElementById('quizCountSentence'); if (elSen) elSen.textContent = counts['sentence'];
        }}

        function setQuizCategoryFilter(catCode) {{
            currentQuizCategoryFilter = catCode;
            const filterBtns = [
                ['all', document.getElementById('btnQuizFilterAll')],
                ['case', document.getElementById('btnQuizFilterCase')],
                ['adverbial', document.getElementById('btnQuizFilterAdverbial')],
                ['compound', document.getElementById('btnQuizFilterCompound')],
                ['sentence', document.getElementById('btnQuizFilterSentence')]
            ];
            filterBtns.forEach(([c, btn]) => {{
                if (btn) btn.classList.toggle('active', catCode === c);
            }});

            if (!state.quiz || !state.quiz.allItems) return;
            const filtered = catCode === 'all' ? state.quiz.allItems : state.quiz.allItems.filter(it => it.categoryCode === catCode);
            if (filtered.length === 0) {{
                showToast(`所選類別在本文中無題目`);
                return;
            }}
            state.quiz.items = filtered;
            state.quiz.currentIdx = 0;
            state.quiz.score = 0;
            state.quiz.answered = new Map();
            renderQuizQuestion();
        }}

        function openParticleQuizModal() {{
            closeParticlePopover();
            const allItems = collectArticleParticleQuizItems();
            if (allItems.length === 0) {{
                showToast('當前文章未偵測到助詞或文型，請先貼上文章或抓取網頁！');
                return;
            }}

            updateQuizCategoryCounts(allItems);

            const filteredItems = currentQuizCategoryFilter === 'all' 
                ? allItems 
                : allItems.filter(it => it.categoryCode === currentQuizCategoryFilter);

            state.quiz = {{
                allItems: allItems,
                items: filteredItems.length > 0 ? filteredItems : allItems,
                currentIdx: 0,
                score: 0,
                answered: new Map()
            }};

            renderQuizQuestion();
            dom.particleQuizModal.classList.add('open');
        }}

        function closeParticleQuizModal() {{
            dom.particleQuizModal.classList.remove('open');
        }}

        function renderQuizQuestion() {{
            const quiz = state.quiz;
            const curItem = quiz.items[quiz.currentIdx];
            if (!curItem) return;

            document.getElementById('quizCounterText').textContent = `第 ${{quiz.currentIdx + 1}} / ${{quiz.items.length}} 題`;
            document.getElementById('quizScoreText').innerHTML = `<i class="fa-solid fa-award"></i> 答對：${{quiz.score}} 題`;

            const progressPct = ((quiz.currentIdx + 1) / quiz.items.length) * 100;
            document.getElementById('quizProgressBar').style.width = `${{progressPct}}%`;

            const sentenceDisplay = document.getElementById('quizSentenceDisplay');
            const optionsContainer = document.getElementById('quizOptionsContainer');
            const feedbackCard = document.getElementById('quizFeedbackCard');

            sentenceDisplay.innerHTML = curItem.maskedHtml;
            optionsContainer.innerHTML = '';
            feedbackCard.style.display = 'none';

            const instructionEl = document.querySelector('.quiz-instruction');
            if (instructionEl) {{
                instructionEl.innerHTML = `請依句意、語境與結構，選出正確的 <span class="cat-badge cat-badge-${{curItem.categoryCode}}">${{escapeHtml(curItem.categoryName)}}</span>：`;
            }}

            const hasAnswered = quiz.answered.has(quiz.currentIdx);
            const prevAnswer = hasAnswered ? quiz.answered.get(quiz.currentIdx) : null;

            curItem.options.forEach((opt, optIdx) => {{
                const btn = document.createElement('button');
                btn.className = 'btn-quiz-option';
                btn.innerHTML = `<strong>${{String.fromCharCode(65 + optIdx)}}.</strong> ${{escapeHtml(opt)}}`;

                if (hasAnswered) {{
                    btn.disabled = true;
                    if (opt === curItem.particle) {{
                        btn.classList.add('correct');
                        btn.innerHTML += ' <i class="fa-solid fa-check"></i>';
                    }} else if (opt === prevAnswer) {{
                        btn.classList.add('wrong');
                        btn.innerHTML += ' <i class="fa-solid fa-xmark"></i>';
                    }}
                }} else {{
                    btn.onclick = () => answerQuizOption(opt, btn);
                }}

                optionsContainer.appendChild(btn);
            }});

            if (hasAnswered) {{
                showQuizFeedback(prevAnswer === curItem.particle);
            }}

            document.getElementById('btnQuizPrev').disabled = (quiz.currentIdx === 0);
            document.getElementById('btnQuizNext').disabled = (quiz.currentIdx === quiz.items.length - 1);
        }}

        function answerQuizOption(chosenOpt, clickedBtn) {{
            const quiz = state.quiz;
            const curItem = quiz.items[quiz.currentIdx];
            if (!curItem || quiz.answered.has(quiz.currentIdx)) return;

            const isCorrect = (chosenOpt === curItem.particle);
            quiz.answered.set(quiz.currentIdx, chosenOpt);

            if (isCorrect) {{
                quiz.score++;
                document.getElementById('quizScoreText').innerHTML = `<i class="fa-solid fa-award"></i> 答對：${{quiz.score}} 題`;
            }}

            // 更新選項狀態
            const container = document.getElementById('quizOptionsContainer');
            container.querySelectorAll('.btn-quiz-option').forEach(btn => {{
                btn.disabled = true;
                if (btn.textContent.includes(curItem.particle)) {{
                    btn.classList.add('correct');
                }}
            }});

            if (!isCorrect && clickedBtn) {{
                clickedBtn.classList.add('wrong');
            }}

            // 替換挖空處為答案
            document.getElementById('quizSentenceDisplay').innerHTML = curItem.sentenceText.replace(
                curItem.particle,
                `<span class="quiz-blank-slot" style="background:#d1fae5;color:#065f46;border-color:#10b981;">${{curItem.particle}}</span>`
            );

            showQuizFeedback(isCorrect);
        }}

        function showQuizFeedback(isCorrect) {{
            const quiz = state.quiz;
            const curItem = quiz.items[quiz.currentIdx];
            const feedbackCard = document.getElementById('quizFeedbackCard');
            feedbackCard.style.display = 'block';

            const usage = curItem.usage;
            let substitutesHtml = '';

            if (usage && usage.substitutes && usage.substitutes.length > 0) {{
                let listHtml = '';
                usage.substitutes.forEach(sub => {{
                    const demoRewrite = generateParaphraseDemo(curItem.sentenceText, curItem.particle, sub.title);
                    listHtml += `
                        <div style="margin-top:0.45rem; background:var(--bg-card); padding:0.5rem 0.75rem; border-radius:6px; border:1px solid var(--border-color);">
                            <div style="display:flex; align-items:center; gap:0.4rem; flex-wrap:wrap;">
                                <span class="substitute-tag">${{escapeHtml(sub.type)}}</span>
                                <strong style="color:var(--text-main); font-family:var(--font-jp);">${{escapeHtml(sub.title)}}</strong>
                                <span class="badge-jlpt badge-${{(sub.level || 'n2').toLowerCase().replace('~','_')}}">${{escapeHtml(sub.level)}}</span>
                            </div>
                            <div style="font-size:0.83rem; color:var(--text-muted); margin-top:0.2rem;">${{escapeHtml(sub.desc || '')}}</div>
                            ${{demoRewrite ? `
                                <div class="paraphrase-demo-box">
                                    <strong><i class="fa-solid fa-pen-nib"></i> 換句話說：</strong>
                                    <span>${{demoRewrite}}</span>
                                </div>
                            ` : ''}}
                            ${{sub.grammarId ? `
                                <div style="margin-top:0.35rem;">
                                    <button class="btn-grammar-detail" style="padding:0.2rem 0.5rem; font-size:0.78rem;" onclick="openGrammarDrawerById(${{sub.grammarId}})">
                                        <i class="fa-solid fa-book-open"></i> 查閱 941 語法庫完整抽屜
                                    </button>
                                </div>
                            ` : ''}}
                        </div>
                    `;
                }});

                substitutesHtml = `
                    <div style="margin-top:0.8rem; border-top:1px dashed var(--border-color); padding-top:0.6rem;">
                        <strong style="color:#059669; font-size:0.88rem;"><i class="fa-solid fa-shuffle"></i> 有無代用的助詞及文型？換句話說解析：</strong>
                        ${{listHtml}}
                    </div>
                `;
            }}

            feedbackCard.innerHTML = `
                <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem;">
                    <span style="font-size:1.1rem; font-weight:800; color:${{isCorrect ? '#10b981' : '#ef4444'}};">
                        ${{isCorrect ? '<i class="fa-solid fa-circle-check"></i> 答對了！' : '<i class="fa-solid fa-circle-xmark"></i> 答錯了！正確助詞是「' + curItem.particle + '」'}}
                    </span>
                    <span class="particle-role-badge">${{escapeHtml(usage ? usage.role : '格助詞')}}</span>
                </div>
                <div style="font-size:0.88rem; color:var(--text-main); line-height:1.5;">
                    <strong>【本句用法】</strong>${{escapeHtml(usage ? usage.desc : '助詞在日語中連接名詞與動詞，構成句子核心語意骨架。')}}
                </div>
                ${{substitutesHtml}}
            `;
        }}

        function revealCurrentQuizAnswer() {{
            const quiz = state.quiz;
            const curItem = quiz.items[quiz.currentIdx];
            if (!curItem) return;
            answerQuizOption(curItem.particle, null);
        }}

        function navQuiz(delta) {{
            const quiz = state.quiz;
            const newIdx = quiz.currentIdx + delta;
            if (newIdx >= 0 && newIdx < quiz.items.length) {{
                quiz.currentIdx = newIdx;
                renderQuizQuestion();
            }}
        }}

        function speakQuizSentence() {{
            const quiz = state.quiz;
            const curItem = quiz.items[quiz.currentIdx];
            if (curItem && curItem.sentenceText) {{
                speakJapanese(curItem.sentenceText);
            }}
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

    print("[4/5] 寫入獨立網頁檔案...")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

    with open("japanese_reader.html", "w", encoding="utf-8") as f:
        f.write(html_template)

    with open("static/index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

    size_kb = os.path.getsize("index.html") / 1024
    print(f"[OK] 產出完成！index.html, japanese_reader.html, static/index.html 已更新，檔案大小：{size_kb:.1f} KB")

if __name__ == "__main__":
    build()
