/**
 * Kanji Dojo ⟷ AnkiFlash 連通擴充套件
 * 為漢字記憶道場增加「一鍵加入 AnkiFlash 抽認卡」功能
 */

window.addEventListener('DOMContentLoaded', () => {
  // 等待 WaniKani 核心載入
  const checkInitTimer = setInterval(() => {
    const wkActions = document.querySelector('.wk-actions');
    if (!wkActions || typeof WK_FULL === 'undefined' || typeof window.AnkiBridge === 'undefined') return;
    clearInterval(checkInitTimer);

    // 1. 在批次操作列注入「送至 AnkiFlash」按鈕
    const btnSyncSelected = document.createElement('button');
    btnSyncSelected.id = 'wkSyncAnkiFlashSelected';
    btnSyncSelected.type = 'button';
    btnSyncSelected.className = 'primary';
    btnSyncSelected.style.cssText = 'background: linear-gradient(135deg, #6366f1, #4f46e5); color: #fff; border: none; font-weight: 700; margin-left: 4px;';
    btnSyncSelected.innerHTML = '🎴 送至 AnkiFlash (所選漢字)';
    btnSyncSelected.title = '將勾選的漢字一鍵同步至 AnkiFlash 抽認卡';

    const btnGoFlashcards = document.createElement('a');
    btnGoFlashcards.href = 'flashcard.html';
    btnGoFlashcards.className = 'outline';
    btnGoFlashcards.style.cssText = 'display: inline-flex; align-items: center; gap: 4px; text-decoration: none; font-weight: 600; color: #6366f1; border-color: #818cf8;';
    btnGoFlashcards.innerHTML = '👉 前往 AnkiFlash 複習 ↗';

    wkActions.appendChild(btnSyncSelected);
    wkActions.appendChild(btnGoFlashcards);

    // 點擊同步所選漢字
    btnSyncSelected.addEventListener('click', () => {
      if (typeof WK_FULL === 'undefined') return;
      const allItems = WK_FULL.items || [];
      
      // 獲取目前勾選的漢字 (從全域或 DOM 讀取)
      const selectedChars = new Set();
      document.querySelectorAll('#wkResults input[type="checkbox"]:checked').forEach(cb => {
        if (cb.value) selectedChars.add(cb.value);
      });

      let targetItems = [];
      if (selectedChars.size > 0) {
        targetItems = allItems.filter(k => selectedChars.has(k.characters));
      } else {
        // 若未勾選，詢問是否匯入目前篩選清單的前 20 字
        const currentFiltered = document.querySelectorAll('#wkResults .char-card, #wkResults [data-char]');
        if (currentFiltered.length > 0) {
          const chars = Array.from(currentFiltered).slice(0, 30).map(el => el.getAttribute('data-char') || el.textContent.trim().charAt(0)).filter(Boolean);
          targetItems = allItems.filter(k => chars.includes(k.characters));
        }
      }

      if (targetItems.length === 0) {
        window.AnkiBridge.showToast('⚠️ 請先勾選至少一個欲複習的漢字！', 'error');
        return;
      }

      syncItemsToAnkiFlash(targetItems);
    });

    // 2. 監聽字條詳解 (#wkLesson) 變化，注入單字加入按鈕
    const wkLesson = document.getElementById('wkLesson');
    if (wkLesson) {
      const observer = new MutationObserver(() => {
        if (wkLesson.querySelector('#btn-lesson-add-ankiflash')) return;
        const charHeader = wkLesson.querySelector('h2, .char-big, h1');
        if (!charHeader) return;

        const char = charHeader.textContent.trim().charAt(0);
        const item = (WK_FULL.items || []).find(k => k.characters === char);
        if (!item) return;

        const btnAddSingle = document.createElement('button');
        btnAddSingle.id = 'btn-lesson-add-ankiflash';
        btnAddSingle.type = 'button';
        btnAddSingle.className = 'primary';
        btnAddSingle.style.cssText = 'background: #6366f1; color: #fff; padding: 6px 14px; border-radius: 8px; border: none; font-size: 0.88rem; font-weight: 700; margin: 8px 0; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;';
        btnAddSingle.innerHTML = '🎴 加入 AnkiFlash 抽認卡';

        btnAddSingle.addEventListener('click', () => {
          syncItemsToAnkiFlash([item]);
        });

        charHeader.parentNode.insertBefore(btnAddSingle, charHeader.nextSibling);
      });
      observer.observe(wkLesson, { childList: true, subtree: true });
    }
  }, 300);

  // 核心轉換與寫入
  function syncItemsToAnkiFlash(items) {
    const cards = items.map(k => {
      const onStr = (k.on && k.on.length) ? '音：' + k.on.join('、') : '';
      const kunStr = (k.kun && k.kun.length) ? '訓：' + k.kun.join('、') : '';
      const readings = [onStr, kunStr].filter(Boolean).join(' ｜ ');

      let backContent = `【字義】${(k.meanings || []).join('；')}`;
      if (k.words && k.words.length) {
        backContent += `\n【核心例詞】\n` + k.words.slice(0, 3).map(w => `・${w.characters}（${w.reading}）：${w.meaning || ''}`).join('\n');
      }

      const sampleWords = (k.words && k.words.length) ? k.words[0].characters + '（' + k.words[0].reading + '）' : '';

      return {
        front: k.characters,
        reading: readings,
        back: backContent,
        example: sampleWords,
        tags: ['漢字道場', `Level_${k.level}`]
      };
    });

    const res = window.AnkiBridge.addCardsBatch(cards, {
      deckId: 'deck_kanji_dojo',
      deckName: '🈩 漢字記憶道場 (WaniKani)',
      deckIcon: '🈩',
      deckColor: '#059669',
      defaultTags: ['漢字道場']
    });

    if (res.success) {
      window.AnkiBridge.showToast(`🎉 成功同步 ${res.addedCount} 個新漢字至 AnkiFlash！(更新 ${res.updatedCount} 個)`);
    } else {
      window.AnkiBridge.showToast('⚠️ 同步失敗，請重試', 'error');
    }
  }
});
