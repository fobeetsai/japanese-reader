/**
 * AnkiFlash 主要應用控制器 (UI Controller & App Logic)
 * 整合：Anki SM-2 引擎、SyncManager、語音合成 TTS、觸控手勢識別
 */

class FlashcardApp {
  constructor() {
    this.anki = new AnkiEngine();
    this.sync = new SyncManager();
    
    // 應用狀態
    this.decks = [];
    this.cards = [];
    this.settings = {};
    this.logs = {};
    
    // 當前學習狀態
    this.currentDeck = null;
    this.studyQueue = [];
    this.currentCardIndex = 0;
    this.isCardFlipped = false;
    this.todayReviewedCount = 0;

    // 觸控手勢追蹤
    this.touchStartX = 0;
    this.touchStartY = 0;

    // 分類篩選狀態 (預設 'all')
    this.currentCategory = 'all';

    this.enricher = null;

    this.init();
  }

  async init() {
    try {
      this.loadData();
      if (typeof WordEnricher !== 'undefined') {
        this.enricher = new WordEnricher({ settings: this.settings });
      }
      if (typeof PhotoOcrEngine !== 'undefined') {
        this.photoOcr = new PhotoOcrEngine(this);
      }
      this.applyTheme();
      this.initPwaBanner();
      this.setupEventListeners();
      this.setupKeyboardShortcuts();
      this.setupGestures();
      this.renderCategoryTabs();
      this.renderDeckList();
      this.updateHeaderStats();

      // 若設定開啟自動同步且有 Token 與 GistID，則在啟動時自動拉取
      if (this.settings.autoSyncOnStart && this.settings.githubToken && this.settings.gistId) {
        this.autoSyncCloud();
      }
    } catch (err) {
      console.error('[AnkiFlash] init 初始化異常:', err);
    }
  }

  // ==========================================
  // 資料載入與持久化
  // ==========================================

  getFallbackBuiltinData() {
    const defaultDecks = (typeof BUILTIN_DECKS !== 'undefined' ? BUILTIN_DECKS : (window.BUILTIN_DECKS || []));
    const defaultCards = (typeof BUILTIN_CARDS !== 'undefined' ? BUILTIN_CARDS : (window.BUILTIN_CARDS || []));
    return {
      decks: JSON.parse(JSON.stringify(defaultDecks)),
      cards: JSON.parse(JSON.stringify(defaultCards))
    };
  }

  loadData() {
    const data = this.sync.loadLocalData();
    this.settings = data.settings || this.sync.getDefaultSettings();
    this.logs = data.logs || {};

    if (data.decks && Array.isArray(data.decks) && data.decks.length > 0) {
      this.decks = data.decks;
      this.cards = (data.cards && Array.isArray(data.cards)) ? data.cards : [];
    } else {
      // 首次啟動或無牌組：載入內建精選高頻字庫
      const fallback = this.getFallbackBuiltinData();
      this.decks = fallback.decks;
      this.cards = fallback.cards.map(c => this.anki.createCard(c));
      this.saveData();
    }

    // 計算今日已複習張數
    const todayKey = new Date().toISOString().slice(0, 10);
    this.todayReviewedCount = (this.logs[todayKey] && this.logs[todayKey].reviewed) || 0;
  }

  saveData() {
    this.sync.saveLocalData({
      decks: this.decks,
      cards: this.cards,
      settings: this.settings,
      logs: this.logs
    });
  }

  restoreDefaultDecks() {
    const fallback = this.getFallbackBuiltinData();
    this.decks = fallback.decks;
    this.cards = fallback.cards.map(c => this.anki.createCard(c));
    this.saveData();
    this.currentCategory = 'all';
    this.renderCategoryTabs();
    this.renderDeckList();
    this.updateHeaderStats();
    alert('🎉 已成功還原所有預設牌組與單字卡片！');
  }

  applyTheme() {
    if (this.settings.theme === 'light') {
      document.body.classList.add('light-theme');
    } else {
      document.body.classList.remove('light-theme');
    }
  }

  // ==========================================
  // 介面切換與渲染
  // ==========================================

  showView(viewId) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
    const target = document.getElementById(viewId);
    if (target) target.classList.add('active');

