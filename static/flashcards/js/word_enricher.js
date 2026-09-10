/**
 * WordEnricher - 智慧單字自動擴充引擎
 * 自動生成：
 * 1. 讀音 (平假名 Hiragana / IPA 音標)
 * 2. 繁體中文翻譯與詞性
 * 3. 實用例句 (日文/英文原文 + 繁體中文翻譯)
 * 
 * 具備三段式引擎：
 * Tier 1: 本地內建詞庫 (包含 JLPT 與 日語營造工程詞彙)
 * Tier 2: 免費免金鑰 Web 翻譯與羅馬字轉換引擎 (Google GTX + Free Dictionary API)
 * Tier 3: 選填 Google Gemini / OpenAI 智慧 AI 模型深度擴充
 */

class WordEnricher {
  constructor(options = {}) {
    this.settings = options.settings || {};
    
    // 內建日語營造工程與高頻詞彙特化字典 (即查即有，零延遲)
    this.builtInDict = {
      '施工': { reading: 'せこう', meaning: '施工、工程進行 (名詞/する動詞)', example: '施工図面に従って正確に施工を進める。(依照施工圖說正確推進施工。)', tags: ['工程', '施工'] },
      '養生': { reading: 'ようじょう', meaning: '養護、保護覆蓋防護 (名詞/する動詞)', example: 'コンクリート打設後は十分な湿潤養生を行う。(混凝土澆置後須進行充分的濕潤養護。)', tags: ['工程', '品管'] },
      '足場': { reading: 'あしば', meaning: '施工架、鷹架、立足點 (名詞)', example: '高所作業の前に足場の安全点検を実施する。(在高空作業前實施施工架安全點檢。)', tags: ['工程', '安全'] },
      '配筋': { reading: 'はいきん', meaning: '鋼筋配置、綁紮鋼筋 (名詞/する動詞)', example: 'コンクリート打設前に配筋のピッチと径を確認する。(混凝土澆置前確認鋼筋間距與號數。)', tags: ['工程', '品管'] },
      '型枠': { reading: 'かたわく', meaning: '模板、模具 (名詞)', example: '型枠の建て込み精度を厳格に確認する。(嚴格確認模板組裝豎立精度。)', tags: ['工程', '施工'] },
      '打設': { reading: 'だせつ', meaning: '混凝土澆置、灌漿 (名詞/する動詞)', example: '明日の朝一番から耐力壁のコンクリート打設を開始する。(明早第一時間開始耐力牆混凝土澆置。)', tags: ['工程', '施工'] },
      '墨出し': { reading: 'すみだし', meaning: '放樣、彈墨線基準標註 (名詞/する動詞)', example: '基礎の基準墨出しを狂いなく実施する。(準確無誤地實施基礎基準放樣。)', tags: ['工程', '測量'] },
      '是正': { reading: 'ぜせい', meaning: '改善、修正、缺失改善 (名詞/する動詞)', example: '監理者からの指摘事項を速やかに是正する。(迅速改善監造建築師指出的缺失事項。)', tags: ['工程', '品管'] },
      '立会い': { reading: 'たちあい', meaning: '會同、會勘、現場監驗 (名詞/する動詞)', example: '施主と設計者の立会いのもとで中間検査を行う。(在業主與建築師會同下進行期中查驗。)', tags: ['工程', '監造'] },
      '工期': { reading: 'こうき', meaning: '施工工期 (名詞)', example: '台風の影響で遅れた工期を挽回する。(挽回因颱風影響延誤的工期。)', tags: ['工程', '管理'] },
      '出来高': { reading: 'できだか', meaning: '工程進度成效、估驗計價完成量 (名詞)', example: '今月の工事出来高を査定して報告書を作成する。(評定本月工程完成進度量並製作報告。)', tags: ['工程', '計價'] },
      '安全帯': { reading: 'あんぜんたい', meaning: '安全帶、防墜背帶 (名詞)', example: '高所作業では必ずフルハーネス型安全帯を着用すること。(高空作業務必佩戴全身背負式安全帶。)', tags: ['安全', '防護'] },
      '危険予知': { reading: 'きけんよち', meaning: '危險預知、KY活動 (名詞)', example: '作業開始前に全員でKY活動を行い、災害ゼロを目指す。(作業開始前全員實施KY危險預知，力求零災害。)', tags: ['安全', '晨會'] },
      '指差呼称': { reading: 'しさこしょう', meaning: '指差確認、指差指差呼喚 (名詞)', example: '合図の確認は指差呼称で徹底する。(信號確認徹底採用指差確認。)', tags: ['安全', '操作'] },
      '開口部': { reading: 'かいこうぶ', meaning: '開口部、樓板留洞 (名詞)', example: '床の開口部には必ず手すりと蓋を設置し、墜落を防ぐ。(樓板開口處務必設置欄杆與封板蓋，防止墜落。)', tags: ['安全', '防墜'] },
      '鉄筋': { reading: 'てっきん', meaning: '鋼筋 (名詞)', example: '構造図に基づいて鉄筋を加工・組み立てる。(根據結構圖加工與組裝鋼筋。)', tags: ['工程', '結構'] },
      '鉄骨': { reading: 'てっこつ', meaning: '鋼骨、鋼結構 (名詞)', example: '鉄骨の建て方工事が順調に進んでいる。(鋼骨吊裝組裝工程順利進行中。)', tags: ['工程', '結構'] },
      '基礎': { reading: 'きそ', meaning: '基礎、地基 (名詞)', example: '建物の耐久性を保つため強固な基礎を築く。(為維持建築物耐久性築起堅固的基礎。)', tags: ['工程', '結構'] },
      '梁': { reading: 'はり', meaning: '樑 (名詞)', example: '大梁と小梁の接合部をボルトで緊結する。(大樑與小樑接合處以螺栓緊固。)', tags: ['工程', '結構'] },
      '柱': { reading: 'はしら', meaning: '柱子 (名詞)', example: '主筋の継手位置を慎重に確認する。(審慎確認柱主筋的搭接位置。)', tags: ['工程', '結構'] },
      'スラブ': { reading: 'すらぶ', meaning: '樓板、底板 (Slab) (名詞)', example: 'コンクリートスラブの厚みを計測する。(測量混凝土樓板厚度。)', tags: ['工程', '結構'] },
      'スランプ': { reading: 'すらんぷ', meaning: '坍度、塌落度 (Slump) (名詞)', example: '生コン受入時にスランプ試験を実施する。(預拌混凝土進場受入時實施坍度試驗。)', tags: ['工程', '品管'] },
      '朝礼': { reading: 'ちょうれい', meaning: '早會、朝會 (名詞)', example: '毎朝の安全朝礼で本日の作業内容を確認する。(每天早上的安全早會確認今日作業內容。)', tags: ['工程', '日常'] },
      '職人': { reading: 'しょくにん', meaning: '工班師傅、技工、匠人 (名詞)', example: '熟練した職人が丁寧にタイルを張る。(由熟練的工班師傅細心鋪貼磁磚。)', tags: ['工程', '人員'] },
      '竣工': { reading: 'しゅんこう', meaning: '竣工、完工 (名詞/する動詞)', example: '無事故で予定通り建物を竣工させた。(零事故地如期使建築物竣工完工。)', tags: ['工程', '管理'] },
      '監理': { reading: 'かんり', meaning: '監造、工程監理 (名詞/する動詞)', example: '監理技術者が現場の施工状況を立ち会う。(監造工程師現場會勘施工狀況。)', tags: ['工程', '監造'] },
      '施主': { reading: 'せしゅ', meaning: '業主、起造人 (名詞)', example: '施主立ち会いのもとで最終引き渡しを行う。(在業主會同下進行最終交屋點交。)', tags: ['工程', '商務'] }
    };
  }

