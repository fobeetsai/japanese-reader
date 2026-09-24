import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

SRC_PATH = r"C:\Users\fobee\.gemini\antigravity\brain\6d082372-7b23-40c1-9376-7edebe56bcfe\scratch\c0fac0b_novel.html"
TARGET_NOVEL = r"C:\Users\fobee\我的雲端硬碟\Antigravity Apps\Ai agent\novel.html"
TARGET_ALIAS = r"C:\Users\fobee\我的雲端硬碟\Antigravity Apps\Ai agent\小說閱讀.html"
SCRIPT9_PATH = r"C:\Users\fobee\.gemini\antigravity\brain\6d082372-7b23-40c1-9376-7edebe56bcfe\scratch\script9_full.js"

print("[1/5] 讀取原始 c0fac0b_novel.html 完整版型與代碼...")
with open(SRC_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# 1. 在 <head> 中加入 no-referrer 與 Tesseract OCR, epub, mammoth
if '<meta name="referrer"' not in html:
    html = html.replace('<meta name="viewport"', '<meta name="referrer" content="no-referrer">\n    <meta name="viewport"')

if 'tesseract.min.js' not in html:
    tesseract_tag = '<script src="https://cdn.jsdelivr.net/npm/tesseract.js@4.1.1/dist/tesseract.min.js"></script>\n    <script src="https://cdn.jsdelivr.net/npm/epubjs/dist/epub.min.js"></script>\n    <script src="https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.6.0/mammoth.browser.min.js"></script>'
    html = html.replace('<!-- JSZip (EPUB / Word docx', tesseract_tag + '\n    <!-- JSZip (EPUB / Word docx')

# 2. 在 novelImportCard 的按鈕列中加入「拍照 / 圖片 OCR」按鈕
ocr_btn_html = """
                <button class="pill-btn" onclick="openOcrModal()" style="padding: 10px 18px; font-weight: 700; background: linear-gradient(135deg, #6366f1, #4f46e5); color: #fff; border: none; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);">
                    <i class="fa-solid fa-camera"></i> 拍照 / 圖片 OCR 辨識
                </button>
"""
if 'openOcrModal()' not in html:
    html = html.replace('<button class="pill-btn" id="btnOpenPasteModal"', ocr_btn_html + '\n                <button class="pill-btn" id="btnOpenPasteModal"')

# 3. 在 novelReadingToolbar 中擴充按鈕
novel_audio_toolbar_html = """
                    <!-- 微軟自然真人語音切換 -->
                    <select id="novelVoiceSelect" class="novel-tool-btn" style="padding: 5px 8px; font-weight: 600;" title="切換微軟真人自然語音">
                        <option value="nanami" selected>🌸 七海 Nanami (微軟自然女聲)</option>
                        <option value="keita">🎙️ 圭太 Keita (微軟自然男聲)</option>
                    </select>

                    <!-- 每句朗讀重複次數 -->
                    <select id="novelRepeatCountSelect" class="novel-tool-btn" style="padding: 5px 8px; font-weight: 600;" title="設定每句重複朗讀次數">
                        <option value="1">朗讀 1 次</option>
                        <option value="2">重複 2 次</option>
                        <option value="3" selected>重複 3 次 (精聽)</option>
                        <option value="5">重複 5 次 (複讀)</option>
                        <option value="999">🔂 單句循環</option>
                    </select>

                    <!-- 停止朗讀按鈕 -->
                    <button class="novel-tool-btn" id="btnStopNovelAudio" style="display: none; background: #fee2e2; color: #b91c1c; border-color: #fca5a5;" title="停止語音朗讀">
                        <i class="fa-solid fa-stop"></i> 停止
                    </button>

                    <!-- 我的生詞本抽屜按鈕 -->
                    <button class="novel-tool-btn" id="btnOpenNotebookModal" onclick="openNotebookModal()" title="開啟日語生詞本">
                        <i class="fa-solid fa-bookmark text-amber-500"></i> 生詞本 <span class="novel-badge" id="savedWordsCountBadge" style="background: #fef3c7; color: #b45309; padding: 2px 6px; border-radius: 9999px; font-size: 0.75rem; margin-left: 4px;">0</span>
                    </button>

                    <!-- 我的收藏句子抽屜按鈕 -->
                    <button class="novel-tool-btn" id="btnOpenSavedSentences" onclick="openSavedSentencesModal()" title="查看已收藏的日語句子">
                        <i class="fa-solid fa-star text-amber-500"></i> 收藏句子 <span class="novel-badge" id="savedSentencesCountBadge" style="background: #fef3c7; color: #b45309; padding: 2px 6px; border-radius: 9999px; font-size: 0.75rem; margin-left: 4px;">0</span>
                    </button>
"""
if 'id="novelVoiceSelect"' not in html:
    html = html.replace('<!-- 語音朗讀此頁 -->', novel_audio_toolbar_html + '\n                    <!-- 語音朗讀此頁 -->')

# 4. 確保 Word Popover 內含發音與存入生詞本按鈕
popover_footer_html = """
        <div class="popover-footer" style="padding: 8px 12px; border-top: 1px solid var(--border-color); display: flex; justify-content: flex-end;">
            <button class="novel-tool-btn" id="btnAddWordToNotebook" style="font-size: 0.85rem; padding: 4px 10px; background: #fffbeb; border-color: #fde68a; color: #b45309;">
                <i class="fa-regular fa-star"></i> 存入生詞本
            </button>
        </div>
"""
if 'id="btnAddWordToNotebook"' not in html:
    html = html.replace('</div>\n    </div>\n\n    <!-- Grammar Detail Drawer Modal', popover_footer_html + '\n    </div>\n\n    <!-- Grammar Detail Drawer Modal')

# 5. 加入拍照 OCR Modal 與 句子收藏庫 Modal
extra_modals_html = """
    <!-- 拍照 / 圖片日語 OCR 辨識視窗 -->
    <div class="modal-overlay" id="ocrModal" style="display: none; align-items: center; justify-content: center; z-index: 10000; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(15,23,42,0.6); backdrop-filter: blur(4px);">
        <div class="modal-container" style="max-width: 620px; background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.2); width: 90%;">
            <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                <h3 style="margin: 0; font-size: 1.15rem; color: #1e293b;"><i class="fa-solid fa-camera text-indigo-600"></i> 拍照 / 圖片日語 OCR 辨識</h3>
                <button class="modal-close-btn" onclick="closeOcrModal()" style="background: none; border: none; font-size: 1.25rem; color: #64748b; cursor: pointer;"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div style="padding: 20px;">
                <div style="background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 14px;">
                    <i class="fa-solid fa-cloud-arrow-up" style="font-size: 2.2rem; color: #64748b; margin-bottom: 10px;"></i>
                    <div style="font-weight: 700; color: #334155; margin-bottom: 4px;">拍照上傳或貼上書籍截圖 (支援 Ctrl + V)</div>
                    <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 14px;">支援實體紙本書頁、漫畫小說、講義截圖日文文字提取</div>
                    
                    <div style="display: flex; justify-content: center; gap: 10px; flex-wrap: wrap;">
                        <label class="btn-primary" style="cursor: pointer; padding: 8px 18px; border-radius: 8px; font-weight: 700; background: #4f46e5; color: #fff;">
                            <i class="fa-solid fa-camera"></i> 啟動相機拍照
                            <input type="file" id="cameraInput" accept="image/*" capture="environment" style="display: none;" onchange="handleImageFileSelect(event)">
                        </label>
                        <label class="pill-btn" style="cursor: pointer; padding: 8px 18px; border-radius: 8px; font-weight: 700;">
                            <i class="fa-solid fa-image"></i> 選取相簿圖片
                            <input type="file" id="imageInput" accept="image/*" style="display: none;" onchange="handleImageFileSelect(event)">
                        </label>
                    </div>
                </div>

                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; padding: 8px 12px; background: #f1f5f9; border-radius: 8px;">
                    <span style="font-size: 0.88rem; font-weight: 700; color: #475569;">辨識方向模式：</span>
                    <div style="display: flex; gap: 8px;">
                        <label style="font-size: 0.85rem; cursor: pointer;">
                            <input type="radio" name="ocrDirection" value="jpn_vert" checked> 日文直排 (小說縱書)
                        </label>
                        <label style="font-size: 0.85rem; cursor: pointer; margin-left: 10px;">
                            <input type="radio" name="ocrDirection" value="jpn"> 日文橫排 (一般排版)
                        </label>
                    </div>
                </div>

                <div id="ocrPreviewArea" style="display: none; margin-bottom: 12px; text-align: center;">
                    <img id="ocrImagePreview" src="" style="max-height: 200px; border-radius: 8px; border: 1px solid #cbd5e1;">
                    <div id="ocrStatusText" style="margin-top: 8px; font-weight: 700; color: #2563eb; font-size: 0.9rem;"></div>
                </div>

                <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 14px;">
                    <button class="pill-btn" onclick="closeOcrModal()">取消</button>
                    <button class="btn-primary" id="btnStartOcrRecognize" onclick="runOcrRecognition()" style="display: none; padding: 8px 20px; font-weight: 700; background: #059669; color: #fff; border-radius: 8px;">
                        <i class="fa-solid fa-wand-magic-sparkles"></i> 開始 OCR 辨識並載入
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- 句子收藏庫 Modal -->
    <div class="modal-overlay" id="savedSentencesModal" style="display: none; align-items: center; justify-content: center; z-index: 10000; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(15,23,42,0.6); backdrop-filter: blur(4px);">
        <div class="modal-container" style="max-width: 680px; background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.2); width: 90%; max-height: 85vh; display: flex; flex-direction: column;">
            <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: #fffbeb; border-bottom: 1px solid #fde68a;">
                <h3 style="margin: 0; font-size: 1.15rem; color: #92400e;"><i class="fa-solid fa-star text-amber-500"></i> 我的收藏句子庫 (<span id="savedModalTotalCount">0</span>)</h3>
                <div style="display: flex; gap: 8px;">
                    <button class="novel-tool-btn" onclick="exportSavedSentences()" style="font-size: 0.8rem; padding: 4px 10px;">
                        <i class="fa-solid fa-file-export"></i> 匯出清單
                    </button>
                    <button class="modal-close-btn" onclick="closeSavedSentencesModal()" style="background: none; border: none; font-size: 1.25rem; color: #64748b; cursor: pointer;"><i class="fa-solid fa-xmark"></i></button>
                </div>
            </div>
            <div id="savedSentencesList" style="padding: 16px 20px; overflow-y: auto; flex: 1;">
                <!-- 動態注入 -->
            </div>
        </div>
    </div>
"""
if 'id="ocrModal"' not in html:
    html = html.replace('<div class="modal-overlay" id="pasteModal"', extra_modals_html + '\n    <div class="modal-overlay" id="pasteModal"')

# 6. 修復 toastMsg
if 'id="toastMsg"' not in html:
    html = html.replace('<div id="toast" class="toast"></div>', '<div id="toast" class="toast"><i class="fa-solid fa-circle-check text-emerald-400"></i> <span id="toastMsg">提示訊息</span></div>')

print("[2/5] 修復 Script 5 (master.html core_ui_script) 中潛在的 null reference 監聽器...")
html = html.replace(
    "dom.articleInput.addEventListener('input', () => {",
    "if (dom.articleInput) dom.articleInput.addEventListener('input', () => {"
).replace(
    "dom.sampleButtonsList.innerHTML = '';",
    "if (dom.sampleButtonsList) dom.sampleButtonsList.innerHTML = '';"
)

print("[3/5] 替換 Script 9 為升級版小說控制模組 (包含 5 本名著範本、Edge真人雙聲道、941文法連動)...")

# 找到 Script 9 的標籤位置
# 在 c0fac0b_novel.html 中，Script 9 是最後一個 <script> 區塊
last_script_tag = html.rfind('<script>')
if last_script_tag == -1:
    last_script_tag = html.rfind('<script ')

with open(SCRIPT9_PATH, "r", encoding="utf-8") as f:
    script9_code = f.read().strip()

# 組合最終 HTML：保留前面的所有 HTML，並確保 <script> 與 </script> 100% 閉合
prefix = html[:last_script_tag]
final_html = f"""{prefix}
    <script>
{script9_code}
    </script>
</body>
</html>
"""

print("[4/5] 寫入目標檔案...")
with open(TARGET_NOVEL, "w", encoding="utf-8") as f:
    f.write(final_html)
print(f"[OK] 成功更新 {TARGET_NOVEL} ({len(final_html)} 字元)")

with open(TARGET_ALIAS, "w", encoding="utf-8") as f:
    f.write(final_html)
print(f"[OK] 成功更新 {TARGET_ALIAS}")