    // 視圖特定處理
    if (viewId === 'view-decks') {
      this.renderDeckList();
      this.updateHeaderStats();
    }
  }

  updateHeaderStats() {
    const now = Date.now();
    let totalNew = 0;
    let totalLearn = 0;
    let totalDue = 0;

    this.cards.forEach(c => {
      if (c.state === 'new') totalNew++;
      else if (c.state === 'learning' || c.state === 'relearning') {
        if (c.due <= now) totalLearn++;
      } else if (c.state === 'review') {
        if (c.due <= now) totalDue++;
      }
    });

    const badgeNew = document.getElementById('header-badge-new');
    const badgeLearn = document.getElementById('header-badge-learn');
    const badgeDue = document.getElementById('header-badge-due');

    if (badgeNew) badgeNew.innerText = `新 ${totalNew}`;
    if (badgeLearn) badgeLearn.innerText = `學 ${totalLearn}`;
    if (badgeDue) badgeDue.innerText = `複 ${totalDue}`;
  }

  // ==========================================
  // 分類標籤渲染與篩選切換
  // ==========================================

  renderCategoryTabs() {
    const bar = document.getElementById('category-filter-bar');
    if (!bar) return;

    // 彙總所有分類 (內建 + 使用者自訂)
    const baseCategories = (window.BUILTIN_CATEGORIES && window.BUILTIN_CATEGORIES.length > 0)
      ? [...window.BUILTIN_CATEGORIES]
      : [
          { id: 'all', name: '全部牌組', icon: '🌟' },
          { id: 'engineering', name: '工程營造', icon: '🏗️' },
          { id: 'daily', name: '日常生活', icon: '🍵' },
          { id: 'business', name: '商務職場', icon: '💼' },
          { id: 'jlpt', name: 'JLPT 檢定', icon: '🇯🇵' }
        ];

    // 動態掃描是否存在不在基本列表中的自訂分類
    const existingIds = new Set(baseCategories.map(c => c.id));
    this.decks.forEach(d => {
      if (d.category && !existingIds.has(d.category)) {
        baseCategories.push({
          id: d.category,
          name: d.categoryName || d.category,
          icon: '🏷️'
        });
        existingIds.add(d.category);
      }
    });

    bar.innerHTML = '';
    baseCategories.forEach(cat => {
      const pill = document.createElement('button');
      pill.className = `category-pill ${this.currentCategory === cat.id ? 'active' : ''}`;
      pill.innerHTML = `<span>${cat.icon || '📁'}</span> <span>${this.escapeHtml(cat.name)}</span>`;
      pill.addEventListener('click', () => {
        this.currentCategory = cat.id;
        document.querySelectorAll('.category-pill').forEach(el => el.classList.remove('active'));
        pill.classList.add('active');
        this.renderDeckList();
      });
      bar.appendChild(pill);
    });
  }

  getCategoryLabel(categoryId) {
    const map = {
      'engineering': '🏗️ 工程營造',
      'daily': '🍵 日常生活',
      'business': '💼 商務職場',
      'jlpt': '🇯🇵 JLPT 檢定'
    };
    return map[categoryId] || (categoryId ? `🏷️ ${categoryId}` : '未分類');
  }

  renderDeckList() {
    const container = document.getElementById('decks-grid-container');
    if (!container) return;

    container.innerHTML = '';
    const now = Date.now();

    // 依照選取的分類進行篩選 (若為 'all' 則顯示全部)
    const filteredDecks = (this.currentCategory === 'all')
      ? this.decks
      : this.decks.filter(d => d.category === this.currentCategory);

    if (filteredDecks.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 50px 20px; color: var(--text-secondary);">
          <div style="font-size: 2.5rem; margin-bottom: 12px;">📂</div>
          <div style="font-size: 1.15rem; font-weight: 700; margin-bottom: 6px; color: var(--text-primary);">目前此處尚無牌組</div>
          <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 18px;">您可以點擊下方按鈕立即一鍵恢復預設牌組，或點選右上角建立新牌組！</p>
          <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
            <button class="btn-primary" onclick="window.app.restoreDefaultDecks()" style="display: inline-flex; align-items: center; gap: 6px; padding: 10px 18px;">
              🔄 一鍵還原預設牌組 (營造工程/KY/日常/JLPT)
            </button>
            <button class="btn-secondary" onclick="window.app.openNewDeckModal()">
              ➕ 新建自訂牌組
            </button>
          </div>
        </div>
      `;
      return;
    }

    filteredDecks.forEach(deck => {
      const deckCards = this.cards.filter(c => c.deckId === deck.id);
      const queue = this.anki.getStudyQueue(deckCards, now, {
        dailyNewLimit: this.settings.dailyNewLimit,
        dailyReviewLimit: this.settings.dailyReviewLimit
      });

      const newCount = queue.newCards.length;
      const learnCount = queue.learning.length;
      const dueCount = queue.review.length;
      const totalAvailable = queue.totalAvailable;
      const categoryTag = this.getCategoryLabel(deck.category);

      const cardEl = document.createElement('div');
      cardEl.className = 'deck-card';
      cardEl.innerHTML = `
        <div class="deck-card-top">
          <div class="deck-icon-bubble" style="color: ${deck.color || '#6366f1'}">${deck.icon || '📚'}</div>
          <div class="deck-info">
            <h3 class="deck-name">${this.escapeHtml(deck.name)}</h3>
            <p class="deck-desc">${this.escapeHtml(deck.desc || '自訂單字牌組')}</p>
            <span class="deck-category-badge">${categoryTag}</span>
          </div>
        </div>

        <div class="deck-counts-row">
          <div class="count-item">
            <span class="count-label">新卡</span>
            <span class="count-val new">${newCount}</span>
          </div>
          <div class="count-item">
            <span class="count-label">學習中</span>
            <span class="count-val learn">${learnCount}</span>
          </div>
          <div class="count-item">
            <span class="count-label">待複習</span>
            <span class="count-val due">${dueCount}</span>
          </div>
          <div class="count-item">
            <span class="count-label">總計</span>
            <span class="count-val">${deckCards.length}</span>
          </div>
        </div>

        <div class="deck-actions-row">
          <button class="btn-study" data-deck-id="${deck.id}">
            ${totalAvailable > 0 ? `🚀 開始複習 (${totalAvailable})` : '✨ 今日已完成'}
          </button>
          <button class="btn-deck-cards btn-icon" data-deck-id="${deck.id}" style="width: 38px; height: 38px; border-radius: 10px;" title="查看與管理此牌組的單字列表 (可逐一刪除或查 MOJi 辭書)">📋</button>
          <button class="btn-deck-menu btn-icon" data-deck-id="${deck.id}" style="width: 38px; height: 38px; border-radius: 10px;" title="牌組選項 (匯出/刪除)">⚙️</button>
        </div>
      `;

      // 綁定事件
      cardEl.querySelector('.btn-study')?.addEventListener('click', (e) => {
        e.stopPropagation();
        this.startStudy(deck.id);
      });

      cardEl.querySelector('.btn-deck-cards')?.addEventListener('click', (e) => {
        e.stopPropagation();
        this.openDeckCardManager(deck.id);
      });

      cardEl.querySelector('.btn-deck-menu')?.addEventListener('click', (e) => {
        e.stopPropagation();
        this.openDeckActionMenu(deck.id);
      });

      cardEl.addEventListener('click', () => {
        this.startStudy(deck.id);
      });

      container.appendChild(cardEl);
    });
  }

  // ==========================================
  // 抽認卡複習模式 (Study Mode)
  // ==========================================

  startStudy(deckId) {
    this.currentDeck = this.decks.find(d => d.id === deckId);
    if (!this.currentDeck) return;

    const deckCards = this.cards.filter(c => c.deckId === deckId);
    const now = Date.now();
    const queueObj = this.anki.getStudyQueue(deckCards, now, {
      dailyNewLimit: this.settings.dailyNewLimit,
      dailyReviewLimit: this.settings.dailyReviewLimit
    });

    this.studyQueue = queueObj.queue;
    this.currentCardIndex = 0;
    this.isCardFlipped = false;

    // 設定標題
    document.getElementById('study-deck-name').innerText = this.currentDeck.name;

    if (this.studyQueue.length === 0) {
      this.renderStudyEmpty(true);
    } else {
      this.showView('view-study');
      this.renderCurrentStudyCard();
    }
  }

  renderCurrentStudyCard() {
    if (this.currentCardIndex >= this.studyQueue.length) {
      this.renderStudyEmpty(false);
      return;
    }

    const card = this.studyQueue[this.currentCardIndex];
    this.isCardFlipped = false;

    // 取得即時間隔預估文字
    const intervalPreviews = this.anki.getIntervalPreviews(card);

    // 更新進度條
    const progressPercent = (this.currentCardIndex / this.studyQueue.length) * 100;
    const fillEl = document.getElementById('study-progress-fill');
    if (fillEl) fillEl.style.width = `${progressPercent}%`;

    const countIndicator = document.getElementById('study-count-indicator');
    if (countIndicator) {
      countIndicator.innerText = `${this.currentCardIndex + 1} / ${this.studyQueue.length}`;
    }

    // 正面內容
    document.getElementById('card-front-word').innerText = card.front;
    document.getElementById('card-front-tag').innerText = (card.tags && card.tags[0]) || this.currentDeck.name.slice(0, 10);
    
    // 背面內容
    document.getElementById('card-back-word').innerText = card.front;
    document.getElementById('card-back-reading').innerText = card.reading ? `[${card.reading}]` : '';
    document.getElementById('card-back-meaning').innerText = card.back || '';
    
    const exBox = document.getElementById('card-back-example-box');
    if (card.example) {
      exBox.style.display = 'block';
      document.getElementById('card-back-example').innerText = card.example;
    } else {
      exBox.style.display = 'none';
    }

    // 按鈕區控制
    const cardEl = document.getElementById('active-flashcard');
    cardEl.classList.remove('is-flipped');

    document.getElementById('show-answer-btn').style.display = 'flex';
    const ankiRow = document.getElementById('anki-buttons-row');
    ankiRow.classList.remove('visible');

    // 填入 4 個按鈕上方動態預估時間
    document.getElementById('interval-again').innerText = intervalPreviews[0];
    document.getElementById('interval-hard').innerText = intervalPreviews[1];
    document.getElementById('interval-good').innerText = intervalPreviews[2];
    document.getElementById('interval-easy').innerText = intervalPreviews[3];

    // 發音
    if (this.settings.autoPlayAudio && card.front) {
      this.speakText(card.front);
    }
  }

  flipCard() {
    if (this.isCardFlipped) return;
    this.isCardFlipped = true;

    const cardEl = document.getElementById('active-flashcard');
    cardEl.classList.add('is-flipped');

    document.getElementById('show-answer-btn').style.display = 'none';
    document.getElementById('anki-buttons-row').classList.add('visible');

    // 若正面沒發音或設定發音，翻面可點發音
    if (this.settings.vibration && navigator.vibrate) {
      navigator.vibrate(15);
    }
  }

  handleRate(rating) {
    if (this.currentCardIndex >= this.studyQueue.length) return;
    const currentCard = this.studyQueue[this.currentCardIndex];
    const now = Date.now();

    // 透過 SM-2 核心計算新數值
    const updatedCard = this.anki.rateCard(currentCard, rating, now);

    // 更新到主 cards 庫存
    const idx = this.cards.findIndex(c => c.id === currentCard.id);
    if (idx !== -1) {
      this.cards[idx] = updatedCard;
    }

    // 若選 Again (rating === 1)，將此卡片重新排進隊列尾端，確保今日再次背誦
    if (rating === 1) {
      this.studyQueue.push(updatedCard);
    }

    // 更新紀錄
    const todayKey = new Date().toISOString().slice(0, 10);
    if (!this.logs[todayKey]) this.logs[todayKey] = { reviewed: 0 };
    this.logs[todayKey].reviewed += 1;
    this.todayReviewedCount = this.logs[todayKey].reviewed;

    this.saveData();

    // 輕觸震動回饋
    if (this.settings.vibration && navigator.vibrate) {
      navigator.vibrate(25);
    }

    // 邁向下張卡片
    this.currentCardIndex++;
    this.renderCurrentStudyCard();
  }

  renderStudyEmpty(isInitiallyEmpty) {
    this.showView('view-study');
    const scene = document.getElementById('card-scene-container');
    const actions = document.getElementById('study-actions-container');
    
    if (scene) {
      scene.innerHTML = `
        <div style="text-align: center; padding: 60px 20px; background: var(--bg-card); border-radius: 24px; border: 1.5px solid var(--border-color); max-width: 600px; margin: 0 auto;">
          <div style="font-size: 3.5rem; margin-bottom: 16px;">🎉</div>
          <h2 style="font-size: 1.5rem; margin-bottom: 8px; color: var(--text-primary);">
            ${isInitiallyEmpty ? '今日複習已全數完成！' : '太棒了！本輪複習已順利結束！'}
          </h2>
          <p style="color: var(--text-secondary); margin-bottom: 24px; font-size: 0.95rem;">
            已遵循 Anki 遺忘曲線將單字妥善排程。持續保持，記憶效果最佳！
          </p>
          <button class="btn-primary" onclick="window.app.showView('view-decks')">
            👈 返回牌組列表
          </button>
        </div>
      `;
    }
    if (actions) actions.style.display = 'none';
  }

  // ==========================================
  // 語音發音朗讀 (Web Speech API TTS)
  // ==========================================

  speakText(text, lang = null) {
    if (!window.speechSynthesis || !text) return;
    try {
      window.speechSynthesis.cancel(); // 停止先前的發音
      const utterance = new SpeechSynthesisUtterance(text);
      
      const targetLang = lang || this.settings.audioLang || 'ja-JP';
      utterance.lang = targetLang;
      utterance.rate = 0.9; // 略微放慢語速，方便聽清

      // 視覺回饋
      const audioBtns = document.querySelectorAll('.audio-btn');
      audioBtns.forEach(btn => btn.classList.add('playing'));
      utterance.onend = () => {
        audioBtns.forEach(btn => btn.classList.remove('playing'));
      };
      utterance.onerror = () => {
        audioBtns.forEach(btn => btn.classList.remove('playing'));
      };

      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('語音合成暫時不可用:', e);
    }
  }

  // ==========================================
  // 觸控手勢與鍵盤快速鍵
  // ==========================================

  setupKeyboardShortcuts() {
    window.addEventListener('keydown', (e) => {
      const activeView = document.querySelector('.view-section.active');
      if (!activeView || activeView.id !== 'view-study') return;

      // 若在輸入框內則不攔截
      if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;

      if (e.code === 'Space') {
        e.preventDefault();
        if (!this.isCardFlipped) {
          this.flipCard();
        }
      } else if (this.isCardFlipped) {
        if (e.key === '1') this.handleRate(1);
        else if (e.key === '2') this.handleRate(2);
        else if (e.key === '3') this.handleRate(3);
        else if (e.key === '4') this.handleRate(4);
      }
    });
  }

  setupGestures() {
    const cardEl = document.getElementById('card-scene-container');
    if (!cardEl) return;

    cardEl.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        this.touchStartX = e.touches[0].clientX;
        this.touchStartY = e.touches[0].clientY;
      }
    }, { passive: true });

    cardEl.addEventListener('touchend', (e) => {
      if (!e.changedTouches || e.changedTouches.length === 0) return;
      const endX = e.changedTouches[0].clientX;
      const endY = e.changedTouches[0].clientY;

      const diffX = endX - this.touchStartX;
      const diffY = endY - this.touchStartY;

      // 判斷是否為大幅滑動 (超過 60px)
      if (Math.abs(diffX) > 60 && Math.abs(diffX) > Math.abs(diffY)) {
        if (this.isCardFlipped) {
          if (diffX > 0) {
            // 往右滑：Good (良好)
            this.handleRate(3);
          } else {
            // 往左滑：Again (重來)
            this.handleRate(1);
          }
        }
      } else if (Math.abs(diffY) > 50 && diffY < 0) {
        // 往上滑：翻轉卡片
        if (!this.isCardFlipped) this.flipCard();
      }
    }, { passive: true });
  }

  // ==========================================
  // 彈窗事件與使用者操作
  // ==========================================

  setupEventListeners() {
    // 導覽列操作
    document.getElementById('nav-brand').addEventListener('click', () => this.showView('view-decks'));
    document.getElementById('btn-back-decks').addEventListener('click', () => this.showView('view-decks'));
    document.getElementById('btn-open-sync').addEventListener('click', () => this.openSyncModal());
    document.getElementById('btn-open-stats').addEventListener('click', () => this.openStatsModal());
    document.getElementById('btn-open-settings').addEventListener('click', () => this.openSettingsModal());
    document.getElementById('btn-new-deck').addEventListener('click', () => this.openNewDeckModal());
    document.getElementById('btn-batch-import').addEventListener('click', () => this.openBatchImportModal());
    const btnPhotoOcr = document.getElementById('btn-photo-ocr');
    if (btnPhotoOcr) btnPhotoOcr.addEventListener('click', () => this.openPhotoOcrModal());
    const addCardBtn = document.getElementById('btn-open-add-card');
    if (addCardBtn) addCardBtn.addEventListener('click', () => this.openAddCardModal());

    // 卡片翻轉與評分
    document.getElementById('active-flashcard').addEventListener('click', () => {
      if (!this.isCardFlipped) this.flipCard();
    });
    document.getElementById('show-answer-btn').addEventListener('click', () => this.flipCard());

    document.getElementById('btn-anki-again').addEventListener('click', () => this.handleRate(1));
    document.getElementById('btn-anki-hard').addEventListener('click', () => this.handleRate(2));
    document.getElementById('btn-anki-good').addEventListener('click', () => this.handleRate(3));
    document.getElementById('btn-anki-easy').addEventListener('click', () => this.handleRate(4));

    // 發音按鈕
    document.getElementById('btn-speak-front').addEventListener('click', (e) => {
      e.stopPropagation();
      const word = document.getElementById('card-front-word').innerText;
      this.speakText(word);
    });

    document.getElementById('btn-speak-back').addEventListener('click', (e) => {
      e.stopPropagation();
      const word = document.getElementById('card-back-word').innerText;
      this.speakText(word);
    });

    // MOJi 辭書聯動按鈕 (正反面)
    const mojiFrontBtn = document.getElementById('btn-open-moji-front');
    if (mojiFrontBtn) {
      mojiFrontBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const word = document.getElementById('card-front-word').innerText;
        this.openMojiDict(word);
      });
    }

    const mojiBackBtn = document.getElementById('btn-open-moji-back');
    if (mojiBackBtn) {
      mojiBackBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const word = document.getElementById('card-back-word').innerText;
        this.openMojiDict(word);
      });
    }

    // 單字刪除按鈕 (正反面)
    const delFrontBtn = document.getElementById('btn-delete-card-front');
    if (delFrontBtn) {
      delFrontBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.deleteCurrentStudyCard();
      });
    }

    const delBackBtn = document.getElementById('btn-delete-card-back');
    if (delBackBtn) {
      delBackBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.deleteCurrentStudyCard();
      });
    }

    // 牌組單字管理搜尋框即時過濾
    const searchInput = document.getElementById('deck-cards-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        if (this.activeManagerDeckId) {
          this.renderDeckCardsList(this.activeManagerDeckId, e.target.value.trim());
        }
      });
    }

    // 彈窗通用關閉
    document.querySelectorAll('.modal-close, .modal-backdrop').forEach(el => {
      el.addEventListener('click', (e) => {
        if (e.target === el) {
          document.querySelectorAll('.modal-backdrop').forEach(m => m.classList.remove('open'));
        }
      });
    });
  }

  // ==========================================
  // 統計與儀表板 (Stats Modal)
  // ==========================================

  openStatsModal() {
    const stats = this.anki.getDeckStats(this.cards);
    
    document.getElementById('stat-total-cards').innerText = stats.total;
    document.getElementById('stat-mastered-cards').innerText = stats.masteredCount;
    document.getElementById('stat-learning-cards').innerText = stats.learningCount;
    document.getElementById('stat-today-reviews').innerText = this.todayReviewedCount;

    // 繪製未來 7 天預測長條圖
    const chartContainer = document.getElementById('stats-forecast-chart');
    if (chartContainer) {
      chartContainer.innerHTML = '';
      const maxVal = Math.max(1, ...stats.next7Days);

      const daysOfWeek = ['今天', '+1天', '+2天', '+3天', '+4天', '+5天', '+6天'];
      stats.next7Days.forEach((val, idx) => {
        const heightPct = Math.round((val / maxVal) * 80) + 10;
        const col = document.createElement('div');
        col.className = 'chart-bar-wrapper';
        col.innerHTML = `
          <div class="chart-val">${val}</div>
          <div class="chart-bar" style="height: ${heightPct}%;"></div>
          <div class="chart-label">${daysOfWeek[idx]}</div>
        `;
        chartContainer.appendChild(col);
      });
    }

    document.getElementById('modal-stats').classList.add('open');
  }

  // ==========================================
  // 雲端同步與備份 (Sync Modal)
  // ==========================================

  openSyncModal() {
    const tokenInput = document.getElementById('sync-github-token');
    const gistInput = document.getElementById('sync-gist-id');
    const statusText = document.getElementById('sync-status-msg');

    if (tokenInput) tokenInput.value = this.settings.githubToken || '';
    if (gistInput) gistInput.value = this.settings.gistId || '';
    if (statusText) {
      statusText.innerText = this.settings.lastSyncTime 
        ? `上次同步時間：${new Date(this.settings.lastSyncTime).toLocaleString('zh-TW')}`
        : '尚未進行雲端同步';
    }

    document.getElementById('modal-sync').classList.add('open');
  }

  async uploadToCloud() {
    const token = document.getElementById('sync-github-token').value.trim();
    const gistId = document.getElementById('sync-gist-id').value.trim();
    const statusText = document.getElementById('sync-status-msg');

    if (!token) {
      alert('請先輸入 GitHub Token！');
      return;
    }

    statusText.innerText = '正在上傳備份至 GitHub Gist...';
    try {
      const result = await this.sync.uploadToGist(token, gistId || null, {
        decks: this.decks,
        cards: this.cards,
        logs: this.logs
      });

      this.settings.githubToken = token;
      this.settings.gistId = result.gistId;
      this.settings.lastSyncTime = Date.now();
      this.saveData();

      document.getElementById('sync-gist-id').value = result.gistId;
      statusText.innerText = `✅ 上傳成功！Gist ID: ${result.gistId}`;
      alert('雲端同步成功！請在其他裝置（手機/iPad）輸入相同的 Token 與 Gist ID 即可下載最新進度！');
    } catch (e) {
      statusText.innerText = `❌ 上傳失敗: ${e.message}`;
      alert(`上傳失敗: ${e.message}`);
    }
  }

  async downloadFromCloud() {
    const token = document.getElementById('sync-github-token').value.trim();
    const gistId = document.getElementById('sync-gist-id').value.trim();
    const statusText = document.getElementById('sync-status-msg');

    if (!token || !gistId) {
      alert('請輸入 GitHub Token 與 Gist ID！');
      return;
    }

    if (!confirm('從雲端下載將會覆蓋本機資料，確定繼續嗎？')) return;

    statusText.innerText = '正在從雲端下載最新進度...';
    try {
      const result = await this.sync.downloadFromGist(token, gistId);
      if (result.decks && result.cards) {
        this.decks = result.decks;
        this.cards = result.cards;
        if (result.logs) this.logs = result.logs;

        this.settings.githubToken = token;
        this.settings.gistId = gistId;
        this.settings.lastSyncTime = Date.now();
        this.saveData();

        this.renderDeckList();
        this.updateHeaderStats();
        statusText.innerText = `✅ 同步完成！共載入 ${this.decks.length} 個牌組、${this.cards.length} 張單字卡。`;
        alert('雲端進度已成功同步到本機！');
      }
    } catch (e) {
      statusText.innerText = `❌ 下載失敗: ${e.message}`;
      alert(`下載失敗: ${e.message}`);
    }
  }

  async autoSyncCloud() {
    try {
      const result = await this.sync.downloadFromGist(this.settings.githubToken, this.settings.gistId);
      if (result.decks && result.cards) {
        this.decks = result.decks;
        this.cards = result.cards;
        if (result.logs) this.logs = result.logs;
        this.renderDeckList();
        this.updateHeaderStats();
        console.log('[AutoSync] 自動同步完成');
      }
    } catch (e) {
      console.warn('[AutoSync] 自動同步未成功:', e.message);
    }
  }

  exportBackupFile() {
    this.sync.exportBackupJson({
      decks: this.decks,
      cards: this.cards,
      logs: this.logs
    });
  }

  importBackupFile(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const parsed = JSON.parse(e.target.result);
        if (parsed.decks && parsed.cards) {
          this.decks = parsed.decks;
          this.cards = parsed.cards;
          if (parsed.logs) this.logs = parsed.logs;
          this.saveData();
          this.renderDeckList();
          this.updateHeaderStats();
          alert('備份檔案已成功還原！');
          document.getElementById('modal-sync').classList.remove('open');
        } else {
          alert('備份檔案格式不正確！');
        }
      } catch (err) {
        alert('解析 JSON 備份檔失敗：' + err.message);
      }
    };
    reader.readAsText(file);
  }

  // ==========================================
  // 批次匯入與牌組新增
  // ==========================================

  openBatchImportModal() {
    const select = document.getElementById('batch-import-deck-select');
    if (select) {
      select.innerHTML = '';
      this.decks.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.id;
        opt.innerText = d.name;
        select.appendChild(opt);
      });
    }
    document.getElementById('modal-batch-import').classList.add('open');
  }

  async executeBatchImport() {
    const deckId = document.getElementById('batch-import-deck-select').value;
    const text = document.getElementById('batch-import-text').value;
    const autoEnrich = document.getElementById('batch-import-auto-enrich').checked;

    const parsedCards = this.sync.parseBatchCards(text, deckId);
    if (parsedCards.length === 0) {
      alert('未識別出有效的單字內容，請檢查格式！');
      return;
    }

    const deck = this.decks.find(d => d.id === deckId);
    const category = deck ? deck.category : 'engineering';

    const submitBtn = document.getElementById('btn-batch-submit');
    const cancelBtn = document.getElementById('btn-batch-cancel');
    const progressWrap = document.getElementById('batch-enrich-progress-wrap');
    const progressText = document.getElementById('batch-enrich-progress-text');

    if (autoEnrich && this.enricher) {
      if (submitBtn) submitBtn.disabled = true;
      if (cancelBtn) cancelBtn.disabled = true;
      if (progressWrap) progressWrap.style.display = 'block';

      try {
        const enrichedList = await this.enricher.batchEnrichWords(parsedCards, { category }, (current, total, word) => {
          if (progressText) {
            progressText.innerText = `⚡ 正在自動生成 (${current}/${total})：${word} 的讀音、繁中翻譯與例句...`;
          }
        });

        enrichedList.forEach(c => {
          this.cards.push(this.anki.createCard(c));
        });
      } catch (e) {
        console.warn('批次自動擴充遭遇異常，改用基礎內容匯入:', e);
        parsedCards.forEach(c => {
          this.cards.push(this.anki.createCard(c));
        });
      } finally {
        if (submitBtn) submitBtn.disabled = false;
        if (cancelBtn) cancelBtn.disabled = false;
        if (progressWrap) progressWrap.style.display = 'none';
      }
    } else {
      parsedCards.forEach(c => {
        this.cards.push(this.anki.createCard(c));
      });
    }

    this.saveData();
    this.renderDeckList();
    this.updateHeaderStats();

    alert(`🎉 成功匯入 ${parsedCards.length} 張單字卡片！${autoEnrich ? '已全數自動補全讀音、繁中翻譯與實用例句。' : ''}`);
    document.getElementById('batch-import-text').value = '';
    document.getElementById('modal-batch-import').classList.remove('open');
  }

  // ==========================================
  // 單張單字卡新增與一鍵自動生成 (Single Card)
  // ==========================================

  openAddCardModal() {
    const select = document.getElementById('add-card-deck-select');
    if (select) {
      select.innerHTML = '';
      this.decks.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.id;
        opt.innerText = d.name;
        select.appendChild(opt);
      });
      // 若當前有選牌組，預設選取當前牌組
      if (this.currentDeck) {
        select.value = this.currentDeck.id;
      }
    }

    document.getElementById('add-card-front').value = '';
    document.getElementById('add-card-reading').value = '';
    document.getElementById('add-card-back').value = '';
    document.getElementById('add-card-example').value = '';
    document.getElementById('add-card-tags').value = '';
    const loadingMsg = document.getElementById('add-card-loading-msg');
    if (loadingMsg) loadingMsg.style.display = 'none';

    // 監聽單字輸入框自動觸發 MOJi 辭書導入 (使用者輸入完成後自動載入)
    const frontInput = document.getElementById('add-card-front');
    if (frontInput && !frontInput.dataset.hasMojiListener) {
      frontInput.dataset.hasMojiListener = 'true';
      let debounceTimer = null;
      frontInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        const val = e.target.value.trim();
        const readingVal = document.getElementById('add-card-reading').value.trim();
        const backVal = document.getElementById('add-card-back').value.trim();
        
        // 若使用者已經自己填寫或單字太短，不自動覆蓋
        if (val.length >= 1 && !readingVal && !backVal) {
          debounceTimer = setTimeout(() => {
            this.importFromMojiDirect(false);
          }, 650);
        }
      });
    }

    document.getElementById('modal-add-card').classList.add('open');
  }

  /**
   * MOJi 辭書直接導入 (一鍵獲取讀音、音調、繁中釋義與權威例句)
   * @param {boolean} isManual 是否為使用者手動點擊按鈕
   */
  async importFromMojiDirect(isManual = true) {
    const wordInput = document.getElementById('add-card-front');
    const word = wordInput ? wordInput.value.trim() : '';

    if (!word) {
      if (isManual) alert('請先在上方輸入欲查詢的單字！');
      return;
    }

    const deckId = document.getElementById('add-card-deck-select').value;
    const deck = this.decks.find(d => d.id === deckId);
    const category = deck ? deck.category : 'engineering';

    const btn = document.getElementById('btn-auto-enrich-single');
    const mojiBtn = document.getElementById('btn-moji-import-single');
    const loadingMsg = document.getElementById('add-card-loading-msg');

    if (btn) btn.classList.add('loading');
    if (mojiBtn) mojiBtn.classList.add('loading');
    if (loadingMsg) {
      loadingMsg.style.display = 'block';
      loadingMsg.innerHTML = `📖 <strong>正在直接調用 MOJi 辭書</strong> 獲取【${word}】的官方讀音、繁中釋義與權威例句...`;
    }

    try {
      // 優先調用 MOJi 辭書專用提取方法
      let mojiData = null;
      if (this.enricher && typeof this.enricher.fetchMojiDict === 'function') {
        mojiData = await this.enricher.fetchMojiDict(word);
      }

      let result = null;
      if (mojiData && (mojiData.meaning || mojiData.reading)) {
        result = {
          front: word,
          reading: mojiData.reading || '',
          back: mojiData.meaning || '',
          example: mojiData.example || '',
          source: mojiData.source || 'MOJi 辭書',
          tags: [category, 'MOJi辭書']
        };
      } else {
        // 若直連未查到，透過通用擴充器 (含備用字典與翻譯)
        result = await this.enricher.enrichWord(word, { category });
      }

      if (result) {
        const readingEl = document.getElementById('add-card-reading');
        const backEl = document.getElementById('add-card-back');
        const exampleEl = document.getElementById('add-card-example');
        const tagsEl = document.getElementById('add-card-tags');

        if (result.reading && readingEl) readingEl.value = result.reading;
        if (result.back && backEl) backEl.value = result.back;
        if (result.example && exampleEl) exampleEl.value = result.example;
        if (result.tags && result.tags.length > 0 && tagsEl) {
          tagsEl.value = result.tags.join(' ');
        }

        // 閃爍高亮提示已成功導入
        [readingEl, backEl, exampleEl].forEach(el => {
          if (el) {
            el.classList.add('field-highlight-success');
            setTimeout(() => el.classList.remove('field-highlight-success'), 1200);
          }
        });

        if (loadingMsg) {
          const isMoji = (result.source && result.source.includes('MOJi'));
          loadingMsg.innerHTML = isMoji
            ? `✅ <strong>已成功自 MOJi 辭書直接導入！</strong>（讀音：${result.reading || '已填入'}）`
            : `✅ 已完成智慧補全（${result.source || '網路字典'}）`;
          setTimeout(() => {
            if (loadingMsg) loadingMsg.style.display = 'none';
          }, 3500);
        }
      } else if (isManual) {
        alert(`未在 MOJi 辭書或詞庫中找到「${word}」，請手動輸入。`);
      }
    } catch (e) {
      console.warn('MOJi 導入失敗:', e);
      if (isManual) alert('MOJi 辭書導入過程遭遇連線問題: ' + e.message);
    } finally {
      if (btn) btn.classList.remove('loading');
      if (mojiBtn) mojiBtn.classList.remove('loading');
    }
  }

  async autoEnrichSingleCard() {
    return this.importFromMojiDirect(true);
  }

  executeAddSingleCard() {
    const deckId = document.getElementById('add-card-deck-select').value;
    const front = document.getElementById('add-card-front').value.trim();
    const reading = document.getElementById('add-card-reading').value.trim();
    const back = document.getElementById('add-card-back').value.trim();
    const example = document.getElementById('add-card-example').value.trim();
    const tagsStr = document.getElementById('add-card-tags').value.trim();
    const tags = tagsStr ? tagsStr.split(/\s+/) : [];

    if (!front) {
      alert('請輸入單字內容！');
      return;
    }

    const newCard = this.anki.createCard({
      deckId,
      front,
      reading,
      back,
      example,
      tags
    });

    this.cards.push(newCard);
    this.saveData();
    this.renderDeckList();
    this.updateHeaderStats();

    alert(`✅ 已成功新增單字【${front}】！`);
    document.getElementById('modal-add-card').classList.remove('open');
  }


  importFromReaderNotes() {
    try {
      if (window.AnkiBridge) {
        const res = window.AnkiBridge.syncFromReaderNotebook();
        if (res.success) {
          this.loadData();
          this.renderDeckList();
          this.updateHeaderStats();
          alert(`🎉 已成功從日文閱讀助手同步匯入 ${res.addedCount} 筆新收藏生詞！(更新 ${res.updatedCount || 0} 筆)`);
          return;
        }
      }

      const rawNotes = localStorage.getItem('japanese_reader_notebook') || localStorage.getItem('saved_notes') || localStorage.getItem('japanese_notes');
      if (!rawNotes) {
        alert('未在日文閱讀助手中找到收藏筆記！\n請先在「日文閱讀助手」閱讀文章時點擊單字星號加入生詞。');
        return;
      }

      const parsed = JSON.parse(rawNotes);
      let wordsList = [];
      if (Array.isArray(parsed.words)) {
        wordsList = parsed.words;
      } else if (typeof parsed === 'object') {
        wordsList = Object.entries(parsed).map(([w, info]) => ({
          surface: w,
          reading: typeof info === 'object' ? (info.reading || info.kana || '') : '',
          meaning: typeof info === 'object' ? (info.meaning || info.def || '') : String(info)
        }));
      }

      let targetDeck = this.decks.find(d => d.id === 'deck_reader_notes');
      if (!targetDeck) {
        targetDeck = {
          id: 'deck_reader_notes',
          name: '📖 日文閱讀助手收藏生詞',
          desc: '從文章閱讀中星號收藏的生詞與句型',
          icon: '⭐',
          color: '#f59e0b'
        };
        this.decks.unshift(targetDeck);
      }

      let count = 0;
      wordsList.forEach(w => {
        const wordStr = (w.surface || w.baseForm || '').trim();
        if (!wordStr) return;
        const exists = this.cards.some(c => c.deckId === targetDeck.id && c.front === wordStr);
        if (!exists) {
          this.cards.push(this.anki.createCard({
            deckId: targetDeck.id,
            front: wordStr,
            reading: w.reading || '',
            back: (w.jlpt ? `[${w.jlpt}] ` : '') + (w.pos ? `(${w.pos}) ` : '') + (w.meaning || '閱讀生詞'),
            tags: ['閱讀收藏', w.jlpt || '未分級']
          }));
          count++;
        }
      });

      this.saveData();
      this.renderDeckList();
      this.updateHeaderStats();
      alert(`🎉 已成功從閱讀助手同步匯入 ${count} 筆收藏生詞！`);
    } catch (e) {
      alert('匯入生詞本失敗: ' + e.message);
    }
  }

  importFromKanjiDojo() {
    const cards = window.AnkiBridge ? window.AnkiBridge.getCards() : this.cards;
    const kanjiCardsCount = cards.filter(c => c.deckId === 'deck_kanji_dojo').length;
    if (kanjiCardsCount > 0) {
      alert(`目前「🈩 漢字道場」牌組內已有 ${kanjiCardsCount} 個漢字卡片！\n點擊牌組即可開始複習。\n若想新增更多漢字，可在「🈩 漢字道場」頁面勾選漢字後點擊「送至 AnkiFlash」！`);
      return;
    }

    if (confirm('目前尚未同步漢字道場。是否自動匯入 WaniKani 常用基礎漢字建立牌組？')) {
      const sampleKanji = [
        { front: '一', reading: '音：イチ ｜ 訓：ひと-', back: '【字義】一；一個\n【例詞】一つ（ひとつ）、一人（ひとり）', example: '一つ（ひとつ）', tags: ['漢字道場', 'Level_1'] },
        { front: '二', reading: '音：ニ ｜ 訓：ふた-', back: '【字義】二；兩個\n【例詞】二つ（ふたつ）、二人（ふたり）', example: '二つ（ふたつ）', tags: ['漢字道場', 'Level_1'] },
        { front: '三', reading: '音：サン ｜ 訓：み-', back: '【字義】三；三個\n【例詞】三つ（みっつ）、三日（みっか）', example: '三つ（みっつ）', tags: ['漢字道場', 'Level_1'] },
        { front: '人', reading: '音：ジン、ニン ｜ 訓：ひと', back: '【字義】人；人類\n【例詞】日本人（にほんじん）、大人（おとな）', example: '日本人（にほんじん）', tags: ['漢字道場', 'Level_1'] },
        { front: '日', reading: '音：ニチ、ジツ ｜ 訓：ひ、か', back: '【字義】太陽；日子；日本\n【例詞】日曜日（にちようび）、毎日（まいにち）', example: '日曜日（にちようび）', tags: ['漢字道場', 'Level_1'] },
        { front: '本', reading: '音：ホン ｜ 訓：もと', back: '【字義】書本；根本；基底\n【例詞】日本（にほん）、本（ほん）', example: '本（ほん）', tags: ['漢字道場', 'Level_1'] },
        { front: '大', reading: '音：ダイ、タイ ｜ 訓：おお-きい', back: '【字義】大；龐大\n【例詞】大学（だいがく）、大人（おとな）', example: '大学（だいがく）', tags: ['漢字道場', 'Level_1'] }
      ];
      if (window.AnkiBridge) {
        window.AnkiBridge.addCardsBatch(sampleKanji, {
          deckId: 'deck_kanji_dojo',
          deckName: '🈩 漢字記憶道場 (WaniKani)',
          deckIcon: '🈩',
          deckColor: '#059669'
        });
      }
      this.loadData();
      this.renderDeckList();
      this.updateHeaderStats();
      alert('🎉 已成功建立「🈩 漢字記憶道場」牌組！您也可以隨時切換至頂部「🈩 漢字道場」選取更多漢字一鍵匯入！');
    }
  }

  // 照片辨識代理方法
  openPhotoOcrModal() {
    if (this.photoOcr) {
      this.photoOcr.openModal();
    } else {
      alert('照片辨識模組載入中，請稍候...');
    }
  }

  handlePhotoSelect(files) {
    if (this.photoOcr) {
      this.photoOcr.handleFiles(files);
    }
  }

  startPhotoOcrScan() {
    if (this.photoOcr) {
      this.photoOcr.startScan();
    }
  }

  commitOcrResultsToDecks() {
    if (this.photoOcr) {
      this.photoOcr.commitImport();
    }
  }

  openNewDeckModal() {
    document.getElementById('new-deck-name').value = '';
    document.getElementById('new-deck-desc').value = '';
    const catSelect = document.getElementById('new-deck-category');
    const customGroup = document.getElementById('custom-category-group');
    if (catSelect) {
      catSelect.value = (this.currentCategory !== 'all') ? this.currentCategory : 'engineering';
      catSelect.onchange = () => {
        if (customGroup) {
          customGroup.style.display = (catSelect.value === 'custom') ? 'block' : 'none';
        }
      };
    }
    if (customGroup) customGroup.style.display = 'none';
    document.getElementById('modal-new-deck').classList.add('open');
  }

  executeCreateDeck() {
    const name = document.getElementById('new-deck-name').value.trim();
    const desc = document.getElementById('new-deck-desc').value.trim();
    const icon = document.getElementById('new-deck-icon').value.trim() || '📚';
    const catSelect = document.getElementById('new-deck-category');
    let category = catSelect ? catSelect.value : 'daily';
    let categoryName = '';

    if (category === 'custom') {
      const customInput = document.getElementById('new-deck-custom-cat');
      category = customInput ? customInput.value.trim() : '';
      if (!category) category = '自訂分類';
      categoryName = category;
    }

    if (!name) {
      alert('請輸入牌組名稱！');
      return;
    }

    const newDeck = {
      id: 'deck_' + Date.now(),
      name: name,
      desc: desc,
      category: category,
      categoryName: categoryName,
      icon: icon,
      color: '#6366f1'
    };

    this.decks.push(newDeck);
    this.saveData();
    this.renderCategoryTabs();
    this.renderDeckList();
    document.getElementById('modal-new-deck').classList.remove('open');
  }

  openDeckActionMenu(deckId) {
    const deck = this.decks.find(d => d.id === deckId);
    if (!deck) return;

    const action = prompt(`牌組選項：【${deck.name}】\n1: 📋 管理/查看此牌組單字列表 (可逐一刪除或查 MOJi 辭書)\n2: 💾 匯出為 Anki TSV 檔案\n3: 🗑️ 刪除整個牌組\n請輸入代號 (1, 2 或 3)：`);
    if (action === '1') {
      this.openDeckCardManager(deckId);
    } else if (action === '2') {
      const cards = this.cards.filter(c => c.deckId === deckId);
      this.sync.exportAnkiTsv(deck.name, cards);
    } else if (action === '3') {
      if (confirm(`確定要刪除牌組【${deck.name}】及其所有單字卡片嗎？此操作無法撤銷。`)) {
        this.decks = this.decks.filter(d => d.id !== deckId);
        this.cards = this.cards.filter(c => c.deckId !== deckId);
        this.saveData();
        this.renderCategoryTabs();
        this.renderDeckList();
        this.updateHeaderStats();
      }
    }
  }

  // ==========================================
  // MOJi 辭書聯動 (APP Deep Link & Web Fallback)
  // ==========================================

  openMojiDict(word) {
    if (!word || !word.trim()) return;
    const cleanWord = word.trim();
    const encoded = encodeURIComponent(cleanWord);
    const webUrl = `https://www.mojidict.com/search?text=${encoded}`;
    const appUrl = `mojidict://search?text=${encoded}`;

    // 判斷是否為手機/平板行動裝置 (iOS Safari / iPad / Android)
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    if (isMobile) {
      // 嘗試喚起 MOJi App，若未安裝或逾時則回退至 MOJi 網頁版
      const startTime = Date.now();
      window.location.href = appUrl;
      setTimeout(() => {
        if (Date.now() - startTime < 1600) {
          window.open(webUrl, '_blank');
        }
      }, 900);
    } else {
      // 電腦網頁端直接開啟新分頁
      window.open(webUrl, '_blank');
    }
  }

  // ==========================================
  // 單字刪除功能 (Delete Cards)
  // ==========================================

  deleteCurrentStudyCard() {
    if (this.currentCardIndex >= this.studyQueue.length) return;
    const currentCard = this.studyQueue[this.currentCardIndex];
    if (!currentCard) return;

    if (!confirm(`確定要刪除單字【${currentCard.front}】嗎？\n此單字將永久自牌組中移除。`)) {
      return;
    }

    // 從主卡片資料庫中刪除
    this.cards = this.cards.filter(c => c.id !== currentCard.id);
    // 從當前複習隊列中移除
    this.studyQueue.splice(this.currentCardIndex, 1);

    this.saveData();
    this.updateHeaderStats();

    alert(`🗑️ 已成功刪除單字【${currentCard.front}】！`);

    // 判斷是否還有下一張卡片
    if (this.studyQueue.length === 0 || this.currentCardIndex >= this.studyQueue.length) {
      if (this.studyQueue.length === 0) {
        this.renderStudyEmpty(false);
      } else {
        this.renderCurrentStudyCard();
      }
    } else {
      this.renderCurrentStudyCard();
    }
  }

  openDeckCardManager(deckId) {
    this.activeManagerDeckId = deckId;
    this.selectedCardIds = new Set();
    const deck = this.decks.find(d => d.id === deckId);
    if (!deck) return;

    const titleEl = document.getElementById('deck-cards-title');
    if (titleEl) {
      titleEl.innerText = `📋 【${deck.name}】單字管理與刪除`;
    }

    const searchInput = document.getElementById('deck-cards-search-input');
    if (searchInput) searchInput.value = '';

    // 綁定全選勾選框事件
    const selectAllBox = document.getElementById('deck-cards-select-all');
    if (selectAllBox && !selectAllBox.dataset.hasListener) {
      selectAllBox.dataset.hasListener = 'true';
      selectAllBox.addEventListener('change', (e) => {
        this.handleToggleSelectAll(e.target.checked);
      });
    }

    this.renderDeckCardsList(deckId);
    document.getElementById('modal-deck-cards').classList.add('open');
  }

  handleToggleSelectAll(isChecked) {
    const searchVal = document.getElementById('deck-cards-search-input')?.value || '';
    const deckCards = this.cards.filter(c => c.deckId === this.activeManagerDeckId);
    const q = searchVal.toLowerCase();
    const filtered = q
      ? deckCards.filter(c => 
          (c.front && c.front.toLowerCase().includes(q)) ||
          (c.reading && c.reading.toLowerCase().includes(q)) ||
          (c.back && c.back.toLowerCase().includes(q))
        )
      : deckCards;

    if (isChecked) {
      filtered.forEach(c => this.selectedCardIds.add(c.id));
    } else {
      filtered.forEach(c => this.selectedCardIds.delete(c.id));
    }

    this.renderDeckCardsList(this.activeManagerDeckId, searchVal);
  }

  updateBatchToolbar(displayedCards) {
    const selectedCount = this.selectedCardIds.size;
    const badge = document.getElementById('selected-count-badge');
    const deleteBtn = document.getElementById('btn-delete-selected-cards');
    const numSpan = document.getElementById('delete-selected-num');
    const selectAllBox = document.getElementById('deck-cards-select-all');
    const selectAllText = document.getElementById('select-all-text');

    if (numSpan) numSpan.innerText = selectedCount;
    if (deleteBtn) deleteBtn.disabled = selectedCount === 0;

    if (badge) {
      badge.style.display = selectedCount > 0 ? 'inline-block' : 'none';
      badge.innerText = `已選取 ${selectedCount} 張`;
    }

    if (selectAllBox && displayedCards.length > 0) {
      const allSelected = displayedCards.every(c => this.selectedCardIds.has(c.id));
      const someSelected = displayedCards.some(c => this.selectedCardIds.has(c.id));
      selectAllBox.checked = allSelected;
      selectAllBox.indeterminate = someSelected && !allSelected;
      if (selectAllText) {
        selectAllText.innerText = allSelected ? '取消全選' : `全選 (${displayedCards.length})`;
      }
    } else if (selectAllBox) {
      selectAllBox.checked = false;
      selectAllBox.indeterminate = false;
      if (selectAllText) selectAllText.innerText = '全選';
    }
  }

  renderDeckCardsList(deckId, filterQuery = '') {
    const container = document.getElementById('deck-cards-list-container');
    const countLabel = document.getElementById('deck-cards-count-label');
    if (!container) return;

    if (!this.selectedCardIds) this.selectedCardIds = new Set();

    const deckCards = this.cards.filter(c => c.deckId === deckId);
    const q = (filterQuery || '').toLowerCase();

    const filtered = q
      ? deckCards.filter(c => 
          (c.front && c.front.toLowerCase().includes(q)) ||
          (c.reading && c.reading.toLowerCase().includes(q)) ||
          (c.back && c.back.toLowerCase().includes(q))
        )
      : deckCards;

    if (countLabel) {
      countLabel.innerText = `共 ${deckCards.length} 個單字${q ? ` (符合篩選: ${filtered.length})` : ''}`;
    }

    this.updateBatchToolbar(filtered);
    container.innerHTML = '';

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 40px 10px; color: var(--text-muted); font-size: 0.9rem;">
          ${q ? '未找到符合搜尋的單字' : '此牌組內尚無單字'}
        </div>
      `;
      return;
    }

    filtered.forEach(card => {
      const isSelected = this.selectedCardIds.has(card.id);
      const item = document.createElement('div');
      item.className = `card-manager-item ${isSelected ? 'selected' : ''}`;
      item.dataset.cardId = card.id;

      item.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0;">
          <input type="checkbox" class="card-checkbox row-card-checkbox" ${isSelected ? 'checked' : ''} style="margin: 0;">
          <div class="card-item-main" style="cursor: pointer;">
            <div class="card-item-word">
              <span>${this.escapeHtml(card.front)}</span>
              ${card.reading ? `<span class="card-item-reading">[${this.escapeHtml(card.reading)}]</span>` : ''}
            </div>
            <div class="card-item-meaning">${this.escapeHtml(card.back || '無釋義')}</div>
          </div>
        </div>
        <div class="card-item-actions">
          <button class="moji-btn btn-open-card-moji" title="在 MOJi 辭書中查詢">
            <span>📖 MOJi</span>
          </button>
          <button class="delete-card-btn btn-del-single-card" title="刪除此單字">🗑️</button>
        </div>
      `;

      // 勾選框切換
      const checkbox = item.querySelector('.row-card-checkbox');
      const toggleSelect = () => {
        if (this.selectedCardIds.has(card.id)) {
          this.selectedCardIds.delete(card.id);
          item.classList.remove('selected');
          if (checkbox) checkbox.checked = false;
        } else {
          this.selectedCardIds.add(card.id);
          item.classList.add('selected');
          if (checkbox) checkbox.checked = true;
        }
        this.updateBatchToolbar(filtered);
      };

      checkbox.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleSelect();
      });

      item.querySelector('.card-item-main').addEventListener('click', (e) => {
        e.stopPropagation();
        toggleSelect();
      });

      item.querySelector('.btn-open-card-moji').addEventListener('click', (e) => {
        e.stopPropagation();
        this.openMojiDict(card.front);
      });

      item.querySelector('.btn-del-single-card').addEventListener('click', (e) => {
        e.stopPropagation();
        this.deleteCardById(card.id, deckId);
      });

      container.appendChild(item);
    });
  }

  deleteCardById(cardId, deckId) {
    const card = this.cards.find(c => c.id === cardId);
    if (!card) return;

    if (!confirm(`確定要刪除單字【${card.front}】嗎？`)) {
      return;
    }

    this.cards = this.cards.filter(c => c.id !== cardId);
    if (this.selectedCardIds) this.selectedCardIds.delete(cardId);
    this.saveData();

    // 更新管理器列表與主牌組清單
    const searchVal = document.getElementById('deck-cards-search-input')?.value || '';
    this.renderDeckCardsList(deckId, searchVal);
    this.renderDeckList();
    this.updateHeaderStats();
  }

  /**
   * 多選批次刪除 (Delete Selected Cards)
   */
  deleteSelectedCards() {
    if (!this.selectedCardIds || this.selectedCardIds.size === 0) {
      alert('請先勾選欲刪除的單字卡片！');
      return;
    }

    const count = this.selectedCardIds.size;
    if (!confirm(`確定要刪除選取的 ${count} 個單字嗎？\n刪除後無法還原！`)) {
      return;
    }

    // 從資料庫中移除所有選取的 ID
    this.cards = this.cards.filter(c => !this.selectedCardIds.has(c.id));
    this.selectedCardIds.clear();
    this.saveData();

    const searchVal = document.getElementById('deck-cards-search-input')?.value || '';
    this.renderDeckCardsList(this.activeManagerDeckId, searchVal);
    this.renderDeckList();
    this.updateHeaderStats();

    alert(`🗑️ 成功批次刪除 ${count} 個單字！`);
  }

  /**
   * 全選刪除 (清空此牌組全部卡片)
   */
  deleteAllCardsInCurrentDeck() {
    if (!this.activeManagerDeckId) return;
    const deck = this.decks.find(d => d.id === this.activeManagerDeckId);
    const deckCards = this.cards.filter(c => c.deckId === this.activeManagerDeckId);

    if (deckCards.length === 0) {
      alert('此牌組內已經沒有任何單字！');
      return;
    }

    const confirmMsg = `⚠️【危險操作警告】\n確定要刪除【${deck ? deck.name : '此牌組'}】內的「全部」${deckCards.length} 個單字嗎？\n\n此操作將清空該牌組的所有卡片且無法撤銷！`;
    if (!confirm(confirmMsg)) {
      return;
    }

    // 第二次防呆確認
    if (!confirm(`請再次確認：您真的要永久清空【${deck ? deck.name : '此牌組'}】共 ${deckCards.length} 個單字嗎？`)) {
      return;
    }

    this.cards = this.cards.filter(c => c.deckId !== this.activeManagerDeckId);
    if (this.selectedCardIds) this.selectedCardIds.clear();
    this.saveData();

    const searchVal = document.getElementById('deck-cards-search-input')?.value || '';
    this.renderDeckCardsList(this.activeManagerDeckId, searchVal);
    this.renderDeckList();
    this.updateHeaderStats();

    alert(`🗑️ 已成功清空【${deck ? deck.name : ''}】牌組內的所有單字卡片！`);
  }


  // ==========================================
  // 設定 (Settings Modal)
  // ==========================================

  openSettingsModal() {
    document.getElementById('setting-auto-audio').checked = this.settings.autoPlayAudio !== false;
    document.getElementById('setting-audio-lang').value = this.settings.audioLang || 'ja-JP';
    document.getElementById('setting-theme-select').value = this.settings.theme || 'dark';
    document.getElementById('setting-new-limit').value = this.settings.dailyNewLimit || 20;
    document.getElementById('setting-review-limit').value = this.settings.dailyReviewLimit || 100;
    const geminiInput = document.getElementById('setting-gemini-key');
    if (geminiInput) geminiInput.value = this.settings.geminiApiKey || '';
    document.getElementById('modal-settings').classList.add('open');
  }

  saveSettingsFromModal() {
    this.settings.autoPlayAudio = document.getElementById('setting-auto-audio').checked;
    this.settings.audioLang = document.getElementById('setting-audio-lang').value;
    this.settings.theme = document.getElementById('setting-theme-select').value;
    this.settings.dailyNewLimit = parseInt(document.getElementById('setting-new-limit').value) || 20;
    this.settings.dailyReviewLimit = parseInt(document.getElementById('setting-review-limit').value) || 100;
    const geminiInput = document.getElementById('setting-gemini-key');
    if (geminiInput) this.settings.geminiApiKey = geminiInput.value.trim();

    if (this.enricher) {
      this.enricher.settings = this.settings;
    }

    this.applyTheme();
    this.saveData();
    document.getElementById('modal-settings').classList.remove('open');
  }

  // ==========================================
  // PWA 與 iOS 安裝導引
  // ==========================================

  initPwaBanner() {
    const isIos = /iPad|iPhone|iPod/.test(navigator.userAgent || '') && !window.MSStream;
    const isStandalone = !!(window.navigator && window.navigator.standalone) || (typeof window.matchMedia === 'function' && window.matchMedia('(display-mode: standalone)')?.matches);

    // 若在 iOS 且非全螢幕 standalone，提示用戶加入主畫面
    const banner = document.getElementById('ios-pwa-banner');
    if (isIos && !isStandalone && banner) {
      banner.style.display = 'flex';
      document.getElementById('close-pwa-banner').onclick = () => {
        banner.style.display = 'none';
      };
    }

    // 註冊 Service Worker
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('sw.js').then(reg => {
          console.log('[PWA] Service Worker 註冊成功, scope:', reg.scope);
        }).catch(err => {
          console.warn('[PWA] Service Worker 註冊失敗:', err);
        });
      });
    }
  }

  escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag));
  }
}

if (typeof window !== 'undefined') window.FlashcardApp = FlashcardApp;
if (typeof globalThis !== 'undefined') globalThis.FlashcardApp = FlashcardApp;

// 啟動全域實例（避免 DOMContentLoaded 競態條件）
function startApp() {
  if (!window.app) {
    try {
      window.app = new FlashcardApp();
    } catch (e) {
      console.error('[AnkiFlash] 啟動失敗:', e);
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', startApp);
} else {
  startApp();
}