  /**
   * 為單一單字自動生成補全資訊
   * @param {string} word 欲查詢單字
   * @param {Object} options { category: 'engineering' | 'daily' | 'business' }
   */
  async enrichWord(word, options = {}) {
    if (!word || !word.trim()) return null;
    const cleanWord = word.trim();

    // 1. 檢查本機專業字典
    if (this.builtInDict[cleanWord]) {
      const entry = this.builtInDict[cleanWord];
      return {
        front: cleanWord,
        reading: entry.reading,
        back: entry.meaning,
        example: entry.example,
        tags: options.category ? [options.category, ...(entry.tags || [])] : entry.tags
      };
    }

    // 2. 判斷是否設定了 AI 金鑰 (Gemini)
    if (this.settings.geminiApiKey) {
      try {
        const aiResult = await this.enrichViaGemini(cleanWord, options);
        if (aiResult) return aiResult;
      } catch (e) {
        console.warn('[WordEnricher] Gemini AI 查詢失敗，降級使用免費引擎:', e.message);
      }
    }

    // 3. 免費引擎 (Google GTX + Transliteration + 智慧例句生成)
    const isEnglish = /^[A-Za-z\s\-]+$/.test(cleanWord);
    if (isEnglish) {
      return await this.enrichEnglishWord(cleanWord, options);
    } else {
      return await this.enrichJapaneseWord(cleanWord, options);
    }
  }

