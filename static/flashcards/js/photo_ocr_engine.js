/**
 * PhotoOcrEngine - 講義/教材照片批次辨識與智慧自動分類模組
 * 支援：
 * 1. 批次多張照片上傳、手機相機直接拍照、剪貼簿 Ctrl+V 貼上螢幕截圖
 * 2. Gemini 1.5/2.0 Flash Vision AI (高精度語境解析、讀音校正、例句繁中生成)
 * 3. 智慧自動分門別類 (JLPT N1~N5、現場營造、商務、生活)
 * 4. 預覽確認清單與一鍵批量導入 Anki 牌組
 */

class PhotoOcrEngine {
  constructor(app) {
    this.app = app;
    this.selectedFiles = [];
    this.detectedWords = [];
    this.init();
  }

  init() {
    // 監聽拖曳與選取
    const dropZone = document.getElementById('ocr-drop-zone');
    const fileInput = document.getElementById('ocr-file-input');

    if (dropZone && fileInput) {
      fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));

      dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
      });

      dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
      });

      dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          this.handleFiles(e.dataTransfer.files);
        }
      });

      // 支援剪貼簿貼上 (Ctrl+V)
      window.addEventListener('paste', (e) => {
        const modal = document.getElementById('modal-photo-ocr');
        if (!modal || !modal.classList.contains('open')) return;
        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
        const imgFiles = [];
        for (let item of items) {
          if (item.kind === 'file' && item.type.startsWith('image/')) {
            imgFiles.push(item.getAsFile());
          }
        }
        if (imgFiles.length > 0) {
          this.handleFiles(imgFiles);
        }
      });
    }

    // 全選/反選
    const checkAll = document.getElementById('ocr-check-all');
    if (checkAll) {
      checkAll.addEventListener('change', (e) => {
        const cbs = document.querySelectorAll('#ocr-table-tbody input[type="checkbox"]');
        cbs.forEach(cb => cb.checked = e.target.checked);
      });
    }
  }

  // 處理選取的檔案
  handleFiles(files) {
    if (!files || files.length === 0) return;
    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      if (f.type.startsWith('image/')) {
        this.selectedFiles.push(f);
      }
    }
    this.renderGallery();
  }

  // 渲染圖片預覽縮圖
  renderGallery() {
    const gallery = document.getElementById('ocr-preview-gallery');
    if (!gallery) return;

    if (this.selectedFiles.length === 0) {
      gallery.style.display = 'none';
      gallery.innerHTML = '';
      return;
    }

    gallery.style.display = 'flex';
    gallery.style.cssText = 'display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; max-height: 120px; overflow-y: auto; padding: 6px; background: var(--bg-tertiary); border-radius: 8px;';
    gallery.innerHTML = '';

    this.selectedFiles.forEach((file, idx) => {
      const thumb = document.createElement('div');
      thumb.style.cssText = 'position: relative; width: 70px; height: 70px; border-radius: 6px; overflow: hidden; border: 1px solid var(--border-color); background: #000; flex-shrink: 0;';
      
      const img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      img.style.cssText = 'width: 100%; height: 100%; object-fit: cover;';
      
      const btnDel = document.createElement('button');
      btnDel.innerHTML = '&times;';
      btnDel.style.cssText = 'position: absolute; top: 2px; right: 2px; background: rgba(239, 68, 68, 0.85); color: #fff; border: none; border-radius: 50%; width: 18px; height: 18px; font-size: 12px; line-height: 1; cursor: pointer; display: flex; align-items: center; justify-content: center;';
      btnDel.title = '移除此圖片';
      btnDel.onclick = (e) => {
        e.stopPropagation();
        this.selectedFiles.splice(idx, 1);
        this.renderGallery();
      };

      thumb.appendChild(img);
      thumb.appendChild(btnDel);
      gallery.appendChild(thumb);
    });
  }

  // 打開拍照辨識彈窗時初始化目標牌組下拉清單
  openModal() {
    this.selectedFiles = [];
    this.detectedWords = [];
    this.renderGallery();

    const resultsArea = document.getElementById('ocr-results-area');
    if (resultsArea) resultsArea.style.display = 'none';

    const commitBtn = document.getElementById('btn-ocr-commit-import');
    if (commitBtn) commitBtn.style.display = 'none';

    const startBtn = document.getElementById('btn-ocr-start-scan');
    if (startBtn) startBtn.style.display = 'inline-block';

    const loading = document.getElementById('ocr-loading-indicator');
    if (loading) loading.style.display = 'none';

    // 填入使用者現有牌組清單
    const targetSelect = document.getElementById('ocr-target-deck-select');
    if (targetSelect && this.app.decks) {
      targetSelect.innerHTML = '<option value="auto">🤖 智慧自動分門別類 (AI 自動分類至 JLPT / 工程 / 商務 / 生活)</option>';
      this.app.decks.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.id;
        opt.textContent = `${d.icon || '📚'} ${d.name}`;
        targetSelect.appendChild(opt);
      });
    }

    document.getElementById('modal-photo-ocr').classList.add('open');
  }

  // 開始照片掃描與辨識
  async startScan() {
    if (this.selectedFiles.length === 0) {
      alert('⚠️ 請先選取或拍攝至少一張照片！');
      return;
    }

    const engine = document.getElementById('ocr-engine-select').value;
    const loading = document.getElementById('ocr-loading-indicator');
    const loadingText = document.getElementById('ocr-loading-text');
    const resultsArea = document.getElementById('ocr-results-area');
    const startBtn = document.getElementById('btn-ocr-start-scan');
    const commitBtn = document.getElementById('btn-ocr-commit-import');

    loading.style.display = 'block';
    resultsArea.style.display = 'none';
    startBtn.style.display = 'none';

    this.detectedWords = [];

    try {
      if (engine === 'gemini') {
        loadingText.textContent = `🤖 正在使用 Gemini Vision 視覺模型辨識 ${this.selectedFiles.length} 張照片...`;
        await this.scanViaGemini();
      } else {
        loadingText.textContent = `⚡ 正在使用瀏覽器前端 OCR 引擎分析中...`;
        await this.scanViaLocalOcr();
      }

      loading.style.display = 'none';

      if (this.detectedWords.length === 0) {
        alert('未在照片中檢測到明確的日文詞彙，請確認照片文字清晰度或嘗試切換辨識引擎。');
        startBtn.style.display = 'inline-block';
        return;
      }

      this.renderResultsTable();
      resultsArea.style.display = 'block';
      commitBtn.style.display = 'inline-block';
    } catch (e) {
      loading.style.display = 'none';
      startBtn.style.display = 'inline-block';
      alert('辨識過程發生錯誤: ' + e.message);
      console.error(e);
    }
  }

  // 將 File 物件轉為 Base64
  fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const b64 = reader.result.split(',')[1];
        resolve({ mimeType: file.type || 'image/jpeg', data: b64 });
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  // 透過 Gemini Vision 深度辨識
  async scanViaGemini() {
    let apiKey = (this.app.settings && this.app.settings.geminiApiKey) ? this.app.settings.geminiApiKey.trim() : '';

    if (!apiKey) {
      apiKey = prompt('💡 提示：Gemini Vision 視覺辨識需要 Google Gemini API Key。\n請輸入您的 Gemini API Key（亦可於「⚙️ 系統設定」中永久儲存）：');
      if (apiKey && apiKey.trim()) {
        apiKey = apiKey.trim();
        this.app.settings.geminiApiKey = apiKey;
        this.app.sync.saveSettings(this.app.settings);
      } else {
        throw new Error('未提供 Gemini API Key。若想免金鑰辨識，請在下拉選單選擇「本地瀏覽器純前端 OCR」！');
      }
    }

    const promptText = `你是一個專業的日語教學與單字抽認卡製作專家。
請分析這批日文照片（包含日語單字書、課本教材、考卷或講義）。
請仔細提取照片中出現的所有核心日語單字與詞彙。
針對辨識出來的每一個詞彙，請輸出符合以下規格的 JSON 陣列：
[
  {
    "word": "單字原型或出現形式（漢字/假名）",
    "reading": "平假名標準讀音（送假名正確分開）",
    "meaning": "精確的繁體中文釋義與詞性標籤（如：名詞、動詞、形容詞）",
    "example": "原文例句或實用語境例句（附繁體中文翻譯）",
    "category": "自動歸納分類，必須為以下之一：JLPT N1、JLPT N2、JLPT N3、JLPT N4、JLPT N5、現場營造工程、商務職場日語、日常生活、慣用表現"
  }
]
注意事項：
1. 繁體中文（台灣習慣用語）。
2. 自動去除頁碼、標題等無關干擾文字。
3. 請只回傳純 JSON 陣列字串，絕對不要包含額外的 Markdown 標記（如 \`\`\`json）或前導後綴說明文字。`;

    for (let f of this.selectedFiles) {
      const imgData = await this.fileToBase64(f);
      
      const payload = {
        contents: [
          {
            parts: [
              { text: promptText },
              { inline_data: { mime_type: imgData.mimeType, data: imgData.data } }
            ]
          }
        ],
        generationConfig: {
          temperature: 0.2,
          maxOutputTokens: 2048
        }
      };

      const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!resp.ok) {
        const errJson = await resp.json().catch(() => ({}));
        throw new Error(errJson.error?.message || `HTTP ${resp.status}`);
      }

      const resJson = await resp.json();
      const rawText = resJson.candidates?.[0]?.content?.parts?.[0]?.text || '';
      
      // 清理可能的 markdown 區塊
      const cleanJson = rawText.replace(/```json/gi, '').replace(/```/g, '').trim();
      try {
        const parsed = JSON.parse(cleanJson);
        if (Array.isArray(parsed)) {
          parsed.forEach(item => {
            if (item.word && !this.detectedWords.some(w => w.word === item.word)) {
              this.detectedWords.push(item);
            }
          });
        }
      } catch (parseErr) {
        console.warn('JSON 解析警告，嘗試正則提取:', rawText);
        // 容錯提取
        const matches = rawText.match(/\{[^}]*"word"[^}]*\}/g);
        if (matches) {
          matches.forEach(m => {
            try {
              const obj = JSON.parse(m);
              if (obj.word && !this.detectedWords.some(w => w.word === obj.word)) {
                this.detectedWords.push(obj);
              }
            } catch(e){}
          });
        }
      }
    }
  }

  // 本地純前端 OCR (免連網 / Tesseract.js)
  async scanViaLocalOcr() {
    if (typeof Tesseract === 'undefined') {
      // 動態載入 Tesseract.js
      await new Promise((resolve, reject) => {
        const s = document.createElement('script');
        s.src = 'https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js';
        s.onload = resolve;
        s.onerror = () => reject(new Error('無法載入本地 OCR 元件，請檢查網路連線或使用 Gemini Vision 引擎'));
        document.head.appendChild(s);
      });
    }

    const worker = await Tesseract.createWorker('jpn');
    
    for (let f of this.selectedFiles) {
      const ret = await worker.recognize(f);
      const text = ret.data.text || '';
      
      // 提取日文行
      const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
      for (let line of lines) {
        // 分離可能單字與讀音
        const words = line.match(/[\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff]{2,8}/g);
        if (words) {
          for (let w of words) {
            if (!this.detectedWords.some(item => item.word === w)) {
              // 透過內建字典或 enricher 補齊
              let info = { word: w, reading: '', meaning: '教材掃描單字', example: line, category: '日常生活' };
              if (this.app.enricher && this.app.enricher.builtInDict && this.app.enricher.builtInDict[w]) {
                const b = this.app.enricher.builtInDict[w];
                info.reading = b.reading;
                info.meaning = b.meaning;
                info.example = b.example;
                info.category = (b.tags && b.tags.includes('工程')) ? '現場營造工程' : '日常生活';
              }
              this.detectedWords.push(info);
            }
          }
        }
      }
    }

    await worker.terminate();
  }

  // 渲染成果預覽表格
  renderResultsTable() {
    const tbody = document.getElementById('ocr-table-tbody');
    const countEl = document.getElementById('ocr-detected-count');
    if (!tbody) return;

    countEl.textContent = this.detectedWords.length;
    tbody.innerHTML = '';

    this.detectedWords.forEach((item, idx) => {
      const tr = document.createElement('tr');
      tr.style.cssText = 'border-bottom: 1px solid var(--border-color);';
      tr.innerHTML = `
        <td style="padding: 8px; text-align: center;">
          <input type="checkbox" class="ocr-row-cb" data-idx="${idx}" checked>
        </td>
        <td style="padding: 8px; font-weight: 700; font-family: 'Noto Sans JP', sans-serif;">
          <input type="text" class="form-input ocr-edit-word" value="${this.escape(item.word)}" style="padding: 4px 6px; font-size: 0.9rem; font-weight: 700;">
        </td>
        <td style="padding: 8px; color: #e11d48; font-weight: 600;">
          <input type="text" class="form-input ocr-edit-reading" value="${this.escape(item.reading || '')}" style="padding: 4px 6px; font-size: 0.85rem; color: #e11d48;">
        </td>
        <td style="padding: 8px;">
          <input type="text" class="form-input ocr-edit-meaning" value="${this.escape(item.meaning || '')}" style="padding: 4px 6px; font-size: 0.85rem;">
        </td>
        <td style="padding: 8px;">
          <input type="text" class="form-input ocr-edit-example" value="${this.escape(item.example || '')}" style="padding: 4px 6px; font-size: 0.82rem;">
        </td>
        <td style="padding: 8px;">
          <select class="form-select ocr-edit-category" style="padding: 4px 6px; font-size: 0.82rem;">
            <option value="JLPT N1" ${item.category === 'JLPT N1' ? 'selected' : ''}>JLPT N1</option>
            <option value="JLPT N2" ${item.category === 'JLPT N2' ? 'selected' : ''}>JLPT N2</option>
            <option value="JLPT N3" ${item.category === 'JLPT N3' ? 'selected' : ''}>JLPT N3</option>
            <option value="JLPT N4" ${item.category === 'JLPT N4' ? 'selected' : ''}>JLPT N4</option>
            <option value="JLPT N5" ${item.category === 'JLPT N5' ? 'selected' : ''}>JLPT N5</option>
            <option value="現場營造工程" ${item.category === '現場營造工程' || item.category === '工程營造' ? 'selected' : ''}>🏗️ 現場營造工程</option>
            <option value="商務職場日語" ${item.category === '商務職場日語' ? 'selected' : ''}>💼 商務職場日語</option>
            <option value="日常生活" ${(!item.category || item.category === '日常生活') ? 'selected' : ''}>🍵 日常生活</option>
          </select>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  escape(str) {
    if (!str) return '';
    return String(str).replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // 確認匯入選取的單字至牌組
  commitImport() {
    const rows = document.querySelectorAll('#ocr-table-tbody tr');
    const targetDeckChoice = document.getElementById('ocr-target-deck-select').value;
    
    let toImport = [];
    rows.forEach(tr => {
      const cb = tr.querySelector('.ocr-row-cb');
      if (cb && cb.checked) {
        const word = tr.querySelector('.ocr-edit-word').value.trim();
        const reading = tr.querySelector('.ocr-edit-reading').value.trim();
        const meaning = tr.querySelector('.ocr-edit-meaning').value.trim();
        const example = tr.querySelector('.ocr-edit-example').value.trim();
        const category = tr.querySelector('.ocr-edit-category').value;
        if (word) {
          toImport.push({ word, reading, meaning, example, category });
        }
      }
    });

    if (toImport.length === 0) {
      alert('請至少勾選一個欲匯入的單字！');
      return;
    }

    // 分流與匯入
    const defaultDeckMap = {
      'JLPT N1': { id: 'deck_jlpt_n1', name: '🎯 JLPT N1 高級單字', icon: '🥇', color: '#86198f' },
      'JLPT N2': { id: 'deck_jlpt_n2', name: '🎯 JLPT N2 中高級單字', icon: '🥈', color: '#1e40af' },
      'JLPT N3': { id: 'deck_jlpt_n3', name: '🎯 JLPT N3 中級單字', icon: '🥉', color: '#166534' },
      'JLPT N4': { id: 'deck_jlpt_n4_n5', name: '🎯 JLPT N4~N5 初級單字', icon: '🌱', color: '#9a3412' },
      'JLPT N5': { id: 'deck_jlpt_n4_n5', name: '🎯 JLPT N4~N5 初級單字', icon: '🌱', color: '#9a3412' },
      '現場營造工程': { id: 'deck_construction', name: '🏗️ 現場營造與工程日語', icon: '👷', color: '#d97706' },
      '工程營造': { id: 'deck_construction', name: '🏗️ 現場營造與工程日語', icon: '👷', color: '#d97706' },
      '商務職場日語': { id: 'deck_business', name: '💼 商務與職場實務日語', icon: '💼', color: '#0891b2' },
      '日常生活': { id: 'deck_daily', name: '🍵 日常生活與教材精選', icon: '🍵', color: '#059669' }
    };

    let count = 0;
    toImport.forEach(item => {
      let targetDeckId = targetDeckChoice;
      let targetDeckConfig = null;

      if (targetDeckChoice === 'auto') {
        targetDeckConfig = defaultDeckMap[item.category] || defaultDeckMap['日常生活'];
        targetDeckId = targetDeckConfig.id;
      }

      // 檢查牌組是否存在
      let deck = this.app.decks.find(d => d.id === targetDeckId);
      if (!deck && targetDeckConfig) {
        deck = {
          id: targetDeckConfig.id,
          name: targetDeckConfig.name,
          desc: '照片辨識自動歸類牌組',
          icon: targetDeckConfig.icon,
          color: targetDeckConfig.color
        };
        this.app.decks.push(deck);
      } else if (!deck) {
        targetDeckId = this.app.decks[0] ? this.app.decks[0].id : 'default';
      }

      // 檢查卡片是否已存在
      const exists = this.app.cards.some(c => c.deckId === targetDeckId && c.front === item.word);
      if (!exists) {
        this.app.cards.push(this.app.anki.createCard({
          deckId: targetDeckId,
          front: item.word,
          reading: item.reading,
          back: item.meaning,
          example: item.example,
          tags: ['照片導入', item.category]
        }));
        count++;
      }
    });

    this.app.saveData();
    this.app.renderDeckList();
    this.app.updateHeaderStats();

    alert(`🎉 恭喜！已成功將 ${count} 個單字分門別類匯入到對應的 Anki 牌組！`);
    document.getElementById('modal-photo-ocr').classList.remove('open');
  }
}

window.PhotoOcrEngine = PhotoOcrEngine;
