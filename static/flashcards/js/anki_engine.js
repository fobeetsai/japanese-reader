/**
 * Anki SM-2 Spaced Repetition Algorithm Engine
 * 仿 Anki 演算法核心：
 * - 狀態：New (0: 新卡), Learning (1: 學習中), Review (2: 複習中), Relearning (3: 重新學習)
 * - 評分：1: Again (重來), 2: Hard (困難), 3: Good (良好), 4: Easy (簡單)
 */

class AnkiEngine {
  constructor(options = {}) {
    this.config = Object.assign({
      learningSteps: [1, 10],      // 學習步階 (分鐘)
      relearningSteps: [10],       // 重學步階 (分鐘)
      graduatingInterval: 1,       // 畢業間隔 (天)
      easyInterval: 4,             // 簡單直接畢業間隔 (天)
      startingEase: 2.50,          // 初始難度因子 (250%)
      easyBonus: 1.30,             // 簡單獎勵加乘
      hardIntervalMultiplier: 1.20,// 困難間隔加乘
      intervalModifier: 1.00,      // 整體間隔修正係數
      minimumEase: 1.30,           // 最低難度因子 (130%)
      lapseNewInterval: 0,         // 忘記時的新間隔比例 (0表示回到步階)
      dailyNewLimit: 20,           // 每日新卡上限
      dailyReviewLimit: 100        // 每日複習上限
    }, options);
  }

  /**
   * 建立全新卡片結構
   */
  createCard({ id, deckId, front, reading = '', back, example = '', notes = '', tags = [] }) {
    const now = Date.now();
    return {
      id: id || 'card_' + now + '_' + Math.random().toString(36).substring(2, 7),
      deckId: deckId || 'default',
      front: front ? front.trim() : '',
      reading: reading ? reading.trim() : '',
      back: back ? back.trim() : '',
      example: example ? example.trim() : '',
      notes: notes ? notes.trim() : '',
      tags: Array.isArray(tags) ? tags : [],
      
      // SRS 參數
      state: 'new',                // 'new' | 'learning' | 'review' | 'relearning'
      stepIndex: 0,                // 學習步階索引
      due: now,                    // 下次複習時間戳記 (ms)
      interval: 0,                 // 當前間隔 (天數，學習中小於1)
      ease: this.config.startingEase, // 當前難度係數 (預設 2.50)
      reps: 0,                     // 累積複習次數
      lapses: 0,                   // 遺忘次數 (選 Again 次數)
      
      // 時間戳記
      createdAt: now,
      lastReviewed: null,
      history: []                  // 歷次評分紀錄 [{ date, rating, interval, ease }]
    };
  }

  /**
   * 根據評分計算卡片的新狀態與下次複習時間
   * @param {Object} card 
   * @param {number} rating 1: Again, 2: Hard, 3: Good, 4: Easy
   * @param {number} now 現在時間戳記
   * @returns {Object} 更新後的卡片物件深拷貝
   */
  rateCard(card, rating, now = Date.now()) {
    const c = JSON.parse(JSON.stringify(card));
    const cfg = this.config;
    let nextDue = now;
    let newInterval = c.interval;
    let newEase = c.ease || cfg.startingEase;
    let newState = c.state;
    let newStepIndex = c.stepIndex || 0;

    const ONE_MINUTE = 60 * 1000;
    const ONE_DAY = 24 * 60 * 60 * 1000;

    c.reps = (c.reps || 0) + 1;

    // 分流處理：新卡或學習中
    if (c.state === 'new' || c.state === 'learning' || c.state === 'relearning') {
      const steps = (c.state === 'relearning') ? cfg.relearningSteps : cfg.learningSteps;

      if (rating === 1) {
        // [Again] 重頭來過
        newState = (c.state === 'review') ? 'relearning' : 'learning';
        newStepIndex = 0;
        nextDue = now + steps[0] * ONE_MINUTE;
        newInterval = 0;
        if (c.state !== 'new') c.lapses = (c.lapses || 0) + 1;
      } 
      else if (rating === 2) {
        // [Hard] 維持當前步階或給予折衷時間 (約原步階的 1.5 倍或 6 分鐘)
        const currentStep = steps[newStepIndex] || steps[0];
        const hardDelay = Math.max(1, Math.round(currentStep * 1.5));
        nextDue = now + hardDelay * ONE_MINUTE;
      } 
      else if (rating === 3) {
        // [Good] 前進下一個步階，若已到最後步階則「畢業」進入 Review
        if (newStepIndex + 1 < steps.length) {
          newStepIndex += 1;
          newState = 'learning';
          nextDue = now + steps[newStepIndex] * ONE_MINUTE;
        } else {
          // 順利畢業！
          newState = 'review';
          newInterval = cfg.graduatingInterval;
          nextDue = now + newInterval * ONE_DAY;
          newStepIndex = 0;
        }
      } 
      else if (rating === 4) {
        // [Easy] 立即畢業跳過所有步階
        newState = 'review';
        newInterval = cfg.easyInterval;
        nextDue = now + newInterval * ONE_DAY;
        newEase = newEase + 0.15;
        newStepIndex = 0;
      }
    } 
    // 複習卡片 (Review 狀態)
    else if (c.state === 'review') {
      if (rating === 1) {
        // [Again] 忘記了！進入重學狀態
        newState = 'relearning';
        newStepIndex = 0;
        c.lapses = (c.lapses || 0) + 1;
        newEase = Math.max(cfg.minimumEase, newEase - 0.20);
        newInterval = Math.max(1, Math.round(c.interval * cfg.lapseNewInterval));
        nextDue = now + cfg.relearningSteps[0] * ONE_MINUTE;
      } 
      else if (rating === 2) {
        // [Hard] 勉強記住：難度降低，間隔增長趨緩
        newEase = Math.max(cfg.minimumEase, newEase - 0.15);
        newInterval = Math.max(c.interval + 1, Math.round(c.interval * cfg.hardIntervalMultiplier * cfg.intervalModifier));
        nextDue = now + newInterval * ONE_DAY;
      } 
      else if (rating === 3) {
        // [Good] 標準記得：間隔正常乘上 Ease
        newInterval = Math.max(c.interval + 1, Math.round(c.interval * newEase * cfg.intervalModifier));
        nextDue = now + newInterval * ONE_DAY;
      } 
      else if (rating === 4) {
        // [Easy] 記得非常清楚：額外加成，Ease 提升
        newEase = newEase + 0.15;
        newInterval = Math.max(c.interval + 2, Math.round(c.interval * newEase * cfg.easyBonus * cfg.intervalModifier));
        nextDue = now + newInterval * ONE_DAY;
      }
    }

    c.state = newState;
    c.stepIndex = newStepIndex;
    c.due = nextDue;
    c.interval = newInterval;
    c.ease = Math.round(newEase * 100) / 100;
    c.lastReviewed = now;

    // 紀錄簡要歷史
    if (!c.history) c.history = [];
    c.history.push({
      date: now,
      rating: rating,
      interval: newInterval,
      ease: c.ease
    });

    return c;
  }

