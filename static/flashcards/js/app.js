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
    // Remove only the retired AI credential; preserve decks, history and other settings.
    if (Object.prototype.hasOwnProperty.call(this.settings, 'geminiApiKey')) {
      delete this.settings.geminiApiKey;
      this.sync.saveLocalData({settings: this.settings});
    }
    this.logs = data.logs || {};

    if (Array.isArray(data.decks)) {
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
    if (viewId !== 'view-study') this.stopAudio();
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
    const target = document.getElementById(viewId);
    if (target) target.classList.add('active');

    // 視圖特定處理
    if (viewId === 'view-decks') {
      this.currentCategory = 'all';
      this.renderCategoryTabs();
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
      if (c.reviewMode === 'manual') return;
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
      'moji': '📖 MOJi 學習',
      'engineering': '🏗️ 工程營造',
      'daily': '🍵 日常生活',
      'business': '💼 商務職場',
      'jlpt': '🇯🇵 JLPT 檢定'
    };
    return map[categoryId] || (categoryId ? `🏷️ ${categoryId}` : '未分類');
  }

  getDeckFamilies() {
    // Present legacy sequential groups together without rewriting any card or deck IDs.
    const families = [];
    let previous = null;
    this.decks.forEach(deck => {
      const match = deck.name.match(/^(.*)（(\d+)\/(\d+)）$/);
      const part = match && Number(match[3]) > 1 ? {base: match[1], index: Number(match[2]), total: Number(match[3])} : null;
      if (part && previous && previous.base === part.base && previous.total === part.total && previous.category === deck.category && part.index > previous.lastIndex) {
        previous.sourceIds.push(deck.id);
        previous.lastIndex = part.index;
        previous.name = part.base;
      } else {
        previous = {id: deck.id, name: deck.name, category: deck.category, sourceIds: [deck.id], reviewGroupSize: deck.reviewGroupSize, base: part?.base, total: part?.total, lastIndex: part?.index};
        families.push(previous);
        if (!part) previous = null;
      }
    });
    return families;
  }

  getFamilyCards(family) {
    const ids = new Set(family?.sourceIds || []);
    return this.cards.filter(card => ids.has(card.deckId));
  }

  renderDeckList() {
    const container = document.getElementById('decks-grid-container');
    if (!container) return;
    this.selectedFamilyIds ||= new Set();
    const families = this.getDeckFamilies();
    document.getElementById('btn-manual-review').textContent = `手動複習（${this.cards.filter(c => c.reviewMode === 'manual').length}）`;
    this.renderCategoryTabs();
    const query = document.getElementById('family-search').value.trim().toLowerCase();
    const filtered = families.filter(f => (this.currentCategory === 'all' || f.category === this.currentCategory) && f.name.toLowerCase().includes(query));
    const pages = Math.max(1, Math.ceil(filtered.length / 12));
    this.deckPage = Math.max(0, Math.min(this.deckPage || 0, pages - 1));
    document.getElementById('deck-page-prev').disabled = this.deckPage === 0;
    document.getElementById('deck-page-next').disabled = this.deckPage === pages - 1;
    document.getElementById('deck-page-label').textContent = `${this.deckPage + 1} / ${pages} 頁`;
    document.getElementById('deck-list-summary').textContent = `共 ${families.length} 個來源牌組、${this.cards.length} 張單字卡；符合搜尋 ${filtered.length} 個。`;
    container.replaceChildren();
    const table = document.createElement('table');
    table.className = 'deck-overview';
    table.innerHTML = '<thead><tr><th scope="col"><input type="checkbox" class="family-select-all" aria-label="全選符合搜尋牌組"></th><th scope="col">來源牌組</th><th scope="col">單字數</th><th scope="col">操作</th></tr></thead><tbody></tbody>';
    const all = table.querySelector('.family-select-all');
    all.checked = !!filtered.length && filtered.every(f => this.selectedFamilyIds.has(f.id));
    all.indeterminate = !all.checked && filtered.some(f => this.selectedFamilyIds.has(f.id));
    all.onchange = () => {filtered.forEach(f => all.checked ? this.selectedFamilyIds.add(f.id) : this.selectedFamilyIds.delete(f.id)); this.renderDeckList();};
    filtered.slice(this.deckPage * 12, this.deckPage * 12 + 12).forEach(family => {
      const row = document.createElement('tr');
      row.dataset.deckId = family.id;
      row.innerHTML = `<td><input type="checkbox" class="family-checkbox" aria-label="選取 ${this.escapeHtml(family.name)}" ${this.selectedFamilyIds.has(family.id) ? 'checked' : ''}></td>
        <td><strong>${this.escapeHtml(family.name)}</strong><small>${this.escapeHtml(this.getCategoryLabel(family.category))}</small></td>
        <td>${this.getFamilyCards(family).length}</td><td><div class="deck-row-actions"><button class="btn-primary btn-open-groups">進入牌組</button><button class="btn-secondary btn-deck-cards">單字一覽</button></div></td>`;
      row.querySelector('.family-checkbox').onchange = e => {e.target.checked ? this.selectedFamilyIds.add(family.id) : this.selectedFamilyIds.delete(family.id); this.renderDeckList();};
      row.querySelector('.btn-open-groups').onclick = () => this.openFamilyGroups(family.id);
      row.querySelector('.btn-deck-cards').onclick = () => this.openDeckCardManager(family.id);
      table.querySelector('tbody').append(row);
    });
    container.append(table);
    const selectedCount = families.filter(f => this.selectedFamilyIds.has(f.id)).length;
    document.getElementById('btn-delete-families').disabled = !selectedCount;
    document.getElementById('btn-delete-families').textContent = `刪除勾選牌組（${selectedCount}）`;
  }

  deleteSelectedFamilies() {
    const families = this.getDeckFamilies().filter(f => this.selectedFamilyIds?.has(f.id));
    if (!families.length) return;
    const ids = new Set(families.flatMap(f => f.sourceIds));
    const count = this.cards.filter(c => ids.has(c.deckId)).length;
    if (!confirm(`確定刪除勾選的 ${families.length} 個牌組及其中 ${count} 個單字？此操作無法撤銷。`)) return;
    if (this.persistDeckChanges(this.decks.filter(d => !ids.has(d.id)), this.cards.filter(c => !ids.has(c.deckId)), false)) {
      this.selectedFamilyIds.clear();
      this.renderDeckList(); this.updateHeaderStats();
    }
  }

  getReviewGroups() {
    const family = this.getDeckFamilies().find(f => f.id === this.activeFamilyId);
    if (!family) return [];
    const size = Math.max(1, Number(family.reviewGroupSize) || 20);
    const cards = this.getFamilyCards(family);
    const groups = [];
    for (let i = 0; i < cards.length; i += size) groups.push(cards.slice(i, i + size));
    return groups;
  }

  openFamilyGroups(familyId, index = 0) {
    const family = this.getDeckFamilies().find(f => f.id === familyId);
    if (!family) return;
    this.activeFamilyId = familyId;
    this.activeGroupIndex = index;
    this.selectedGroupIndices = new Set();
    document.getElementById('review-group-size').value = family.reviewGroupSize || 20;
    document.getElementById('group-status').textContent = '';
    document.getElementById('group-display-mode').value = 'current';
    document.getElementById('group-expand-all').checked = false;
    this.showView('view-groups'); this.renderGroupList();
  }

  applyGroupSize() {
    const input = document.getElementById('review-group-size');
    const size = Number(input.value);
    if (!Number.isInteger(size) || size < 1 || size > 1000) { document.getElementById('group-status').textContent = '請輸入 1～1000 的整數。'; return; }
    const decks = this.decks.map(d => d.id === this.activeFamilyId ? {...d, reviewGroupSize: size} : d);
    if (!this.persistDeckChanges(decks, this.cards, false)) return;
    this.selectedGroupIndices.clear(); this.activeGroupIndex = 0;
    this.renderGroupList();
    document.getElementById('group-status').textContent = `已改為每組 ${size} 個單字，單字與學習紀錄保留。`;
  }

  renderGroupList() {
    const family = this.getDeckFamilies().find(f => f.id === this.activeFamilyId);
    if (!family) { this.showView('view-decks'); return; }
    const groups = this.getReviewGroups();
    this.activeGroupIndex = Math.max(0, Math.min(this.activeGroupIndex || 0, groups.length - 1));
    document.getElementById('group-family-title').textContent = family.name;
    document.getElementById('group-counter').textContent = groups.length ? `第 ${this.activeGroupIndex + 1} / ${groups.length} 組` : '此牌組尚無單字';
    document.getElementById('group-prev').disabled = !groups.length || this.activeGroupIndex === 0;
    document.getElementById('group-next').disabled = this.activeGroupIndex >= groups.length - 1;
    const all = document.getElementById('groups-select-all');
    all.checked = !!groups.length && this.selectedGroupIndices.size === groups.length;
    all.indeterminate = !!this.selectedGroupIndices.size && !all.checked;
    document.getElementById('btn-delete-groups').disabled = !this.selectedGroupIndices.size;
    document.getElementById('btn-delete-groups').textContent = `刪除勾選小組（${this.selectedGroupIndices.size}）`;
    const table = document.createElement('table'); table.className = 'deck-overview group-overview';
    table.innerHTML = '<thead><tr><th scope="col">選取</th><th scope="col">小組與內容</th><th scope="col">操作</th></tr></thead><tbody></tbody>';
    const showAll = document.getElementById('group-display-mode').value === 'all';
    groups.forEach((cards, i) => {
      if (!showAll && i !== this.activeGroupIndex) return;
      const row = document.createElement('tr'); row.dataset.groupIndex = i;
      row.innerHTML = `<td><input type="checkbox" class="group-checkbox" aria-label="選取第 ${i+1} 組" ${this.selectedGroupIndices.has(i) ? 'checked' : ''}></td>
        <td><details class="group-preview" ${document.getElementById('group-expand-all').checked ? 'open' : ''}><summary>第 ${i+1} 組 · ${cards.length} 個單字</summary><div class="group-words"></div></details></td>
        <td><div class="deck-row-actions"><button class="btn-primary btn-browse-group">開始瀏覽</button><button class="btn-secondary btn-schedule-group">Anki 複習</button><button class="btn-secondary btn-group-words">單字一覽</button></div></td>`;
      const preview = row.querySelector('.group-words');
      cards.forEach(card => {const entry = document.createElement('p'); entry.textContent = `${card.front}　${card.reading || ''}\n${card.back || ''}`; preview.append(entry);});
      row.querySelector('.group-checkbox').onchange = e => {e.target.checked ? this.selectedGroupIndices.add(i) : this.selectedGroupIndices.delete(i); this.renderGroupList();};
      row.querySelector('.btn-browse-group').onclick = () => this.startGroupStudy(i, true);
      row.querySelector('.btn-schedule-group').onclick = () => this.startGroupStudy(i, false);
      row.querySelector('.btn-group-words').onclick = () => this.openDeckCardManager(family.id, 'all', cards.map(c => c.id));
      table.querySelector('tbody').append(row);
    });
    document.getElementById('group-list').replaceChildren(table);
  }

  moveGroup(direction) {
    this.activeGroupIndex = Math.max(0, Math.min(this.activeGroupIndex + direction, this.getReviewGroups().length - 1));
    this.renderGroupList();
  }

  selectAllGroups(checked) {
    this.selectedGroupIndices = checked ? new Set(this.getReviewGroups().map((_, i) => i)) : new Set();
    this.renderGroupList();
  }

  deleteSelectedGroups() {
    const groups = this.getReviewGroups();
    const ids = new Set([...this.selectedGroupIndices].flatMap(i => (groups[i] || []).map(c => c.id)));
    if (!ids.size) return;
    if (!confirm(`確定刪除勾選的 ${this.selectedGroupIndices.size} 個小組，共 ${ids.size} 個單字？包含其中的手動複習單字，其他單字保留。此操作無法撤銷。`)) return;
    if (!this.persistDeckChanges(this.decks, this.cards.filter(c => !ids.has(c.id)), false)) return;
    this.selectedGroupIndices.clear(); this.activeGroupIndex = 0; this.renderGroupList(); this.updateHeaderStats();
    document.getElementById('group-status').textContent = `已刪除 ${ids.size} 個單字；剩餘單字依設定重新分組。`;
  }

  startGroupStudy(index, browseAll = true) {
    const family = this.getDeckFamilies().find(f => f.id === this.activeFamilyId);
    const cards = this.getReviewGroups()[index];
    if (!family || !cards) return;
    this.activeGroupIndex = index;
    this.startStudy(null, browseAll, cards, `${family.name} · 第 ${index + 1} 組`, {familyId: family.id, index});
  }

  moveStudyGroup(direction) {
    if (!this.studyGroupContext) return;
    this.activeFamilyId = this.studyGroupContext.familyId;
    const index = this.studyGroupContext.index + direction;
    if (index >= 0 && index < this.getReviewGroups().length) this.startGroupStudy(index, this.browseAll);
  }

  // ==========================================
  // 抽認卡複習模式 (Study Mode)
  // ==========================================

  startStudy(deckId, browseAll = false, manualCards = null, title = '手動複習', groupContext = null) {
    this.studyGroupContext = groupContext;
    document.getElementById('study-group-controls').hidden = !groupContext;
    if (groupContext) {
      document.getElementById('study-prev-group').disabled = groupContext.index === 0;
      document.getElementById('study-next-group').disabled = groupContext.index >= this.getReviewGroups().length - 1;
    }
    this.browseAll = browseAll;
    this.currentDeck = manualCards ? {id: 'custom-review', name: title} : this.decks.find(d => d.id === deckId);
    if (!this.currentDeck) return;

    const deckCards = manualCards || this.cards.filter(c => c.deckId === deckId);
    const now = Date.now();
    const queueObj = this.anki.getStudyQueue(deckCards, now, {
      dailyNewLimit: groupContext ? deckCards.length : this.settings.dailyNewLimit,
      dailyReviewLimit: groupContext ? deckCards.length : this.settings.dailyReviewLimit
    });

    this.studyQueue = browseAll ? deckCards.slice() : queueObj.queue;
    this.currentCardIndex = 0;
    this.isCardFlipped = false;

    // 設定標題
    document.getElementById('study-deck-name').innerText = this.currentDeck.name + (browseAll ? ' · 瀏覽全部' : ' · 排程複習');
    document.getElementById('study-navigation-help').textContent = browseAll
      ? '瀏覽全部：不受每日上限限制。← → 切換，空白鍵看答案，不評分。'
      : '← → 切換不評分。只有按重來／困難／良好／簡單才會更新複習進度。';
    document.querySelector('.card-back .card-footer-tip').textContent = browseAll
      ? '使用上一張／下一張按鈕或鍵盤 ← → 自由切換'
      : '👈 左滑重來 ｜ 右滑良好 👉';

    if (this.studyQueue.length === 0) {
      this.renderStudyEmpty(true);
    } else {
      this.showView('view-study');
      this.renderCurrentStudyCard();
    }
  }

  updateStudyNavigation() {
    document.getElementById('btn-prev-card').disabled = !this.studyQueue.length || this.currentCardIndex <= 0;
    document.getElementById('btn-next-card').disabled = this.currentCardIndex >= this.studyQueue.length - 1;
  }

  moveStudyCard(direction) {
    const target = this.currentCardIndex + direction;
    if (target < 0 || target >= this.studyQueue.length) return;
    this.currentCardIndex = target;
    this.renderCurrentStudyCard();
  }

  renderCurrentStudyCard() {
    this.updateStudyNavigation();
    if (this.currentCardIndex >= this.studyQueue.length) {
      this.renderStudyEmpty(false);
      return;
    }

    document.getElementById('study-empty-message').hidden = true;
    document.getElementById('card-scene-container').style.display = '';
    document.getElementById('study-actions-container').style.display = '';
    const queued = this.studyQueue[this.currentCardIndex];
    const card = this.cards.find(c => c.id === queued.id) || queued;
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
    document.getElementById('study-reading-input').value = card.reading || '';
    document.getElementById('reading-editor').open = false;
    document.querySelector('.card-back').scrollTop = 0;
    document.getElementById('reading-save-status').textContent = '優先朗讀這裡的假名；留空時由裝置判讀原文。';
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

    if (this.continuousAudio) this.speakStudyCard();
    else this.cancelCurrentSpeech();
    this.updateAudioControls();
  }

  flipCard() {
    if (this.currentCardIndex >= this.studyQueue.length) return;
    if (this.isCardFlipped) return;
    this.isCardFlipped = true;

    const cardEl = document.getElementById('active-flashcard');
    cardEl.classList.add('is-flipped');

    document.getElementById('show-answer-btn').style.display = 'none';
    document.getElementById('anki-buttons-row').classList.toggle('visible', !this.browseAll);

    // 若正面沒發音或設定發音，翻面可點發音
    if (this.settings.vibration && navigator.vibrate) {
      navigator.vibrate(15);
    }
  }

  handleRate(rating) {
    if (this.browseAll) return;
    if (this.currentCardIndex >= this.studyQueue.length) return;
    const currentCard = this.cards.find(c => c.id === this.studyQueue[this.currentCardIndex].id);
    if (!currentCard) return;
    if (currentCard.reviewMode === 'manual') return;
    const now = Date.now();

    // 透過 SM-2 核心計算新數值
    const updatedCard = this.anki.rateCard(currentCard, rating, now);

    // 更新到主 cards 庫存
    const idx = this.cards.findIndex(c => c.id === currentCard.id);
    if (idx !== -1) {
      this.cards[idx] = updatedCard;
    }
    this.studyQueue = this.studyQueue.map(c => c.id === updatedCard.id ? updatedCard : c);

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
    this.stopAudio();
    this.showView('view-study');
    this.isCardFlipped = false;
    this.updateStudyNavigation();
    const scene = document.getElementById('card-scene-container');
    const message = document.getElementById('study-empty-message');
    const actions = document.getElementById('study-actions-container');

    if (scene) scene.style.display = 'none';
    if (message) {
      message.hidden = false;
      message.innerHTML = `
        <div style="text-align: center; padding: 60px 20px; background: var(--bg-card); border-radius: 24px; border: 1.5px solid var(--border-color); max-width: 600px; margin: 0 auto;">
          <div style="font-size: 3.5rem; margin-bottom: 16px;">🎉</div>
          <h2 style="font-size: 1.5rem; margin-bottom: 8px; color: var(--text-primary);">
            ${this.browseAll ? '此牌組目前沒有卡片' : isInitiallyEmpty ? '目前沒有排程內的待複習卡片' : '已到本輪最後一張'}
          </h2>
          <p style="color: var(--text-secondary); margin-bottom: 24px; font-size: 0.95rem;">
            可以返回列表選擇「瀏覽全部」，或按上一張回看。只有評分的卡片會更新排程。
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

  kanaReading(value) {
    const reading = String(value || '').normalize('NFKC').trim().replace(/^[[(【]\s*|\s*[\])】]$/g, '');
    return /^[ぁ-ゖゝ-ゟァ-ヺヽ-ヿー\s・]+$/u.test(reading) ? reading : '';
  }

  currentStudyCard() {
    const queued = this.studyQueue[this.currentCardIndex];
    return queued && (this.cards.find(card => card.id === queued.id) || queued);
  }

  speakStudyCard(event = null) {
    const card = this.currentStudyCard();
    if (!card) return;
    const kana = /[一-龯々ぁ-ゖァ-ヺ]/u.test(card.front) ? this.kanaReading(card.reading) : '';
    this.speakText(kana || card.front, kana ? 'ja-JP' : null, event);
  }

  saveStudyReading() {
    this.stopAudio();
    const card = this.currentStudyCard();
    if (!card) return;
    const input = document.getElementById('study-reading-input').value.trim();
    const reading = this.kanaReading(input);
    const status = document.getElementById('reading-save-status');
    if (input && !reading) { status.textContent = '請填入一種正確的平假名或片假名讀音，不要填漢字或多個候選讀音。'; return; }
    card.reading = reading;
    this.studyQueue = this.studyQueue.map(item => item.id === card.id ? {...item, reading} : item);
    this.saveData();
    document.getElementById('card-back-reading').textContent = reading ? `[${reading}]` : '';
    document.getElementById('study-reading-input').value = reading;
    status.textContent = reading ? '已儲存。按喇叭可試聽；這張卡之後會優先使用此假名。' : '已清除指定讀音，之後由裝置判讀原文。';
  }

  speakText(text, lang = null, event = null) {
    const single = event?.isTrusted && event.currentTarget?.classList.contains('audio-btn');
    if (single) this.stopAudio();
    if (!single && !this.continuousAudio) return;
    if (!window.speechSynthesis || !text) return;
    try {
      this.cancelCurrentSpeech();
      const generation = this.audioGeneration;
      const utterance = new SpeechSynthesisUtterance(text);

      const targetLang = lang || this.settings.audioLang || 'ja-JP';
      utterance.lang = targetLang;
      utterance.rate = 0.9; // 略微放慢語速，方便聽清

      // 視覺回饋
      const audioBtns = document.querySelectorAll('.audio-btn');
      audioBtns.forEach(btn => btn.classList.add('playing'));
      utterance.onend = () => {
        if (generation !== this.audioGeneration) return;
        audioBtns.forEach(btn => btn.classList.remove('playing'));
        if (this.continuousAudio && document.getElementById('audio-auto-next').checked) {
          const reveal = document.getElementById('audio-reveal-answer').checked;
          if (reveal) this.flipCard();
          const delay = reveal ? Number(document.getElementById('audio-answer-delay').value) * 1000 : 500;
          if (this.currentCardIndex >= this.studyQueue.length - 1) {
            this.stopAudio();
            document.getElementById('study-audio-status').textContent = '本組朗讀完畢，已停止。';
          } else {
            this.audioNextTimer = setTimeout(() => {
              if (generation === this.audioGeneration && this.continuousAudio) this.moveStudyCard(1);
            }, delay);
          }
        }
      };
      utterance.onerror = error => {
        if (generation !== this.audioGeneration) return;
        this.stopAudio();
        if (!['canceled', 'interrupted'].includes(error.error)) document.getElementById('study-audio-status').textContent = '發音未成功，請再按一次或檢查裝置語音設定。';
      };

      window.flashcardAudio?.speak(utterance, event);
    } catch (e) {
      this.stopAudio();
      console.warn('語音合成暫時不可用:', e);
    }
  }

  cancelCurrentSpeech() {
    this.audioGeneration = (this.audioGeneration || 0) + 1;
    clearTimeout(this.audioNextTimer);
    window.speechSynthesis?.cancel();
    document.querySelectorAll('.audio-btn').forEach(button => button.classList.remove('playing'));
  }

  stopAudio() {
    this.continuousAudio = false;
    this.cancelCurrentSpeech();
    window.flashcardAudio?.stop();
    this.updateAudioControls();
  }

  updateAudioControls() {
    const button = document.getElementById('btn-audio-continuous');
    if (!button) return;
    button.textContent = this.continuousAudio ? '⏸ 關閉連續發音' : '▶ 開啟連續發音';
    button.setAttribute('aria-pressed', String(!!this.continuousAudio));
    button.disabled = !window.flashcardAudio || !this.studyQueue.length || this.currentCardIndex >= this.studyQueue.length;
    document.getElementById('btn-audio-single').disabled = button.disabled;
    document.getElementById('study-audio-status').textContent = !window.flashcardAudio ? '此瀏覽器不支援語音朗讀。' : this.continuousAudio
      ? (document.getElementById('audio-auto-next').checked ? (document.getElementById('audio-reveal-answer').checked ? '讀完翻面看中文，停留後換張；不評分，本組結束即停止。' : '讀完自動下一張；不評分，本組結束即停止。') : '連續發音已開啟：切換單字時會朗讀。')
      : '連續發音已關閉；可按單次發音。';
  }

  toggleContinuousAudio(event) {
    if (this.continuousAudio) { this.stopAudio(); return; }
    const card = this.studyQueue[this.currentCardIndex];
    if (!card || !window.flashcardAudio?.enable(event)) return;
    this.continuousAudio = true;
    this.updateAudioControls();
    this.speakStudyCard();
  }

  // ==========================================
  // 觸控手勢與鍵盤快速鍵
  // ==========================================

  setupKeyboardShortcuts() {
    window.addEventListener('keydown', (e) => {
      const activeView = document.querySelector('.view-section.active');
      if (!activeView || activeView.id !== 'view-study') return;

      // 若在輸入框內則不攔截
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName) || e.target.isContentEditable || document.querySelector('.modal-backdrop.open')) return;
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        e.preventDefault();
        this.moveStudyCard(e.key === 'ArrowLeft' ? -1 : 1);
        return;
      }

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
        if (this.browseAll) {
          this.moveStudyCard(diffX < 0 ? 1 : -1);
        } else if (this.isCardFlipped) {
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
    document.getElementById('btn-audio-continuous').addEventListener('click', e => this.toggleContinuousAudio(e));
    document.getElementById('btn-audio-stop').addEventListener('click', () => this.stopAudio());
    document.getElementById('reading-editor').querySelector('summary').addEventListener('click', () => this.stopAudio());
    document.getElementById('btn-save-reading').addEventListener('click', e => {e.stopPropagation(); this.saveStudyReading();});
    for (const id of ['audio-reveal-answer', 'audio-answer-delay']) {
      document.getElementById(id).addEventListener('change', () => {
        this.updateAudioControls();
        if (this.continuousAudio) this.speakStudyCard();
      });
    }
    document.getElementById('btn-audio-single').addEventListener('click', e => this.speakStudyCard(e));
    document.getElementById('audio-auto-next').addEventListener('change', () => {
      this.updateAudioControls();
      if (this.continuousAudio) this.speakStudyCard();
    });
    document.addEventListener('visibilitychange', () => { if (document.hidden) this.stopAudio(); });
    window.addEventListener('pagehide', () => this.stopAudio());
    document.getElementById('btn-prev-card').addEventListener('click', () => this.moveStudyCard(-1));
    document.getElementById('btn-next-card').addEventListener('click', () => this.moveStudyCard(1));
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
      this.speakStudyCard(e);
    });

    document.getElementById('btn-speak-back').addEventListener('click', (e) => {
      e.stopPropagation();
      this.speakStudyCard(e);
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
        if (document.getElementById('modal-deck-cards').classList.contains('open')) {
          this.managerVisibleLimit = 100;
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

    document.getElementById('sync-auto-start').checked = !!this.settings.autoSyncOnStart;
    document.getElementById('modal-sync').classList.add('open');
  }

  syncSnapshot() {
    return JSON.parse(JSON.stringify({decks: this.decks, cards: this.cards, logs: this.logs}));
  }

  async uploadToCloud() { return this.syncCloud('sync'); }
  async downloadFromCloud() { return this.syncCloud('download'); }
  async autoSyncCloud() { return this.syncCloud('sync', true); }

  async syncCloud(mode = 'sync', automatic = false) {
    if (this.syncBusy) return;
    const status = document.getElementById('sync-status-msg');
    const token = automatic ? this.settings.githubToken : document.getElementById('sync-github-token').value.trim();
    let gistId = automatic ? this.settings.gistId : document.getElementById('sync-gist-id').value.trim();
    const show = message => { status.textContent = message; document.getElementById('sync-summary').textContent = message; };
    if (!token) { show('請先設定自己的 GitHub Token，或使用下方 JSON 檔案移轉。'); return; }
    if (document.getElementById('view-study').classList.contains('active')) { show('請先返回牌組列表，再同步資料。'); return; }
    this.syncBusy = true;
    const buttons = document.querySelectorAll('#modal-sync button, #modal-sync input');
    buttons.forEach(b => b.disabled = true);
    show('正在比對本機與雲端資料…');
    try {
      const local = this.syncSnapshot();
      const localHash = await this.sync.fingerprint(local);
      let remote = null, remoteHash = null, direction = 'upload';
      if (gistId) {
        remote = await this.sync.downloadFromGist(token, gistId);
        remoteHash = await this.sync.fingerprint(remote);
        const base = this.settings.syncBase?.gistId === gistId ? this.settings.syncBase.hash : null;
        direction = this.sync.syncDirection(localHash, remoteHash, base);
        if (mode === 'download') direction = 'download';
        if (mode === 'overwrite') direction = 'upload';
        if (direction === 'conflict') {
          show('⚠️ 首次連接或兩端都有變更。請先匯出備份，再於「選擇資料來源」決定保留本機或雲端；目前未覆蓋任何資料。');
          document.getElementById('sync-resolution').open = true;
          return;
        }
        if (!automatic && (mode === 'download' || mode === 'overwrite') && localHash !== remoteHash) {
          const source = direction === 'upload' ? '本機' : '雲端';
          if (!confirm('本機：' + local.decks.length + ' 個牌組／' + local.cards.length + ' 張卡；雲端：' + remote.decks.length + ' 個牌組／' + remote.cards.length + ' 張卡。\n以' + source + '為準將取代另一份資料（不合併）。覆蓋前會保留兩份復原備份。確定繼續？')) { show('已取消，資料未變更。'); return; }
        }
      } else {
        if (automatic || mode === 'download') { show('請先填入 A 裝置建立的 Gist ID。'); return; }
        if (!confirm('將把本機牌組及進度上傳到你自己的 GitHub Secret Gist。知道 Gist 網址的人可以讀取內容，請勿放入個資或機密教材。確定建立？')) { show('已取消建立。'); return; }
      }
      // Do not replace edits made during a slow request or by a second tab.
      const stored = this.sync.loadLocalData();
      if (await this.sync.fingerprint(this.syncSnapshot()) !== localHash ||
          await this.sync.fingerprint(stored) !== localHash) throw new Error('同步期間本機資料已變更，請重新整理後再同步');
      if (direction !== 'equal') this.sync.saveRecovery(local, remote);
      if (direction === 'upload') {
        // Gist has no transaction lock; recheck immediately before writing.
        if (gistId && await this.sync.fingerprint(await this.sync.downloadFromGist(token, gistId)) !== remoteHash) throw new Error('另一台裝置剛更新雲端，已停止上傳，請重試');
        const result = await this.sync.uploadToGist(token, gistId || null, local);
        gistId = result.gistId;
      }
      const selected = direction === 'download' ? this.sync.validateData(remote) : local;
      const settings = {...this.settings, githubToken: token, gistId, lastSyncTime: Date.now(),
        autoSyncOnStart: automatic ? this.settings.autoSyncOnStart : document.getElementById('sync-auto-start').checked,
        syncBase: {gistId, hash: direction === 'download' ? remoteHash : localHash}};
      // A user may keep studying while an upload is in flight. Preserve those new edits.
      if (await this.sync.fingerprint(this.syncSnapshot()) !== localHash ||
          await this.sync.fingerprint(this.sync.loadLocalData()) !== localHash) throw new Error('雲端操作已完成，但本機在等待時又有變更；本機保留原樣，請重新整理後再同步');
      if (!this.sync.saveLocalData({...selected, settings})) throw new Error('本機儲存空間不足；請先匯出備份');
      this.settings = settings;
      this.decks = selected.decks; this.cards = selected.cards; this.logs = selected.logs;
      this.refreshAfterSync();
      document.getElementById('sync-gist-id').value = gistId;
      show('✅ ' + (direction === 'equal' ? '兩端資料一致' : direction === 'upload' ? '已上傳本機進度' : '已下載雲端進度') + ' · ' + new Date().toLocaleString('zh-TW'));
    } catch (error) {
      show('❌ 同步未完成：' + error.message + '。請確認網路與 Token；上傳逾時時請先檢查雲端再重試。');
    } finally {
      this.syncBusy = false;
      buttons.forEach(b => b.disabled = false);
    }
  }

  refreshAfterSync() {
    this.currentCategory = 'all';
    this.todayReviewedCount = this.logs[new Date().toISOString().slice(0, 10)]?.reviewed || 0;
    this.renderCategoryTabs(); this.renderDeckList(); this.updateHeaderStats();
  }

  exportSyncRecovery(which) {
    try {
      const recovery = JSON.parse(localStorage.getItem('ankiflash_sync_recovery_v1'));
      if (!recovery?.[which]) throw new Error('尚無這一份復原備份');
      this.sync.exportBackupJson(recovery[which]);
    } catch (e) { alert(e.message); }
  }

  exportBackupFile() {
    this.sync.exportBackupJson({
      decks: this.decks,
      cards: this.cards,
      logs: this.logs
    });
  }

  async importBackupFile(file) {
    if (!file || this.syncBusy) return;
    try {
      const parsed = JSON.parse(await file.text());
      parsed.logs = parsed.logs || {};
      const data = this.sync.validateData(parsed);
      if (!confirm('以備份中的 ' + data.decks.length + ' 個牌組、' + data.cards.length + ' 張卡片取代本機資料？本機舊資料會保留為復原備份。')) return;
      this.sync.saveRecovery(this.syncSnapshot());
      if (!this.sync.saveLocalData(data)) throw new Error('儲存失敗，請檢查剩餘空間');
      this.decks = data.decks; this.cards = data.cards; this.logs = data.logs;
      this.refreshAfterSync();
      alert('備份已還原；如有設定雲端，請再按立即同步。');
    } catch (e) { alert('還原失敗：' + e.message); }
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

    document.getElementById('modal-add-card').classList.add('open');
  }

  /**
   * MOJi 官方查詞入口 (會員登入留在官方網站)
   * @param {boolean} isManual 是否為使用者手動點擊按鈕
   */
  async importFromMojiDirect(isManual = true) {
    if (!isManual) return;
    const word=document.getElementById('add-card-front').value.trim();
    if (!word) { alert('請先輸入要查的單字或文型。'); return; }
    this.openMojiDict(word);
    const msg=document.getElementById('add-card-loading-msg');
    msg.style.display='block';msg.textContent='已開啟 MOJi 查詢。請回來填寫自己的讀音、中文及例句；要整理整份詞表，請用 MOJi 學習工作台。';
  }

  async autoEnrichSingleCard() {
    const word=document.getElementById('add-card-front').value.trim();
    if(!word)return alert('請先輸入單字。');
    const msg=document.getElementById('add-card-loading-msg');msg.style.display='block';msg.textContent='正在查詢一般字典…';
    try {
      const result=await this.enricher.enrichWord(word,{});
      if(document.getElementById('add-card-front').value.trim()!==word)return;
      for(const [field,key] of [['reading','reading'],['back','back'],['example','example']]) {
        const el=document.getElementById('add-card-'+field);if(!el.value && result?.[key])el.value=result[key];
      }
      msg.textContent='一般字典補全完成，請核對內容；這不是 MOJi 會員資料。';
    }catch(e){msg.textContent='查詢失敗，請手動填寫：'+e.message;}
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

  persistDeckChanges(decks, cards, refresh = true) {
    const keys = [this.sync.STORAGE_KEY_CARDS, this.sync.STORAGE_KEY_DECKS];
    const previous = [];
    let written = 0;
    try {
      keys.forEach(key => previous.push(localStorage.getItem(key)));
      [cards, decks].forEach((data, i) => {
        localStorage.setItem(keys[i], JSON.stringify(data));
        written++;
      });
    } catch (error) {
      for (let i = written - 1; i >= 0; i--) {
        if (previous[i] === null) localStorage.removeItem(keys[i]);
        else localStorage.setItem(keys[i], previous[i]);
      }
      alert('儲存失敗，牌組未變更。請確認瀏覽器儲存空間後再試。');
      return false;
    }
    this.decks = decks;
    this.cards = cards;
    if (refresh) this.showView('view-decks');
    return true;
  }

  deleteDeck(deckId) {
    const deck = this.decks.find(d => d.id === deckId);
    if (!deck) return;
    const count = this.cards.filter(c => c.deckId === deckId).length;
    if (!confirm(`確定刪除「${deck.name}」及其中 ${count} 張卡片？其他牌組不受影響。此操作無法撤銷。`)) return;
    this.persistDeckChanges(this.decks.filter(d => d.id !== deckId), this.cards.filter(c => c.deckId !== deckId));
  }

  splitDeck(deckId) {
    const deck = this.decks.find(d => d.id === deckId);
    const source = this.cards.filter(c => c.deckId === deckId);
    if (!deck || source.length <= 20) return;
    const count = Math.ceil(source.length / 20);
    if (!confirm(`將「${deck.name}」的 ${source.length} 張卡片分成 ${count} 個牌組，每組最多 20 張？單字與複習進度會保留。`)) return;
    const groups = Array.from({length: count}, (_, i) => ({
      ...deck,
      id: i === 0 ? deck.id : 'deck_' + crypto.randomUUID(),
      name: `${deck.name}（${i + 1}/${count}）`
    }));
    const destinations = new Map(source.map((c, i) => [c.id, groups[Math.floor(i / 20)].id]));
    const decks = this.decks.flatMap(d => d.id === deckId ? groups : [d]);
    const cards = this.cards.map(c => destinations.has(c.id) ? {...c, deckId: destinations.get(c.id)} : c);
    this.persistDeckChanges(decks, cards);
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
      this.deleteDeck(deckId);
    }
  }

  // ==========================================
  // MOJi 辭書聯動 (官方網頁入口)
  // ==========================================

  openMojiDict(word) {
    if (!word || !word.trim()) return;
    window.open('https://www.mojidict.com/search?text='+encodeURIComponent(word.trim()), '_blank', 'noopener,noreferrer');
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
    this.studyQueue = this.studyQueue.filter(c => c.id !== currentCard.id);
    this.currentCardIndex = Math.max(0, Math.min(this.currentCardIndex, this.studyQueue.length - 1));

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

  openDeckCardManager(deckId, mode = 'all', cardIds = null) {
    const family = this.getDeckFamilies().find(f => f.id === deckId);
    this.managerSourceIds = family ? new Set(family.sourceIds) : null;
    this.managerCardIds = cardIds ? new Set(cardIds) : null;
    this.activeManagerDeckId = deckId;
    this.selectedCardIds = new Set();
    this.managerVisibleLimit = 100;
    const deck = family || this.decks.find(d => d.id === deckId);
    if (deckId && !deck) return;
    document.getElementById('deck-cards-title').textContent = deck ? `📋 ${deck.name} · 單字一覽` : mode === 'manual' ? '手動複習 · 單字一覽' : '📋 全部單字';
    document.getElementById('deck-cards-search-input').value = '';
    document.getElementById('manager-review-filter').value = mode;
    document.getElementById('manager-review-status').textContent = '';
    document.getElementById('btn-delete-all-deck-cards').hidden = true;
    const selectAllBox = document.getElementById('deck-cards-select-all');
    if (!selectAllBox.dataset.hasListener) {
      selectAllBox.dataset.hasListener = 'true';
      selectAllBox.addEventListener('change', e => this.handleToggleSelectAll(e.target.checked));
    }
    this.renderDeckCardsList(deckId);
    document.getElementById('modal-deck-cards').classList.add('open');
  }

  getManagerCards(query = '') {
    const mode = document.getElementById('manager-review-filter').value;
    const q = query.trim().toLowerCase();
    return this.cards.filter(card =>
      (!this.activeManagerDeckId || (this.managerSourceIds ? this.managerSourceIds.has(card.deckId) : card.deckId === this.activeManagerDeckId)) &&
      (!this.managerCardIds || this.managerCardIds.has(card.id)) &&
      (mode === 'all' || (card.reviewMode === 'manual' ? 'manual' : 'anki') === mode) &&
      (!q || [card.front, card.reading, card.back].some(text => String(text || '').toLowerCase().includes(q)))
    );
  }

  handleToggleSelectAll(isChecked) {
    const query = document.getElementById('deck-cards-search-input').value;
    this.getManagerCards(query).forEach(card => {
      if (isChecked) this.selectedCardIds.add(card.id);
      else this.selectedCardIds.delete(card.id);
    });
    this.renderDeckCardsList(this.activeManagerDeckId, query);
  }

  setSelectedReviewMode(mode) {
    if (!['manual', 'anki'].includes(mode) || !this.selectedCardIds?.size) return;
    const selected = new Set(this.selectedCardIds);
    const cards = this.cards.map(card => selected.has(card.id) ? {...card, reviewMode: mode} : card);
    if (!this.persistDeckChanges(this.decks, cards, false)) return;
    // A manual-only card must also leave a queue that was already open.
    if (!this.browseAll && this.studyQueue.length) {
      const currentId = this.studyQueue[this.currentCardIndex]?.id;
      this.studyQueue = this.studyQueue.filter(card => cards.some(c => c.id === card.id && c.reviewMode !== 'manual'));
      const index = this.studyQueue.findIndex(card => card.id === currentId);
      this.currentCardIndex = index >= 0 ? index : Math.max(0, Math.min(this.currentCardIndex, this.studyQueue.length - 1));
      if (document.getElementById('view-study').classList.contains('active')) this.renderCurrentStudyCard();
    }
    this.selectedCardIds.clear();
    this.renderDeckCardsList(this.activeManagerDeckId, document.getElementById('deck-cards-search-input').value);
    this.renderDeckList();
    this.updateHeaderStats();
    document.getElementById('manager-review-status').textContent = mode === 'manual'
      ? `已將 ${selected.size} 個單字移至手動複習，不再加入 Anki 排程；原有學習紀錄保留。`
      : `已將 ${selected.size} 個單字改回 Anki，依原有學習進度排程。`;
  }

  startManualReview() {
    const cards = this.getManagerCards(document.getElementById('deck-cards-search-input').value).filter(c => c.reviewMode === 'manual');
    if (!cards.length) return;
    document.getElementById('modal-deck-cards').classList.remove('open');
    this.startStudy(null, true, cards);
  }

  updateBatchToolbar(displayedCards) {
    const selectedCount = this.selectedCardIds.size;
    document.getElementById('btn-set-manual').disabled = selectedCount === 0;
    document.getElementById('btn-set-anki').disabled = selectedCount === 0;
    document.getElementById('btn-start-manual').disabled = !displayedCards.some(c => c.reviewMode === 'manual');
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
        selectAllText.innerText = allSelected ? '取消全選' : `全選符合篩選 (${displayedCards.length})`;
      }
    } else if (selectAllBox) {
      selectAllBox.checked = false;
      selectAllBox.indeterminate = false;
      if (selectAllText) selectAllText.innerText = '全選';
    }
  }

  renderDeckCardsList(deckId, filterQuery = '') {
    const container = document.getElementById('deck-cards-list-container');
    if (!container) return;
    if (!this.selectedCardIds) this.selectedCardIds = new Set();
    const filtered = this.getManagerCards(filterQuery);
    const visible = filtered.slice(0, this.managerVisibleLimit || 100);
    document.getElementById('deck-cards-count-label').textContent = `符合篩選 ${filtered.length} 個單字 · 已顯示 ${visible.length} 個`;
    this.updateBatchToolbar(filtered);
    container.replaceChildren();
    if (!filtered.length) {
      const empty = document.createElement('p');
      empty.textContent = '沒有符合篩選的單字。';
      container.append(empty);
      return;
    }
    visible.forEach(card => {
      const isSelected = this.selectedCardIds.has(card.id);
      const item = document.createElement('div');
      item.className = `card-manager-item word-detail-row ${isSelected ? 'selected' : ''}`;
      item.dataset.cardId = card.id;
      item.innerHTML = `
        <input type="checkbox" class="card-checkbox row-card-checkbox" aria-label="選取 ${this.escapeHtml(card.front)}" ${isSelected ? 'checked' : ''}>
        <details class="word-detail">
          <summary>
            <div class="card-item-word"><span lang="ja">${this.escapeHtml(card.front)}</span>
              ${card.reading ? `<span class="card-item-reading" lang="ja">${this.escapeHtml(card.reading)}</span>` : ''}</div>
            <div class="card-item-meaning">${this.escapeHtml(card.back || '尚未填寫中文翻譯')}</div>
            <small>${card.reviewMode === 'manual' ? '手動複習' : 'Anki 排程'} · 點一下看例句與說明</small>
          </summary>
          <div class="word-example-detail"><strong>例句</strong><p>${this.escapeHtml(card.example || '尚未提供例句。')}</p>
            ${card.notes ? `<strong>說明／筆記</strong><p>${this.escapeHtml(card.notes)}</p>` : ''}</div>
        </details>
        <button class="delete-card-btn btn-del-single-card" aria-label="刪除 ${this.escapeHtml(card.front)}">🗑️</button>`;
      item.querySelector('.row-card-checkbox').addEventListener('change', e => {
        if (e.target.checked) this.selectedCardIds.add(card.id);
        else this.selectedCardIds.delete(card.id);
        item.classList.toggle('selected', e.target.checked);
        this.updateBatchToolbar(filtered);
      });
      item.querySelector('.btn-del-single-card').onclick = () => this.deleteCardById(card.id, deckId);
      container.append(item);
    });
    if (visible.length < filtered.length) {
      const more = document.createElement('button');
      more.className = 'btn-secondary';
      more.textContent = `再顯示 ${Math.min(100, filtered.length - visible.length)} 個單字`;
      more.onclick = () => { this.managerVisibleLimit += 100; this.renderDeckCardsList(deckId, filterQuery); };
      container.append(more);
    }
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
    document.getElementById('setting-audio-lang').value = this.settings.audioLang || 'ja-JP';
    document.getElementById('setting-theme-select').value = this.settings.theme || 'dark';
    document.getElementById('setting-new-limit').value = this.settings.dailyNewLimit || 20;
    document.getElementById('setting-review-limit').value = this.settings.dailyReviewLimit || 100;
    document.getElementById('modal-settings').classList.add('open');
  }

  saveSettingsFromModal() {
    this.settings.autoPlayAudio = false;
    this.settings.audioLang = document.getElementById('setting-audio-lang').value;
    this.settings.theme = document.getElementById('setting-theme-select').value;
    this.settings.dailyNewLimit = parseInt(document.getElementById('setting-new-limit').value) || 20;
    this.settings.dailyReviewLimit = parseInt(document.getElementById('setting-review-limit').value) || 100;

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
        navigator.serviceWorker.register('sw.js', { updateViaCache: 'none' }).then(reg => {
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