  /**
   * 簡體中文轉繁體中文 (涵蓋營造工程、商務與日常生活高頻字詞)
   */
  toTraditional(text) {
    if (!text) return '';
    const map = {
      '施工': '施工', '建设': '建設', '堤坝': '堤壩', '本月': '本月',
      '铁路': '鐵路', '路基': '路基', '建造': '建造', '工程': '工程',
      '作业': '作業', '修建': '修建', '筹款': '籌款', '募捐': '募捐',
      '自动': '自動', '他动': '他動', 'サ变': 'サ變', '名': '名', '副': '副',
      '安全带': '安全帶', '保险带': '保險帶', '检查': '檢查', '确认': '確認',
      '点检': '點檢', '养护': '養護', '保护': '保護', '防护': '防護',
      '脚手架': '施工架(鷹架)', '立足点': '立足點', '基础': '基礎', '支架': '支架',
      '浇筑': '澆置(灌漿)', '打设': '打設', '布置': '配置', '钢筋': '鋼筋',
      '晨会': '早會(晨會)', '早会': '早會', '举行': '舉行', '星期': '星期',
      '活动': '活動', '预测': '預測', '飞机': '飛機', '新闻': '新聞',
      '关于': '關於', '飞行': '飛行', '调养': '調養', '身体': '身體',
      '保养': '保養', '养病': '養病', '夫妻': '夫妻', '关系': '關係',
      '说了': '說了', '说什么': '說什麼', '这么': '這麼', '那么': '那麼',
      '义': '義', '释': '釋', '词': '詞', '语': '語', '变': '變',
      '动': '動', '标': '標', '准': '準', '结': '結', '构': '構',
      '发': '發', '达': '達', '关': '關', '连': '連', '进': '進',
      '实': '實', '现': '現', '场': '場', '门': '門', '间': '間',
      '阶': '階', '段': '段', '预': '預', '防': '防', '规': '規',
      '则': '則', '电': '電', '话': '話', '线': '線', '计': '計',
      '划': '劃', '经': '經', '济': '濟', '调': '調', '查': '查',
      '质': '質', '量': '量', '项': '項', '目': '目', '机': '機',
      '器': '器', '备': '備', '设': '設', '图': '圖', '说': '說',
      '明': '明', '报': '報', '告': '告', '书': '書', '钢': '鋼',
      '筋': '筋', '混': '混', '凝': '凝', '土': '土', '养': '養',
      '体': '體', '态': '態', '度': '度', '专': '專', '业': '業',
      '劳': '勞', '务': '務', '资': '資', '料': '料', '买': '買',
      '卖': '賣', '开': '開', '关': '關', '车': '車', '会': '會',
      '话': '話', '国': '國', '学': '學', '习': '習', '难': '難',
      '易': '易', '简': '簡', '单': '單', '复': '複', '杂': '雜',
      '从': '從', '这': '這', '则': '則', '点': '點'
    };
    let res = text;
    for (const [s, t] of Object.entries(map)) {
      res = res.split(s).join(t);
    }
    return res;
  }

