/**
 * AnkiFlash 內建精選詞庫與預設牌組資料
 * 包含分類體系：工程營造、日常生活、商務職場、JLPT 檢定
 */

const BUILTIN_CATEGORIES = [
  { id: 'all', name: '全部牌組', icon: '🌟' },
  { id: 'engineering', name: '工程營造', icon: '🏗️' },
  { id: 'daily', name: '日常生活', icon: '🍵' },
  { id: 'business', name: '商務職場', icon: '💼' },
  { id: 'jlpt', name: 'JLPT 檢定', icon: '🇯🇵' }
];

const BUILTIN_DECKS = [
  // --- 工程營造類別 (Engineering & Construction) ---
  {
    id: 'deck_construction_core',
    name: '🏗️ 日語營造工程核心專業術語',
    desc: '日商營造工程、現場施工、品管監造、安全衛生必備實用日文詞彙。',
    category: 'engineering',
    icon: '🏗️',
    color: '#0284c7' // 施工藍
  },
  {
    id: 'deck_safety_ky',
    name: '🦺 工地安全衛生與危險預知 (KY)',
    desc: '現場安全晨會、安全帶防護、KY危險預知活動、災害防範關鍵用語。',
    category: 'engineering',
    icon: '🦺',
    color: '#ea580c' // 安全橘
  },

  // --- 日常生活類別 (Daily Life) ---
  {
    id: 'deck_daily_life',
    name: '🍵 實用日本日常生活會話單字',
    desc: '涵蓋餐飲、交通、購物、就醫問診、租屋與生活交流常用單字。',
    category: 'daily',
    icon: '🍵',
    color: '#10b981' // 翠綠
  },

  // --- 商務職場類別 (Business) ---
  {
    id: 'deck_toeic',
    name: '💼 TOEIC 多益高頻商務核心 500 字',
    desc: '辦公室溝通、商務書信、合約談判最常出現的關鍵英文單字。',
    category: 'business',
    icon: '💼',
    color: '#06b6d4'
  },

  // --- JLPT 檢定類別 (JLPT) ---
  {
    id: 'deck_jlpt_n5',
    name: '🇯🇵 JLPT N5 基礎生活核心單字',
    desc: '日語初學者必背，涵蓋基礎動詞、形容詞與生活名詞。',
    category: 'jlpt',
    icon: '🌸',
    color: '#eab308'
  },
  {
    id: 'deck_jlpt_n4',
    name: '🇯🇵 JLPT N4 初中階生活日語',
    desc: '進階日常溝通、旅遊對話、職場基礎用詞。',
    category: 'jlpt',
    icon: '🍊',
    color: '#f97316'
  },
  {
    id: 'deck_jlpt_n3',
    name: '🇯🇵 JLPT N3 中級實用單字',
    desc: '銜接初階與高階的關鍵轉折點，新聞與日常常見詞彙。',
    category: 'jlpt',
    icon: '🌿',
    color: '#10b981'
  },
  {
    id: 'deck_jlpt_n2',
    name: '🇯🇵 JLPT N2 商務職場高頻詞彙',
    desc: '求職就業、日商工作必備中高階單字與抽象觀念詞。',
    category: 'jlpt',
    icon: '🔷',
    color: '#3b82f6'
  },
  {
    id: 'deck_jlpt_n1',
    name: '🇯🇵 JLPT N1 高階論說與專門詞彙',
    desc: '日檢最高榮譽，包含各領域學術、時事評論與深奧語彙。',
    category: 'jlpt',
    icon: '👑',
    color: '#8b5cf6'
  }
];

