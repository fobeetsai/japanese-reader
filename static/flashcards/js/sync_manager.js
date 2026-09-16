/**
 * AnkiFlash Sync Manager (跨裝置同步管理器)
 * 支援：
 * 1. Local-First (本機儲存 IndexedDB / LocalStorage)
 * 2. GitHub Gist 雲端同步 (使用個人帳號；Secret Gist 並非加密儲存)
 * 3. 同步基準比對與覆蓋前復原備份
 * 4. 完整備份 JSON 與 Anki TSV/CSV 匯入匯出
 */

class SyncManager {
  constructor() {
    this.STORAGE_KEY_DECKS = 'ankiflash_decks_v1';
    this.STORAGE_KEY_CARDS = 'ankiflash_cards_v1';
    this.STORAGE_KEY_SETTINGS = 'ankiflash_settings_v1';
    this.STORAGE_KEY_LOGS = 'ankiflash_logs_v1';
  }

  // ==========================================
  // 1. 本地 Local-First 讀寫核心
  // ==========================================

  loadLocalData() {
    try {
      const rawDecks = localStorage.getItem(this.STORAGE_KEY_DECKS);
      const rawCards = localStorage.getItem(this.STORAGE_KEY_CARDS);
      const rawSettings = localStorage.getItem(this.STORAGE_KEY_SETTINGS);
      const rawLogs = localStorage.getItem(this.STORAGE_KEY_LOGS);

      return {
        decks: rawDecks ? JSON.parse(rawDecks) : null,
        cards: rawCards ? JSON.parse(rawCards) : null,
        settings: rawSettings ? JSON.parse(rawSettings) : this.getDefaultSettings(),
        logs: rawLogs ? JSON.parse(rawLogs) : {}
      };
    } catch (e) {
      console.error('[SyncManager] 載入本機資料失敗:', e);
      return { decks: null, cards: null, settings: this.getDefaultSettings(), logs: {} };
    }
  }

  saveLocalData({ decks, cards, settings, logs }) {
    const previous = new Map();
    try {
      const entries = [[this.STORAGE_KEY_DECKS, decks], [this.STORAGE_KEY_CARDS, cards],
        [this.STORAGE_KEY_SETTINGS, settings], [this.STORAGE_KEY_LOGS, logs]];
      for (const [key, value] of entries) {
        if (value === undefined || value === null) continue;
        const encoded = JSON.stringify(value);
        previous.set(key, localStorage.getItem(key));
        localStorage.setItem(key, encoded);
      }
      return true;
    } catch (e) {
      for (const [key, value] of [...previous].reverse()) {
        try { if (value === null) localStorage.removeItem(key); else localStorage.setItem(key, value); }
        catch (rollbackError) { console.error('[SyncManager] 回復失敗，請使用復原備份', rollbackError); }
      }
      console.error('[SyncManager] 儲存本機資料失敗:', e);
      return false;
    }
  }

  getDefaultSettings() {
    return {
      autoPlayAudio: false,
      audioLang: 'ja-JP',          // 'ja-JP' | 'en-US' | 'zh-TW'
      theme: 'dark',               // 'dark' | 'light'
      dailyNewLimit: 20,
      dailyReviewLimit: 100,
      vibration: true,
      githubToken: '',
      gistId: '',
      lastSyncTime: null,
      autoSyncOnStart: false
    };
  }

  validateData(data) {
    if (!data || !Array.isArray(data.decks) || !Array.isArray(data.cards) ||
        !data.logs || typeof data.logs !== 'object' || Array.isArray(data.logs)) {
      throw new Error('資料格式不正確，未修改本機資料');
    }
    const ids = new Set();
    for (const deck of data.decks) {
      if (!deck || typeof deck.id !== 'string' || !deck.id || typeof deck.name !== 'string' || ids.has(deck.id)) throw new Error('牌組資料不正確');
      ids.add(deck.id);
    }
    const cards = new Set();
    for (const card of data.cards) {
      if (!card || typeof card.id !== 'string' || !card.id || cards.has(card.id) || !ids.has(card.deckId) ||
          typeof card.front !== 'string' || typeof card.back !== 'string') throw new Error('卡片資料不正確');
      cards.add(card.id);
    }
    return {decks: data.decks, cards: data.cards, logs: data.logs};
  }

