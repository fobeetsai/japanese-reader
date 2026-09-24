# -*- coding: utf-8 -*-
"""
日文小說閱讀器 (Novel Master) 產生器 - 全方位升級版
以 master.html 為基礎，打造專屬小說沉浸閱讀工作台：
1. 萬能檔案導入：PDF (.pdf), EPUB (.epub), TXT (.txt), Word (.docx), Markdown (.md), 剪貼簿貼上, 內建名作
2. 彈性頁數選擇器：自動分析總頁數/總字數，可自訂起始頁與結束頁（如 1~5 頁、1~10 頁、單頁精讀），避免整本小說一次性載入卡頓
3. 閱讀進度記憶：自動記憶每本書讀到的頁數，下次開啟一鍵接續閱讀
4. 沉浸式排版：縱書 (日文直排豎讀 writing-mode: vertical-rl) 與 橫書 (橫排) 一鍵切換
5. 四大經典主題：紙質暖黃、清新豆沙綠、夜間深色、水墨純白
6. 全新獨立強韌語音朗讀系統 (NovelAudioEngine)：
   - 支援 播放、暫停 (Pause)、繼續 (Resume)、停止 (Stop)
   - 多重降級保障：微軟七海/圭太真人音 -> Google 日本語 -> 系統日語 -> Web Speech 合成音 -> Google TTS 音訊，100% 絕對能發出聲音！
   - 自訂重複次數：1次、2次、3次 (跟讀特訓)、5次 (聽寫特訓)、∞ 無限循環 (單句復讀)
   - Karaoke 隨音變色高亮追蹤
7. 單句選取與朗讀 (Sentence Selection & Playback)：
   - 點擊任何句子即選取該句，浮現專屬控制列：朗讀、暫停、重複、收藏、翻譯、文法
8. 收藏句子功能 (Favorite Sentences Library)：
   - 每句皆有 ⭐ 收藏按鈕，點擊即存入本機句子庫
   - 頂部提供「⭐ 收藏句子 (X)」抽屜面板，可查看、發音、複製與導出
9. 941 文法深度解說即時彈出：
   - 點擊含有文法的字詞或句子旁的文法膠囊標籤，立即彈出 941 文型卡片（級別、接續、含義、例句）
"""

import os
import re
import sys
import shutil

def build():
    root = r"C:\Users\fobee\我的雲端硬碟\Antigravity Apps\Ai agent"
    master_path = os.path.join(root, "master.html")
    
    if not os.path.exists(master_path):
        print(f"[Error] 找不到基礎檔案：{master_path}")
        return

    print("[1/4] 讀取 master.html 核心資源...")
    with open(master_path, "r", encoding="utf-8") as f:
        master_html = f.read()

    # 提取 <style> 內容
    style_match = re.search(r'<style>(.*?)</style>', master_html, re.DOTALL)
    master_css = style_match.group(1) if style_match else ""

    # 提取各 <script> 區塊
    scripts = list(re.finditer(r'<script([^>]*)>(.*?)</script>', master_html, re.DOTALL))
    
    # Script 1: Database (GRAMMAR_DATA, JLPT_VOCAB, KANJI_COMPACT, PARTICLE_DATA)
    db_script = scripts[0].group(2)
    # Script 2: Tokenizer, morphological analysis, grammar pattern matcher
    nlp_script = scripts[1].group(2)
    # Script 3: Core UI state, helpers, word popover, particle logic
    core_ui_script = scripts[2].group(2)
    # Script 5: AnkiFlash bridge
    anki_script = scripts[4].group(2)

    print("[2/4] 設計小說閱讀專屬樣式與排版...")
    
    novel_css = """
/* ==========================================================================
   日文小說閱讀器 (Novel Master) 專屬沉浸式樣式
   ========================================================================== */

:root {
    --novel-bg: #fcf8f2;
    --novel-text: #2c2724;
    --novel-card-bg: rgba(255, 255, 255, 0.9);
    --novel-border: rgba(44, 39, 36, 0.12);
    --novel-accent: #d97706;
    --novel-accent-hover: #b45309;
    --novel-font-size: 1.25rem;
    --novel-line-height: 2.2;
    --novel-ruby-size: 0.58em;
}

/* 經典暖黃紙質 */
body[data-novel-theme="sepia"] {
    --novel-bg: #fbf6ec;
    --novel-text: #2d261e;
    --novel-card-bg: #f5eedf;
    --novel-border: #e3d5be;
    background-color: var(--novel-bg) !important;
    color: var(--novel-text) !important;
}

/* 清新護眼豆沙綠 */
body[data-novel-theme="mint"] {
    --novel-bg: #edf5ed;
    --novel-text: #1e3321;
    --novel-card-bg: #e1ede1;
    --novel-border: #c8dec8;
    background-color: var(--novel-bg) !important;
    color: var(--novel-text) !important;
}

/* 沉浸夜間暗黑 */
body[data-novel-theme="dark"] {
    --novel-bg: #181920;
    --novel-text: #d2d5e2;
    --novel-card-bg: #21222c;
    --novel-border: #323444;
    background-color: var(--novel-bg) !important;
    color: var(--novel-text) !important;
}

/* 簡約水墨純白 */
body[data-novel-theme="white"] {
    --novel-bg: #ffffff;
    --novel-text: #1f2937;
    --novel-card-bg: #f9fafb;
    --novel-border: #e5e7eb;
    background-color: var(--novel-bg) !important;
    color: var(--novel-text) !important;
}

/* 字體風格 */
body[data-novel-font="serif"] .novel-text-content,
body[data-novel-font="serif"] .sentence-jp-text,
body[data-novel-font="serif"] .novel-paragraph {
    font-family: "Noto Serif JP", "Source Han Serif JP", "Yu Mincho", "Hiragino Mincho ProN", serif !important;
}
body[data-novel-font="sans"] .novel-text-content,
body[data-novel-font="sans"] .sentence-jp-text,
body[data-novel-font="sans"] .novel-paragraph {
    font-family: "Noto Sans JP", "Source Han Sans JP", "Yu Gothic", sans-serif !important;
}

.novel-app-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 16px 20px 80px 20px;
    transition: all 0.25s ease;
}

/* 檔案匯入面板 */
.novel-import-card {
    background: var(--novel-card-bg);
    border: 2px dashed var(--novel-border);
    border-radius: 16px;
    padding: 32px 24px;
    text-align: center;
    margin-bottom: 24px;
    transition: all 0.2s ease;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}
.novel-import-card:hover, .novel-import-card.drag-over {
    border-color: var(--novel-accent);
    background: rgba(217, 119, 6, 0.04);
    transform: translateY(-2px);
}
.novel-dropzone-icon {
    font-size: 3.2rem;
    color: var(--novel-accent);
    margin-bottom: 12px;
}
.novel-file-types {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 8px;
    margin: 16px 0;
}
.file-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.8rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.06);
    color: var(--novel-text);
}
body[data-novel-theme="dark"] .file-badge {
    background: rgba(255, 255, 255, 0.1);
}
.file-badge.pdf { color: #dc2626; }
.file-badge.epub { color: #2563eb; }
.file-badge.txt { color: #059669; }
.file-badge.docx { color: #0284c7; }

/* 範本名作推薦鈕 */
.novel-samples-row {
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid var(--novel-border);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    gap: 10px;
}
.sample-novel-btn {
    border: 1px solid var(--novel-border);
    background: rgba(255, 255, 255, 0.5);
    color: var(--novel-text);
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.86rem;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
}
body[data-novel-theme="dark"] .sample-novel-btn {
    background: rgba(255, 255, 255, 0.08);
}
.sample-novel-btn:hover {
    border-color: var(--novel-accent);
    color: var(--novel-accent);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(217, 119, 6, 0.2);
}

/* 頁數選擇器卡片 */
.page-selector-card {
    background: var(--novel-card-bg);
    border: 1.5px solid var(--novel-border);
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 24px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.06);
    display: none;
    animation: fadeInModal 0.25s ease;
}
@keyframes fadeInModal {
    from { opacity: 0; transform: translateY(-8px); }
    to { opacity: 1; transform: translateY(0); }
}
.page-selector-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--novel-border);
}
.book-meta-title {
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--novel-accent);
    display: flex;
    align-items: center;
    gap: 10px;
}
.book-total-pages {
    font-size: 0.92rem;
    font-weight: 700;
    padding: 4px 12px;
    background: rgba(217, 119, 6, 0.12);
    color: var(--novel-accent);
    border-radius: 9999px;
}
.page-range-selector-box {
    background: rgba(0, 0, 0, 0.02);
    border: 1px solid var(--novel-border);
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 18px;
}
body[data-novel-theme="dark"] .page-range-selector-box {
    background: rgba(255, 255, 255, 0.03);
}
.page-inputs-row {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    gap: 16px;
    font-size: 1.05rem;
    font-weight: 700;
}
.page-num-input {
    width: 80px;
    padding: 8px 12px;
    font-size: 1.15rem;
    font-weight: 800;
    text-align: center;
    border: 2px solid var(--novel-border);
    border-radius: 8px;
    background: var(--novel-bg);
    color: var(--novel-text);
    outline: none;
    transition: border-color 0.2s;
}
.page-num-input:focus {
    border-color: var(--novel-accent);
    box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.2);
}
.quick-batch-buttons {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 14px;
}
.quick-batch-btn {
    border: 1px solid var(--novel-border);
    background: var(--novel-bg);
    color: var(--novel-text);
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 0.88rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
}
.quick-batch-btn:hover {
    background: var(--novel-accent);
    color: #fff;
    border-color: var(--novel-accent);
}
.range-slider-wrap {
    margin-top: 18px;
    padding: 0 8px;
}
.range-slider-wrap input[type="range"] {
    width: 100%;
    accent-color: var(--novel-accent);
    cursor: pointer;
}
.resume-bookmark-prompt {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 16px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 10px;
    margin-bottom: 16px;
    color: #065f46;
    font-size: 0.92rem;
    font-weight: 600;
}
body[data-novel-theme="dark"] .resume-bookmark-prompt {
    color: #34d399;
}
.btn-resume-bookmark {
    background: #059669;
    color: #fff;
    border: none;
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.15s;
}
.btn-resume-bookmark:hover {
    background: #047857;
}

/* 小說導航控制列 (Novel Sticky Reading Toolbar) */
.novel-reading-toolbar {
    position: sticky;
    top: 48px;
    z-index: 50;
    background: var(--novel-card-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--novel-border);
    border-radius: 14px;
    padding: 10px 16px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
}
.novel-nav-group {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
}
.novel-tool-btn {
    border: 1px solid var(--novel-border);
    background: var(--novel-bg);
    color: var(--novel-text);
    padding: 6px 12px;
    border-radius: 8px;
    font-size: 0.88rem;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: all 0.15s;
    user-select: none;
}
.novel-tool-btn:hover {
    background: rgba(217, 119, 6, 0.12);
    border-color: var(--novel-accent);
    color: var(--novel-accent);
}
.novel-tool-btn.active {
    background: var(--novel-accent);
    color: #fff;
    border-color: var(--novel-accent);
}
.novel-tool-btn.btn-audio-play {
    background: linear-gradient(135deg, #10b981, #059669);
    color: #fff;
    font-weight: 700;
    border-color: #059669;
}
.novel-tool-btn.btn-audio-pause {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: #fff;
    font-weight: 700;
    border-color: #d97706;
}
.novel-tool-btn.btn-audio-stop {
    background: rgba(239, 68, 68, 0.12);
    color: #dc2626;
    border-color: rgba(239, 68, 68, 0.3);
}
.novel-page-indicator {
    font-size: 0.95rem;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.05);
    color: var(--novel-text);
}
body[data-novel-theme="dark"] .novel-page-indicator {
    background: rgba(255, 255, 255, 0.08);
}
.novel-progress-bar-container {
    width: 100%;
    height: 4px;
    background: rgba(0, 0, 0, 0.08);
    border-radius: 2px;
    overflow: hidden;
    margin-top: 4px;
}
body[data-novel-theme="dark"] .novel-progress-bar-container {
    background: rgba(255, 255, 255, 0.1);
}
.novel-progress-bar-fill {
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg, #d97706, #f59e0b);
    transition: width 0.3s ease;
}

/* ==========================================================================
   小說閱讀核心區域 (支援 縱書 vertical-rl 與 橫書 horizontal-tb)
   ========================================================================== */
.novel-reader-deck {
    background: var(--novel-card-bg);
    border: 1px solid var(--novel-border);
    border-radius: 16px;
    padding: 36px 40px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
    min-height: 600px;
    position: relative;
    transition: all 0.25s ease;
}

/* 橫書模式 (Horizontal) */
.novel-reader-deck.mode-horizontal {
    writing-mode: horizontal-tb !important;
    line-height: var(--novel-line-height);
    font-size: var(--novel-font-size);
}
.mode-horizontal .novel-paragraph {
    margin-bottom: 1.6em;
    text-indent: 1em;
    word-break: break-word;
    position: relative;
}

/* 縱書模式 (Vertical Writing - 日文小說正宗直排) */
.novel-reader-deck.mode-vertical {
    writing-mode: vertical-rl !important;
    text-orientation: upright !important;
    line-height: var(--novel-line-height) !important;
    font-size: var(--novel-font-size) !important;
    height: 720px !important;
    max-height: 80vh !important;
    overflow-x: auto !important;
    overflow-y: hidden !important;
    padding: 40px 32px !important;
    -webkit-overflow-scrolling: touch;
    box-sizing: border-box;
}
.mode-vertical .novel-paragraph {
    margin-left: 2.2em;
    margin-bottom: 0;
    text-indent: 1em;
    display: inline-block;
    vertical-align: top;
}
.mode-vertical ruby {
    ruby-position: right;
}
.mode-vertical .sentence-row {
    display: inline;
}

/* 單頁分界標籤 */
.novel-page-divider {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    margin: 28px 0;
    color: var(--novel-accent);
    font-size: 0.88rem;
    font-weight: 800;
    letter-spacing: 1px;
    border-bottom: 1px dashed var(--novel-border);
    padding-bottom: 12px;
}
.mode-vertical .novel-page-divider {
    margin: 0 28px;
    padding-bottom: 0;
    padding-left: 12px;
    border-bottom: none;
    border-left: 1px dashed var(--novel-border);
    height: 100%;
}

/* 單字與假名 */
.word-token {
    cursor: pointer;
    border-radius: 4px;
    padding: 0 1px;
    transition: background 0.15s;
    user-select: text;
}
.word-token:hover {
    background: rgba(217, 119, 6, 0.18) !important;
}

/* 941 文法高亮標記 */
.grammar-highlight {
    border-bottom: 2.5px solid #6366f1 !important;
    background: rgba(99, 102, 241, 0.12) !important;
    border-radius: 3px;
    cursor: pointer;
    position: relative;
}
.grammar-highlight:hover {
    background: rgba(99, 102, 241, 0.25) !important;
    box-shadow: 0 0 8px rgba(99, 102, 241, 0.4);
}
.grammar-highlight::after {
    content: '🔖';
    font-size: 0.65em;
    position: relative;
    top: -0.6em;
    margin-left: 1px;
}
body[data-novel-grammar="hide"] .grammar-highlight {
    background: transparent !important;
    border-bottom: none !important;
}
body[data-novel-grammar="hide"] .grammar-highlight::after {
    display: none !important;
}

/* 句子旁的文法標籤膠囊 (Grammar Pill) */
.novel-grammar-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.72rem;
    font-weight: 800;
    padding: 2px 7px;
    border-radius: 6px;
    background: rgba(99, 102, 241, 0.15);
    color: #6366f1;
    border: 1px solid rgba(99, 102, 241, 0.35);
    cursor: pointer;
    vertical-align: middle;
    margin: 0 3px;
    transition: all 0.15s ease;
    user-select: none;
}
.novel-grammar-badge:hover {
    background: #6366f1;
    color: #ffffff;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}
body[data-novel-grammar="hide"] .novel-grammar-badge {
    display: none !important;
}

/* 假名注音模式切換 */
body[data-novel-ruby="hard-only"] .word-token[data-jlpt="N5"] ruby rt,
body[data-novel-ruby="hard-only"] .word-token[data-jlpt="N4"] ruby rt {
    display: none !important;
}
body[data-novel-ruby="hide"] ruby rt {
    display: none !important;
}
body[data-novel-ruby="hide"] .word-token:hover ruby rt {
    display: block !important;
    color: var(--novel-accent) !important;
}

/* JLPT色彩開關 */
body[data-novel-vocab-color="hide"] .word-token {
    color: inherit !important;
}

/* 句子行 (Sentence Row) 與選取狀態 */
.sentence-row {
    position: relative;
    border-radius: 6px;
    transition: all 0.15s ease;
    padding: 2px 4px;
    cursor: pointer;
}
.sentence-row:hover {
    background: rgba(217, 119, 6, 0.08);
}
.sentence-row.selected-sentence {
    background: rgba(217, 119, 6, 0.14) !important;
    outline: 2px solid var(--novel-accent);
    box-shadow: 0 2px 10px rgba(217, 119, 6, 0.2);
}

/* 收藏按鈕 (Star on Sentence) */
.sentence-star-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: none;
    background: transparent;
    color: rgba(0, 0, 0, 0.25);
    cursor: pointer;
    font-size: 0.85rem;
    margin: 0 3px;
    vertical-align: middle;
    transition: all 0.15s ease;
}
body[data-novel-theme="dark"] .sentence-star-btn {
    color: rgba(255, 255, 255, 0.3);
}
.sentence-star-btn:hover {
    color: #eab308;
    transform: scale(1.2);
}
.sentence-star-btn.is-fav {
    color: #eab308 !important;
    text-shadow: 0 0 8px rgba(234, 179, 8, 0.5);
}

/* Karaoke 隨音變色高亮 */
.karaoke-current-word {
    background: #fde047 !important;
    color: #854d0e !important;
    border-radius: 4px;
    box-shadow: 0 0 10px rgba(250, 204, 21, 0.8);
    font-weight: 800;
}
body[data-novel-theme="dark"] .karaoke-current-word {
    background: #ca8a04 !important;
    color: #ffffff !important;
}
.karaoke-active-sentence {
    background: rgba(217, 119, 6, 0.16) !important;
    border-radius: 6px;
    box-shadow: 0 0 12px rgba(217, 119, 6, 0.2);
}

/* 句子專屬浮動操作欄 (Floating Sentence Action Toolbar) */
.sentence-floating-toolbar {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%) translateY(100px);
    z-index: 9999;
    background: var(--novel-card-bg);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1.5px solid var(--novel-border);
    border-radius: 9999px;
    padding: 8px 16px;
    box-shadow: 0 10px 35px rgba(0, 0, 0, 0.2);
    display: flex;
    align-items: center;
    gap: 8px;
    transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s;
    opacity: 0;
    pointer-events: none;
}
.sentence-floating-toolbar.active {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
    pointer-events: auto;
}
.s-bar-btn {
    border: 1px solid var(--novel-border);
    background: var(--novel-bg);
    color: var(--novel-text);
    padding: 7px 13px;
    border-radius: 9999px;
    font-size: 0.86rem;
    font-weight: 700;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: all 0.15s;
    white-space: nowrap;
}
.s-bar-btn:hover {
    background: var(--novel-accent);
    color: #fff;
    border-color: var(--novel-accent);
}
.s-bar-btn.primary {
    background: linear-gradient(135deg, #10b981, #059669);
    color: #fff;
    border-color: #059669;
}
.s-bar-btn.pause-btn {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: #fff;
    border-color: #d97706;
}

/* 句子收藏中心抽屜 / 彈窗 */
.saved-sentences-modal {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.55);
    z-index: 99999;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(5px);
}
.saved-sentences-content {
    background: var(--novel-card-bg);
    border: 1.5px solid var(--novel-border);
    border-radius: 20px;
    padding: 24px;
    max-width: 780px;
    width: 92%;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 16px 45px rgba(0, 0, 0, 0.3);
}
.saved-sentences-list {
    overflow-y: auto;
    flex: 1;
    padding-right: 6px;
    margin: 16px 0;
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.saved-sentence-item {
    background: var(--novel-bg);
    border: 1px solid var(--novel-border);
    border-radius: 12px;
    padding: 14px 16px;
    transition: all 0.15s;
}
.saved-sentence-item:hover {
    border-color: var(--novel-accent);
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
}

/* 底部導覽 */
.novel-bottom-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 24px;
    padding: 12px 18px;
    background: var(--novel-card-bg);
    border: 1px solid var(--novel-border);
    border-radius: 12px;
}

@media (max-width: 768px) {
    .novel-app-container {
        padding: 10px 12px 60px 12px;
    }
    .novel-reader-deck {
        padding: 20px 16px;
    }
    .mode-vertical {
        height: 560px !important;
    }
    .novel-reading-toolbar {
        top: 40px;
        padding: 8px 10px;
    }
    .sentence-floating-toolbar {
        bottom: 12px;
        padding: 6px 10px;
        gap: 4px;
        width: 96%;
        justify-content: space-around;
    }
    .s-bar-btn {
        padding: 6px 8px;
        font-size: 0.78rem;
    }
}
"""

    print("[3/4] 整合 HTML 架構與升級版小說引擎...")
    
    novel_html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>日文小說閱讀器 (Novel Master) | PDF/EPUB/TXT多格式導入・自選頁數・縱橫排切換・941文法與自然朗讀</title>
    
    <!-- Google Fonts & Font Awesome -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700;900&family=Noto+Sans+TC:wght@400;500;600;700;900&family=Noto+Serif+JP:wght@500;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- PDF.js (Mozilla) 萬能 PDF 閱讀解析庫 -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script>
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    </script>
    
    <!-- JSZip (EPUB / Word docx 萬能解包解析庫) -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>

    <!-- 站台統一整合樣式 -->
    <link rel="stylesheet" href="static/cross_nav.css">
    
    <!-- 閱讀高手核心繼承樣式 -->
    <style>
{master_css}
{novel_css}
    </style>
