# -*- coding: utf-8 -*-
"""
日文小說閱讀器 (Novel Master) 產生器
以 master.html (閱讀高手) 為基礎，打造專屬小說沉浸閱讀工作台：
1. 萬能檔案導入：PDF (.pdf), EPUB (.epub), TXT (.txt), Word (.docx), Markdown (.md), 剪貼簿貼上, 內建名作
2. 彈性頁數選擇器：自動分析總頁數/總字數，可自訂起始頁與結束頁（如 1~5 頁、1~10 頁、單頁精讀），避免整本小說一次性載入卡頓
3. 閱讀進度記憶：自動記憶每本書讀到的頁數，下次開啟一鍵接續閱讀
4. 沉浸式排版：縱書 (日文直排豎讀 writing-mode: vertical-rl) 與 橫書 (橫排) 一鍵切換
5. 四大經典主題：紙質暖黃、清新豆沙綠、夜間深色、水墨純白
6. 閱讀高手日語學習能力繼承：
   - 941條《絵でわかる日本語》文法自動標註與點擊解說
   - JLPT N1~N5 分級單字色彩標記
   - 振假名 (Ruby) 智慧切換（全部 / 僅難字 / 隱藏）
   - 微軟 Edge 自然真人語音（七海 / 圭太）朗讀與 Karaoke 隨音變色高亮
   - 點擊單字浮動字典（讀音、詞性、釋義、一鍵存入生詞本）
   - 單句雙語對照展開
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
    # Script 7: Edge TTS audio & Karaoke
    audio_script = scripts[6].group(2)

    print("[2/4] 設計小說閱讀專屬樣式與排版...")
    
    novel_css = """
/* ==========================================================================
   日文小說閱讀器 (Novel Master) 專屬沉浸式樣式
   ========================================================================== */

/* 主題配色定義 */
:root {
    --novel-bg: #fcf8f2;
    --novel-text: #2c2724;
    --novel-card-bg: rgba(255, 255, 255, 0.85);
    --novel-border: rgba(44, 39, 36, 0.12);
    --novel-accent: #d97706;
    --novel-accent-hover: #b45309;
    --novel-font-size: 1.22rem;
    --novel-line-height: 2.1;
    --novel-ruby-size: 0.58em;
}

/* 經典暖黃紙質 (Sepia Paper) */
body[data-novel-theme="sepia"] {
    --novel-bg: #fbf6ec;
    --novel-text: #2d261e;
    --novel-card-bg: #f5eedf;
    --novel-border: #e3d5be;
    background-color: var(--novel-bg) !important;
    color: var(--novel-text) !important;
}

/* 清新護眼豆沙綠 (Mint Care) */
body[data-novel-theme="mint"] {
    --novel-bg: #edf5ed;
    --novel-text: #1e3321;
    --novel-card-bg: #e1ede1;
    --novel-border: #c8dec8;
    background-color: var(--novel-bg) !important;
    color: var(--novel-text) !important;
}

/* 沉浸夜間暗黑 (Night Dark) */
body[data-novel-theme="dark"] {
    --novel-bg: #181920;
    --novel-text: #d2d5e2;
    --novel-card-bg: #21222c;
    --novel-border: #323444;
    background-color: var(--novel-bg) !important;
    color: var(--novel-text) !important;
}

/* 簡約水墨純白 (Pure White) */
body[data-novel-theme="white"] {
    --novel-bg: #ffffff;
    --novel-text: #1f2937;
    --novel-card-bg: #f9fafb;
    --novel-border: #e5e7eb;
    background-color: var(--novel-bg) !important;
    color: var(--novel-text) !important;
}

/* 字體切換 */
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

/* 小說主版面容器 */
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

/* 頁數選擇器卡片 (關鍵功能：可選頁數，要不然一本太多) */
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
    margin-bottom: 1.5em;
    text-indent: 1em;
    word-break: break-word;
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
    margin-left: 2em;
    margin-bottom: 0;
    text-indent: 1em;
    display: inline-block;
    vertical-align: top;
}
/* 縱書下標點符號與引號微調 */
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

/* 單字與假名微調 */
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