  async fingerprint(data) {
    const canonical = value => Array.isArray(value) ? value.map(canonical) :
      value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])])) : value;
    const bytes = new TextEncoder().encode(JSON.stringify(canonical(this.validateData(data))));
    const digest = await crypto.subtle.digest('SHA-256', bytes);
    return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
  }

  syncDirection(localHash, remoteHash, baseHash) {
    if (localHash === remoteHash) return 'equal';
    if (!baseHash) return 'conflict';
    if (remoteHash === baseHash) return 'upload';
    if (localHash === baseHash) return 'download';
    return 'conflict';
  }

  saveRecovery(local, remote = null) {
    // Abort if storage is full: never overwrite data without a recovery copy.
    localStorage.setItem('ankiflash_sync_recovery_v1', JSON.stringify({
      savedAt: Date.now(), local: this.validateData(local), remote: remote ? this.validateData(remote) : null
    }));
  }

  // ==========================================
  // 2. GitHub Gist 雲端同步 (支援電腦、手機、iPad 無縫同步)
  // ==========================================

  /**
   * 驗證 GitHub Token 並測試連線
   */
  async testGithubToken(token) {
    if (!token) throw new Error('請提供有效的 GitHub Personal Access Token');
    const res = await fetch('https://api.github.com/user', {
      headers: {
        'Authorization': `Bearer ${token.trim()}`,
        'Accept': 'application/vnd.github.v3+json'
      }
    });
    if (!res.ok) {
      throw new Error(`GitHub 驗證失敗 (${res.status}): 請檢查 Token 權限是否包含 gist`);
    }
    const user = await res.json();
    return user.login;
  }

  /**
   * 上傳至 GitHub Gist (雲端備份)
   */
  async uploadToGist(token, gistId = null, appData) {
    if (!token) throw new Error('未設定 GitHub Token');
    this.validateData(appData);
    if (gistId && !/^[a-f0-9]{20,64}$/i.test(gistId)) throw new Error('Gist ID 格式不正確');

    const payload = {
      description: 'AnkiFlash 智慧抽認卡跨裝置同步資料庫',
      public: false,
      files: {
        'ankiflash_sync_data.json': {
          content: JSON.stringify({
            version: '1.0',
            exportedAt: Date.now(),
            decks: appData.decks,
            cards: appData.cards,
            logs: appData.logs
          }, null, 2)
        }
      }
    };

    let url = 'https://api.github.com/gists';
    let method = 'POST';

    if (gistId) {
      url += `/${gistId.trim()}`;
      method = 'PATCH';
    }

    const res = await fetch(url, {
      signal: AbortSignal.timeout(30000),
      method: method,
      headers: {
        'Authorization': `Bearer ${token.trim()}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.message || `雲端同步上傳失敗 (${res.status})`);
    }

    const gistData = await res.json();
    return {
      gistId: gistData.id,
      htmlUrl: gistData.html_url,
      updatedAt: gistData.updated_at
    };
  }

  /**
   * 從 GitHub Gist 下載 (雲端還原至手機/平板)
   */
  async downloadFromGist(token, gistId) {
    if (!token || !gistId) throw new Error('請提供 GitHub Token 與 Gist ID');
    if (!/^[a-f0-9]{20,64}$/i.test(gistId)) throw new Error('Gist ID 格式不正確');

    const res = await fetch(`https://api.github.com/gists/${gistId.trim()}`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(30000),
      headers: {
        'Authorization': `Bearer ${token.trim()}`,
        'Accept': 'application/vnd.github.v3+json'
      }
    });

    if (!res.ok) {
      throw new Error(`雲端下載失敗 (${res.status}): 找不到指定的 Gist`);
    }

    const gistData = await res.json();
    const file = gistData.files?.['ankiflash_sync_data.json'];
    if (!file || !file.content) {
      throw new Error('Gist 中未發現 AnkiFlash 專用資料檔案');
    }

    if (file.truncated) throw new Error('雲端資料超出 Gist 完整下載範圍，請改用 JSON 檔案移轉，未修改資料');
    const parsed = JSON.parse(file.content);
    parsed.logs = parsed.logs || {};
    this.validateData(parsed);
    return {
      decks: parsed.decks,
      cards: parsed.cards,
      logs: parsed.logs,
      exportedAt: parsed.exportedAt,
      updatedAt: gistData.updated_at
    };
  }

  // ==========================================
  // 3. 檔案匯出 / 匯入 (JSON 與 Anki TSV 格式)
  // ==========================================

  /**
   * 匯出完整 JSON 備份檔
   */
  exportBackupJson(appData) {
    const backup = {
      appName: 'AnkiFlash',
      version: '1.0',
      timestamp: Date.now(),
      dateStr: new Date().toISOString(),
      decks: appData.decks,
      cards: appData.cards,
      logs: appData.logs
    };
    const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `AnkiFlash_Backup_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  /**
   * 匯出指定牌組為 Anki 原生 TSV 檔案
   */
  exportAnkiTsv(deckName, cards) {
    let tsv = `#separator:tab\n#html:true\n#tags column:5\n`;
    tsv += `正面單字\t背面釋義\t平假名讀音\t例句與翻譯\t標籤\n`;
    
    cards.forEach(c => {
      const front = (c.front || '').replace(/\t/g, ' ').replace(/\n/g, '<br>');
      const back = (c.back || '').replace(/\t/g, ' ').replace(/\n/g, '<br>');
      const reading = (c.reading || '').replace(/\t/g, ' ').replace(/\n/g, '<br>');
      const example = (c.example || '').replace(/\t/g, ' ').replace(/\n/g, '<br>');
      const tags = (c.tags || []).join(' ');
      tsv += `${front}\t${back}\t${reading}\t${example}\t${tags}\n`;
    });

    const blob = new Blob([tsv], { type: 'text/tab-separated-values;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Anki_${deckName.replace(/\s+/g, '_')}_Deck.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  /**
   * 智慧批次文字解析 (支援「單字 讀音 釋義 例句」或 TSV / CSV 格式)
   */
  parseBatchCards(text, targetDeckId) {
    if (!text || !text.trim()) return [];
    const lines = text.split(/\r?\n/).map(l => l.trim()).filter(l => l && !l.startsWith('#'));
    const cards = [];

    for (const line of lines) {
      let front = '';
      let reading = '';
      let back = '';
      let example = '';

      // 檢查是否為 Tab 分隔
      if (line.includes('\t')) {
        const parts = line.split('\t').map(p => p.trim());
        front = parts[0] || '';
        back = parts[1] || '';
        reading = parts[2] || '';
        example = parts[3] || '';
      } 
      // 檢查是否為直管 | 分隔 (如: 単語 | たんご | 單字名詞 | 例文)
      else if (line.includes('|')) {
        const parts = line.split('|').map(p => p.trim());
        front = parts[0] || '';
        reading = parts[1] || '';
        back = parts[2] || '';
        example = parts[3] || '';
      }
      // 檢查是否為逗號 CSV
      else if (line.includes(',')) {
        const parts = line.split(',').map(p => p.trim());
        front = parts[0] || '';
        reading = parts[1] || '';
        back = parts[2] || '';
        example = parts[3] || '';
      }
      // 智能正則辨識：例如 "相変わらず [あいかわらず] 依然、照舊" 或 "猫 (ねこ) 貓咪"
      else {
        const bracketMatch = line.match(/^([^\s\[\(]+)\s*[\[\(]([^\]\)]+)[\]\)]\s*(.*)$/);
        if (bracketMatch) {
          front = bracketMatch[1];
          reading = bracketMatch[2];
          back = bracketMatch[3];
        } else {
          // 以空白切割
          const spaceParts = line.split(/\s+/);
          front = spaceParts[0] || '';
          if (spaceParts.length >= 3) {
            reading = spaceParts[1];
            back = spaceParts.slice(2).join(' ');
          } else {
            back = spaceParts.slice(1).join(' ') || front;
          }
        }
      }

      if (front) {
        cards.push({
          deckId: targetDeckId,
          front: front.trim(),
          reading: reading.trim(),
          back: back.trim(),
          example: example.trim()
        });
      }
    }

    return cards;
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = SyncManager;
} else {
  window.SyncManager = SyncManager;
}
