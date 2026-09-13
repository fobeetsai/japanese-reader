/* Excel imports are local-only and always create a separate deck. */
document.addEventListener('DOMContentLoaded', () => {
  const $ = id => document.getElementById(id);
  const modal = $('modal-excel-import');
  let workbook = null;
  let rows = [];
  let cards = [];
  let generation = 0;
  const fields = ['zh', 'ja', 'reading'];
  const aliases = {
    zh: ['中文', '繁體中文', '繁中', '中文意思', '中文釋義', '釋義', '意思', 'chinese', 'zh', 'back'],
    ja: ['日文', '日語', '日本語', '單字', '日文單字', 'japanese', 'ja', 'front'],
    reading: ['讀音', '読み', 'よみ', '読み方', '假名', '平假名', 'ふりがな', 'reading', 'kana']
  };
  const value = cell => String(cell ?? '').trim();
  function status(message) { $('excel-status').textContent = message; }
  function reset() {
    generation++;
    workbook = null;
    rows = [];
    cards = [];
    $('excel-options').hidden = true;
    $('excel-preview').replaceChildren();
    $('excel-submit').disabled = true;
  }
  $('btn-excel-import').addEventListener('click', () => {
    reset();
    $('excel-file').value = '';
    $('excel-name').value = '';
    $('excel-header').checked = true;
    $('excel-group-size').value = '20';
    status('選檔後可預覽，再確認建立。');
    modal.classList.add('open');
    $('excel-file').focus();
  });
  // Invalidate pending reads when the user cancels, including backdrop clicks.
  modal.addEventListener('click', event => {
    if (event.target === modal || event.target.closest('.modal-close')) reset();
  });
  $('excel-file').addEventListener('change', async () => {
    reset();
    const ticket = generation;
    const file = $('excel-file').files[0];
    if (!file) return status('請選擇 Excel 檔案。');
    if (!/\.(xlsx|xls)$/i.test(file.name)) return status('請選擇 .xlsx 或 .xls 格式的 Excel 檔案。');
    if (file.size > 10 * 1024 * 1024) return status('檔案超過 10 MB，請拆成較小的檔案。');
    $('excel-name').value = file.name.replace(/\.[^.]+$/, '').slice(0, 100);
    status('正在讀取 Excel…');
    try {
      if (!window.XLSX) throw new Error('Excel 讀取元件尚未載入，請重新整理網頁後再試。');
      const buffer = await file.arrayBuffer();
      if (ticket !== generation) return;
      // Reject renamed text files instead of silently interpreting them as Excel.
      const bytes = new Uint8Array(buffer);
      const zip = bytes[0] === 0x50 && bytes[1] === 0x4b;
      const ole = bytes[0] === 0xd0 && bytes[1] === 0xcf;
      if (!zip && !ole) throw new Error('檔案不是標準 Excel 活頁簿，請用 Excel 另存為 .xlsx 後再試。');
      workbook = XLSX.read(buffer, { type: 'array', sheetRows: 10002 });
      if (!workbook.SheetNames.length) throw new Error('檔案中沒有工作表。');
      $('excel-sheet').replaceChildren(...workbook.SheetNames.map(name => new Option(name, name)));
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
    const sheet = workbook.Sheets[$('excel-sheet').value];
    const range = XLSX.utils.decode_range(sheet['!fullref'] || sheet['!ref'] || 'A1');
    if (range.e.r > 10000 || range.e.c > 99) {
      rows = [];
      return status('工作表範圍過大：每張表最多 10,000 列資料、100 欄。請移除多餘空白列欄或拆檔。');
    }
    rows = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '', raw: false, blankrows: true, range: 0 });
    configureColumns();
  }
  function configureColumns() {
    const width = Math.max(0, ...rows.map(row => row.length));
    fields.forEach((field, index) => {
      const select = $('excel-' + field);
      select.replaceChildren(new Option(field === 'reading' ? '不匯入讀音' : '請選擇欄位', '-1'));
      for (let col = 0; col < width; col++) {
        const label = $('excel-header').checked ? value(rows[0]?.[col]) : '';
        select.add(new Option(`${XLSX.utils.encode_col(col)} 欄${label ? '：' + label.slice(0, 40) : ''}`, String(col)));
      }
      const detected = $('excel-header').checked
        ? (rows[0] || []).findIndex(cell => aliases[field].includes(value(cell).toLowerCase().replace(/\s/g, '')))
        : (index < width ? index : -1);
      select.value = String(detected);
    });
    preview();
  }
  function preview() {
    cards = [];
    $('excel-preview').replaceChildren();
    $('excel-submit').disabled = true;
    const [zh, ja, reading] = fields.map(field => Number($('excel-' + field).value));
    if (zh < 0 || ja < 0) return status('請選擇中文欄與日文欄，讀音可選填。');
    const used = [zh, ja, reading].filter(col => col >= 0);
    if (new Set(used).size !== used.length) return status('中文、日文與讀音必須使用不同欄位。');
    let blank = 0;
    const invalid = [];
    rows.forEach((row, index) => {
      if (index === 0 && $('excel-header').checked) return;
      if (!row.some(cell => value(cell))) { blank++; return; }
      const back = value(row[zh]), front = value(row[ja]);
      if (!back || !front) { invalid.push(index + 1); return; }
      cards.push({ front, back, reading: reading >= 0 ? value(row[reading]) : '' });
    });
    cards.slice(0, 8).forEach(card => {
      const tr = document.createElement('tr');
      [card.back, card.front, card.reading || '—'].forEach(text => {
        const td = document.createElement('td');
        td.textContent = text;
        td.style.overflowWrap = 'anywhere';
        tr.append(td);
      });
      $('excel-preview').append(tr);
    });
    if (invalid.length) {
      status(`第 ${invalid.slice(0, 10).join('、')} 列${invalid.length > 10 ? '等' : ''}缺少中文或日文，共 ${invalid.length} 列。請補齊或刪除後重新選檔，尚未匯入。`);
      return;
    }
    const groupSize = Number($('excel-group-size').value);
    if (!Number.isInteger(groupSize) || groupSize < 1 || groupSize > 1000) return status('每組字數請輸入 1～1000 的整數。');
    const groupCount = Math.ceil(cards.length / groupSize);
    status(cards.length ? `將建立 ${cards.length} 張卡片，收在同一來源牌組，內含 ${groupCount} 個複習小組（預覽前 8 張，略過 ${blank} 個空白列）。` : '此工作表沒有可匯入的單字。');
    $('excel-submit').disabled = !cards.length || !$('excel-name').value.trim();
  }
  $('excel-sheet').addEventListener('change', selectSheet);
  $('excel-header').addEventListener('change', configureColumns);
  $('excel-group-size').addEventListener('input', () => { if (workbook) preview(); });
  fields.forEach(field => $('excel-' + field).addEventListener('change', preview));
  $('excel-name').addEventListener('input', () => { if (workbook) preview(); });
  $('excel-submit').addEventListener('click', () => {
    if ($('excel-submit').disabled || !cards.length) return;
    const app = window.app;
    if (!app) return status('應用程式尚未就緒，請重新整理再試。');
    $('excel-submit').disabled = true;
    const name = $('excel-name').value.trim();
    const groupSize = Number($('excel-group-size').value);
    const groupCount = Math.ceil(cards.length / groupSize);
    const deck = {id: 'deck_excel_' + crypto.randomUUID(), name, desc: '從 Excel 匯入', category: 'excel', categoryName: 'Excel 匯入', icon: '📊', color: '#10b981', reviewGroupSize: groupSize};
    const newDecks = [...app.decks, deck];
    const newCards = [...app.cards, ...cards.map(card => app.anki.createCard({...card, id: 'card_' + crypto.randomUUID(), deckId: deck.id}))];
    // Snapshot both keys and roll back if either write fails (e.g. storage quota).
    const keys = [app.sync.STORAGE_KEY_CARDS, app.sync.STORAGE_KEY_DECKS];
    const previous = [];
    let written = 0;
    try {
      keys.forEach(key => previous.push(localStorage.getItem(key)));
      [newCards, newDecks].forEach((data, index) => {
        localStorage.setItem(keys[index], JSON.stringify(data));
        written++;
      });
    } catch (error) {
      for (let index = written - 1; index >= 0; index--) {
        if (previous[index] === null) localStorage.removeItem(keys[index]);
        else localStorage.setItem(keys[index], previous[index]);
      }
      status('儲存失敗，未建立牌組。請確認瀏覽器允許儲存，或減少檔案中的單字數再試。');
      $('excel-submit').disabled = false;
      return;
    }
    const count = cards.length;
    app.decks = newDecks;
    app.cards = newCards;
    app.currentCategory = 'all';
    app.renderCategoryTabs();
    app.renderDeckList();
    app.updateHeaderStats();
    modal.classList.remove('open');
    reset();
    alert(`已匯入「${name}」共 ${count} 張卡片，建立一個來源牌組，內含 ${groupCount} 個複習小組。`);
  });
});