/* 假名注音模式切換 */
/* 1. 全部顯示 (預設) */
/* 2. 僅難字顯示 (隱藏 N4, N5 假名) */
body[data-novel-ruby="hard-only"] .word-token[data-jlpt="N5"] ruby rt,
body[data-novel-ruby="hard-only"] .word-token[data-jlpt="N4"] ruby rt {
    display: none !important;
}
/* 3. 完全隱藏假名 (沉浸純文字) */
body[data-novel-ruby="hide"] ruby rt {
    display: none !important;
}
body[data-novel-ruby="hide"] .word-token:hover ruby rt {
    display: block !important;
    color: var(--novel-accent) !important;
}

/* 文法高亮開關 */
body[data-novel-grammar="hide"] .grammar-highlight {
    background: transparent !important;
    border-bottom: none !important;
}

/* JLPT色彩開關 */
body[data-novel-vocab-color="hide"] .word-token {
    color: inherit !important;
}

/* Karaoke 跟讀變色追蹤 (小說沉浸式版) */
.karaoke-current-word {
    background: #fde047 !important;
    color: #854d0e !important;
    border-radius: 4px;
    box-shadow: 0 0 10px rgba(250, 204, 21, 0.7);
    font-weight: 800;
}
body[data-novel-theme="dark"] .karaoke-current-word {
    background: #ca8a04 !important;
    color: #ffffff !important;
}
.karaoke-active-sentence {
    background: rgba(217, 119, 6, 0.08) !important;
    border-radius: 6px;
    transition: background 0.2s ease;
}

/* 單句懸浮與 Trancy 雙語卡片彈出按鈕 */
.sentence-row {
    position: relative;
    border-radius: 4px;
    transition: background 0.15s;
    padding: 2px 0;
}
.sentence-row:hover {
    background: rgba(217, 119, 6, 0.06);
}
.sentence-row.active {
    background: rgba(217, 119, 6, 0.12);
}

