/* Excel Import - Seamless auto-detection, tolerant parsing, and flexible group/deck targeting */
document.addEventListener('DOMContentLoaded', () => {
  const $ = id => document.getElementById(id);
  const modal = $('modal-excel-import');
  if (!modal) return;

  let workbook = null;
  let rows = [];
  let cards = [];
  let generation = 0;

  const fields = ['ja', 'zh', 'reading'];
  const aliases = {
    ja: [
      '日文', '日語', '日本語', '單字', '單詞', '詞彙', '語彙', '項目', '見出語', '原語',
      '日文術語', '日文原文', '日語單詞', '日文單字', '日文表現', 'japanese', 'ja', 'front',
      'word', 'vocab', 'vocabulary', 'term', 'jp', 'nihongo', '原文', '生詞', '單字名稱'
    ],
    zh: [
      '中文', '繁體中文', '繁中', '繁體', '中文意思', '中文釋義', '中文術語', '中文翻譯',
      '釋義', '意思', '翻譯', '譯文', '解釋', '說明', '備註', 'chinese', 'zh', 'back',
      'meaning', 'definition', 'translation', 'trans', '定義', '簡體中文', '簡中', '說明/釋義'
    ],
    reading: [
      '讀音', '読み', 'よみ', '読み方', '假名', '平假名', '片假名', '振假名', 'ふりがな',
      'reading', 'kana', 'hiragana', 'katakana', 'pronunciation', 'furigana', '音標',
      '發音', '拼音', '讀法', '唸法', 'yomi'
    ]
  };

  const value = cell => String(cell ?? '').trim();
  function status(message) {
    const el = $('excel-status');
    if (el) el.textContent = message;
  }

  function reset() {
    generation++;
    workbook = null;
    rows = [];
    cards = [];
    $('excel-options').hidden = true;
    $('excel-preview').replaceChildren();
    $('excel-submit').disabled = true;
    const progressWrap = $('excel-enrich-progress-wrap');
    if (progressWrap) progressWrap.style.display = 'none';
  }

  function populateTargetDecks(selectedDeckId = null) {
    const app = window.app;
    const select = $('excel-target-deck');
    if (!select) return;
    select.replaceChildren();

    const decks = app?.decks || [];
    if (!decks.length) {
      $('excel-mode-new').checked = true;
      $('excel-mode-existing').disabled = true;
      updateTargetModeVisibility();
      return;
    }

    $('excel-mode-existing').disabled = false;
    decks.forEach(d => {
      const cardCount = (app.cards || []).filter(c => c.deckId === d.id).length;
      const opt = new Option(`${d.name}（現有 ${cardCount} 詞）`, d.id);
      select.add(opt);
    });

    const targetId = selectedDeckId || (app?.activeFamilyId && decks.some(d => d.id === app.activeFamilyId) ? app.activeFamilyId : decks[0]?.id);
    if (targetId && decks.some(d => d.id === targetId)) {
      select.value = targetId;
      $('excel-mode-existing').checked = true;
    }
    updateTargetModeVisibility();
  }

  function updateTargetModeVisibility() {
    const isExisting = $('excel-mode-existing').checked;
    $('excel-target-existing-wrap').style.display = isExisting ? 'block' : 'none';
    $('excel-target-new-wrap').style.display = isExisting ? 'none' : 'block';
    updateSubmitButton();
  }

  function openExcelImportModal(targetDeckId = null) {
    reset();
    $('excel-file').value = '';
    $('excel-name').value = '';
    $('excel-header').checked = true;
    $('excel-group-size').value = '20';
    $('excel-auto-enrich').checked = true;
    populateTargetDecks(targetDeckId);
    status('請選擇 Excel 檔案，選入後將自動讀入並解析單字。');
    modal.classList.add('open');
    $('excel-file').focus();
  }

  window.openExcelImportModal = openExcelImportModal;
  if (window.app) {
    window.app.openExcelImport = openExcelImportModal;
  }

  // Radio toggle & input changes
  $('excel-mode-existing').addEventListener('change', updateTargetModeVisibility);
  $('excel-mode-new').addEventListener('change', updateTargetModeVisibility);
  $('excel-target-deck').addEventListener('change', updateSubmitButton);
  $('excel-name').addEventListener('input', updateSubmitButton);

  $('btn-excel-import').addEventListener('click', () => {
    openExcelImportModal();
  });

  modal.addEventListener('click', event => {
    if (event.target === modal || event.target.closest('.modal-close')) {
      reset();
      modal.classList.remove('open');
    }
  });

  // Handle File Input Change - "只要選入就立刻自動讀入"
  $('excel-file').addEventListener('change', async () => {
    reset();
    const ticket = generation;
    const file = $('excel-file').files[0];
    if (!file) return status('請選擇 Excel 檔案。');
    if (!/\.(xlsx|xls)$/i.test(file.name)) return status('請選擇 .xlsx 或 .xls 格式的 Excel 檔案。');
    if (file.size > 20 * 1024 * 1024) return status('檔案超過 20 MB，請拆成較小的檔案。');

    const defaultName = file.name.replace(/\.[^.]+$/, '').slice(0, 100);
    $('excel-name').value = defaultName;
    status('⚡ 正在讀取並自動解析 Excel…');

    try {
      if (!window.XLSX) throw new Error('Excel 讀取元件尚未載入，請重新整理網頁後再試。');
      const buffer = await file.arrayBuffer();
      if (ticket !== generation) return;

      const bytes = new Uint8Array(buffer);
      const zip = bytes[0] === 0x50 && bytes[1] === 0x4b;
      const ole = bytes[0] === 0xd0 && bytes[1] === 0xcf;
      if (!zip && !ole) throw new Error('檔案不是標準 Excel 活頁簿，請用 Excel 另存為 .xlsx 後再試。');

      workbook = XLSX.read(buffer, { type: 'array', sheetRows: 10002 });
      if (!workbook.SheetNames || !workbook.SheetNames.length) throw new Error('檔案中沒有工作表。');

      // Populate sheet selector
      $('excel-sheet').replaceChildren(...workbook.SheetNames.map(name => new Option(name, name)));

      // Find first sheet that actually has content
      let bestSheet = workbook.SheetNames[0];
      for (const name of workbook.SheetNames) {
        const s = workbook.Sheets[name];
        if (s && (s['!ref'] || s['!fullref'])) {
          bestSheet = name;
          break;
        }
      }
      $('excel-sheet').value = bestSheet;
      $('excel-options').hidden = false;

      selectSheet();
    } catch (error) {
      reset();
      status(error.message.startsWith('Excel') || error.message.startsWith('檔案') ? error.message : '無法讀取檔案，請確認檔案未損壞、未加密，並另存為 .xlsx 再試。');
    }
  });

  function selectSheet() {
    cards = [];
    $('excel-submit').disabled = true;
    $('excel-preview').replaceChildren();

    const sheetName = $('excel-sheet').value;
    const sheet = workbook.Sheets[sheetName];
    if (!sheet) {
      return status('找不到所選的工作表。');
    }

    const range = XLSX.utils.decode_range(sheet['!fullref'] || sheet['!ref'] || 'A1');
    if (range.e.r > 10000 || range.e.c > 99) {
      rows = [];
      return status('工作表範圍過大：每張表最多 10,000 列資料、100 欄。請移除多餘空白列欄或拆檔。');
    }

    // Parse sheet to 2D array
    rows = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '', raw: false, blankrows: false });

    // Filter out rows that are entirely empty
    rows = rows.filter(r => Array.isArray(r) && r.some(c => value(c) !== ''));
    if (!rows.length) {
      return status('此工作表為空，沒有任何文字資料。');
    }

    // Auto-detect whether row 0 looks like a header
    const r0 = rows[0] || [];
    const r0Text = r0.map(c => value(c).toLowerCase().replace(/[\s\-_()（）]/g, ''));
    const matchesAnyAlias = r0Text.some(txt =>
      txt && (aliases.ja.includes(txt) || aliases.zh.includes(txt) || aliases.reading.includes(txt) ||
              ['id', 'no', '編號', '序號', '題號', '項目'].includes(txt))
    );
    // If row 0 matches headers or contains "日文"/"中文" keyword, check header
    if (matchesAnyAlias) {
      $('excel-header').checked = true;
    }

    configureColumns();
  }

  function detectColumns(width) {
    const isHeader = $('excel-header').checked;
    const headerRow = rows[0] || [];
    let ja = -1, zh = -1, reading = -1;

    // 1. Header Alias Matching
    if (isHeader) {
      headerRow.forEach((cell, col) => {
        const txt = value(cell).toLowerCase().replace(/[\s\-_()（）[\]]/g, '');
        if (!txt) return;
        if (ja < 0 && aliases.ja.some(a => txt === a || txt.includes(a))) ja = col;
        if (zh < 0 && aliases.zh.some(a => txt === a || txt.includes(a))) zh = col;
        if (reading < 0 && aliases.reading.some(a => txt === a || txt.includes(a))) reading = col;
      });
    }

    // 2. Content Heuristics for remaining unassigned columns
    const startRow = isHeader ? 1 : 0;
    const sampleRows = rows.slice(startRow, startRow + 35).filter(r => r && r.some(c => value(c)));

    if (sampleRows.length > 0) {
      const stats = [];
      for (let c = 0; c < width; c++) {
        let nonBlank = 0, hasKana = 0, pureKana = 0, hasKanji = 0;
        sampleRows.forEach(r => {
          const val = value(r[c]);
          if (!val) return;
          nonBlank++;
          if (/[\u3040-\u309F\u30A0-\u30FF]/.test(val)) hasKana++;
          if (/^[\u3040-\u309F\u30A0-\u30FF\s、。・…—~～\(\)（）]+$/.test(val)) pureKana++;
          if (/[\u4E00-\u9FAF]/.test(val)) hasKanji++;
        });
        stats.push({
          col: c,
          nonBlank,
          pureKanaRate: nonBlank ? pureKana / nonBlank : 0,
          hasKanaRate: nonBlank ? hasKana / nonBlank : 0,
          hasKanjiRate: nonBlank ? hasKanji / nonBlank : 0
        });
      }

      // Detect reading column: predominantly pure kana (> 35%)
      if (reading < 0) {
        const bestReading = stats.find(s => s.pureKanaRate >= 0.35 && s.col !== ja && s.col !== zh);
        if (bestReading) reading = bestReading.col;
      }

      // Detect Japanese column: highest kana presence
      if (ja < 0) {
        const candidates = stats
          .filter(s => s.col !== reading && s.col !== zh)
          .sort((a, b) => b.hasKanaRate - a.hasKanaRate || b.hasKanjiRate - a.hasKanjiRate);
        if (candidates.length && (candidates[0].hasKanaRate > 0.1 || candidates[0].hasKanjiRate > 0.2)) {
          ja = candidates[0].col;
        }
      }

      // Detect Chinese column: contains kanji/chinese, excluding ja & reading
      if (zh < 0) {
        const candidates = stats
          .filter(s => s.col !== ja && s.col !== reading)
          .sort((a, b) => b.hasKanjiRate - a.hasKanjiRate || b.nonBlank - a.nonBlank);
        if (candidates.length) zh = candidates[0].col;
      }
    }

    // 3. Fallback Guarantees: Never leave Japanese or Chinese unassigned if columns exist
    const available = Array.from({ length: width }, (_, i) => i);
    if (ja < 0) {
      ja = available.find(c => c !== zh && c !== reading) ?? 0;
    }
    if (zh < 0) {
      zh = available.find(c => c !== ja && c !== reading) ?? (width > 1 ? (ja === 0 ? 1 : 0) : -1);
    }

    return { ja, zh, reading };
  }

  function configureColumns() {
    const width = Math.max(0, ...rows.map(row => row ? row.length : 0));
    if (width === 0) return;

    const detected = detectColumns(width);

    fields.forEach(field => {
      const select = $('excel-' + field);
      select.replaceChildren(new Option(field === 'reading' ? '不匯入讀音（選填）' : '請選擇欄位', '-1'));
      for (let col = 0; col < width; col++) {
        const label = $('excel-header').checked ? value(rows[0]?.[col]) : '';
        select.add(new Option(`${XLSX.utils.encode_col(col)} 欄${label ? '：' + label.slice(0, 30) : ''}`, String(col)));
      }
      select.value = String(detected[field]);
    });

    preview();
  }

  function preview() {
    cards = [];
    $('excel-preview').replaceChildren();
    $('excel-submit').disabled = true;

    const ja = Number($('excel-ja').value);
    const zh = Number($('excel-zh').value);
    const reading = Number($('excel-reading').value);

    if (ja < 0) {
      status('⚠️ 請選擇日文單字欄（正面）。');
      updateSubmitButton();
      return;
    }

    let blankCount = 0;
    let skippedCount = 0;
    const startRow = $('excel-header').checked ? 1 : 0;

    for (let index = startRow; index < rows.length; index++) {
      const row = rows[index];
      if (!row || !row.some(cell => value(cell))) {
        blankCount++;
        continue;
      }

      let front = value(row[ja]);
      let back = zh >= 0 ? value(row[zh]) : '';
      let read = reading >= 0 ? value(row[reading]) : '';

      // If front is empty but back has Japanese, treat back as front
      if (!front && back && /[\u3040-\u309F\u30A0-\u30FF]/.test(back)) {
        front = back;
        back = '';
      }

      // If still no front, skip this non-word/title row
      if (!front) {
        skippedCount++;
        continue;
      }

      // If back is empty, don't fail! Fill with reading or placeholder for auto-enrich
      if (!back) {
        back = read || '（待補全釋義）';
      }

      cards.push({ front, back, reading: read });
    }

    // Render preview rows (up to 12)
    cards.slice(0, 12).forEach(card => {
      const tr = document.createElement('tr');
      tr.style.borderBottom = '1px solid var(--border-color, #e2e8f0)';
      [card.front, card.reading || '—', card.back].forEach(text => {
        const td = document.createElement('td');
        td.textContent = text;
        td.style.padding = '6px 10px';
        td.style.overflowWrap = 'anywhere';
        tr.append(td);
      });
      $('excel-preview').append(tr);
    });

    if (!cards.length) {
      status('⚠️ 此工作表未讀取到有效單字，請檢查所選工作表與欄位。');
      updateSubmitButton();
      return;
    }

    let infoMsg = `✅ 成功讀入 ${cards.length} 筆單字卡`;
    const notes = [];
    if (blankCount) notes.push(`略過 ${blankCount} 列空白`);
    if (skippedCount) notes.push(`略過 ${skippedCount} 列非單字行`);
    if (notes.length) infoMsg += `（${notes.join('、')}）`;
    infoMsg += '。點擊下方按鈕即可立即匯入！';
    status(infoMsg);

    updateSubmitButton();
  }

  function updateSubmitButton() {
    const submitBtn = $('excel-submit');
    if (!submitBtn) return;

    if (!cards.length) {
      submitBtn.disabled = true;
      submitBtn.textContent = '🚀 確認匯入單字';
      return;
    }

    const mode = $('excel-mode-existing').checked ? 'existing' : 'new';
    if (mode === 'existing') {
      const select = $('excel-target-deck');
      const selectedOpt = select.options[select.selectedIndex];
      const deckName = selectedOpt ? selectedOpt.text.replace(/（現有 \d+ 詞）$/, '') : '目標牌組';
      submitBtn.disabled = !select.value;
      submitBtn.textContent = `📥 匯入至「${deckName}」（共 ${cards.length} 詞）`;
    } else {
      const name = $('excel-name').value.trim() || '新牌組';
      submitBtn.disabled = !name;
      submitBtn.textContent = `✨ 建立「${name}」並匯入（共 ${cards.length} 詞）`;
    }
  }

  // Listeners for adjustments
  $('excel-sheet').addEventListener('change', selectSheet);
  $('excel-header').addEventListener('change', configureColumns);
  $('excel-group-size').addEventListener('input', updateSubmitButton);
  fields.forEach(field => $('excel-' + field).addEventListener('change', preview));

  // Execute Import on Submit
  $('excel-submit').addEventListener('click', async () => {
    if ($('excel-submit').disabled || !cards.length) return;
    const app = window.app;
    if (!app) return status('應用程式尚未就緒，請重新整理再試。');

    const submitBtn = $('excel-submit');
    const cancelBtn = modal.querySelector('.modal-close');
    const mode = $('excel-mode-existing').checked ? 'existing' : 'new';

    let targetDeckId = null;
    let targetDeckName = '';
    let targetCategory = 'daily';
    let newDecks = [...app.decks];

    if (mode === 'existing') {
      targetDeckId = $('excel-target-deck').value;
      const deck = app.decks.find(d => d.id === targetDeckId);
      if (!deck) {
        alert('請選擇有效的目標牌組！');
        return;
      }
      targetDeckName = deck.name;
      targetCategory = deck.category || 'daily';
    } else {
      targetDeckName = $('excel-name').value.trim() || 'Excel 匯入牌組';
      const groupSize = Number($('excel-group-size').value) || 20;
      const newDeck = {
        id: 'deck_excel_' + crypto.randomUUID(),
        name: targetDeckName,
        desc: '從 Excel 匯入',
        category: 'excel',
        categoryName: 'Excel 匯入',
        icon: '📊',
        color: '#10b981',
        reviewGroupSize: groupSize
      };
      targetDeckId = newDeck.id;
      newDecks.push(newDeck);
    }

    // Auto-Enrichment if requested
    const autoEnrich = $('excel-auto-enrich').checked;
    let cardsToProcess = [...cards];

    if (autoEnrich && app.enricher) {
      submitBtn.disabled = true;
      if (cancelBtn) cancelBtn.disabled = true;

      const progressWrap = $('excel-enrich-progress-wrap');
      const progressBar = $('excel-enrich-progress-bar');
      const progressText = $('excel-enrich-progress-text');

      if (progressWrap) progressWrap.style.display = 'block';

      try {
        const enrichedList = await app.enricher.batchEnrichWords(
          cardsToProcess.map(c => ({ front: c.front, back: c.back, reading: c.reading })),
          { category: targetCategory },
          (current, total, word) => {
            if (progressText) progressText.textContent = `⚡ 正在自動補全單字 (${current}/${total})：${word}…`;
            if (progressBar) progressBar.style.width = `${Math.round((current / total) * 100)}%`;
          }
        );
        cardsToProcess = enrichedList;
      } catch (e) {
        console.warn('Excel 自動補全過程異常，使用原始內容匯入:', e);
      } finally {
        if (progressWrap) progressWrap.style.display = 'none';
        submitBtn.disabled = false;
        if (cancelBtn) cancelBtn.disabled = false;
      }
    }

    // Build card models
    const createdCards = cardsToProcess.map(c =>
      app.anki.createCard({
        id: 'card_' + crypto.randomUUID(),
        front: c.front,
        back: c.back,
        reading: c.reading || '',
        example: c.example || '',
        tags: c.tags || ['Excel匯入'],
        deckId: targetDeckId
      })
    );

    const newCards = [...app.cards, ...createdCards];

    // Persist to storage
    if (!app.persistDeckChanges(newDecks, newCards, false)) {
      status('儲存失敗，未完成匯入。請確認瀏覽器儲存空間後再試。');
      submitBtn.disabled = false;
      return;
    }

    app.decks = newDecks;
    app.cards = newCards;
    app.saveData();
    app.renderCategoryTabs();
    app.renderDeckList();
    app.updateHeaderStats();

    if (app.activeFamilyId === targetDeckId) {
      app.renderGroupList();
    }

    modal.classList.remove('open');
    reset();

    const groupSizeMsg = mode === 'new'
      ? `，每組 ${$('excel-group-size').value} 個字收在複習群組中`
      : '，已自動納入該牌組的群組複習中';

    alert(`🎉 成功匯入 ${cardsToProcess.length} 張單字卡至「${targetDeckName}」${groupSizeMsg}！`);
  });
});