const BUILTIN_CARDS = [
  // ==========================================
  // 【工程營造類別】核心單字 (極具實務價值)
  // ==========================================
  {
    deckId: 'deck_construction_core',
    front: '施工',
    reading: 'せこう / しこう',
    back: '施工、工程進行 (名詞/する動詞)',
    example: '施工図面に従って正確に施工を進める。(依照施工圖說正確推進施工。)',
    tags: ['工程', '施工']
  },
  {
    deckId: 'deck_construction_core',
    front: '養生',
    reading: 'ようじょう',
    back: '養護、保護防護措施 (混凝土養護、成品防護包覆) (名詞/する動詞)',
    example: 'コンクリート打設後は十分な湿潤養生を行う。(混凝土澆置後須進行充分的濕潤養護。)',
    tags: ['工程', '品質']
  },
  {
    deckId: 'deck_construction_core',
    front: '足場',
    reading: 'あしば',
    back: '施工架、鷹架、立足點 (名詞)',
    example: '高所作業の前に外部足場の点検を実施する。(在高空作業前實施外側施工架點檢。)',
    tags: ['工程', '安全']
  },
  {
    deckId: 'deck_construction_core',
    front: '躯体',
    reading: 'くたい',
    back: '建築物結構體、主體骨架 (名詞)',
    example: '躯体工事が予定通り完了しました。(結構體工程已如期完成。)',
    tags: ['工程', '結構']
  },
  {
    deckId: 'deck_construction_core',
    front: '配筋',
    reading: 'はいきん',
    back: '鋼筋配置、綁紮鋼筋 (名詞/する動詞)',
    example: 'コンクリートを打設する前に配筋検査を行う。(在澆置混凝土之前進行配筋檢查。)',
    tags: ['工程', '品管']
  },
  {
    deckId: 'deck_construction_core',
    front: '型枠',
    reading: 'かたわく',
    back: '模板、模具 (名詞)',
    example: '型枠の建て込み精度を厳格に確認する。(嚴格確認模板組裝豎立精度。)',
    tags: ['工程', '施工']
  },
  {
    deckId: 'deck_construction_core',
    front: '打設',
    reading: 'だせつ',
    back: '混凝土澆置、灌漿 (名詞/する動詞)',
    example: '明日の朝一番から耐力壁のコンクリート打設を開始する。(明早第一時間開始耐力牆混凝土澆置。)',
    tags: ['工程', '施工']
  },
  {
    deckId: 'deck_construction_core',
    front: '墨出し',
    reading: 'すみだし',
    back: '放樣、彈墨線基準標記 (名詞/する動詞)',
    example: '基礎の基準墨出しを狂いなく実施する。(準確無誤地實施基礎基準放樣。)',
    tags: ['工程', '測量']
  },
  {
    deckId: 'deck_construction_core',
    front: '是正',
    reading: 'ぜせい',
    back: '改善、修正、缺失改善 (名詞/する動詞)',
    example: '監理者からの指摘事項を速やかに是正する。(迅速改善監造建築師指出的缺失事項。)',
    tags: ['工程', '品管']
  },
  {
    deckId: 'deck_construction_core',
    front: '立会い',
    reading: 'たちあい',
    back: '會同、會勘、現場監驗 (名詞/する動詞)',
    example: '施主と設計者の立会いのもとで中間検査を行う。(在業主與建築師會同下進行期中查驗。)',
    tags: ['工程', '監造']
  },
  {
    deckId: 'deck_construction_core',
    front: '工期',
    reading: 'こうき',
    back: '施工工期 (名詞)',
    example: '台風の影響で遅れた工期を挽回する。(挽回因颱風影響延誤的工期。)',
    tags: ['工程', '管理']
  },
  {
    deckId: 'deck_construction_core',
    front: '出来高',
    reading: 'できだか',
    back: '工程進度成效、估驗計價完成量 (名詞)',
    example: '今月の工事出来高を査定して報告書を作成する。(評定本月工程完成進度量並製作報告。)',
    tags: ['工程', '計價']
  },

  // --- 工地安全衛生與危險預知 (KY) ---
  {
    deckId: 'deck_safety_ky',
    front: '安全帯',
    reading: 'あんぜんたい',
    back: '安全帶、防墜背帶 (名詞)',
    example: '高所作業では必ずフルハーネス型安全帯を着用すること。(高空作業務必佩戴全身背負式安全帶。)',
    tags: ['安全', '防護']
  },
  {
    deckId: 'deck_safety_ky',
    front: '危険予知 (KY活動)',
    reading: 'きけんよち',
    back: '危險預知、KY活動 (作業前預先找出危險因子並制定對策) (名詞)',
    example: '作業開始前に全員でKY活動を行い、災害ゼロを目指す。(作業開始前全員實施KY危險預知，力求零災害。)',
    tags: ['安全', '晨會']
  },
  {
    deckId: 'deck_safety_ky',
    front: '指差呼称',
    reading: 'しさこしょう',
    back: '指差確認、指差指差呼喚 (手指標的物並大聲唸出確認) (名詞)',
    example: '合図の確認は指差呼称で徹底する。(信號確認徹底採用指差確認。)',
    tags: ['安全', '操作']
  },
  {
    deckId: 'deck_safety_ky',
    front: '開口部',
    reading: 'かいこうぶ',
    back: '開口部、樓板留洞 (名詞)',
    example: '床の開口部には必ず手すりと蓋を設置し、墜落を防ぐ。(樓板開口處務必設置欄杆與封板蓋，防止墜落。)',
    tags: ['安全', '防墜']
  },

  // ==========================================
  // 【日常生活類別】實用單字
  // ==========================================
  {
    deckId: 'deck_daily_life',
    front: '買い物',
    reading: 'かいもの',
    back: '購物、買東西 (名詞/する動詞)',
    example: '週末にスーパーへ買い物に行きます。(週末去超市買東西。)',
    tags: ['日常', '生活']
  },
  {
    deckId: 'deck_daily_life',
    front: '乗り換える',
    reading: 'のりかえる',
    back: '轉乘 (電車/捷運/公車) (動詞)',
    example: '新宿駅で山手線に乗り換えてください。(請在新宿站轉乘山手線。)',
    tags: ['日常', '交通']
  },
  {
    deckId: 'deck_daily_life',
    front: 'お会計',
    reading: 'おかいけい',
    back: '結帳、買單 (名詞)',
    example: 'すみません、別々でお会計をお願いできますか。(不好意思，可以分開結帳買單嗎？)',
    tags: ['日常', '餐飲']
  },
  {
    deckId: 'deck_daily_life',
    front: '体調',
    reading: 'たいちょう',
    back: '身體狀況、健康狀況 (名詞)',
    example: '体調が悪いので、少し休ませてください。(身體不太舒服，請讓我稍微休息一下。)',
    tags: ['日常', '健康']
  },
  {
    deckId: 'deck_daily_life',
    front: '問い合わせ',
    reading: 'といあわせ',
    back: '諮詢、詢問、查詢 (名詞)',
    example: '荷物の配送状況について問い合わせる。(查詢包裹貨物的配送進度狀況。)',
    tags: ['日常', '通訊']
  },

  // ==========================================
  // 【商務英語 TOEIC】
  // ==========================================
  {
    deckId: 'deck_toeic',
    front: 'Implement',
    reading: '[ˈɪm.plə.ment]',
    back: '實施、執行、落實 (v.)',
    example: 'We need to implement the new site safety rules immediately. (我們需要立即落實新工地安全規則。)',
    tags: ['商務', '動詞']
  },
  {
    deckId: 'deck_toeic',
    front: 'Specifications',
    reading: '[ˌspes.ə.fɪˈkeɪ.ʃənz]',
    back: '規格、工程規範、技術規格書 (n.)',
    example: 'The building must be constructed according to structural specifications. (建築必須嚴格按照結構規格建造。)',
    tags: ['工程', '商務']
  },
  {
    deckId: 'deck_toeic',
    front: 'Contractor',
    reading: '[ˈkɑːn.træk.tɚ]',
    back: '承包商、營造商、包商 (n.)',
    example: 'The general contractor is responsible for on-site management. (總承包營造商負責工地現場管理。)',
    tags: ['工程', '商務']
  },

  // ==========================================
  // 【JLPT 檢定類別】
  // ==========================================
  {
    deckId: 'deck_jlpt_n5',
    front: '食べる',
    reading: 'たべる',
    back: '吃 (動詞 二類)',
    example: '朝ごはんを食べる。(吃早餐。)',
    tags: ['JLPT_N5', '動詞']
  },
  {
    deckId: 'deck_jlpt_n4',
    front: '案内',
    reading: 'あんない',
    back: '引導、帶路、介紹 (名詞/する動詞)',
    example: '東京の街を案内します。(帶你遊覽導覽東京街頭。)',
    tags: ['JLPT_N4', '名詞']
  },
  {
    deckId: 'deck_jlpt_n3',
    front: '相変わらず',
    reading: 'あいかわらず',
    back: '依然、照舊、一如既往 (副詞)',
    example: '彼は相変わらず元気にしている。(他依然過得很有精神。)',
    tags: ['JLPT_N3', '副詞']
  },
  {
    deckId: 'deck_jlpt_n2',
    front: '把握',
    reading: 'はあく',
    back: '掌握、理解、領會 (名詞/する動詞)',
    example: '現場の進捗状況を正確に把握することが重要だ。(準確掌握工地現場的進度狀況至關重要。)',
    tags: ['JLPT_N2', '商務']
  },
  {
    deckId: 'deck_jlpt_n1',
    front: '模索',
    reading: 'もさく',
    back: '摸索、探求解決之道 (名詞/する動詞)',
    example: '新しい工法と安全対策を模索している。(正在摸索新的施工工法與安全對策。)',
    tags: ['JLPT_N1', '高階']
  }
];

if (typeof window !== 'undefined') {
  window.BUILTIN_CATEGORIES = BUILTIN_CATEGORIES;
  window.BUILTIN_DECKS = BUILTIN_DECKS;
  window.BUILTIN_CARDS = BUILTIN_CARDS;
}
if (typeof globalThis !== 'undefined') {
  globalThis.BUILTIN_CATEGORIES = BUILTIN_CATEGORIES;
  globalThis.BUILTIN_DECKS = BUILTIN_DECKS;
  globalThis.BUILTIN_CARDS = BUILTIN_CARDS;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { BUILTIN_CATEGORIES, BUILTIN_DECKS, BUILTIN_CARDS };
}