  /**
   * MOJi 辭書 (MOJi Dictionary) 原生雲端直連查詢
   * 抓取官方讀音 (含音調標記)、官方詞性與中文釋義、原生權威例句
   * @param {string} word 欲查詢單字
   */
  async fetchMojiDict(word) {
    if (!word || !word.trim()) return null;
    const cleanWord = word.trim();

    // 1. 優先查詢本機 FastAPI 後端 (/api/moji/search)
    const backendEndpoints = [
      `/api/moji/search?word=${encodeURIComponent(cleanWord)}`,
      `http://localhost:8000/api/moji/search?word=${encodeURIComponent(cleanWord)}`
    ];

    for (const ep of backendEndpoints) {
      try {
        const ctrl = new AbortController();
        const timeoutId = setTimeout(() => ctrl.abort(), 2000);
        const res = await fetch(ep, { signal: ctrl.signal });
        clearTimeout(timeoutId);
        if (res.ok) {
          const data = await res.json();
          if (data && data.status === 'success') {
            return {
              word: data.word || cleanWord,
              reading: data.reading || '',
              meaning: data.meaning || '',
              example: data.example || '',
              source: data.source || 'MOJi 辭書 (官方直接導出)'
            };
          }
        }
      } catch (e) {
        // 後端未啟動或連線超時，繼續嘗試其他路徑
      }
    }

    // 2. 嘗試調用 MOJi 原生 Parse 雲端 API (前端支援環境)
    try {
      const ctrl = new AbortController();
      const timeoutId = setTimeout(() => ctrl.abort(), 2500);
      const res = await fetch('https://api.mojidict.com/parse/functions/search-all', {
        method: 'POST',
        headers: {
          'X-Parse-Application-Id': 'E62VyFVLMiW7kvbtVq3p',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: cleanWord,
          types: [102, 103, 106]
        }),
        signal: ctrl.signal
      });
      clearTimeout(timeoutId);

      if (res.ok) {
        const data = await res.json();
        const resObj = (data && data.result && data.result.result) || {};
        const wList = (resObj.word && resObj.word.searchResult) || [];
        const exList = (resObj.example && resObj.example.searchResult) || [];

        if (wList.length > 0) {
          let best = wList.find(w => (w.title || '').split('|')[0].trim() === cleanWord) || wList[0];
          const parts = (best.title || '').split('|').map(s => s.trim());
          const reading = parts[1] || '';
          const meaning = this.toTraditional(best.excerpt || '');
          let example = '';
          if (exList.length > 0) {
            const ex0 = exList[0];
            const jpSent = (ex0.title || '').trim();
            const zhSent = this.toTraditional((ex0.excerpt || '').trim());
            example = jpSent && zhSent ? `${jpSent} (${zhSent})` : jpSent;
          }
          return {
            word: parts[0] || cleanWord,
            reading: reading,
            meaning: meaning,
            example: example,
            source: 'MOJi 辭書 (原生 API)'
          };
        }
      }
    } catch (e) {
      // 網路或 CORS 限制，進入本地辭書與備用模式
    }