/* 浮動式單字字典卡片微調 */
.word-popover {
    z-index: 99999 !important;
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
}
"""

    print("[3/4] 整合 HTML 架構與專屬小說引擎...")
    
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

                    <!-- 語音朗讀此頁 -->
                    <button class="novel-tool-btn" id="btnPlayNovelAudio" style="background: linear-gradient(135deg, #10b981, #059669); color: #fff; font-weight: 700;" title="微軟自然語音朗讀當前頁 (支援 Karaoke 同步高亮)">
                        <i class="fa-solid fa-volume-high"></i> <span id="audioPlayBtnText">朗讀此頁</span>
                    </button>

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

    <!-- 941 文法深度解說彈窗卡片 -->
    <div id="novelGrammarModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.55); z-index: 99999; align-items: center; justify-content: center; backdrop-filter: blur(4px);">
        <div style="background: var(--novel-card-bg); border: 1.5px solid var(--novel-border); border-radius: 18px; padding: 28px; max-width: 680px; width: 92%; max-height: 85vh; overflow-y: auto; box-shadow: 0 12px 40px rgba(0,0,0,0.25);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-bottom: 1px solid var(--novel-border); padding-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="background: rgba(99, 102, 241, 0.15); color: #6366f1; padding: 3px 10px; border-radius: 9999px; font-weight: 800; font-size: 0.82rem;" id="novelGrammarLevelBadge">N3 文型</span>
                    <h3 style="font-size: 1.35rem; font-weight: 800; color: var(--text-main);" id="novelGrammarTitle">文法標題</h3>
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

    <!-- 微軟自然語音與 Karaoke 高亮引擎 -->
    <script id="masterInteractiveScript">
{audio_script}
    </script>

    <!-- ==========================================================================
         小說專屬核心引擎 (Novel Engine)
         ========================================================================== -->
    <script>
    (function() {{
        // 小說專屬狀態管理
        window.novelState = {{
            currentBook: null,       // 當前書籍對象 {{ title, type, totalPages, pagesData: [] }}
            loadedBatchStart: 1,     // 當前載入的起始頁
            loadedBatchEnd: 5,       // 當前載入的結束頁
            currentPageIndex: 1,     // 目前正在閱讀的頁碼 (1-indexed)
            pagesCache: {{}},         // 各頁純文字與解析結果快取 {{ [pageNum]: {{ text, analyzed }} }}
            writingMode: 'horizontal', // 'horizontal' | 'vertical'
            rubyMode: 'show',        // 'show' | 'hard-only' | 'hide'
            theme: 'sepia',          // 'sepia' | 'mint' | 'dark' | 'white'
            fontFamily: 'serif',     // 'serif' | 'sans'
            fontSize: 1.22,          // rem
            showGrammar: true,
            showVocabColor: true,
            isPlayingAudio: false,
            currentAudioPage: null
        }};

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
            loadSavedPreferences();
        }});

        // 讀取偏好設定
        function loadSavedPreferences() {{
            const savedTheme = localStorage.getItem('novel_theme') || 'sepia';
            setNovelTheme(savedTheme);

            const savedFont = localStorage.getItem('novel_font') || 'serif';
            setNovelFont(savedFont);

            const savedRuby = localStorage.getItem('novel_ruby') || 'show';
            setNovelRuby(savedRuby);

            const savedMode = localStorage.getItem('novel_writing_mode') || 'horizontal';
            setWritingMode(savedMode);
        }}

        // 萬能拖曳上傳與檔案選擇
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

        // 處理使用者上傳的檔案 (支援 PDF, EPUB, TXT, DOCX)
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
                    // txt, md, plain text
                    await parseTextFile(file);
                }}
            }} catch (err) {{
                console.error(err);
                showToast(`檔案載入失敗：${{err.message}}`);
            }}
        }}

        // 1. 解析 PDF 檔案 (使用 PDF.js)
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

                    // 日文換行正規化：段落內部不補空格，對話「」或句號。換行
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

        // 2. 解析 EPUB 檔案 (使用 JSZip)
        async function parseEpub(file) {{
            const zip = await JSZip.loadAsync(file);
            // 讀取 container.xml 尋找 OPF 路徑
            const containerXml = await zip.file("META-INF/container.xml").async("text");
            const opfMatch = containerXml.match(/full-path="([^"]+)"/);
            const opfPath = opfMatch ? opfMatch[1] : "OEBPS/content.opf";
            const opfDir = opfPath.includes('/') ? opfPath.substring(0, opfPath.lastIndexOf('/') + 1) : '';

            const opfContent = await zip.file(opfPath).async("text");
            const parser = new DOMParser();
            const opfDoc = parser.parseFromString(opfContent, "application/xml");

            // 尋找 spine 與 manifest
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

            // 依章節提取文字並進行分頁切分
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

        // 3. 解析 Word DOCX 檔案 (使用 JSZip)
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

        // 4. 解析純文字檔案 (TXT / MD / 青空文庫)
        async function parseTextFile(file) {{
            const buffer = await file.arrayBuffer();
            let text = '';
            // 自動偵測編碼：先嘗試 UTF-8，若有亂碼再嘗試 Shift-JIS (日文常見)
            try {{
                const decoder = new TextDecoder('utf-8', {{ fatal: true }});
                text = decoder.decode(buffer);
            }} catch (e) {{
                const decoder = new TextDecoder('shift-jis');
                text = decoder.decode(buffer);
            }}

            // 青空文庫標記清理 (移除 ［＃...］註記，將 ｜漢字《かんじ》 轉換為乾淨漢字)
            text = text.replace(/［＃[^］]+］/g, '');
            text = text.replace(/｜?([一-龯々]+)《([^》]+)》/g, '$1');

            paginateTextBook(file.name, text, 'txt');
        }}

        // 長文智慧分頁演算法 (~1,000 字一頁，避免一次載入太多)
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

        // 開啟範本名著
        window.loadSampleNovel = function(key) {{
            const sample = window.SAMPLE_NOVELS[key];
            if (!sample) return;
            paginateTextBook(sample.title, sample.text, 'sample');
        }};

        // 開啟頁數選擇器卡片 (可選頁數，要不然一本太多)
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

            // 檢查是否有儲存之閱讀進度
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

            // 滑桿與輸入連動
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

        // 快速頁數批次設定
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

        // 開始解析所選頁面並渲染
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
                // 逐頁提取並解析
                for (let p = startPage; p <= endPage; p++) {{
                    if (!window.novelState.pagesCache[p] || !window.novelState.pagesCache[p].analyzed) {{
                        const rawText = await book.getPageText(p);
                        // 調用閱讀高手核心 NLP 分析引擎
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

                // 儲存進度
                saveBookmark(book.title, startPage);
            }} catch (err) {{
                console.error(err);
                document.getElementById('novelLoadingState').style.display = 'none';
                showToast(`解析出錯：${{err.message}}`);
            }}
        }}

        document.getElementById('btnStartNovelReading').addEventListener('click', startNovelReading);

        // 渲染當前頁面
        function renderCurrentPage() {{
            const pNum = window.novelState.currentPageIndex;
            const pageData = window.novelState.pagesCache[pNum];
            const contentBox = document.getElementById('novelContentBox');
            contentBox.innerHTML = '';

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

            // 依句子與段落建立 DOM 元素
            let curParagraphEl = document.createElement('div');
            curParagraphEl.className = 'novel-paragraph';

            analyzed.sentences.forEach((s, sIdx) => {{
                const sRow = document.createElement('span');
                sRow.className = 'sentence-row';
                sRow.dataset.sentenceIdx = sIdx;
                sRow.dataset.pageNum = pNum;

                // 點擊句子播放發音與 Trancy 雙語連動
                sRow.addEventListener('click', (e) => {{
                    if (e.target.closest('.word-token')) return;
                    playSentenceAudio(s.text, sRow);
                }});

                // 呼叫閱讀高手核心 renderSentenceTokens 注入假名與單字卡
                renderSentenceTokens(sRow, s, sIdx);

                curParagraphEl.appendChild(sRow);

                // 若句子以句號或換行結束，或是包含換行符
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
            // 自動儲存書籤
            saveBookmark(bookTitle, pNum);

            // 滾動回頂端 (橫排) 或滾動回最右側 (縱書)
            if (window.novelState.writingMode === 'vertical') {{
                contentBox.scrollLeft = contentBox.scrollWidth;
            }} else {{
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }}
        }}

        // 更新工具列進度與頁碼
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

            // 進度條
            const pct = Math.min(100, Math.max(0, (cur / total) * 100));
            document.getElementById('novelProgressBarFill').style.width = pct + '%';

            // 翻頁按鈕狀態
            document.getElementById('btnPrevPage').disabled = (cur <= 1);
            document.getElementById('btnBottomPrev').disabled = (cur <= 1);
            document.getElementById('btnNextPage').disabled = (cur >= total);
            document.getElementById('btnBottomNext').disabled = (cur >= total);
        }}

        // 書籤儲存至 LocalStorage
        function saveBookmark(title, pageNum) {{
            const key = 'novel_bookmark_' + encodeURIComponent(title);
            localStorage.setItem(key, pageNum.toString());
        }}

        // 翻頁邏輯 (自動無縫載入)
        async function goToPage(targetPage) {{
            const book = window.novelState.currentBook;
            if (!book) return;

            if (targetPage < 1) targetPage = 1;
            if (targetPage > book.totalPages) targetPage = book.totalPages;

            // 若目標頁在目前載入範圍內
            if (targetPage >= window.novelState.loadedBatchStart && targetPage <= window.novelState.loadedBatchEnd) {{
                window.novelState.currentPageIndex = targetPage;
                renderCurrentPage();
            }} else {{
                // 自動延伸或切換至目標頁之新批次 (5頁為一組)
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

        // 工具列事件綁定
        function setupToolbarEvents() {{
            document.getElementById('btnPrevPage').onclick = () => goToPage(window.novelState.currentPageIndex - 1);
            document.getElementById('btnBottomPrev').onclick = () => goToPage(window.novelState.currentPageIndex - 1);
            document.getElementById('btnNextPage').onclick = () => goToPage(window.novelState.currentPageIndex + 1);
            document.getElementById('btnBottomNext').onclick = () => goToPage(window.novelState.currentPageIndex + 1);
            document.getElementById('btnFirstPage').onclick = () => goToPage(1);
            document.getElementById('btnLastPage').onclick = () => goToPage(window.novelState.currentBook.totalPages);

            // 點擊頁碼直接跳轉
            document.getElementById('novelPageIndicator').onclick = () => {{
                const target = prompt(`請輸入欲跳轉之頁碼 (1 ~ ${{window.novelState.currentBook.totalPages}})：`, window.novelState.currentPageIndex);
                if (target) {{
                    const p = parseInt(target, 10);
                    if (!isNaN(p)) goToPage(p);
                }}
            }};

            // 重新調整範圍
            document.getElementById('btnChangeRange').onclick = () => {{
                openPageSelector(window.novelState.currentBook.title, window.novelState.currentBook.totalPages);
            }};

            // 縱書 / 橫書 切換
            document.getElementById('btnToggleWritingMode').onclick = () => {{
                const newMode = window.novelState.writingMode === 'horizontal' ? 'vertical' : 'horizontal';
                setWritingMode(newMode);
            }};

            // 假名顯示三段切換 (全部 -> 僅難字 -> 隱藏)
            document.getElementById('btnCycleRuby').onclick = () => {{
                const modes = ['show', 'hard-only', 'hide'];
                const nextIdx = (modes.indexOf(window.novelState.rubyMode) + 1) % modes.length;
                setNovelRuby(modes[nextIdx]);
            }};

            // 文型開關
            document.getElementById('btnToggleNovelGrammar').onclick = (e) => {{
                window.novelState.showGrammar = !window.novelState.showGrammar;
                document.body.setAttribute('data-novel-grammar', window.novelState.showGrammar ? 'show' : 'hide');
                e.currentTarget.classList.toggle('active', window.novelState.showGrammar);
                showToast(window.novelState.showGrammar ? '已開啟 941 文法標註' : '已關閉文法標註 (純閱讀)');
            }};

            // 單字著色開關
            document.getElementById('btnToggleNovelVocab').onclick = (e) => {{
                window.novelState.showVocabColor = !window.novelState.showVocabColor;
                document.body.setAttribute('data-novel-vocab-color', window.novelState.showVocabColor ? 'show' : 'hide');
                e.currentTarget.classList.toggle('active', window.novelState.showVocabColor);
                showToast(window.novelState.showVocabColor ? '已開啟 JLPT 單字色彩' : '已關閉單字色彩 (純閱讀)');
            }};

            // 字體風格切換 (明朝 / 黑體)
            document.getElementById('btnToggleFontFamily').onclick = () => {{
                const nextFont = window.novelState.fontFamily === 'serif' ? 'sans' : 'serif';
                setNovelFont(nextFont);
            }};

            // 字級縮放
            document.getElementById('btnFontInc').onclick = () => {{
                window.novelState.fontSize = Math.min(2.0, window.novelState.fontSize + 0.1);
                document.documentElement.style.setProperty('--novel-font-size', window.novelState.fontSize + 'rem');
            }};
            document.getElementById('btnFontDec').onclick = () => {{
                window.novelState.fontSize = Math.max(0.9, window.novelState.fontSize - 0.1);
                document.documentElement.style.setProperty('--novel-font-size', window.novelState.fontSize + 'rem');
            }};

            // 主題切換 (紙質 -> 豆沙 -> 夜間 -> 純白)
            document.getElementById('btnCycleTheme').onclick = () => {{
                const themes = ['sepia', 'mint', 'dark', 'white'];
                const nextIdx = (themes.indexOf(window.novelState.theme) + 1) % themes.length;
                setNovelTheme(themes[nextIdx]);
            }};

            // 朗讀當前頁 (Karaoke 變色跟讀)
            document.getElementById('btnPlayNovelAudio').onclick = togglePlayCurrentPageAudio;

            // 鍵盤左右鍵快捷翻頁
            document.addEventListener('keydown', (e) => {{
                if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;
                if (window.novelState.currentBook) {{
                    if (e.key === 'ArrowRight' || e.key === 'PageDown') {{
                        e.preventDefault();
                        goToPage(window.novelState.currentPageIndex + 1);
                    }} else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{
                        e.preventDefault();
                        goToPage(window.novelState.currentPageIndex - 1);
                    }}
                }}
            }});
        }}

        // 切換縱書與橫書
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

        // 切換假名模式
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

        // 切換字體
        function setNovelFont(font) {{
            window.novelState.fontFamily = font;
            localStorage.setItem('novel_font', font);
            document.body.setAttribute('data-novel-font', font);
            const btn = document.getElementById('btnToggleFontFamily');
            btn.innerHTML = font === 'serif' ? '<i class="fa-solid fa-pen-nib"></i> 明朝體' : '<i class="fa-solid fa-font"></i> 黑體';
        }}

        // 切換主題
        function setNovelTheme(theme) {{
            window.novelState.theme = theme;
            localStorage.setItem('novel_theme', theme);
            document.body.setAttribute('data-novel-theme', theme);
            const label = document.getElementById('themeLabel');
            const map = {{
                'sepia': '紙質',
                'mint': '豆沙',
                'dark': '夜間',
                'white': '純白'
            }};
            label.textContent = map[theme] || '主題';
        }}

        // 朗讀當前頁 (整合 Karaoke)
        function togglePlayCurrentPageAudio() {{
            if (window.novelState.isPlayingAudio) {{
                stopNovelAudio();
                return;
            }}

            const pNum = window.novelState.currentPageIndex;
            const pageData = window.novelState.pagesCache[pNum];
            if (!pageData || !pageData.analyzed) return;

            const sentences = pageData.analyzed.sentences;
            if (sentences.length === 0) return;

            window.novelState.isPlayingAudio = true;
            document.getElementById('audioPlayBtnText').textContent = '暫停朗讀';

            let curSentenceIdx = 0;

            function playNextSentence() {{
                if (!window.novelState.isPlayingAudio || curSentenceIdx >= sentences.length) {{
                    stopNovelAudio();
                    return;
                }}

                const s = sentences[curSentenceIdx];
                const sRow = document.querySelector(`.sentence-row[data-sentence-idx="${{curSentenceIdx}}"][data-page-num="${{pNum}}"]`);
                
                // 高亮當前句子
                document.querySelectorAll('.karaoke-active-sentence').forEach(el => el.classList.remove('karaoke-active-sentence'));
                if (sRow) {{
                    sRow.classList.add('karaoke-active-sentence');
                    sRow.scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }});
                }}

                // 調用微軟自然語音與 Karaoke 隨音變色高亮
                speakWithKaraoke(s.text, sRow, () => {{
                    curSentenceIdx++;
                    playNextSentence();
                }});
            }}

            playNextSentence();
        }}

        function stopNovelAudio() {{
            window.novelState.isPlayingAudio = false;
            document.getElementById('audioPlayBtnText').textContent = '朗讀此頁';
            if (window.speechSynthesis) window.speechSynthesis.cancel();
            document.querySelectorAll('.karaoke-active-sentence').forEach(el => el.classList.remove('karaoke-active-sentence'));
            document.querySelectorAll('.karaoke-current-word').forEach(el => el.classList.remove('karaoke-current-word'));
        }}

        // 單句點擊朗讀
        function playSentenceAudio(text, rowEl) {{
            document.querySelectorAll('.karaoke-active-sentence').forEach(el => el.classList.remove('karaoke-active-sentence'));
            if (rowEl) rowEl.classList.add('karaoke-active-sentence');
            speakWithKaraoke(text, rowEl, () => {{
                if (rowEl) rowEl.classList.remove('karaoke-active-sentence');
            }}, true);
        }}

        // 點擊文法標籤彈出解說卡
        window.showNovelGrammarCard = function(grammarId) {{
            const g = (typeof GRAMMAR_DATA !== 'undefined') ? GRAMMAR_DATA.find(item => item.id === grammarId) : null;
            if (!g) return;

            document.getElementById('novelGrammarTitle').textContent = g.title || g.pattern;
            document.getElementById('novelGrammarLevelBadge').textContent = g.level ? `${{g.level}} 文型` : '941 句型';
            
            let html = `
                <div style="margin-bottom: 14px; background: rgba(99, 102, 241, 0.08); padding: 12px 16px; border-radius: 10px;">
                    <div style="font-weight: 800; color: #6366f1; margin-bottom: 4px;">【接續形式】</div>
                    <div>${{g.connection || '（無特定接續形式）'}}</div>
                </div>
                <div style="margin-bottom: 14px;">
                    <div style="font-weight: 800; color: var(--text-main); margin-bottom: 4px;">【文法意思】</div>
                    <div>${{g.meaning || g.meaning_zh || '請參照例句理解語意。'}}</div>
                </div>
            `;

            if (g.examples && g.examples.length > 0) {{
                html += `<div style="font-weight: 800; color: var(--text-main); margin-bottom: 6px;">【精選例句】</div><ul style="padding-left: 20px; line-height: 2;">`;
                g.examples.forEach(ex => {{
                    html += `<li><strong>${{ex.ja || ex}}</strong>${{ex.zh ? `<br><span style="color: var(--text-muted); font-size: 0.9em;">${{ex.zh}}</span>` : ''}}</li>`;
                }});
                html += `</ul>`;
            }}

            document.getElementById('novelGrammarBody').innerHTML = html;
            document.getElementById('novelGrammarModal').style.display = 'flex';
        }};

        window.closeNovelGrammarModal = function() {{
            document.getElementById('novelGrammarModal').style.display = 'none';
        }};

        // 剪貼簿貼上視窗
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

    # 另外建立 小說閱讀.html 供本地雙擊開啟
    alias_file = os.path.join(root, "小說閱讀.html")
    shutil.copy2(out_file, alias_file)
    print(f"[OK] 成功產出本地別名：{alias_file}")

if __name__ == "__main__":
    build()
