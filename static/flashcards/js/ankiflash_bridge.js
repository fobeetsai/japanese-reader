/**
 * AnkiFlash Bridge (跨模組單字資料同源同步橋接器)
 * 供 index.html (日文閱讀助手)、kanji.html (漢字記憶道場) 與 flashcard.html (AnkiFlash) 共享使用
 */

class AnkiFlashBridge {
  constructor() {
    this.STORAGE_KEY_DECKS = 'ankiflash_decks_v1';
    this.STORAGE_KEY_CARDS = 'ankiflash_cards_v1';
    this.STORAGE_KEY_SETTINGS = 'ankiflash_settings_v1';
    this.STORAGE_KEY_NOTEBOOK = 'japanese_reader_notebook';
  }

  // 取得本機所有牌組
  getDecks() {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEY_DECKS);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      console.error('[AnkiBridge] 讀取牌組失敗:', e);
      return [];
    }
  }

  // 取得本機所有卡片
  getCards() {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEY_CARDS);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      console.error('[AnkiBridge] 讀取卡片失敗:', e);
      return [];
    }
  }

  // 儲存牌組
  saveDecks(decks) {
    try {
      localStorage.setItem(this.STORAGE_KEY_DECKS, JSON.stringify(decks));
    } catch (e) {
      console.error('[AnkiBridge] 儲存牌組失敗:', e);
    }
  }

  // 儲存卡片
  saveCards(cards) {
    try {
      localStorage.setItem(this.STORAGE_KEY_CARDS, JSON.stringify(cards));
      window.dispatchEvent(new CustomEvent('ankiflash_cards_updated', { detail: { count: cards.length } }));
    } catch (e) {
      console.error('[AnkiBridge] 儲存卡片失敗:', e);
    }
  }

  /**
   * 新增單張單字卡片
   */
  addCard({ deckId, deckName, deckIcon = '📚', deckColor = '#6366f1', front, reading = '', back = '', example = '', notes = '', tags = [] }) {
    if (!front || !front.trim()) return { success: false, reason: '單字不可為空' };

    const decks = this.getDecks();
    const cards = this.getCards();

    const targetDeckId = deckId || 'deck_reader_notes';
    let deck = decks.find(d => d.id === targetDeckId);
    if (!deck) {
      deck = {
        id: targetDeckId,
        name: deckName || '📖 日文閱讀助手收藏生詞',
        desc: '自動同步至 AnkiFlash 的單字牌組',
        icon: deckIcon,
        color: deckColor
      };
      decks.unshift(deck);
      this.saveDecks(decks);
    }

    const cleanFront = front.trim();
    let card = cards.find(c => c.deckId === targetDeckId && c.front === cleanFront);
    let isNew = false;

    if (card) {
      // 已存在，若新資料更完整則補充
      if (reading && !card.reading) card.reading = reading.trim();
      if (back && (!card.back || card.back.length < back.length)) card.back = back.trim();
      if (example && !card.example) card.example = example.trim();
      if (Array.isArray(tags)) {
        card.tags = Array.from(new Set([...(card.tags || []), ...tags]));
      }
    } else {
      isNew = true;
      card = {
        id: 'card_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7),
        deckId: targetDeckId,
        front: cleanFront,
        reading: reading ? reading.trim() : '',
        back: back ? back.trim() : '',
        example: example ? example.trim() : '',
        notes: notes ? notes.trim() : '',
        tags: Array.isArray(tags) ? tags : (tags ? [tags] : []),
        state: 'new',
        stepIndex: 0,
        due: Date.now(),
        interval: 0,
        ease: 2.50,
        reps: 0,
        lapses: 0,
        createdAt: Date.now()
      };
      cards.push(card);
    }

    this.saveCards(cards);
    return { success: true, isNew, card };
  }

  /**
   * 批次新增單字卡片
   */
  addCardsBatch(cardsList, { deckId, deckName, deckIcon = '📚', deckColor = '#6366f1', defaultTags = [] } = {}) {
    if (!Array.isArray(cardsList) || cardsList.length === 0) {
      return { success: false, addedCount: 0, updatedCount: 0 };
    }

    const decks = this.getDecks();
    const cards = this.getCards();

    const targetDeckId = deckId || 'deck_reader_notes';
    let deck = decks.find(d => d.id === targetDeckId);
    if (!deck) {
      deck = {
        id: targetDeckId,
        name: deckName || '📖 日文閱讀助手收藏生詞',
        desc: '批次匯入至 AnkiFlash 的單字牌組',
        icon: deckIcon,
        color: deckColor
      };
      decks.unshift(deck);
      this.saveDecks(decks);
    }

    let addedCount = 0;
    let updatedCount = 0;

    cardsList.forEach(item => {
      if (!item || !item.front || !item.front.trim()) return;
      const cleanFront = item.front.trim();
      let card = cards.find(c => c.deckId === targetDeckId && c.front === cleanFront);

      const itemTags = Array.from(new Set([...defaultTags, ...(Array.isArray(item.tags) ? item.tags : [])]));

      if (card) {
        if (item.reading && !card.reading) card.reading = item.reading.trim();
        if (item.back && (!card.back || card.back.length < item.back.length)) card.back = item.back.trim();
        if (item.example && !card.example) card.example = item.example.trim();
        card.tags = Array.from(new Set([...(card.tags || []), ...itemTags]));
        updatedCount++;
      } else {
        cards.push({
          id: 'card_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7) + '_' + addedCount,
          deckId: targetDeckId,
          front: cleanFront,
          reading: item.reading ? item.reading.trim() : '',
          back: item.back ? item.back.trim() : '',
          example: item.example ? item.example.trim() : '',
          notes: item.notes ? item.notes.trim() : '',
          tags: itemTags,
          state: 'new',
          stepIndex: 0,
          due: Date.now(),
          interval: 0,
          ease: 2.50,
          reps: 0,
          lapses: 0,
          createdAt: Date.now()
        });
        addedCount++;
      }
    });

    this.saveCards(cards);
    return { success: true, addedCount, updatedCount, total: cards.length };
  }

  /**
   * 自動同步閱讀助手的生詞本 (japanese_reader_notebook)
   */
  syncFromReaderNotebook() {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEY_NOTEBOOK);
      if (!raw) return { success: false, reason: '未找到閱讀助手生詞本' };

      const nb = JSON.parse(raw);
      const words = nb.words || [];
      if (words.length === 0) return { success: false, reason: '生詞本內尚無單字' };

      const cardsToAdd = words.map(w => ({
        front: w.surface || w.baseForm,
        reading: w.reading || '',
        back: (w.jlpt ? `[${w.jlpt}] ` : '') + (w.pos ? `(${w.pos}) ` : '') + (w.meaning || w.def || '閱讀生詞'),
        example: w.example || '',
        tags: ['閱讀收藏', w.jlpt || '未分級'].filter(Boolean)
      }));

      const res = this.addCardsBatch(cardsToAdd, {
        deckId: 'deck_reader_notes',
        deckName: '📖 閱讀助手收藏生詞',
        deckIcon: '⭐',
        deckColor: '#f59e0b'
      });

      return { success: true, ...res };
    } catch (e) {
      console.error('[AnkiBridge] 同步閱讀助手生詞失敗:', e);
      return { success: false, reason: e.message };
    }
  }

  /**
   * 建立全站浮動 Toast 通知
   */
  showToast(message, type = 'success', duration = 3000) {
    let container = document.getElementById('ankiflash-bridge-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'ankiflash-bridge-toast-container';
      container.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 99999;
        display: flex;
        flex-direction: column;
        gap: 8px;
        pointer-events: none;
      `;
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.style.cssText = `
      background: ${type === 'success' ? '#0f172a' : '#ef4444'};
      color: #ffffff;
      padding: 12px 18px;
      border-radius: 10px;
      font-size: 0.92rem;
      font-weight: 600;
      box-shadow: 0 10px 25px rgba(0,0,0,0.25);
      border: 1px solid rgba(255,255,255,0.15);
      display: flex;
      align-items: center;
      gap: 10px;
      pointer-events: auto;
      transform: translateY(10px);
      opacity: 0;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans JP", sans-serif;
    `;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    requestAnimationFrame(() => {
      toast.style.transform = 'translateY(0)';
      toast.style.opacity = '1';
    });

    setTimeout(() => {
      toast.style.transform = 'translateY(10px)';
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }
}

// 掛載到全域變數
window.AnkiBridge = new AnkiFlashBridge();