    return null;
  }

  /**
   * 日語單字自動擴充 (深度整合 MOJi 辭書)
   */
  async enrichJapaneseWord(word, options = {}) {
    // 1. 優先直接使用 MOJi 辭書原生資料
    try {
      const moji = await this.fetchMojiDict(word);
      if (moji && (moji.meaning || moji.reading)) {
        return {
          front: word,
          reading: moji.reading || '',
          back: moji.meaning || '繁體中文釋義',
          example: moji.example || await this.generateJapaneseExample(word, moji.meaning, options.category),
          source: moji.source || 'MOJi 辭書',
          tags: options.category ? [options.category, 'MOJi辭書'] : ['MOJi辭書']
        };
      }
    } catch (e) {
      console.warn('[WordEnricher] MOJi 直連查詢異常，切換備用管道:', e);
    }

    // 2. 備用：呼叫 Google GTX Translate (自帶繁中翻譯與羅馬字拼音)
    try {
      const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=ja&tl=zh-TW&dt=t&dt=rm&q=${encodeURIComponent(word)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      let meaning = '';
      let romaji = '';

      if (data && data[0]) {
        // 中文翻譯
        meaning = data[0].map(item => item[0]).filter(Boolean).join('');
        // 羅馬字讀音
        if (data[0][1] && data[0][1][3]) {
          romaji = data[0][1][3];
        } else if (data[0][0] && data[0][0][3]) {
          romaji = data[0][0][3];
        }
      }

      // 將羅馬字讀音轉為平假名
      let reading = this.romajiToHiragana(romaji);
      if (!reading && /^[ぁ-んァ-ヶー]+$/.test(word)) {
        reading = word;
      }

      // 自動產生適合該分類的精美實用例句
      const example = await this.generateJapaneseExample(word, meaning, options.category);

      return {
        front: word,
        reading: reading,
        back: meaning || '繁體中文釋義',
        example: example,
        source: 'Google Translate',
        tags: options.category ? [options.category, '自動生成'] : ['自動生成']
      };
    } catch (e) {
      console.warn('[WordEnricher] 日文自動擴充降級處理:', e);
      return {
        front: word,
        reading: '',
        back: word,
        example: `${word}を使用します。(使用${word}。)`,
        source: '預設範本',
        tags: ['待補充']
      };
    }
  }

  /**
   * 免費英語單字自動生成
   */
  async enrichEnglishWord(word, options = {}) {
    try {
      let phonetic = '';
      let meaning = '';
      let example = '';

      // 先查 Google 翻譯
      const gUrl = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-TW&dt=t&q=${encodeURIComponent(word)}`;
      const gRes = await fetch(gUrl);
      if (gRes.ok) {
        const gData = await gRes.json();
        if (gData && gData[0]) {
          meaning = gData[0].map(i => i[0]).filter(Boolean).join('');
        }
      }

      // 再查 Free Dictionary API 取音標與例句
      try {
        const dUrl = `https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(word)}`;
        const dRes = await fetch(dUrl);
        if (dRes.ok) {
          const dData = await dRes.json();
          if (Array.isArray(dData) && dData.length > 0) {
            const entry = dData[0];
            phonetic = entry.phonetic || (entry.phonetics && entry.phonetics[0] && entry.phonetics[0].text) || '';
            
            // 尋找例句
            if (entry.meanings) {
              for (const m of entry.meanings) {
                if (m.definitions) {
                  for (const d of m.definitions) {
                    if (d.example) {
                      example = d.example;
                      break;
                    }
                  }
                }
                if (example) break;
              }
            }
          }
        }
      } catch (e) {
        // ignore dictionary api error
      }

      // 若有英文例句，翻譯成中文
      let fullExample = '';
      if (example) {
        const transExUrl = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-TW&dt=t&q=${encodeURIComponent(example)}`;
        const exRes = await fetch(transExUrl);
        let exZh = '';
        if (exRes.ok) {
          const exData = await exRes.json();
          if (exData && exData[0]) exZh = exData[0].map(i => i[0]).filter(Boolean).join('');
        }
        fullExample = `${example} (${exZh || ''})`;
      } else {
        fullExample = `We need to review the ${word} carefully. (我們需要仔細審查該項內容。)`;
      }

      return {
        front: word,
        reading: phonetic,
        back: meaning || word,
        example: fullExample,
        tags: options.category ? [options.category, '英語'] : ['英語']
      };
    } catch (e) {
      console.warn('[WordEnricher] 英文自動擴充失敗:', e);
      return {
        front: word,
        reading: '',
        back: word,
        example: `The ${word} is important.`,
        tags: ['待補充']
      };
    }
  }

  /**
   * 智慧生成符合上下文的日語例句並翻譯為繁中
   */
  async generateJapaneseExample(word, meaning, category = 'engineering') {
    let sentenceJp = '';
    
    // 依分類選擇最道地的句型範本
    if (category === 'engineering') {
      const templates = [
        `${word}の作業手順を事前に確認する。`,
        `現場で${word}の進捗状況を点検する。`,
        `${word}に関する安全対策を徹底する。`,
        `仕様書に基づいて${word}を実施する。`
      ];
      sentenceJp = templates[Math.floor(Math.random() * templates.length)];
    } else if (category === 'business') {
      const templates = [
        `${word}について明日の会議で議論する。`,
        `${word}の最新状況を上司に報告する。`,
        `今後の事業展開において${word}が重要となる。`
      ];
      sentenceJp = templates[Math.floor(Math.random() * templates.length)];
    } else {
      // 日常生活
      const templates = [
        `${word}について詳しく調べる。`,
        `毎日の生活の中で${word}を心がける。`,
        `友達と一緒に${word}を体験する。`
      ];
      sentenceJp = templates[Math.floor(Math.random() * templates.length)];
    }

    // 取得例句繁中翻譯
    try {
      const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=ja&tl=zh-TW&dt=t&q=${encodeURIComponent(sentenceJp)}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        const sentenceZh = data[0].map(i => i[0]).filter(Boolean).join('');
        return `${sentenceJp}(${sentenceZh})`;
      }
    } catch (e) {}

    return `${sentenceJp}`;
  }

  /**
   * 使用 Google Gemini API 進行專業級深度自動生成
   */
  async enrichViaGemini(word, options = {}) {
    const apiKey = this.settings.geminiApiKey;
    if (!apiKey) return null;

    const categoryPrompt = (options.category === 'engineering')
      ? '此單字用於營造/建築工程與現場監造施工場景。'
      : (options.category === 'daily')
      ? '此單字用於日本日常生活交流或觀光場景。'
      : '商務職場場景。';

    const prompt = `請為單字「${word}」提供詳細背誦資料。${categoryPrompt}
請以繁體中文回答，並輸出嚴格合法的 JSON 格式（不可包含 Markdown 或額外文字）：
{
  "reading": "讀音（日語填平假名，英語填音標）",
  "meaning": "繁體中文精確釋義（含詞性，如名詞、動詞）",
  "example": "例句原文(繁體中文例句翻譯)"
}`;

    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { responseMimeType: 'application/json' }
      })
    });

    if (!res.ok) throw new Error(`Gemini API 回應錯誤 ${res.status}`);
    const data = await res.json();
    const text = data.candidates[0].content.parts[0].text;
    const parsed = JSON.parse(text);

    return {
      front: word,
      reading: parsed.reading || '',
      back: parsed.meaning || '',
      example: parsed.example || '',
      tags: options.category ? [options.category, 'AI生成'] : ['AI生成']
    };
  }

  /**
   * 批次自動生成單字 (附進度回呼)
   */
  async batchEnrichWords(wordList, options = {}, onProgress = null) {
    const results = [];
    const total = wordList.length;

    for (let i = 0; i < total; i++) {
      const item = wordList[i];
      const word = typeof item === 'string' ? item : (item.front || item.word);
      if (!word || !word.trim()) continue;

      if (onProgress) {
        onProgress(i + 1, total, word);
      }

      // 若原有資料已經有完整釋義與讀音，則保留原資訊；否則進行自動生成
      if (typeof item === 'object' && item.back && item.reading && item.example) {
        results.push(item);
      } else {
        const enriched = await this.enrichWord(word, options);
        if (enriched) {
          // 合併既有資訊
          if (typeof item === 'object') {
            results.push(Object.assign({}, enriched, item, {
              reading: item.reading || enriched.reading,
              back: item.back || enriched.back,
              example: item.example || enriched.example
            }));
          } else {
            results.push(enriched);
          }
        }
        // 輕微間隔防被限流
        await new Promise(r => setTimeout(r, 120));
      }
    }

    return results;
  }

  /**
   * 將赫本式羅馬字轉換為平假名 (Hepburn Romaji to Hiragana)
   */
  romajiToHiragana(romaji) {
    if (!romaji) return '';
    let s = romaji.toLowerCase()
      .replace(/ō/g, 'ou')
      .replace(/ū/g, 'uu')
      .replace(/ā/g, 'aa')
      .replace(/ī/g, 'ii')
      .replace(/ē/g, 'ee')
      .replace(/'/g, '');

    const table = {
      'kya':'きゃ','kyu':'きゅ','kyo':'きょ',
      'sha':'しゃ','shu':'しゅ','sho':'しょ','shi':'し',
      'cha':'ちゃ','chu':'ちゅ','cho':'ちょ','chi':'ち','tsu':'つ',
      'nya':'にゃ','nyu':'にゅ','nyo':'にょ',
      'hya':'ひゃ','hyu':'ひゅ','hyo':'ひょ',
      'mya':'みゃ','myu':'みゅ','myo':'みょ',
      'rya':'りゃ','ryu':'りゅ','ryo':'りょ',
      'gya':'ぎゃ','gyu':'ぎゅ','gyo':'ぎょ',
      'ja':'じゃ','ju':'じゅ','jo':'じょ','ji':'じ',
      'bya':'びゃ','byu':'びゅ','byo':'びょ',
      'pya':'ぴゃ','pyu':'ぴゅ','pyo':'ぴょ',
      'ka':'か','ki':'き','ku':'く','ke':'け','ko':'こ',
      'sa':'さ','su':'す','se':'せ','so':'そ',
      'ta':'た','te':'て','to':'と',
      'na':'な','ni':'に','nu':'ぬ','ne':'ね','no':'の',
      'ha':'は','hi':'ひ','fu':'ふ','he':'へ','ho':'ほ',
      'ma':'ま','mi':'み','mu':'む','me':'め','mo':'も',
      'ya':'や','yu':'ゆ','yo':'よ',
      'ra':'ら','ri':'り','ru':'る','re':'れ','ro':'ろ',
      'wa':'わ','wo':'を',
      'ga':'が','gi':'ぎ','gu':'ぐ','ge':'げ','go':'ご',
      'za':'ざ','zu':'ず','ze':'ぜ','zo':'ぞ',
      'da':'だ','de':'で','do':'ど',
      'ba':'ば','bi':'び','bu':'ぶ','be':'べ','bo':'ぼ',
      'pa':'ぱ','pi':'ぴ','pu':'ぷ','pe':'ぺ','po':'ぽ',
      'a':'あ','i':'い','u':'う','e':'え','o':'お','n':'ん'
    };

    // 處理促音 (雙子音)
    s = s.replace(/([bcdfghjklmpqrstvwxyz])\1/g, 'っ$1');

    const keys = Object.keys(table).sort((a, b) => b.length - a.length);
    for (const k of keys) {
      s = s.split(k).join(table[k]);
    }
    return s;
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = WordEnricher;
} else {
  window.WordEnricher = WordEnricher;
}