</head>
<body data-theme="light" data-novel-theme="sepia" data-novel-font="serif" data-novel-ruby="show" data-novel-grammar="show" data-novel-vocab-color="show">

    <!-- 全站同源統一頂部導覽列 -->
    <nav class="cross-app-nav-bar" id="learningAppsNav" aria-label="其他學習工具">
        <a href="master.html" class="nav-brand">
            <span>🇯🇵 日語學習全方位生態系</span>
            <span class="badge-sync">小說閱讀專用版</span>
        </a>
        <div class="nav-group">
            <a href="master.html" class="nav-link-btn" title="閱讀高手（大成版）：句解霸、941文法、沉浸雙語、跟讀聽力">
                <span>👑 閱讀高手</span>
            </a>
            <a href="novel.html" class="nav-link-btn active-novel" title="日文小說閱讀器：PDF/EPUB/TXT多格式導入・自選頁數・縱橫排切換">
                <span>📚 小說閱讀</span>
            </a>
            <a href="index.html" class="nav-link-btn" title="日文閱讀助手：基礎閱讀拆解">
                <span>📖 閱讀助手</span>
            </a>
            <a href="kanji.html" class="nav-link-btn" title="漢字記憶道場：2101常用漢字音訓讀道場">
                <span>🈩 漢字道場</span>
            </a>
            <a href="flashcard.html" class="nav-link-btn" title="AnkiFlash 抽認卡：間隔重複複習系統">
                <span>🎴 AnkiFlash</span>
            </a>
        </div>
    </nav>

    <div class="novel-app-container">

        <!-- 檔案匯入面板 (可導入任何類型的檔案 如PDF 等) -->
        <section class="novel-import-card" id="novelImportCard">
            <div class="novel-dropzone-icon">
                <i class="fa-solid fa-book-open-reader"></i>
            </div>
            <h2 style="font-size: 1.6rem; font-weight: 800; margin-bottom: 8px;">開啟日文小說與萬能文件</h2>
            <p style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 16px;">
                支援拖曳或上傳各類日文書籍，支援<strong>自訂頁數範圍解析</strong>，一本再厚也能輕鬆分頁精讀！
            </p>

            <div class="novel-file-types">
                <span class="file-badge pdf"><i class="fa-solid fa-file-pdf"></i> PDF (.pdf)</span>
                <span class="file-badge epub"><i class="fa-solid fa-book"></i> EPUB (.epub)</span>
                <span class="file-badge txt"><i class="fa-solid fa-file-lines"></i> 青空文庫/純文字 (.txt)</span>
                <span class="file-badge docx"><i class="fa-solid fa-file-word"></i> Word (.docx)</span>
                <span class="file-badge"><i class="fa-solid fa-file-code"></i> Markdown (.md)</span>
            </div>

            <div style="display: flex; justify-content: center; gap: 12px; margin-top: 14px;">
                <label class="btn-primary" style="padding: 10px 24px; font-size: 1.05rem; border-radius: 10px; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #d97706, #b45309); color: #fff; font-weight: 700; box-shadow: 0 4px 14px rgba(217, 119, 6, 0.35);">
                    <i class="fa-solid fa-folder-open"></i> 選擇檔案 (PDF/EPUB/TXT/DOCX)
                    <input type="file" id="novelFileInput" accept=".pdf,.epub,.txt,.docx,.md,.text" style="display: none;">
                </label>
                <button class="pill-btn" id="btnOpenPasteModal" style="padding: 10px 18px; font-weight: 700;">
                    <i class="fa-solid fa-paste"></i> 貼上文章
                </button>
            </div>

            <!-- 名著範本文摘快速載入 -->
            <div class="novel-samples-row">
                <span style="font-size: 0.85rem; font-weight: 700; color: var(--text-muted);"><i class="fa-solid fa-wand-magic-sparkles"></i> 名作試讀：</span>
                <button class="sample-novel-btn" onclick="loadSampleNovel('kokoro')">
                    <span>🌸 夏目漱石《心》</span>
                </button>
                <button class="sample-novel-btn" onclick="loadSampleNovel('melos')">
                    <span>🏃 太宰治《走れメロス》</span>
                </button>
                <button class="sample-novel-btn" onclick="loadSampleNovel('ginga')">
                    <span>🌌 宮沢賢治《銀河鉄道の夜》</span>
                </button>
                <button class="sample-novel-btn" onclick="loadSampleNovel('rashomon')">
                    <span>⛩️ 芥川龍之介《羅生門》</span>
                </button>
            </div>
        </section>

        <!-- 頁數選擇器卡片 (可選頁數，要不然一本太多) -->
        <section class="page-selector-card" id="pageSelectorCard">
            <div class="page-selector-header">
                <div class="book-meta-title">
                    <i class="fa-solid fa-book-bookmark"></i>
                    <span id="selectorBookTitle">檔案名稱</span>
                </div>
                <div class="book-total-pages" id="selectorTotalPagesBadge">
                    共 1 頁
                </div>
            </div>

            <!-- 上次閱讀進度記憶提醒 -->
            <div class="resume-bookmark-prompt" id="resumeBookmarkPrompt" style="display: none;">
                <span><i class="fa-solid fa-bookmark text-emerald-600"></i> 您上次閱讀至第 <strong id="resumePageNum">1</strong> 頁</span>
                <button class="btn-resume-bookmark" id="btnResumeLastRead">
                    <i class="fa-solid fa-play"></i> 接續上次進度
                </button>
            </div>

            <div class="page-range-selector-box">
                <div style="text-align: center; margin-bottom: 12px; font-size: 0.95rem; color: var(--text-muted);">
                    <i class="fa-solid fa-circle-info text-amber-500"></i> 日文書籍篇幅宏大，建議每次選擇 <strong>1 ~ 10 頁</strong> 分批精讀解析，兼顧極速載入與深度文法拆解！
                </div>

                <div class="page-inputs-row">
                    <span>從第</span>
                    <input type="number" id="inputStartPage" class="page-num-input" min="1" value="1">
                    <span>頁　至　第</span>
                    <input type="number" id="inputEndPage" class="page-num-input" min="1" value="5">
                    <span>頁</span>
                </div>

                <div class="range-slider-wrap">
                    <input type="range" id="pageRangeSlider" min="1" max="100" value="1">
                </div>

                <div class="quick-batch-buttons">
                    <button class="quick-batch-btn" onclick="setPageBatch(1)">單頁精讀 (1 頁)</button>
                    <button class="quick-batch-btn" onclick="setPageBatch(5)">讀 5 頁 (推薦)</button>
                    <button class="quick-batch-btn" onclick="setPageBatch(10)">讀 10 頁</button>
                    <button class="quick-batch-btn" onclick="setPageBatch(20)">讀 20 頁</button>
                    <button class="quick-batch-btn" onclick="shiftPageBatch(1)">下一批 ⏩</button>
                </div>
            </div>

            <div style="display: flex; justify-content: center; gap: 14px;">
                <button class="btn-primary" id="btnStartNovelReading" style="padding: 12px 36px; font-size: 1.15rem; font-weight: 800; border-radius: 12px; background: linear-gradient(135deg, #d97706, #b45309); color: #fff; cursor: pointer; box-shadow: 0 4px 16px rgba(217, 119, 6, 0.4);">
                    <i class="fa-solid fa-bolt"></i> 開始解析並閱讀所選頁面
                </button>
                <button class="pill-btn" onclick="closePageSelector()" style="padding: 12px 20px;">
                    取消
                </button>
            </div>
        </section>

        <!-- 閱讀載入中狀態 -->
        <div id="novelLoadingState" style="display: none; align-items: center; justify-content: center; flex-direction: column; gap: 14px; padding: 60px 0;">
            <i class="fa-solid fa-spinner fa-spin" style="font-size: 2.8rem; color: var(--novel-accent);"></i>
            <div id="novelLoadingText" style="font-size: 1.1rem; font-weight: 700; color: var(--novel-accent);">正在提取頁面文字並執行 941 文法標註與日語分詞...</div>
        </div>

        <!-- 小說閱讀器主體區塊 (含浮動控制列與正文) -->
        <section id="novelMainSection" style="display: none;">
            
            <!-- 小說浮動導航控制列 -->
            <div class="novel-reading-toolbar" id="novelReadingToolbar">
                
                <!-- 翻頁控制組 -->
                <div class="novel-nav-group">
                    <button class="novel-tool-btn" id="btnFirstPage" title="第一頁"><i class="fa-solid fa-backward-step"></i></button>
                    <button class="novel-tool-btn" id="btnPrevPage" title="上一頁"><i class="fa-solid fa-chevron-left"></i> 上一頁</button>
                    <div class="novel-page-indicator" id="novelPageIndicator" title="點擊輸入頁碼跳頁" style="cursor: pointer;">
                        第 <strong id="curPageNumDisplay">1</strong> / <span id="totalPageNumDisplay">1</span> 頁
                    </div>
                    <button class="novel-tool-btn" id="btnNextPage" title="下一頁">下一頁 <i class="fa-solid fa-chevron-right"></i></button>
                    <button class="novel-tool-btn" id="btnLastPage" title="最後一頁"><i class="fa-solid fa-forward-step"></i></button>
                    
                    <button class="novel-tool-btn" id="btnChangeRange" title="重新調整頁面載入範圍" style="background: rgba(217, 119, 6, 0.12); color: var(--novel-accent); font-weight: 700;">
                        <i class="fa-solid fa-sliders"></i> 換批次 (<span id="batchRangeBadge">1~5</span>)
                    </button>

                    <!-- 收藏句子清單按鈕 -->
                    <button class="novel-tool-btn" id="btnOpenSavedSentences" title="開啟已收藏句子庫" style="background: rgba(234, 179, 8, 0.14); color: #b45309; font-weight: 700; border-color: rgba(234, 179, 8, 0.4);">
                        <i class="fa-solid fa-star text-amber-500"></i> 收藏句子 (<span id="savedSentencesCount">0</span>)
                    </button>
                </div>

                <!-- 排版與外觀切換組 -->
                <div class="novel-nav-group">
                    <!-- 縱橫排切換 -->
                    <button class="novel-tool-btn" id="btnToggleWritingMode" title="切換縱書 (日文直排豎讀) / 橫書 (橫排)">
                        <i class="fa-solid fa-arrows-split-up-and-left"></i> <span id="writingModeLabel">縱書豎讀</span>
                    </button>

                    <!-- 假名注音切換 -->
                    <button class="novel-tool-btn" id="btnCycleRuby" title="假名注音顯示切換：全部 / 僅難字(N1~N3) / 隱藏">
                        <i class="fa-solid fa-font"></i> <span id="rubyModeLabel">假名: 全部</span>
                    </button>

                    <!-- 941文法標註 -->
                    <button class="novel-tool-btn active" id="btnToggleNovelGrammar" title="941條文型高亮開關">
                        <i class="fa-solid fa-highlighter"></i> 文型
                    </button>

                    <!-- JLPT單字色彩 -->
                    <button class="novel-tool-btn active" id="btnToggleNovelVocab" title="JLPT單字分級著色開關">
                        <i class="fa-solid fa-palette"></i> 單字
                    </button>

                    <!-- 字體風格 (明朝 / 黑體) -->
                    <button class="novel-tool-btn" id="btnToggleFontFamily" title="字體風格：典雅明朝體 / 現代黑體">
                        <i class="fa-solid fa-pen-nib"></i> 明朝體
                    </button>

                    <!-- 字級大小調整 -->
                    <button class="novel-tool-btn" id="btnFontDec" title="字體縮小">A-</button>
                    <button class="novel-tool-btn" id="btnFontInc" title="字體放大">A+</button>

                    <!-- 四大佈景主題 -->
                    <button class="novel-tool-btn" id="btnCycleTheme" title="切換閱讀主題：紙質暖黃 / 護眼豆沙綠 / 夜間暗黑 / 水墨純白">
                        <i class="fa-solid fa-brush"></i> <span id="themeLabel">紙質</span>
                    </button>
                </div>

                <!-- 語音朗讀與重複次數控制組 (全新強化) -->
                <div class="novel-nav-group" style="background: rgba(0, 0, 0, 0.04); padding: 4px 8px; border-radius: 10px;">
                    <!-- 朗讀 / 暫停 / 繼續 主按鈕 -->
                    <button class="novel-tool-btn btn-audio-play" id="btnPlayNovelAudio" title="朗讀整頁 / 暫停">
                        <i class="fa-solid fa-play" id="mainAudioIcon"></i> <span id="audioPlayBtnText">朗讀此頁</span>
                    </button>

                    <!-- 停止朗讀按鈕 -->
                    <button class="novel-tool-btn btn-audio-stop" id="btnStopNovelAudio" title="停止朗讀" style="display: none;">
                        <i class="fa-solid fa-stop"></i>
                    </button>

                    <!-- 重複次數選擇 (1次、2次、3次、5次、無限循環) -->
                    <div style="display: flex; align-items: center; gap: 4px; font-size: 0.84rem; font-weight: 700;">
                        <i class="fa-solid fa-repeat text-amber-500"></i>
                        <select id="novelRepeatCountSelect" class="novel-tool-btn" style="padding: 4px 6px; font-size: 0.84rem;" title="設定每句重複朗讀次數">
                            <option value="1">朗讀 1 次</option>
                            <option value="2">重複 2 次</option>
                            <option value="3" selected>重複 3 次 (推薦跟讀)</option>
                            <option value="5">重複 5 次 (精聽)</option>
                            <option value="999">∞ 無限循環</option>
                        </select>
                    </div>

                    <!-- 人聲語音選擇 -->
                    <select id="novelVoiceSelect" class="novel-tool-btn" style="padding: 4px 6px; font-size: 0.84rem;" title="選擇發音人聲">
                        <option value="auto">日語真人音 (自動最佳)</option>
                        <option value="nanami">女聲：七海 (Nanami)</option>
                        <option value="keita">男聲：圭太 (Keita)</option>
                        <option value="google">Google 日本語</option>
                    </select>

                    <button class="novel-tool-btn" onclick="openFilePicker()" title="開啟其他檔案">
                        <i class="fa-solid fa-folder-open"></i> 換書
                    </button>
                </div>

                <!-- 閱讀進度條 -->
                <div class="novel-progress-bar-container" title="全書閱讀進度">
                    <div class="novel-progress-bar-fill" id="novelProgressBarFill"></div>
                </div>
            </div>

            <!-- 小說正文展示卡片 -->
            <div class="novel-reader-deck mode-horizontal" id="novelContentBox">
                <!-- 動態注入各頁文章與段落 -->
            </div>

            <!-- 小說底部翻頁列 -->
            <div class="novel-bottom-bar">
                <button class="novel-tool-btn" id="btnBottomPrev"><i class="fa-solid fa-chevron-left"></i> 上一頁</button>
                <div style="font-size: 0.95rem; font-weight: 700; color: var(--text-muted);" id="bottomProgressText">
                    進度：第 1 / 1 頁
                </div>
                <button class="novel-tool-btn" id="btnBottomNext">下一頁 <i class="fa-solid fa-chevron-right"></i></button>
            </div>
        </section>

    </div>

    <!-- 單句選取浮動操作列 (選句子朗讀、暫停、收藏、文法) -->
    <div class="sentence-floating-toolbar" id="sentenceFloatingToolbar">
        <button class="s-bar-btn primary" id="btnSentencePlay" title="朗讀此句">
            <i class="fa-solid fa-play" id="sBarPlayIcon"></i> <span>朗讀此句</span>
        </button>
        <button class="s-bar-btn" id="btnSentenceFav" title="收藏此句至收藏庫">
            <i class="fa-regular fa-star" id="sBarFavIcon"></i> <span>收藏</span>
        </button>
        <button class="s-bar-btn" id="btnSentenceGrammars" title="查看本句包含的 941 文法">
            <i class="fa-solid fa-book-bookmark text-indigo-500"></i> <span>文法</span> (<span id="sBarGrammarCount">0</span>)
        </button>
        <button class="s-bar-btn" id="btnSentenceTranslate" title="顯示繁體中文翻譯對照">
            <i class="fa-solid fa-language text-blue-500"></i> <span>翻譯</span>
        </button>
        <button class="s-bar-btn" id="btnSentencePrev" title="上一句"><i class="fa-solid fa-chevron-left"></i></button>
        <button class="s-bar-btn" id="btnSentenceNext" title="下一句"><i class="fa-solid fa-chevron-right"></i></button>
        <button class="s-bar-btn" onclick="closeSentenceToolbar()" title="關閉選取" style="padding: 6px 10px; color: var(--text-muted);"><i class="fa-solid fa-xmark"></i></button>
    </div>

    <!-- 收藏句子中心抽屜面板 (Modal) -->
    <div class="saved-sentences-modal" id="savedSentencesModal">
        <div class="saved-sentences-content">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1.5px solid var(--novel-border); padding-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <i class="fa-solid fa-star text-amber-500" style="font-size: 1.4rem;"></i>
                    <h3 style="font-size: 1.3rem; font-weight: 800; color: var(--text-main); margin: 0;">已收藏句子庫</h3>
                    <span style="font-size: 0.85rem; padding: 2px 8px; border-radius: 9999px; background: rgba(234, 179, 8, 0.15); color: #b45309; font-weight: 700;" id="savedModalTotalCount">0 句</span>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="pill-btn" onclick="exportSavedSentences()" style="font-size: 0.84rem; padding: 5px 12px;"><i class="fa-solid fa-download"></i> 匯出文字</button>
                    <button onclick="closeSavedSentencesModal()" style="border: none; background: transparent; font-size: 1.3rem; cursor: pointer; color: var(--text-muted);"><i class="fa-solid fa-xmark"></i></button>
                </div>
            </div>

            <div class="saved-sentences-list" id="savedSentencesList">
                <!-- 動態注入已收藏之句子清單 -->
            </div>
        </div>
    </div>

    <!-- 剪貼簿貼上彈窗 -->
    <div id="pasteModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 9999; align-items: center; justify-content: center; backdrop-filter: blur(4px);">
        <div style="background: var(--novel-card-bg); border: 1px solid var(--novel-border); border-radius: 16px; padding: 24px; max-width: 650px; width: 92%; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3 style="font-weight: 800; font-size: 1.25rem; color: var(--novel-accent);"><i class="fa-solid fa-paste"></i> 貼上日文小說文字</h3>
                <button onclick="closePasteModal()" style="border: none; background: transparent; font-size: 1.2rem; cursor: pointer; color: var(--text-muted);"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <textarea id="pastedNovelText" rows="10" style="width: 100%; border: 1px solid var(--novel-border); border-radius: 10px; padding: 12px; font-family: inherit; font-size: 1rem; line-height: 1.8; background: var(--novel-bg); color: var(--novel-text); outline: none;" placeholder="請在此貼上日文小說內容、青空文庫章節或任何日語長文..."></textarea>
            <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 14px;">
                <button class="pill-btn" onclick="closePasteModal()">取消</button>
                <button class="btn-primary" onclick="confirmPastedNovel()" style="background: linear-gradient(135deg, #d97706, #b45309); color: #fff; padding: 8px 24px; border-radius: 8px; font-weight: 700; cursor: pointer;">
                    確認匯入並分頁
                </button>
            </div>
        </div>
    </div>

    <!-- 浮動單字字典卡片 (與閱讀高手完全相容) -->
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
            <div class="meaning-spinner"><i class="fa-solid fa-spinner fa-spin"></i> 載入中...</div>
        </div>
        <div class="popover-action-row">
            <button class="popover-btn-fav" id="btnAddWordToNotebook">
                <i class="fa-regular fa-star"></i> 存入生詞本
            </button>
        </div>
    </div>

    <!-- 941 文法深度解說彈窗卡片 (全面即時彈出) -->
    <div id="novelGrammarModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.55); z-index: 99999; align-items: center; justify-content: center; backdrop-filter: blur(4px);">
        <div style="background: var(--novel-card-bg); border: 1.5px solid var(--novel-border); border-radius: 18px; padding: 28px; max-width: 680px; width: 92%; max-height: 85vh; overflow-y: auto; box-shadow: 0 12px 40px rgba(0,0,0,0.25);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-bottom: 1px solid var(--novel-border); padding-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="background: rgba(99, 102, 241, 0.15); color: #6366f1; padding: 3px 10px; border-radius: 9999px; font-weight: 800; font-size: 0.82rem;" id="novelGrammarLevelBadge">N3 文型</span>
                    <h3 style="font-size: 1.35rem; font-weight: 800; color: var(--text-main); margin: 0;" id="novelGrammarTitle">文法標題</h3>
                </div>
                <button onclick="closeNovelGrammarModal()" style="border: none; background: transparent; font-size: 1.3rem; cursor: pointer; color: var(--text-muted);"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div id="novelGrammarBody" style="line-height: 1.8; font-size: 1.02rem;">
                <!-- 動態注入文法解說、接續、中文意義與例句 -->
            </div>
        </div>
    </div>

    <!-- 浮動提示 Toast -->
    <div id="toast" class="toast"></div>

    <!-- 核心資料庫 (941文法、JLPT單字、漢字字典、助詞) -->
    <script>
{db_script}
    </script>

    <!-- 形態素分析與分詞引擎 -->
    <script>
{nlp_script}
    </script>

    <!-- 閱讀高手核心狀態與字典查詢函式 -->
    <script>
{core_ui_script}
    </script>

    <!-- AnkiFlash 單字連動 -->
    <script src="static/flashcards/js/ankiflash_bridge.js"></script>
    <script>
{anki_script}
    </script>

    <!-- ==========================================================================
         小說專屬核心引擎 (Novel Engine) - 全面強化版
         包含：
         1. 獨立強韌日語語音引擎 (NovelAudio)：播放、暫停、繼續、停止、自選重複次數、Karaoke
         2. 單句選取與朗讀、收藏句子管理 (NovelBookmark)
         3. 941 文法點擊彈出 (NovelGrammar)
         ========================================================================== -->
    <script>
    (function() {{
        // 小說專屬狀態管理
        window.novelState = {{
            currentBook: null,          // 當前書籍對象 {{ title, type, totalPages, pagesData: [] }}
            loadedBatchStart: 1,        // 當前載入的起始頁
            loadedBatchEnd: 5,          // 當前載入的結束頁
            currentPageIndex: 1,        // 目前正在閱讀的頁碼 (1-indexed)
            pagesCache: {{}},            // 各頁純文字與解析結果快取 {{ [pageNum]: {{ text, analyzed }} }}
            selectedSentenceIdx: null,  // 當前選取之句子索引
            writingMode: 'horizontal',  // 'horizontal' | 'vertical'
            rubyMode: 'show',           // 'show' | 'hard-only' | 'hide'
            theme: 'sepia',             // 'sepia' | 'mint' | 'dark' | 'white'
            fontFamily: 'serif',        // 'serif' | 'sans'
            fontSize: 1.25,             // rem
            showGrammar: true,
            showVocabColor: true,
            repeatCount: 3              // 每句重複次數 (預設 3 次跟讀)
        }};

        // ==========================================================================
        // 1. 獨立強韌日語語音引擎 (NovelAudio)
        // 具備：播放、暫停 (Pause)、繼續 (Resume)、停止 (Stop)、重複次數、Karaoke
        // ==========================================================================
        window.NovelAudio = {{
            status: 'idle', // 'idle' | 'playing' | 'paused'
            currentUtterance: null,
            currentAudioElement: null,
            activeTokens: [],
            repeatLeft: 1,
            totalRepeats: 3,
            currentText: '',
            onEndCallback: null,
            availableVoices: [],

            init() {{
                if ('speechSynthesis' in window) {{
                    const updateVoices = () => {{
                        this.availableVoices = window.speechSynthesis.getVoices() || [];
                    }};
                    updateVoices();
                    window.speechSynthesis.onvoiceschanged = updateVoices;
                }}
            }},

            // 尋找最佳日語語音人聲 (多重降級保障，確保絕對能發聲)
            getBestJapaneseVoice(preferred = 'auto') {{
                if (!('speechSynthesis' in window)) return null;
                const voices = this.availableVoices.length > 0 ? this.availableVoices : (window.speechSynthesis.getVoices() || []);
                if (voices.length === 0) return null;

                const jaVoices = voices.filter(v => v.lang && (v.lang.startsWith('ja') || v.lang.includes('JP')));
                if (jaVoices.length === 0) {{
                    return voices.find(v => /ja|japanese/i.test(v.name || '')) || null;
                }}

                if (preferred === 'nanami') {{
                    const nanami = jaVoices.find(v => /七海|Nanami|Natural/i.test(v.name) && !/Desktop/i.test(v.name));
                    if (nanami) return nanami;
                }} else if (preferred === 'keita') {{
                    const keita = jaVoices.find(v => /圭太|Keita|Natural/i.test(v.name) && !/Desktop/i.test(v.name));
                    if (keita) return keita;
                }} else if (preferred === 'google') {{
                    const gVoice = jaVoices.find(v => /Google|Chrome/i.test(v.name));
                    if (gVoice) return gVoice;
                }}

                // 自動推薦順序：Edge Natural > Google 日本語 > 本機日語音
                return jaVoices.find(v => /Natural|Online/i.test(v.name) && !/Desktop/i.test(v.name)) ||
                       jaVoices.find(v => /Google/i.test(v.name)) ||
                       jaVoices[0];
            }},

            // 朗讀指定文本 (支援 Karaoke 與重複次數)
            speak(text, containerEl, onEnd, customRepeats = null) {{
                if (!text) return;
                const cleanText = text.replace(/<[^>]+>/g, '').trim();
                if (!cleanText) return;

                // 若為暫停狀態且文本相同 -> 直接 Resume
                if (this.status === 'paused' && this.currentText === cleanText) {{
                    this.resume();
                    return;
                }}

                this.stop(false);
                this.currentText = cleanText;
                this.onEndCallback = onEnd;

                // 設定重複次數
                const repeatSetting = customRepeats !== null ? customRepeats : parseInt(document.getElementById('novelRepeatCountSelect')?.value || '3', 10);
                this.totalRepeats = repeatSetting;
                this.repeatLeft = repeatSetting;

                this.executePlay(cleanText, containerEl);
            }},

            executePlay(cleanText, containerEl) {{
                this.status = 'playing';
                this.updateUIStatus('playing');

                let tokens = [];
                if (containerEl) {{
                    tokens = Array.from(containerEl.querySelectorAll('.word-token, ruby, .grammar-highlight'));
                }}
                this.activeTokens = tokens;

                const voicePref = document.getElementById('novelVoiceSelect')?.value || 'auto';
                const matchedVoice = this.getBestJapaneseVoice(voicePref);

                // 優先使用 Web SpeechSynthesis (最穩定、無 CORS 阻礙)
                if ('speechSynthesis' in window && matchedVoice) {{
                    try {{
                        window.speechSynthesis.cancel();
                        const u = new SpeechSynthesisUtterance(cleanText);
                        u.voice = matchedVoice;
                        u.lang = 'ja-JP';
                        u.rate = 0.95;
                        this.currentUtterance = u;

                        // Karaoke 隨音變色追蹤 (依字元索引高亮)
                        if (tokens.length > 0) {{
                            u.onboundary = (e) => {{
                                if (this.status !== 'playing') return;
                                const charIdx = e.charIndex || 0;
                                let acc = 0;
                                let activeIdx = 0;
                                for (let i = 0; i < tokens.length; i++) {{
                                    const w = tokens[i].dataset.surface || tokens[i].textContent || '';
                                    acc += Math.max(1, w.length);
                                    if (acc > charIdx) {{ activeIdx = i; break; }}
                                }}
                                this.applyTokenHighlight(tokens, activeIdx);
                            }};
                        }}

                        u.onend = () => {{
                            this.handleIterationEnd(containerEl);
                        }};
                        u.onerror = (err) => {{
                            console.warn('SpeechSynthesis error:', err);
                            this.fallbackAudioElement(cleanText, containerEl);
                        }};

                        window.speechSynthesis.speak(u);
                        return;
                    }} catch (e) {{
                        console.warn('SpeechSynthesis speak failed:', e);
                    }}
                }}

                // 備用方案：Google Translate TTS HTML5 Audio
                this.fallbackAudioElement(cleanText, containerEl);
            }},

            fallbackAudioElement(cleanText, containerEl) {{
                const audioUrl = `https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=ja&q=${{encodeURIComponent(cleanText.slice(0, 190))}}`;
                const audio = new Audio(audioUrl);
                this.currentAudioElement = audio;

                audio.onended = () => {{
                    this.handleIterationEnd(containerEl);
                }};
                audio.onerror = () => {{
                    showToast('語音播放失敗，請檢查瀏覽器聲音設定或改用本機語音。');
                    this.stop();
                }};

                audio.play().catch(e => {{
                    console.warn('Audio play failed:', e);
                    this.stop();
                }});
            }},

            // 當單次播放完畢時，處理重複次數邏輯
            handleIterationEnd(containerEl) {{
                this.clearHighlights();

                if (this.totalRepeats === 999) {{
                    // 無限循環復讀
                    setTimeout(() => {{
                        if (this.status === 'playing') {{
                            this.executePlay(this.currentText, containerEl);
                        }}
                    }}, 550);
                    return;
                }}

                this.repeatLeft--;
                if (this.repeatLeft > 0 && this.status === 'playing') {{
                    // 繼續重複播放下一遍
                    showToast(`🔁 正在重複朗讀 (剩餘 ${{this.repeatLeft}} 次)...`);
                    setTimeout(() => {{
                        if (this.status === 'playing') {{
                            this.executePlay(this.currentText, containerEl);
                        }}
                    }}, 600);
                }} else {{
                    // 全部重複次數播畢
                    this.status = 'idle';
                    this.updateUIStatus('idle');
                    if (typeof this.onEndCallback === 'function') {{
                        this.onEndCallback();
                    }}
                }}
            }},

            // 暫停播放
            pause() {{
                if (this.status !== 'playing') return;
                this.status = 'paused';
                if ('speechSynthesis' in window && window.speechSynthesis.speaking) {{
                    window.speechSynthesis.pause();
                }}
                if (this.currentAudioElement) {{
                    this.currentAudioElement.pause();
                }}
                this.updateUIStatus('paused');
                showToast('語音已暫停');
            }},

            // 繼續播放 (Resume)
            resume() {{
                if (this.status !== 'paused') return;
                this.status = 'playing';
                if ('speechSynthesis' in window && window.speechSynthesis.paused) {{
                    window.speechSynthesis.resume();
                }} else if (this.currentAudioElement) {{
                    this.currentAudioElement.play();
                }} else if (this.currentText) {{
                    this.executePlay(this.currentText, null);
                }}
                this.updateUIStatus('playing');
                showToast('繼續朗讀');
            }},

            // 停止播放
            stop(notify = true) {{
                this.status = 'idle';
                this.repeatLeft = 0;
                if ('speechSynthesis' in window) {{
                    window.speechSynthesis.cancel();
                }}
                if (this.currentAudioElement) {{
                    this.currentAudioElement.pause();
                    this.currentAudioElement = null;
                }}
                this.clearHighlights();
                this.updateUIStatus('idle');
                if (notify) showToast('已停止朗讀');
            }},

            // Karaoke 變色高亮
            applyTokenHighlight(tokens, activeIdx) {{
                tokens.forEach((t, i) => {{
                    t.classList.toggle('karaoke-current-word', i === activeIdx);
                }});
            }},

            clearHighlights() {{
                document.querySelectorAll('.karaoke-current-word').forEach(el => el.classList.remove('karaoke-current-word'));
                document.querySelectorAll('.karaoke-active-sentence').forEach(el => el.classList.remove('karaoke-active-sentence'));
            }},

            // 同步更新工具列與單句按鈕圖示與文字
            updateUIStatus(st) {{
                const mainBtn = document.getElementById('btnPlayNovelAudio');
                const mainText = document.getElementById('audioPlayBtnText');
                const mainIcon = document.getElementById('mainAudioIcon');
                const stopBtn = document.getElementById('btnStopNovelAudio');

                const sBarPlayBtn = document.getElementById('btnSentencePlay');
                const sBarPlayIcon = document.getElementById('sBarPlayIcon');

                if (st === 'playing') {{
                    if (mainBtn) mainBtn.className = 'novel-tool-btn btn-audio-pause';
                    if (mainText) mainText.textContent = '暫停朗讀';
                    if (mainIcon) mainIcon.className = 'fa-solid fa-pause';
                    if (stopBtn) stopBtn.style.display = 'inline-flex';

                    if (sBarPlayBtn) {{
                        sBarPlayBtn.className = 's-bar-btn pause-btn';
                        sBarPlayBtn.innerHTML = '<i class="fa-solid fa-pause"></i> <span>暫停</span>';
                    }}
                }} else if (st === 'paused') {{
                    if (mainBtn) mainBtn.className = 'novel-tool-btn btn-audio-play';
                    if (mainText) mainText.textContent = '繼續朗讀';
                    if (mainIcon) mainIcon.className = 'fa-solid fa-play';
                    if (stopBtn) stopBtn.style.display = 'inline-flex';

                    if (sBarPlayBtn) {{
                        sBarPlayBtn.className = 's-bar-btn primary';
                        sBarPlayBtn.innerHTML = '<i class="fa-solid fa-play"></i> <span>繼續</span>';
                    }}
                }} else {{
                    if (mainBtn) mainBtn.className = 'novel-tool-btn btn-audio-play';
                    if (mainText) mainText.textContent = '朗讀此頁';
                    if (mainIcon) mainIcon.className = 'fa-solid fa-play';
                    if (stopBtn) stopBtn.style.display = 'none';

                    if (sBarPlayBtn) {{
                        sBarPlayBtn.className = 's-bar-btn primary';
                        sBarPlayBtn.innerHTML = '<i class="fa-solid fa-play"></i> <span>朗讀此句</span>';
                    }}
                }}
            }}
        }};

        // 初始化語音
        window.NovelAudio.init();

        // 預設經典名著文本
        window.SAMPLE_NOVELS = {{
            kokoro: {{
                title: "心 (こころ) - 夏目漱石",
                text: `私はその人を常に先生と呼んでいた。だからここでもただ先生と書くだけで本名は打ち明けない。これは世間を憚る遠慮というよりも、その方が私にとって自然だからである。私はその人の記憶を呼び起こすごとに、すぐ「先生」と言いたくなる。筆を執っても心持は同じ事である。よそよそしい頭文字などはとても使う気にならない。\\n\\n私が先生と知り合いになったのは鎌倉である。その時私はまだ若々しい書生であった。暑中休暇を利用して友達から海へ泳ぎに行こうという端書を受け取ったので、私は多少の金を工面して出掛ける事にした。私は金の工面に二三日を費やした。ところが私が鎌倉に着いて三日と経たないうちに、私を呼び寄せた友達は、急に国元から帰れという電報を受け取った。電報には母が病気だからと断ってあったけれども友達はそれを信じなかった。友達はかねてから親たちに気乗り味のしない結婚を迫られていたのである。彼は現代の風を帯びた東京の言葉でそれを親父の策略だと私に言った。\\n\\n一人取り残された私は、毎日海へ入った。由比ヶ浜へ下りて行く道で、私はよくその先生を見かけた。先生はいつも同じ宿から出て来て、同じ時間に海へ浸かり、静かに戻って行った。ある日、先生が脱ぎ捨てた手拭いを波が攫おうとした時、私が走ってそれを拾い上げた。それが先生と私との会話の始まりであった。`
            }},
            melos: {{
                title: "走れメロス - 太宰治",
                text: `メロスは激怒した。必ず、かの邪智暴虐の王を除かなければならぬと決意した。メロスには政治がわからぬ。メロスは、村の牧人である。笛を吹き、羊と遊んで暮して来た。けれども邪悪に対しては、人一倍に敏感であった。きょう未明メロスは村を出発し、野を越え山越え、十里はなれた此のシラクスの市にやって来た。メロスには父も、母も無い。女房も無い。十六の、内気な妹と二人暮しであった。この妹は、村の或る律気な一牧人を、近々、花婿として迎える事になっていた。結婚式も間近かなのである。メロスは、それゆえ、花嫁の衣裳やら祝宴の御馳走やらを買いに、はるばる市にやって来たのだ。\\n\\nまず、その品々を買い集め、それから市の大路をぶらぶら歩いた。メロスには竹馬の友があった。セリヌンティウスである。今は此のシラクスの市で、石工をしている。その友を、これから訪ねてみるつもりなのだ。久しく逢わなかったのだから、訪ねて行くのが楽しみである。歩いているうちにメロスは、まちの様子を怪しく思った。ひっそりしている。もう既に日も落ちて、まちの暗いのは當りまえだが、それにしても、なんだか夜のせいばかりでは無く、市全体が、うっすら寂しい。のんきなメロスも、だんだん不安になって来た。路で逢った若い衆をつかまえて、何かあったのか、二年まえに此の市に来たときは、夜でも皆が歌をうたって、まちは賑やかであった筈だが、と質問した。`
            }},
            ginga: {{
                title: "銀河鉄道の夜 - 宮沢賢治",
                text: `「ではみなさんは、そういうふうに川だと云われたり、乳の流れたあとだと云われたりしていたこのぼんやりと白いものがほんとうは何かご承知ですか」\\n先生は、黒板に吊した大きな黒い星座の図の、上から下へ白くけむった銀河の帯のようなところを指しながら、みんなに問をかけました。\\nカムパネルラが手をあげました。それから四五人手をあげました。ジョバンニも手をあげようとして、急いでそれをやめました。たしかにあれはみんな星だと、いつか雑誌で読んだのでしたが、このごろジョバンニはまるで毎日教室でもねむく、本を読むひまも読む本もないので、なんだかどんなこともよくわからないという気持ちがするのでした。\\n\\nところが先生は早くもそれを見附けたのでした。\\n「ジョバンニさん。あなたはあるでしょう」\\nジョバンニは勢よく立ちあがりましたが、立って見るともうはっきりとそれを答えることができませんでした。ザネリが前の席からふりかえって、じっとジョバンニを見てくすくすわらいました。ジョバンニはもうどぎまぎしてまっ赤になってしまいました。先生がまた云いました。\\n「大きな望遠鏡で銀河をよっく調べると、銀河のなかには無数の星が見えるのでしたね。そうですね」\\nジョバンニは赤くなってうなずきました。`
            }},
            rashomon: {{
                title: "羅生門 - 芥川龍之介",
                text: `ある日の暮方の事である。一人の下人が、羅生門の下で雨やみを待っていた。\\n広い門の下には、この男のほかに誰もいない。ただ、所々丹塗の剥げた、大きな円柱に、蟋蟀が一匹とまっている。羅生門が、朱雀大路にある以上は、この男のほかにも、雨やみをする市女笠や揉烏帽子が、もう二三人はありそうなものである。それが、この男のほかには誰もいない。\\n\\nなぜかと云うと、この二三年、京都には、地震とか辻風とか火事とか饑饉とかいう災いがつづいて起った。そこで洛中のさびれ方は一通りではない。旧記によると、仏像や仏具を打砕いて、その丹がついたり、金銀の箔がついたりした木を、路ばたにつみ重ねて、薪の料に売っていたと云う事である。洛中がその始末であるから、羅生門の修理などは、元より誰も捨てて顧る者がなかった。するとその荒れ果てたのをよい事にして、狐狸が棲む。盗人が棲む。とうとうしまいには、引取り手のない死人を、この門へ持って来て、棄てて行くと云う習慣さえ出来た。そこで、日の目が見えなくなると、誰でも気味を悪がって、この門の近所へは足ぶみをしない事になってしまったのである。`
            }}
        }};

        // 初始化頁面監聽
        document.addEventListener('DOMContentLoaded', () => {{
            setupDropZone();
            setupToolbarEvents();
            setupSentenceToolbarEvents();
            loadSavedPreferences();
            updateSavedSentencesCountBadge();
        }});

        function loadSavedPreferences() {{
            const savedTheme = localStorage.getItem('novel_theme') || 'sepia';
            setNovelTheme(savedTheme);

            const savedFont = localStorage.getItem('novel_font') || 'serif';
            setNovelFont(savedFont);

            const savedRuby = localStorage.getItem('novel_ruby') || 'show';
            setNovelRuby(savedRuby);

            const savedMode = localStorage.getItem('novel_writing_mode') || 'horizontal';
            setWritingMode(savedMode);

            const savedRepeat = localStorage.getItem('novel_repeat_count') || '3';
            const repSelect = document.getElementById('novelRepeatCountSelect');
            if (repSelect) repSelect.value = savedRepeat;
        }}

        function setupDropZone() {{
            const card = document.getElementById('novelImportCard');
            const fileInput = document.getElementById('novelFileInput');

            card.addEventListener('dragover', (e) => {{
                e.preventDefault();
                card.classList.add('drag-over');
            }});
            card.addEventListener('dragleave', () => {{
                card.classList.remove('drag-over');
            }});
            card.addEventListener('drop', (e) => {{
                e.preventDefault();
                card.classList.remove('drag-over');
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {{
                    handleFileSelection(e.dataTransfer.files[0]);
                }}
            }});

            fileInput.addEventListener('change', (e) => {{
                if (e.target.files && e.target.files.length > 0) {{
                    handleFileSelection(e.target.files[0]);
                }}
            }});
        }}

        async function handleFileSelection(file) {{
            const fileName = file.name;
            const ext = fileName.split('.').pop().toLowerCase();
            showToast(`正在偵測檔案架構：${{fileName}}...`);

            try {{
                if (ext === 'pdf') {{
                    await parsePdf(file);
                }} else if (ext === 'epub') {{
                    await parseEpub(file);
                }} else if (ext === 'docx') {{
                    await parseDocx(file);
                }} else {{
                    await parseTextFile(file);
                }}
            }} catch (err) {{
                console.error(err);
                showToast(`檔案載入失敗：${{err.message}}`);
            }}
        }}

        async function parsePdf(file) {{
            const arrayBuffer = await file.arrayBuffer();
            const loadingTask = pdfjsLib.getDocument({{ data: arrayBuffer }});
            const pdfDoc = await loadingTask.promise;
            const totalPages = pdfDoc.numPages;

            window.novelState.currentBook = {{
                title: file.name,
                type: 'pdf',
                totalPages: totalPages,
                pdfDoc: pdfDoc,
                getPageText: async function(pageNum) {{
                    if (window.novelState.pagesCache[pageNum]) {{
                        return window.novelState.pagesCache[pageNum].text;
                    }}
                    const page = await pdfDoc.getPage(pageNum);
                    const content = await page.getTextContent();
                    
                    let lastY = null;
                    let pageLines = [];
                    let curLine = '';
                    
                    for (const item of content.items) {{
                        const y = item.transform ? Math.round(item.transform[5]) : 0;
                        if (lastY !== null && Math.abs(y - lastY) > 5) {{
                            if (curLine.trim()) pageLines.push(curLine.trim());
                            curLine = item.str;
                        }} else {{
                            curLine += item.str;
                        }}
                        lastY = y;
                    }}
                    if (curLine.trim()) pageLines.push(curLine.trim());

                    let fullText = '';
                    pageLines.forEach((l, idx) => {{
                        if (idx > 0) {{
                            const prev = pageLines[idx - 1];
                            if (/[。！？!?]$/.test(prev) || l.startsWith('「') || l.startsWith('『') || l.startsWith('　')) {{
                                fullText += '\\n' + l;
                            }} else {{
                                fullText += l;
                            }}
                        }} else {{
                            fullText = l;
                        }}
                    }});

                    window.novelState.pagesCache[pageNum] = {{ text: fullText }};
                    return fullText;
                }}
            }};

            openPageSelector(file.name, totalPages);
        }}

        async function parseEpub(file) {{
            const zip = await JSZip.loadAsync(file);
            const containerXml = await zip.file("META-INF/container.xml").async("text");
            const opfMatch = containerXml.match(/full-path="([^"]+)"/);
            const opfPath = opfMatch ? opfMatch[1] : "OEBPS/content.opf";
            const opfDir = opfPath.includes('/') ? opfPath.substring(0, opfPath.lastIndexOf('/') + 1) : '';

            const opfContent = await zip.file(opfPath).async("text");
            const parser = new DOMParser();
            const opfDoc = parser.parseFromString(opfContent, "application/xml");

            const itemRefs = Array.from(opfDoc.querySelectorAll("spine itemref"));
            const items = Array.from(opfDoc.querySelectorAll("manifest item"));
            const idMap = {{}};
            items.forEach(it => {{
                idMap[it.getAttribute("id")] = it.getAttribute("href");
            }});

            const chapterFiles = itemRefs.map(ref => {{
                const id = ref.getAttribute("idref");
                return opfDir + idMap[id];
            }}).filter(Boolean);

            let allBookText = '';
            for (const cPath of chapterFiles) {{
                const f = zip.file(cPath);
                if (f) {{
                    const html = await f.async("text");
                    const doc = parser.parseFromString(html, "text/html");
                    const paras = Array.from(doc.querySelectorAll("p, div, h1, h2, h3, h4"));
                    if (paras.length > 0) {{
                        paras.forEach(p => {{
                            const t = p.textContent.trim();
                            if (t) allBookText += t + '\\n\\n';
                        }});
                    }} else {{
                        const bodyText = doc.body.textContent.trim();
                        if (bodyText) allBookText += bodyText + '\\n\\n';
                    }}
                }}
            }}

            paginateTextBook(file.name, allBookText, 'epub');
        }}

        async function parseDocx(file) {{
            const zip = await JSZip.loadAsync(file);
            const docXml = await zip.file("word/document.xml").async("text");
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(docXml, "application/xml");
            const paras = Array.from(xmlDoc.querySelectorAll("w\\\\:p, p"));

            let text = '';
            paras.forEach(p => {{
                const runs = Array.from(p.querySelectorAll("w\\\\:t, t"));
                const pText = runs.map(r => r.textContent).join('');
                if (pText.trim()) text += pText.trim() + '\\n\\n';
            }});

            paginateTextBook(file.name, text, 'docx');
        }}

        async function parseTextFile(file) {{
            const buffer = await file.arrayBuffer();
            let text = '';
            try {{
                const decoder = new TextDecoder('utf-8', {{ fatal: true }});
                text = decoder.decode(buffer);
            }} catch (e) {{
                const decoder = new TextDecoder('shift-jis');
                text = decoder.decode(buffer);
            }}

            text = text.replace(/［＃[^］]+］/g, '');
            text = text.replace(/｜?([一-龯々]+)《([^》]+)》/g, '$1');

            paginateTextBook(file.name, text, 'txt');
        }}

        function paginateTextBook(title, fullText, type) {{
            const paragraphs = fullText.split(/\\r?\\n+/);
            const pages = [];
            let curPage = '';
            const CHARS_PER_PAGE = 900;

            for (const p of paragraphs) {{
                const trimmed = p.trim();
                if (!trimmed) continue;
                if ((curPage.length + trimmed.length) > CHARS_PER_PAGE && curPage.length > 300) {{
                    pages.push(curPage.trim());
                    curPage = trimmed + '\\n\\n';
                }} else {{
                    curPage += trimmed + '\\n\\n';
                }}
            }}
            if (curPage.trim()) {{
                pages.push(curPage.trim());
            }}

            if (pages.length === 0) pages.push("（此檔案無有效日文文本）");

            window.novelState.currentBook = {{
                title: title,
                type: type,
                totalPages: pages.length,
                pagesData: pages,
                getPageText: async function(pageNum) {{
                    const idx = pageNum - 1;
                    return pages[idx] || '';
                }}
            }};

            openPageSelector(title, pages.length);
        }}

        window.loadSampleNovel = function(key) {{
            const sample = window.SAMPLE_NOVELS[key];
            if (!sample) return;
            paginateTextBook(sample.title, sample.text, 'sample');
        }};

        function openPageSelector(title, totalPages) {{
            const card = document.getElementById('pageSelectorCard');
            document.getElementById('selectorBookTitle').textContent = title;
            document.getElementById('selectorTotalPagesBadge').textContent = `共 ${{totalPages}} 頁`;

            const startInput = document.getElementById('inputStartPage');
            const endInput = document.getElementById('inputEndPage');
            const slider = document.getElementById('pageRangeSlider');

            startInput.max = totalPages;
            endInput.max = totalPages;
            slider.max = totalPages;

            const bookmarkKey = 'novel_bookmark_' + encodeURIComponent(title);
            const savedPage = parseInt(localStorage.getItem(bookmarkKey) || '0', 10);
            const resumePrompt = document.getElementById('resumeBookmarkPrompt');

            if (savedPage > 1 && savedPage <= totalPages) {{
                resumePrompt.style.display = 'flex';
                document.getElementById('resumePageNum').textContent = savedPage;
                document.getElementById('btnResumeLastRead').onclick = () => {{
                    startInput.value = savedPage;
                    endInput.value = Math.min(savedPage + 4, totalPages);
                    slider.value = savedPage;
                    startNovelReading();
                }};
                startInput.value = savedPage;
                endInput.value = Math.min(savedPage + 4, totalPages);
                slider.value = savedPage;
            }} else {{
                resumePrompt.style.display = 'none';
                startInput.value = 1;
                endInput.value = Math.min(5, totalPages);
                slider.value = 1;
            }}

            slider.oninput = (e) => {{
                const val = parseInt(e.target.value, 10);
                startInput.value = val;
                endInput.value = Math.min(val + 4, totalPages);
            }};
            startInput.onchange = () => {{
                slider.value = startInput.value;
                if (parseInt(endInput.value) < parseInt(startInput.value)) {{
                    endInput.value = Math.min(parseInt(startInput.value) + 4, totalPages);
                }}
            }};

            card.style.display = 'block';
            card.scrollIntoView({{ behavior: 'smooth' }});
        }}

        window.closePageSelector = function() {{
            document.getElementById('pageSelectorCard').style.display = 'none';
        }};

        window.setPageBatch = function(count) {{
            const book = window.novelState.currentBook;
            if (!book) return;
            const startInput = document.getElementById('inputStartPage');
            const endInput = document.getElementById('inputEndPage');
            const start = parseInt(startInput.value, 10) || 1;
            endInput.value = Math.min(start + count - 1, book.totalPages);
        }};

        window.shiftPageBatch = function(direction) {{
            const book = window.novelState.currentBook;
            if (!book) return;
            const startInput = document.getElementById('inputStartPage');
            const endInput = document.getElementById('inputEndPage');
            const currentBatch = (parseInt(endInput.value, 10) - parseInt(startInput.value, 10) + 1) || 5;
            
            let newStart = parseInt(startInput.value, 10) + (direction * currentBatch);
            if (newStart < 1) newStart = 1;
            if (newStart > book.totalPages) newStart = Math.max(1, book.totalPages - currentBatch + 1);
            
            startInput.value = newStart;
            endInput.value = Math.min(newStart + currentBatch - 1, book.totalPages);
            document.getElementById('pageRangeSlider').value = newStart;
        }};

        async function startNovelReading() {{
            const book = window.novelState.currentBook;
            if (!book) return;

            const startPage = Math.max(1, parseInt(document.getElementById('inputStartPage').value, 10) || 1);
            const endPage = Math.min(book.totalPages, Math.max(startPage, parseInt(document.getElementById('inputEndPage').value, 10) || 1));

            window.novelState.loadedBatchStart = startPage;
            window.novelState.loadedBatchEnd = endPage;
            window.novelState.currentPageIndex = startPage;

            closePageSelector();
            document.getElementById('novelImportCard').style.display = 'none';
            document.getElementById('novelMainSection').style.display = 'none';
            document.getElementById('novelLoadingState').style.display = 'flex';

            const totalBatch = endPage - startPage + 1;
            document.getElementById('novelLoadingText').textContent = `正在提取並深入解析第 ${{startPage}} ~ ${{endPage}} 頁 (共 ${{totalBatch}} 頁)...`;

            try {{
                for (let p = startPage; p <= endPage; p++) {{
                    if (!window.novelState.pagesCache[p] || !window.novelState.pagesCache[p].analyzed) {{
                        const rawText = await book.getPageText(p);
                        const analyzed = await clientAnalyzeText(rawText, false);
                        window.novelState.pagesCache[p] = {{
                            text: rawText,
                            analyzed: analyzed
                        }};
                    }}
                }}

                document.getElementById('novelLoadingState').style.display = 'none';
                document.getElementById('novelMainSection').style.display = 'block';

                updateToolbarInfo();
                renderCurrentPage();
                showToast(`已成功載入第 ${{startPage}} ~ ${{endPage}} 頁！`);
                saveBookmark(book.title, startPage);
            }} catch (err) {{
                console.error(err);
                document.getElementById('novelLoadingState').style.display = 'none';
                showToast(`解析出錯：${{err.message}}`);
            }}
        }}

        document.getElementById('btnStartNovelReading').addEventListener('click', startNovelReading);

        // ==========================================================================
        // 渲染當前頁面 (包含 941 文法標籤、收藏按鈕、單句選取)
        // ==========================================================================
        function renderCurrentPage() {{
            const pNum = window.novelState.currentPageIndex;
            const pageData = window.novelState.pagesCache[pNum];
            const contentBox = document.getElementById('novelContentBox');
            contentBox.innerHTML = '';
            closeSentenceToolbar();

            if (!pageData || !pageData.analyzed) {{
                contentBox.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--text-muted);">正在載入第 ${{pNum}} 頁...</div>`;
                return;
            }}

            const analyzed = pageData.analyzed;
            const bookTitle = window.novelState.currentBook.title;

            // 頁首標籤
            const pageHeader = document.createElement('div');
            pageHeader.className = 'novel-page-divider';
            pageHeader.innerHTML = `<span><i class="fa-solid fa-leaf"></i> ${{bookTitle}} —— 第 ${{pNum}} 頁</span>`;
            contentBox.appendChild(pageHeader);

            let curParagraphEl = document.createElement('div');
            curParagraphEl.className = 'novel-paragraph';

            const savedList = getSavedSentences();

            analyzed.sentences.forEach((s, sIdx) => {{
                const sRow = document.createElement('span');
                sRow.className = 'sentence-row';
                sRow.dataset.sentenceIdx = sIdx;
                sRow.dataset.pageNum = pNum;

                // 檢查是否已收藏
                const isFav = savedList.some(item => item.text === s.text);

                // 收藏星號圖示
                const starBtn = document.createElement('button');
                starBtn.className = `sentence-star-btn ${{isFav ? 'is-fav' : ''}}`;
                starBtn.title = isFav ? '已收藏此句' : '收藏此句';
                starBtn.innerHTML = `<i class="fa-${{isFav ? 'solid' : 'regular'}} fa-star"></i>`;
                starBtn.addEventListener('click', (e) => {{
                    e.stopPropagation();
                    toggleFavoriteSentence(s.text, pNum, bookTitle);
                    const nowFav = getSavedSentences().some(item => item.text === s.text);
                    starBtn.className = `sentence-star-btn ${{nowFav ? 'is-fav' : ''}}`;
                    starBtn.innerHTML = `<i class="fa-${{nowFav ? 'solid' : 'regular'}} fa-star"></i>`;
                }});
                sRow.appendChild(starBtn);

                // 點擊選取句子
                sRow.addEventListener('click', (e) => {{
                    if (e.target.closest('.word-token') || e.target.closest('.sentence-star-btn') || e.target.closest('.novel-grammar-badge')) return;
                    selectNovelSentence(sIdx, pNum, sRow, s);
                }});

                // 渲染單字與假名 (加強文法點擊支援)
                renderSentenceTokensWithGrammar(sRow, s, sIdx);

                // 若本句含有 941 文法，在句尾附上清晰文法膠囊標籤
                if (s.grammars && s.grammars.length > 0) {{
                    s.grammars.forEach(g => {{
                        const gBadge = document.createElement('span');
                        gBadge.className = 'novel-grammar-badge';
                        gBadge.innerHTML = `<i class="fa-solid fa-bookmark"></i> ${{g.level || '941'}} ${{g.title || g.pattern}}`;
                        gBadge.title = `點擊查看【${{g.title || g.pattern}}】文法解說`;
                        gBadge.addEventListener('click', (e) => {{
                            e.stopPropagation();
                            showNovelGrammarCard(g.id);
                        }});
                        sRow.appendChild(gBadge);
                    }});
                }}

                curParagraphEl.appendChild(sRow);

                if (s.text.includes('\\n') || /[。！？!?]$/.test(s.text.trim())) {{
                    contentBox.appendChild(curParagraphEl);
                    curParagraphEl = document.createElement('div');
                    curParagraphEl.className = 'novel-paragraph';
                }}
            }});

            if (curParagraphEl.children.length > 0) {{
                contentBox.appendChild(curParagraphEl);
            }}

            updateToolbarInfo();
            saveBookmark(bookTitle, pNum);

            if (window.novelState.writingMode === 'vertical') {{
                contentBox.scrollLeft = contentBox.scrollWidth;
            }} else {{
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }}
        }}

        // 改良版 Token 渲染器：點擊文法字詞直接彈出 941 文法卡片！
        function renderSentenceTokensWithGrammar(container, sentence, sIdx) {{
            const words = sentence.words || [];
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
                tokenSpan.className = `word-token ${{w.jlpt ? `jlpt-${{w.jlpt}}` : ''}}`;
                tokenSpan.innerHTML = w.ruby_html || w.surface;
                tokenSpan.dataset.surface = w.surface;
                tokenSpan.dataset.reading = w.reading || w.surface;
                tokenSpan.dataset.jlpt = w.jlpt || '';
                tokenSpan.dataset.sentenceIdx = sIdx;
                tokenSpan.dataset.wordIdx = wIdx;

                // 檢查是否與 941 文法重疊標註
                const tokenStart = wordOffsets[wIdx].start;
                const tokenEnd = wordOffsets[wIdx].end;

                const matchedGrammar = grammars.find(g => {{
                    if (g.matches && Array.isArray(g.matches)) {{
                        return g.matches.some(m => tokenStart < m.end && tokenEnd > m.start);
                    }}
                    if (typeof g.start === 'number' && typeof g.end === 'number') {{
                        return tokenStart < g.end && tokenEnd > g.start;
                    }}
                    return false;
                }});

                if (matchedGrammar) {{
                    tokenSpan.classList.add('grammar-highlight');
                    tokenSpan.dataset.grammarId = matchedGrammar.id;
                    tokenSpan.title = `【${{matchedGrammar.level || '941文型'}}】${{matchedGrammar.title || matchedGrammar.pattern}} (點擊查看深度解說)`;
                }}

                // 點擊事件：若為文法標註，優先彈出 941 文法詳細解說卡！
                tokenSpan.addEventListener('click', (e) => {{
                    e.stopPropagation();
                    if (matchedGrammar) {{
                        showNovelGrammarCard(matchedGrammar.id);
                        return;
                    }}
                    // 否則彈出單字字典卡
                    showWordPopover(tokenSpan, w, e);
                }});

                container.appendChild(tokenSpan);
            }});
        }}

        // ==========================================================================
        // 2. 單句選取與朗讀、操作列 (Sentence Selection & Action Toolbar)
        // ==========================================================================
        function selectNovelSentence(sIdx, pNum, rowEl, sObj) {{
            document.querySelectorAll('.selected-sentence').forEach(el => el.classList.remove('selected-sentence'));
            rowEl.classList.add('selected-sentence');
            window.novelState.selectedSentenceIdx = sIdx;

            const toolbar = document.getElementById('sentenceFloatingToolbar');
            toolbar.classList.add('active');

            // 檢查本句是否已收藏
            const isFav = getSavedSentences().some(item => item.text === sObj.text);
            const favIcon = document.getElementById('sBarFavIcon');
            if (favIcon) {{
                favIcon.className = `fa-${{isFav ? 'solid' : 'regular'}} fa-star text-amber-500`;
            }}

            // 文法數量
            const gCount = (sObj.grammars || []).length;
            document.getElementById('sBarGrammarCount').textContent = gCount;

            // 綁定單句朗讀 (支援重複次數)
            document.getElementById('btnSentencePlay').onclick = () => {{
                if (window.NovelAudio.status === 'playing') {{
                    window.NovelAudio.pause();
                }} else if (window.NovelAudio.status === 'paused') {{
                    window.NovelAudio.resume();
                }} else {{
                    document.querySelectorAll('.karaoke-active-sentence').forEach(el => el.classList.remove('karaoke-active-sentence'));
                    rowEl.classList.add('karaoke-active-sentence');
                    window.NovelAudio.speak(sObj.text, rowEl, () => {{
                        rowEl.classList.remove('karaoke-active-sentence');
                    }});
                }}
            }};

            // 綁定單句收藏
            document.getElementById('btnSentenceFav').onclick = () => {{
                const bookTitle = window.novelState.currentBook.title;
                toggleFavoriteSentence(sObj.text, pNum, bookTitle);
                const nowFav = getSavedSentences().some(item => item.text === sObj.text);
                if (favIcon) favIcon.className = `fa-${{nowFav ? 'solid' : 'regular'}} fa-star text-amber-500`;
                const starInSentence = rowEl.querySelector('.sentence-star-btn');
                if (starInSentence) {{
                    starInSentence.className = `sentence-star-btn ${{nowFav ? 'is-fav' : ''}}`;
                    starInSentence.innerHTML = `<i class="fa-${{nowFav ? 'solid' : 'regular'}} fa-star"></i>`;
                }}
            }};

            // 綁定查看文法
            document.getElementById('btnSentenceGrammars').onclick = () => {{
                if (gCount === 0) {{
                    showToast('本句未包含 941 特殊文型。');
                    return;
                }}
                showNovelGrammarCard(sObj.grammars[0].id);
            }};

            // 綁定單句翻譯
            document.getElementById('btnSentenceTranslate').onclick = async () => {{
                let zhBox = rowEl.querySelector('.novel-sentence-zh');
                if (zhBox) {{
                    zhBox.remove();
                    return;
                }}
                showToast('正在即時翻譯句子...');
                const zh = await translateJaToZh(sObj.text);
                zhBox = document.createElement('div');
                zhBox.className = 'novel-sentence-zh';
                zhBox.style.cssText = 'font-size: 0.95rem; color: var(--text-muted); margin: 6px 0; border-left: 3px solid #3b82f6; padding-left: 10px; font-family: "Noto Sans TC", sans-serif;';
                zhBox.textContent = zh || '(無翻譯)';
                rowEl.appendChild(zhBox);
            }};
        }}

        window.closeSentenceToolbar = function() {{
            const toolbar = document.getElementById('sentenceFloatingToolbar');
            if (toolbar) toolbar.classList.remove('active');
            document.querySelectorAll('.selected-sentence').forEach(el => el.classList.remove('selected-sentence'));
        }};

        function setupSentenceToolbarEvents() {{
            document.getElementById('btnSentencePrev').onclick = () => {{
                const cur = window.novelState.selectedSentenceIdx;
                if (cur !== null && cur > 0) {{
                    const prevRow = document.querySelector(`.sentence-row[data-sentence-idx="${{cur - 1}}"]`);
                    if (prevRow) prevRow.click();
                }}
            }};
            document.getElementById('btnSentenceNext').onclick = () => {{
                const cur = window.novelState.selectedSentenceIdx;
                if (cur !== null) {{
                    const nextRow = document.querySelector(`.sentence-row[data-sentence-idx="${{cur + 1}}"]`);
                    if (nextRow) nextRow.click();
                }}
            }};
        }}

        // ==========================================================================
        // 3. 收藏句子管理 (Favorite Sentences Library)
        // ==========================================================================
        function getSavedSentences() {{
            try {{
                return JSON.parse(localStorage.getItem('novel_saved_sentences') || '[]');
            }} catch (e) {{
                return [];
            }}
        }}

        function toggleFavoriteSentence(text, pageNum, bookTitle) {{
            let list = getSavedSentences();
            const idx = list.findIndex(item => item.text === text);
            if (idx >= 0) {{
                list.splice(idx, 1);
                showToast('已自收藏庫移除。');
            }} else {{
                list.unshift({{
                    id: Date.now(),
                    text: text,
                    pageNum: pageNum,
                    bookTitle: bookTitle,
                    time: new Date().toLocaleDateString()
                }});
                showToast('⭐ 已成功存入句子收藏庫！');
            }}
            localStorage.setItem('novel_saved_sentences', JSON.stringify(list));
            updateSavedSentencesCountBadge();
        }}

        function updateSavedSentencesCountBadge() {{
            const count = getSavedSentences().length;
            const badge = document.getElementById('savedSentencesCount');
            if (badge) badge.textContent = count;
        }}

        window.openSavedSentencesModal = function() {{
            const list = getSavedSentences();
            const container = document.getElementById('savedSentencesList');
            document.getElementById('savedModalTotalCount').textContent = `${{list.length}} 句`;
            container.innerHTML = '';

            if (list.length === 0) {{
                container.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--text-muted); font-size: 1rem;"><i class="fa-regular fa-star" style="font-size: 2rem; margin-bottom: 8px;"></i><br>目前尚無收藏句子，在閱讀時點擊星號即可快速收藏！</div>`;
            }} else {{
                list.forEach((item, idx) => {{
                    const itemEl = document.createElement('div');
                    itemEl.className = 'saved-sentence-item';
                    itemEl.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span style="font-size: 0.78rem; font-weight: 700; color: var(--novel-accent);"><i class="fa-solid fa-book"></i> ${{item.bookTitle}} (第 ${{item.pageNum}} 頁)</span>
                            <div style="display: flex; gap: 8px;">
                                <button class="pill-btn" onclick="NovelAudio.speak('${{item.text.replace(/'/g, "\\\\'") }}', null, null, 1)" style="padding: 3px 8px; font-size: 0.75rem;"><i class="fa-solid fa-volume-high"></i> 朗讀</button>
                                <button class="pill-btn" onclick="copyToClipboard('${{item.text.replace(/'/g, "\\\\'") }}')" style="padding: 3px 8px; font-size: 0.75rem;"><i class="fa-solid fa-copy"></i> 複製</button>
                                <button class="pill-btn" onclick="deleteSavedSentence(${{item.id}})" style="padding: 3px 8px; font-size: 0.75rem; color: #dc2626;"><i class="fa-solid fa-trash"></i></button>
                            </div>
                        </div>
                        <div style="font-size: 1.15rem; font-weight: 600; line-height: 1.8; color: var(--text-main);">${{item.text}}</div>
                    `;
                    container.appendChild(itemEl);
                }});
            }}

            document.getElementById('savedSentencesModal').style.display = 'flex';
        }};

        window.closeSavedSentencesModal = function() {{
            document.getElementById('savedSentencesModal').style.display = 'none';
        }};

        window.deleteSavedSentence = function(id) {{
            let list = getSavedSentences().filter(item => item.id !== id);
            localStorage.setItem('novel_saved_sentences', JSON.stringify(list));
            updateSavedSentencesCountBadge();
            openSavedSentencesModal();
            showToast('已刪除收藏句子。');
        }};

        window.exportSavedSentences = function() {{
            const list = getSavedSentences();
            if (list.length === 0) {{
                showToast('目前無收藏句子可匯出。');
                return;
            }}
            const content = list.map((item, i) => `${{i + 1}}. [${{item.bookTitle}} P.${{item.pageNum}}]\\n${{item.text}}\\n`).join('\\n');
            const blob = new Blob([content], {{ type: 'text/plain;charset=utf-8' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `日文小說句子收藏_${{new Date().toISOString().slice(0, 10)}}.txt`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('已成功匯出句子文字檔！');
        }};

        window.copyToClipboard = function(str) {{
            navigator.clipboard.writeText(str).then(() => showToast('已複製到剪貼簿！'));
        }};

        // ==========================================================================
        // 4. 941 文法詳細解說彈出 (Grammar Detail Popover)
        // ==========================================================================
        window.showNovelGrammarCard = function(grammarId) {{
            const g = (typeof GRAMMAR_DATA !== 'undefined') ? GRAMMAR_DATA.find(item => item.id === grammarId) : null;
            if (!g) {{
                showToast('找不到該文法之詳細資料。');
                return;
            }}

            document.getElementById('novelGrammarTitle').textContent = g.title || g.pattern;
            document.getElementById('novelGrammarLevelBadge').textContent = g.level ? `${{g.level}} 文型` : '941 句型';
            
            let html = `
                <div style="margin-bottom: 14px; background: rgba(99, 102, 241, 0.08); padding: 12px 16px; border-radius: 10px; border-left: 4px solid #6366f1;">
                    <div style="font-weight: 800; color: #6366f1; margin-bottom: 4px;"><i class="fa-solid fa-link"></i> 【接續形式】</div>
                    <div style="font-weight: 600;">${{g.connection || '（無特定接續形式）'}}</div>
                </div>
                <div style="margin-bottom: 14px; background: rgba(0, 0, 0, 0.03); padding: 12px 16px; border-radius: 10px;">
                    <div style="font-weight: 800; color: var(--text-main); margin-bottom: 4px;"><i class="fa-solid fa-lightbulb text-amber-500"></i> 【文法意思】</div>
                    <div style="font-size: 1.05rem;">${{g.meaning || g.meaning_zh || '請參照例句理解語意。'}}</div>
                </div>
            `;

            if (g.examples && g.examples.length > 0) {{
                html += `<div style="font-weight: 800; color: var(--text-main); margin-bottom: 6px;"><i class="fa-solid fa-book-open"></i> 【精選例句】</div><ul style="padding-left: 20px; line-height: 2;">`;
                g.examples.forEach(ex => {{
                    html += `<li><strong style="color: var(--novel-accent);">${{ex.ja || ex}}</strong>${{ex.zh ? `<br><span style="color: var(--text-muted); font-size: 0.9em;">${{ex.zh}}</span>` : ''}}</li>`;
                }});
                html += `</ul>`;
            }}

            document.getElementById('novelGrammarBody').innerHTML = html;
            document.getElementById('novelGrammarModal').style.display = 'flex';
        }};

        window.closeNovelGrammarModal = function() {{
            document.getElementById('novelGrammarModal').style.display = 'none';
        }};

        // 工具列事件綁定
        function setupToolbarEvents() {{
            document.getElementById('btnPrevPage').onclick = () => goToPage(window.novelState.currentPageIndex - 1);
            document.getElementById('btnBottomPrev').onclick = () => goToPage(window.novelState.currentPageIndex - 1);
            document.getElementById('btnNextPage').onclick = () => goToPage(window.novelState.currentPageIndex + 1);
            document.getElementById('btnBottomNext').onclick = () => goToPage(window.novelState.currentPageIndex + 1);
            document.getElementById('btnFirstPage').onclick = () => goToPage(1);
            document.getElementById('btnLastPage').onclick = () => goToPage(window.novelState.currentBook.totalPages);

            document.getElementById('novelPageIndicator').onclick = () => {{
                const target = prompt(`請輸入欲跳轉之頁碼 (1 ~ ${{window.novelState.currentBook.totalPages}})：`, window.novelState.currentPageIndex);
                if (target) {{
                    const p = parseInt(target, 10);
                    if (!isNaN(p)) goToPage(p);
                }}
            }};

            document.getElementById('btnChangeRange').onclick = () => {{
                openPageSelector(window.novelState.currentBook.title, window.novelState.currentBook.totalPages);
            }};

            document.getElementById('btnOpenSavedSentences').onclick = openSavedSentencesModal;

            document.getElementById('btnToggleWritingMode').onclick = () => {{
                const newMode = window.novelState.writingMode === 'horizontal' ? 'vertical' : 'horizontal';
                setWritingMode(newMode);
            }};

            document.getElementById('btnCycleRuby').onclick = () => {{
                const modes = ['show', 'hard-only', 'hide'];
                const nextIdx = (modes.indexOf(window.novelState.rubyMode) + 1) % modes.length;
                setNovelRuby(modes[nextIdx]);
            }};

            document.getElementById('btnToggleNovelGrammar').onclick = (e) => {{
                window.novelState.showGrammar = !window.novelState.showGrammar;
                document.body.setAttribute('data-novel-grammar', window.novelState.showGrammar ? 'show' : 'hide');
                e.currentTarget.classList.toggle('active', window.novelState.showGrammar);
                showToast(window.novelState.showGrammar ? '已開啟 941 文法標註' : '已關閉文法標註 (純閱讀)');
            }};

            document.getElementById('btnToggleNovelVocab').onclick = (e) => {{
                window.novelState.showVocabColor = !window.novelState.showVocabColor;
                document.body.setAttribute('data-novel-vocab-color', window.novelState.showVocabColor ? 'show' : 'hide');
                e.currentTarget.classList.toggle('active', window.novelState.showVocabColor);
                showToast(window.novelState.showVocabColor ? '已開啟 JLPT 單字色彩' : '已關閉單字色彩 (純閱讀)');
            }};

            document.getElementById('btnToggleFontFamily').onclick = () => {{
                const nextFont = window.novelState.fontFamily === 'serif' ? 'sans' : 'serif';
                setNovelFont(nextFont);
            }};

            document.getElementById('btnFontInc').onclick = () => {{
                window.novelState.fontSize = Math.min(2.0, window.novelState.fontSize + 0.1);
                document.documentElement.style.setProperty('--novel-font-size', window.novelState.fontSize + 'rem');
            }};
            document.getElementById('btnFontDec').onclick = () => {{
                window.novelState.fontSize = Math.max(0.9, window.novelState.fontSize - 0.1);
                document.documentElement.style.setProperty('--novel-font-size', window.novelState.fontSize + 'rem');
            }};

            document.getElementById('btnCycleTheme').onclick = () => {{
                const themes = ['sepia', 'mint', 'dark', 'white'];
                const nextIdx = (themes.indexOf(window.novelState.theme) + 1) % themes.length;
                setNovelTheme(themes[nextIdx]);
            }};

            // 朗讀與暫停主按鈕
            document.getElementById('btnPlayNovelAudio').onclick = () => {{
                if (window.NovelAudio.status === 'playing') {{
                    window.NovelAudio.pause();
                }} else if (window.NovelAudio.status === 'paused') {{
                    window.NovelAudio.resume();
                }} else {{
                    playWholePageAudio();
                }}
            }};

            document.getElementById('btnStopNovelAudio').onclick = () => {{
                window.NovelAudio.stop();
            }};

            document.getElementById('novelRepeatCountSelect').onchange = (e) => {{
                window.novelState.repeatCount = parseInt(e.target.value, 10);
                localStorage.setItem('novel_repeat_count', e.target.value);
                showToast(`已設定每句重複 ${{e.target.options[e.target.selectedIndex].text}}`);
            }};

            document.addEventListener('keydown', (e) => {{
                if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;
                if (window.novelState.currentBook) {{
                    if (e.key === 'ArrowRight' || e.key === 'PageDown') {{
                        e.preventDefault();
                        goToPage(window.novelState.currentPageIndex + 1);
                    }} else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{
                        e.preventDefault();
                        goToPage(window.novelState.currentPageIndex - 1);
                    }} else if (e.code === 'Space') {{
                        e.preventDefault();
                        document.getElementById('btnPlayNovelAudio')?.click();
                    }}
                }}
            }});
        }}

        // 朗讀整頁句子
        function playWholePageAudio() {{
            const pNum = window.novelState.currentPageIndex;
            const pageData = window.novelState.pagesCache[pNum];
            if (!pageData || !pageData.analyzed) return;

            const sentences = pageData.analyzed.sentences;
            if (sentences.length === 0) return;

            let curSentenceIdx = 0;

            function playNext() {{
                if (curSentenceIdx >= sentences.length || window.NovelAudio.status === 'idle') {{
                    window.NovelAudio.stop(false);
                    return;
                }}

                const s = sentences[curSentenceIdx];
                const sRow = document.querySelector(`.sentence-row[data-sentence-idx="${{curSentenceIdx}}"][data-page-num="${{pNum}}"]`);
                
                document.querySelectorAll('.karaoke-active-sentence').forEach(el => el.classList.remove('karaoke-active-sentence'));
                if (sRow) {{
                    sRow.classList.add('karaoke-active-sentence');
                    sRow.scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }});
                }}

                window.NovelAudio.speak(s.text, sRow, () => {{
                    curSentenceIdx++;
                    playNext();
                }});
            }}

            playNext();
        }}

        function setWritingMode(mode) {{
            window.novelState.writingMode = mode;
            localStorage.setItem('novel_writing_mode', mode);
            const box = document.getElementById('novelContentBox');
            const label = document.getElementById('writingModeLabel');

            if (mode === 'vertical') {{
                box.className = 'novel-reader-deck mode-vertical';
                label.textContent = '橫書橫排';
                showToast('已切換為【日文直排豎讀 (縱書)】模式');
                box.scrollLeft = box.scrollWidth;
            }} else {{
                box.className = 'novel-reader-deck mode-horizontal';
                label.textContent = '縱書豎讀';
                showToast('已切換為【現代橫排 (橫書)】模式');
            }}
        }}

        function setNovelRuby(mode) {{
            window.novelState.rubyMode = mode;
            localStorage.setItem('novel_ruby', mode);
            document.body.setAttribute('data-novel-ruby', mode);
            const label = document.getElementById('rubyModeLabel');
            if (mode === 'show') {{
                label.textContent = '假名: 全部';
                showToast('已開啟【全部漢字振假名】');
            }} else if (mode === 'hard-only') {{
                label.textContent = '假名: 僅難字';
                showToast('已開啟【僅難字/N1-N3振假名】(進階沉浸)');
            }} else {{
                label.textContent = '假名: 隱藏';
                showToast('已開啟【純日文閱讀 (懸停查讀音)】');
            }}
        }}

        function setNovelFont(font) {{
            window.novelState.fontFamily = font;
            localStorage.setItem('novel_font', font);
            document.body.setAttribute('data-novel-font', font);
            const btn = document.getElementById('btnToggleFontFamily');
            btn.innerHTML = font === 'serif' ? '<i class="fa-solid fa-pen-nib"></i> 明朝體' : '<i class="fa-solid fa-font"></i> 黑體';
        }}

        function setNovelTheme(theme) {{
            window.novelState.theme = theme;
            localStorage.setItem('novel_theme', theme);
            document.body.setAttribute('data-novel-theme', theme);
            const label = document.getElementById('themeLabel');
            const map = {{ 'sepia': '紙質', 'mint': '豆沙', 'dark': '夜間', 'white': '純白' }};
            label.textContent = map[theme] || '主題';
        }}

        function updateToolbarInfo() {{
            const book = window.novelState.currentBook;
            if (!book) return;

            const cur = window.novelState.currentPageIndex;
            const total = book.totalPages;
            const start = window.novelState.loadedBatchStart;
            const end = window.novelState.loadedBatchEnd;

            document.getElementById('curPageNumDisplay').textContent = cur;
            document.getElementById('totalPageNumDisplay').textContent = total;
            document.getElementById('batchRangeBadge').textContent = `${{start}}~${{end}}`;
            document.getElementById('bottomProgressText').textContent = `閱讀進度：第 ${{cur}} / ${{total}} 頁 (${{((cur / total) * 100).toFixed(1)}}%)`;

            const pct = Math.min(100, Math.max(0, (cur / total) * 100));
            document.getElementById('novelProgressBarFill').style.width = pct + '%';

            document.getElementById('btnPrevPage').disabled = (cur <= 1);
            document.getElementById('btnBottomPrev').disabled = (cur <= 1);
            document.getElementById('btnNextPage').disabled = (cur >= total);
            document.getElementById('btnBottomNext').disabled = (cur >= total);
        }}

        function saveBookmark(title, pageNum) {{
            const key = 'novel_bookmark_' + encodeURIComponent(title);
            localStorage.setItem(key, pageNum.toString());
        }}

        async function goToPage(targetPage) {{
            const book = window.novelState.currentBook;
            if (!book) return;

            window.NovelAudio.stop(false);

            if (targetPage < 1) targetPage = 1;
            if (targetPage > book.totalPages) targetPage = book.totalPages;

            if (targetPage >= window.novelState.loadedBatchStart && targetPage <= window.novelState.loadedBatchEnd) {{
                window.novelState.currentPageIndex = targetPage;
                renderCurrentPage();
            }} else {{
                const newStart = Math.max(1, targetPage - 2);
                const newEnd = Math.min(book.totalPages, newStart + 4);
                document.getElementById('inputStartPage').value = newStart;
                document.getElementById('inputEndPage').value = newEnd;
                showToast(`正在切換並解析第 ${{newStart}} ~ ${{newEnd}} 頁...`);
                await startNovelReading();
                window.novelState.currentPageIndex = targetPage;
                renderCurrentPage();
            }}
        }}

        window.openPasteModal = function() {{
            document.getElementById('pasteModal').style.display = 'flex';
        }};
        document.getElementById('btnOpenPasteModal').onclick = openPasteModal;

        window.closePasteModal = function() {{
            document.getElementById('pasteModal').style.display = 'none';
        }};

        window.confirmPastedNovel = function() {{
            const text = document.getElementById('pastedNovelText').value.trim();
            if (!text) {{
                showToast('請輸入或貼上文章內容！');
                return;
            }}
            closePasteModal();
            paginateTextBook('自訂貼附文章', text, 'pasted');
        }};

        window.openFilePicker = function() {{
            document.getElementById('novelFileInput').click();
        }};

    }})();
    </script>

</body>
</html>
"""

    out_file = os.path.join(root, "novel.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(novel_html)

    size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f"[OK] 成功產出日文小說閱讀器：{out_file} ({size_mb:.2f} MB)")

    alias_file = os.path.join(root, "小說閱讀.html")
    shutil.copy2(out_file, alias_file)
    print(f"[OK] 成功產出本地別名：{alias_file}")

if __name__ == "__main__":
    build()