  /**
   * 計算 4 個按鈕上方即時預估的下次複習時間文字 (例如: "<1分", "1天", "4天")
   * 讓用戶在點擊前清楚知道評分後果
   */
  getIntervalPreviews(card, now = Date.now()) {
    const ratings = [1, 2, 3, 4];
    return ratings.map(r => {
      const simulated = this.rateCard(card, r, now);
      const diffMs = simulated.due - now;
      return this.formatTimeDiff(diffMs);
    });
  }

  /**
   * 格式化時間差為簡潔好讀字串
   */
  formatTimeDiff(diffMs) {
    if (diffMs <= 0) return '即時';
    const minutes = Math.round(diffMs / (60 * 1000));
    if (minutes < 1) return '< 1分';
    if (minutes < 60) return `${minutes} 分鐘`;
    const hours = Math.round(minutes / 60);
    if (hours < 24) return `${hours} 小時`;
    const days = Math.round(hours / 24);
    if (days < 30) return `${days} 天`;
    const months = Math.round(days / 30);
    if (months < 12) return `${months} 個月`;
    const years = (days / 365).toFixed(1);
    return `${years} 年`;
  }

  /**
   * 篩選並排序今日待學習/待複習的隊列
   * 優先順序：學習中 > 待複習(到期) > 新卡
   */
  getStudyQueue(cards, now = Date.now(), options = {}) {
    const dailyNewLimit = options.dailyNewLimit || this.config.dailyNewLimit;
    const dailyReviewLimit = options.dailyReviewLimit || this.config.dailyReviewLimit;

    const learningCards = [];
    const reviewCards = [];
    const newCards = [];

    cards.forEach(card => {
      if (card.state === 'learning' || card.state === 'relearning') {
        if (card.due <= now) {
          learningCards.push(card);
        }
      } else if (card.state === 'review') {
        if (card.due <= now) {
          reviewCards.push(card);
        }
      } else if (card.state === 'new') {
        newCards.push(card);
      }
    });

    // 依到期時間排序
    learningCards.sort((a, b) => a.due - b.due);
    reviewCards.sort((a, b) => a.due - b.due);

    // 套用每日限制
    const limitedReviews = reviewCards.slice(0, dailyReviewLimit);
    const limitedNews = newCards.slice(0, dailyNewLimit);

    return {
      learning: learningCards,
      review: limitedReviews,
      newCards: limitedNews,
      // 合併完整複習隊列
      queue: [...learningCards, ...limitedReviews, ...limitedNews],
      totalAvailable: learningCards.length + limitedReviews.length + limitedNews.length
    };
  }

  /**
   * 計算整體學習統計與未來複習負載
   */
  getDeckStats(cards, now = Date.now()) {
    let newCount = 0;
    let learningCount = 0;
    let reviewCount = 0;
    let masteredCount = 0; // 間隔 >= 21 天視為精通
    let dueCount = 0;

    const next7Days = Array(7).fill(0);

    cards.forEach(c => {
      if (c.state === 'new') {
        newCount++;
      } else if (c.state === 'learning' || c.state === 'relearning') {
        learningCount++;
        if (c.due <= now) dueCount++;
      } else if (c.state === 'review') {
        reviewCount++;
        if (c.interval >= 21) masteredCount++;
        if (c.due <= now) dueCount++;
      }

      // 未來7天到期卡片預測
      if (c.state === 'review' || c.state === 'learning') {
        const diffDays = Math.floor((c.due - now) / (24 * 60 * 60 * 1000));
        if (diffDays >= 0 && diffDays < 7) {
          next7Days[diffDays]++;
        }
      }
    });

    return {
      total: cards.length,
      newCount,
      learningCount,
      reviewCount,
      masteredCount,
      dueCount,
      next7Days
    };
  }
}

// 支援模組與瀏覽器全域載入
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AnkiEngine;
} else {
  window.AnkiEngine = AnkiEngine;
}
