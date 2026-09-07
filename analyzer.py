# -*- coding: utf-8 -*-
"""
日文閱讀助手 - 核心解析引擎 (Analyzer Engine)
包含：
1. Janome 形態素分詞與漢字振假名生成
2. JLPT N1~N5 單字庫等級匹配與詞性解析
3. 《絵でわかる日本語》941 條文法匹配引擎 (GrammarMatcher)
4. 網頁正文抽取 (URL Extractor)
5. Google Translate 繁體中文翻譯引擎
"""

import os
import re
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from janome.tokenizer import Tokenizer

# 假名轉換表
KATAKANA_START = 0x30A1
KATAKANA_END = 0x30F6

def kata_to_hira(text: str) -> str:
    """將片假名轉為平假名"""
    if not text or text == '*':
        return ''
    res = []
    for c in text:
        code = ord(c)
        if KATAKANA_START <= code <= KATAKANA_END:
            res.append(chr(code - 96))
        else:
            res.append(c)
    return ''.join(res)

def make_ruby(surface: str, reading_kata: str) -> str:
    """
    智能生成漢字與振假名 ruby 標籤
    例如：
      時間, ジカン -> <ruby>時間<rt>じかん</rt></ruby>
      悩んだ, ナヤンダ -> <ruby>悩<rt>なや</rt></ruby>んだ
      食べました, タベマシタ -> <ruby>食<rt>た</rt></ruby>べました
    """
    if not reading_kata or reading_kata == '*':
        return surface
    
    reading = kata_to_hira(reading_kata)
    has_kanji = bool(re.search(r'[\u4e00-\u9faf]', surface))
    if not has_kanji:
        return surface
        
    # 全漢字情況
    if re.fullmatch(r'[\u4e00-\u9faf]+', surface):
        return f'<ruby>{surface}<rt>{reading}</rt></ruby>'
        
    # 比對尾部送假名 (okurigana)
    common_suffix_len = 0
    while (common_suffix_len < len(surface) and 
           common_suffix_len < len(reading) and 
           surface[-1 - common_suffix_len] == reading[-1 - common_suffix_len]):
        common_suffix_len += 1
        
    # 比對頭部前綴 (如有假名前綴)
    common_prefix_len = 0
    while (common_prefix_len < (len(surface) - common_suffix_len) and 
           common_prefix_len < (len(reading) - common_suffix_len) and 
           surface[common_prefix_len] == reading[common_prefix_len]):
        common_prefix_len += 1
        
    prefix = surface[:common_prefix_len]
    kanji_part = surface[common_prefix_len: len(surface) - common_suffix_len if common_suffix_len > 0 else len(surface)]
    suffix = surface[len(surface) - common_suffix_len:] if common_suffix_len > 0 else ''
    
    reading_kanji = reading[common_prefix_len: len(reading) - common_suffix_len if common_suffix_len > 0 else len(reading)]
    
    if kanji_part and reading_kanji:
        return f'{prefix}<ruby>{kanji_part}<rt>{reading_kanji}</rt></ruby>{suffix}'
    return f'<ruby>{surface}<rt>{reading}</rt></ruby>'

# 定義各層級語法與助詞清單，確保文型與複合助詞不被拆解為零碎助詞
SPECIAL_GRAMMAR_PATTERNS = [
    {'pattern': 'ながらも', 'title': '〜ながら（も）（逆接）', 'level': 'N2', 'category': '文型', 'grammar_id': 551},
    {'pattern': 'ながら', 'title': '〜ながら（同時進行・逆接）', 'level': 'N3', 'category': '文型', 'grammar_id': 550},
    {'pattern': 'つつも', 'title': '〜つつ（も）', 'level': 'N2', 'category': '文型', 'grammar_id': 330},
    {'pattern': 'つつ', 'title': '〜つつ', 'level': 'N2', 'category': '文型', 'grammar_id': 331},
    {'pattern': 'に伴い', 'title': '〜に伴って・〜に伴い', 'level': 'N2', 'category': '文型', 'grammar_id': 663},
    {'pattern': 'に伴って', 'title': '〜に伴って・〜に伴い', 'level': 'N2', 'category': '文型', 'grammar_id': 663},
    {'pattern': 'にほかならない', 'title': '〜にほかならない', 'level': 'N1', 'category': '文型', 'grammar_id': 676},
    {'pattern': 'わけにはいかない', 'title': '〜わけにはいかない', 'level': 'N2', 'category': '文型', 'grammar_id': 897},
    {'pattern': 'のみならず', 'title': '〜のみならず', 'level': 'N2', 'category': '文型', 'grammar_id': 704},
    {'pattern': '一方である', 'title': '〜一方だ', 'level': 'N3', 'category': '文型', 'grammar_id': 24},
    {'pattern': '一方で', 'title': '〜一方で', 'level': 'N3', 'category': '文型', 'grammar_id': 25},
    {'pattern': '一方だ', 'title': '〜一方だ', 'level': 'N3', 'category': '文型', 'grammar_id': 24},
    {'pattern': 'あげく', 'title': '〜あげく（に）', 'level': 'N3', 'category': '文型', 'grammar_id': 9},
    {'pattern': 'あまり', 'title': '〜あまり', 'level': 'N2', 'category': '文型', 'grammar_id': 11},
    {'pattern': 'がち', 'title': '〜がちだ', 'level': 'N3', 'category': '文型', 'grammar_id': 71}
]

COMPOUND_PARTICLES = [
    {'pattern': 'についての', 'title': '複合助詞：についての', 'category': '複合助詞', 'base': 'について'},
    {'pattern': 'について', 'title': '複合助詞：について', 'category': '複合助詞', 'base': 'について'},
    {'pattern': 'に関する', 'title': '複合助詞：に関する', 'category': '複合助詞', 'base': 'に関して'},
    {'pattern': 'に関して', 'title': '複合助詞：に関して', 'category': '複合助詞', 'base': 'に関して'},
    {'pattern': 'に対する', 'title': '複合助詞：に対する', 'category': '複合助詞', 'base': 'に対して'},
    {'pattern': 'に対して', 'title': '複合助詞：に対して', 'category': '複合助詞', 'base': 'に対して'},
    {'pattern': 'にとっての', 'title': '複合助詞：にとっての', 'category': '複合助詞', 'base': 'にとって'},
    {'pattern': 'にとって', 'title': '複合助詞：にとって', 'category': '複合助詞', 'base': 'にとって'},
    {'pattern': 'としての', 'title': '複合助詞：としての', 'category': '複合助詞', 'base': 'として'},
    {'pattern': 'として', 'title': '複合助詞：として', 'category': '複合助詞', 'base': 'として'},
    {'pattern': 'をめぐって', 'title': '複合助詞：をめぐって', 'category': '複合助詞', 'base': 'をめぐって'},
    {'pattern': 'をめぐる', 'title': '複合助詞：をめぐる', 'category': '複合助詞', 'base': 'をめぐって'},
    {'pattern': 'を通して', 'title': '複合助詞：を通して', 'category': '複合助詞', 'base': 'を通じて'},
    {'pattern': 'を通じて', 'title': '複合助詞：を通じて', 'category': '複合助詞', 'base': 'を通じて'},
    {'pattern': 'をもとにして', 'title': '複合助詞：をもとにして', 'category': '複合助詞', 'base': 'をもとに'},
    {'pattern': 'をもとに', 'title': '複合助詞：をもとに', 'category': '複合助詞', 'base': 'をもとに'},
    {'pattern': 'にあたって', 'title': '複合助詞：にあたって', 'category': '複合助詞', 'base': 'にあたって'},
    {'pattern': 'にあたり', 'title': '複合助詞：にあたり', 'category': '複合助詞', 'base': 'にあたって'},
    {'pattern': 'に際して', 'title': '複合助詞：に際して', 'category': '複合助詞', 'base': 'に際して'},
    {'pattern': 'に沿って', 'title': '複合助詞：に沿って', 'category': '複合助詞', 'base': 'に沿って'},
    {'pattern': 'に応じて', 'title': '複合助詞：に応じて', 'category': '複合助詞', 'base': 'に応じて'},
    {'pattern': 'に先立って', 'title': '複合助詞：に先立って', 'category': '複合助詞', 'base': 'に先立って'},
    {'pattern': 'にかけて', 'title': '複合助詞：にかけて', 'category': '複合助詞', 'base': 'にかけて'},
    {'pattern': 'につれて', 'title': '複合助詞：につれて', 'category': '複合助詞', 'base': 'につれて'},
    {'pattern': 'にわたって', 'title': '複合助詞：にわたって', 'category': '複合助詞', 'base': 'にわたって'},
    {'pattern': 'をはじめ', 'title': '複合助詞：をはじめ', 'category': '複合助詞', 'base': 'をはじめ'},
    {'pattern': 'によって', 'title': '複合助詞：によって', 'category': '複合助詞', 'base': 'によって'},
    {'pattern': 'により', 'title': '複合助詞：により', 'category': '複合助詞', 'base': 'によって'},
    {'pattern': 'による', 'title': '複合助詞：による', 'category': '複合助詞', 'base': 'によって'},
    {'pattern': 'に伴って', 'title': '複合助詞：に伴って', 'category': '複合助詞', 'base': 'に伴って'},
    {'pattern': 'に伴い', 'title': '複合助詞：に伴い', 'category': '複合助詞', 'base': 'に伴って'},
    {'pattern': 'に伴う', 'title': '複合助詞：に伴う', 'category': '複合助詞', 'base': 'に伴って'},
    {'pattern': 'において', 'title': '複合助詞：において', 'category': '複合助詞', 'base': 'において'},
    {'pattern': 'における', 'title': '複合助詞：における', 'category': '複合助詞', 'base': 'において'},
    {'pattern': 'に比べて', 'title': '複合助詞：に比べて', 'category': '複合助詞', 'base': 'に比べて'}
]

ADVERBIAL_PARTICLES = [
    {'pattern': 'ばかりか', 'title': '副助詞：ばかりか', 'category': '副助詞', 'base': 'ばかりか'},
    {'pattern': 'ばかりでなく', 'title': '副助詞：ばかりでなく', 'category': '副助詞', 'base': 'ばかりでなく'},
    {'pattern': 'ばかり', 'title': '副助詞：ばかり', 'category': '副助詞', 'base': 'ばかり'},
    {'pattern': 'くらい', 'title': '副助詞：くらい', 'category': '副助詞', 'base': 'くらい'},
    {'pattern': 'ぐらい', 'title': '副助詞：ぐらい', 'category': '副助詞', 'base': 'くらい'},
    {'pattern': 'ほど', 'title': '副助詞：ほど', 'category': '副助詞', 'base': 'ほど'},
    {'pattern': 'だけ', 'title': '副助詞：だけ', 'category': '副助詞', 'base': 'だけ'},
    {'pattern': 'のみ', 'title': '副助詞：のみ', 'category': '副助詞', 'base': 'のみ'},
    {'pattern': 'しか', 'title': '副助詞：しか', 'category': '副助詞', 'base': 'しか'},
    {'pattern': 'さえ', 'title': '副助詞：さえ', 'category': '副助詞', 'base': 'さえ'},
    {'pattern': 'こそ', 'title': '副助詞：こそ', 'category': '副助詞', 'base': 'こそ'},
    {'pattern': 'など', 'title': '副助詞：など', 'category': '副助詞', 'base': 'など'},
    {'pattern': 'なんか', 'title': '副助詞：なんか', 'category': '副助詞', 'base': 'なんか'},
    {'pattern': 'なんて', 'title': '副助詞：なんて', 'category': '副助詞', 'base': 'なんて'},
    {'pattern': 'ずつ', 'title': '副助詞：ずつ', 'category': '副助詞', 'base': 'ずつ'},
    {'pattern': 'は', 'title': '係助詞：は', 'category': '副助詞', 'base': 'は'},
    {'pattern': 'も', 'title': '係助詞：も', 'category': '副助詞', 'base': 'も'}
]

CONJUNCTIVE_PARTICLES = [
    {'pattern': 'ものの', 'title': '接續助詞：ものの', 'category': '接續助詞', 'base': 'ものの'},
    {'pattern': 'ので', 'title': '接續助詞：ので', 'category': '接續助詞', 'base': 'ので'},
    {'pattern': 'のに', 'title': '接續助詞：のに', 'category': '接續助詞', 'base': 'のに'},
    {'pattern': 'ても', 'title': '接續助詞：ても', 'category': '接續助詞', 'base': 'ても'},
    {'pattern': 'でも', 'title': '接續助詞：でも', 'category': '接續助詞', 'base': 'でも'}
]

CASE_PARTICLES = [
    {'pattern': 'から', 'title': '格助詞：から', 'category': '格助詞', 'base': 'から'},
    {'pattern': 'より', 'title': '格助詞：より', 'category': '格助詞', 'base': 'より'},
    {'pattern': 'まで', 'title': '格助詞：まで', 'category': '格助詞', 'base': 'まで'},
    {'pattern': 'が', 'title': '格助詞：が', 'category': '格助詞', 'base': 'が'},
    {'pattern': 'を', 'title': '格助詞：を', 'category': '格助詞', 'base': 'を'},
    {'pattern': 'に', 'title': '格助詞：に', 'category': '格助詞', 'base': 'に'},
    {'pattern': 'で', 'title': '格助詞：で', 'category': '格助詞', 'base': 'で'},
    {'pattern': 'へ', 'title': '格助詞：へ', 'category': '格助詞', 'base': 'へ'},
    {'pattern': 'と', 'title': '格助詞：と', 'category': '格助詞', 'base': 'と'},
    {'pattern': 'の', 'title': '格助詞：の', 'category': '格助詞', 'base': 'の'}
]

class JapaneseAnalyzer:
    def __init__(self, grammar_path: str = "grammar_data.json", jlpt_path: str = "jlpt_vocab_all.json", particle_path: str = "particle_data.json"):
        self.tokenizer = Tokenizer()
        self.grammars = []
        self.grammar_patterns = []
        self.grammar_id_map = {}
        self.jlpt_vocab = {}
        self.particle_data = {}
        
        # 載入 941 條文法資料庫
        if os.path.exists(grammar_path):
            try:
                with open(grammar_path, "r", encoding="utf-8") as f:
                    self.grammars = json.load(f)
                self.grammar_id_map = {g.get("id"): g for g in self.grammars if "id" in g}
                self._build_grammar_patterns()
                print(f"[JapaneseAnalyzer] 成功載入 {len(self.grammars)} 條文法資料庫")
            except Exception as e:
                print(f"[JapaneseAnalyzer] 載入文法資料庫失敗: {e}")

        # 載入助詞與代用文型知識庫
        if os.path.exists(particle_path):
            try:
                with open(particle_path, "r", encoding="utf-8") as f:
                    self.particle_data = json.load(f)
                print(f"[JapaneseAnalyzer] 成功載入 {len(self.particle_data)} 組助詞代用與換句話說資料庫")
            except Exception as e:
                print(f"[JapaneseAnalyzer] 載入助詞資料庫失敗: {e}")
                
        # 載入 JLPT 單字庫
        if os.path.exists(jlpt_path):
            try:
                with open(jlpt_path, "r", encoding="utf-8") as f:
                    self.jlpt_vocab = json.load(f)
                print(f"[JapaneseAnalyzer] 成功載入 {len(self.jlpt_vocab)} 筆 JLPT 單字庫")
            except Exception as e:
                print(f"[JapaneseAnalyzer] 載入 JLPT 單字庫失敗: {e}")
                
        # 詞性中文對照表
        self.pos_map = {
            "名詞": "名詞",
            "動詞": "動詞",
            "形容詞": "形容詞",
            "副詞": "副詞",
            "助詞": "助詞",
            "助動詞": "助動詞",
            "接続詞": "接續詞",
            "連体詞": "連體詞",
            "感動詞": "感嘆詞",
            "記號": "符號",
            "フィラー": "語氣詞",
            "その他": "其他"
        }

    def _build_grammar_patterns(self):
        """編譯文法搜尋索引，依照長度由長至短排序以優先匹配長句型"""
        self.grammar_patterns = []
        for g in self.grammars:
            raw_title = g.get("title", "").strip()
            # 去除前綴 〜、~
            key = re.sub(r'^[〜~・\s]+', '', raw_title)
            # 分割多個文法變體（例如：〜かける・〜かけのN）
            sub_titles = re.split(r'[・／/]', key)
            
            variants = []
            for sub in sub_titles:
                # 去除圓圈數字與末端標籤
                cleaned = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩]', '', sub)
                # 處理可選助詞（如：あげく（に）、以上（は）、ことに（は））
                m_opt = re.search(r'（([にはでとがをも]+)）|\(([にはでとがをも]+)\)', cleaned)
                if m_opt:
                    particle = m_opt.group(1) or m_opt.group(2)
                    base = re.sub(r'（[^\)にはでとがをも]+）|\([^\)にはでとがをも]+\)', '', cleaned)
                    v1 = re.sub(r'（[にはでとがをも]+）|\([にはでとがをも]+\)', particle, base)
                    v2 = re.sub(r'（[にはでとがをも]+）|\([にはでとがをも]+\)', '', base)
                    candidates = [v1, v2]
                else:
                    base = re.sub(r'（.*?）|\(.*?\)', '', cleaned)
                    candidates = [base]
                    
                for cand in candidates:
                    # 去除多餘符號及 N、NAV 代稱
                    c = re.sub(r'^[〜~・\s]+', '', cand)
                    c = re.sub(r'[〜~・\s]+$', '', c)
                    c = re.sub(r'[の\s]*[NAV]$', '', c)
                    c = c.strip()
                    if len(c) >= 2:
                        variants.append(c)
                        
            # 去重後加入比對清單
            for v_clean in set(variants):
                self.grammar_patterns.append({
                    "pattern": v_clean,
                    "data": g
                })
                    
        # 優先比對較長的文型（如「〜わけにはいかない」比「〜わけ」優先）
        self.grammar_patterns.sort(key=lambda x: len(x["pattern"]), reverse=True)

    def find_grammars(self, sentence_text: str) -> List[Dict[str, Any]]:
        """在句子中搜尋符合的 941 條文法"""
        found = []
        matched_spans = [] # 記錄已匹配的位置區間避免完全重疊
        
        for p_info in self.grammar_patterns:
            pat = p_info["pattern"]
            g_data = p_info["data"]
            
            # 尋找所有出現位置
            start_idx = 0
            while True:
                pos = sentence_text.find(pat, start_idx)
                if pos == -1:
                    break
                end_pos = pos + len(pat)
                
                # 特殊防誤判規則：如「ちゃ」不可匹配於「ちゃんと」中
                if pat in ['ちゃ', 'じゃ'] and end_pos < len(sentence_text) and sentence_text[end_pos] in ['ん', 'ン']:
                    start_idx = pos + 1
                    continue
                
                # 檢查是否有更長模式已經覆蓋此區間
                is_overlap = any(s <= pos and end_pos <= e for s, e in matched_spans)
                if not is_overlap:
                    matched_spans.append((pos, end_pos))
                    found.append({
                        "id": g_data.get("id"),
                        "title": g_data.get("title"),
                        "clean_title": g_data.get("clean_title"),
                        "level": g_data.get("level"),
                        "category": g_data.get("category", ""),
                        "form": g_data.get("form", ""),
                        "meaningZh": g_data.get("meaningZh", ""),
                        "meaningJa": g_data.get("meaningJa", ""),
                        "example": g_data.get("example", ""),
                        "exampleRuby": g_data.get("exampleRuby", ""),
                        "translation": g_data.get("translation", ""),
                        "note": g_data.get("note", ""),
                        "sourceUrl": g_data.get("sourceUrl", ""),
                        "matched_text": pat,
                        "start": pos,
                        "end": end_pos
                    })
                start_idx = pos + 1
                
        # 依在句子中的出現順序排序
        found.sort(key=lambda x: x["start"])
        return found

    def get_jlpt_level(self, base_form: str, surface: str, reading_hira: str) -> Optional[str]:
        """查核詞彙的 JLPT 等級 (N1~N5)"""
        candidates = [base_form, surface, reading_hira]
        for c in candidates:
            if c and c in self.jlpt_vocab:
                entries = self.jlpt_vocab[c]
                if entries and isinstance(entries, list):
                    lvl_num = entries[0].get("level")
                    if lvl_num in [1, 2, 3, 4, 5]:
                        return f"N{lvl_num}"
        return None

    def translate_to_traditional_chinese(self, text: str) -> str:
        """透過 Google Translate 免費端點將日語翻譯為繁體中文"""
        if not text.strip():
            return ""
        try:
            url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=ja&tl=zh-TW&dt=t&q=" + urllib.parse.quote(text)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=6) as response:
                content = response.read().decode("utf-8")
                data = json.loads(content)
                result = "".join([item[0] for item in data[0] if item and item[0]])
                return result
        except Exception as e:
            print(f"[Translate Error]: {e}")
            return ""

    def split_sentences(self, text: str) -> List[str]:
        """將日文長文分句（保留標點符號與換行結構）"""
        raw_lines = text.splitlines()
        sentences = []
        for line in raw_lines:
            line_str = line.strip()
            if not line_str:
                continue
            parts = re.split(r'([。！？!?]+)', line_str)
            for i in range(0, len(parts), 2):
                s = parts[i]
                p = parts[i+1] if i+1 < len(parts) else ""
                combined = (s + p).strip()
                if combined:
                    sentences.append(combined)
        return sentences

    def analyze_sentence_hierarchy(self, text: str) -> List[Dict[str, Any]]:
        """
        以階層鎖定防拆解演算法（Non-overlapping Hierarchical Segmenter）：
        1. 文型／句型（941 文法庫及〜ながらも、〜に伴い等複合句型）：優先鎖定，嚴禁拆解！
        2. 複合助詞（について、に対して、として等）：第二優先鎖定
        3. 接續助詞（ものの、ので、のに、ても等）
        4. 副助詞／係助詞（は、も、ばかり、だけ、さえ、こそ等）
        5. 格助詞（が、を、に、で、へ、と、から、より、まで、の）
        """
        occupied = [False] * len(text)
        elements = []

        # 1. 文型層級 (第一優先匹配並鎖定位置)
        all_gp = list(SPECIAL_GRAMMAR_PATTERNS)
        for g in self.grammars:
            raw = g.get('title', '').strip()
            cleaned = re.sub(r'^[〜~・\s]+', '', raw)
            for sub in re.split(r'[・／/]', cleaned):
                sub_c = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩]', '', sub)
                m_opt = re.search(r'（([にはでとがをも]+)）|\(([にはでとがをも]+)\)', sub_c)
                if m_opt:
                    pt = m_opt.group(1) or m_opt.group(2)
                    base = re.sub(r'（[^）]+）|\([^)]+\)', '', sub_c)
                    v1 = re.sub(r'（[にはでとがをも]+）|\([にはでとがをも]+\)', pt, base)
                    v2 = re.sub(r'（[にはでとがをも]+）|\([にはでとがをも]+\)', '', base)
                    for cand in [v1, v2]:
                        c = re.sub(r'^[〜~・\s]+|[〜~・\s]+$|[の\s]*[NAV]$', '', cand).strip()
                        if len(c) >= 2:
                            all_gp.append({'pattern': c, 'title': g['title'], 'level': g.get('level', 'JLPT'), 'category': '文型', 'grammar_id': g.get('id')})
                else:
                    base = re.sub(r'（.*?）|\(.*?\)', '', sub_c)
                    c = re.sub(r'^[〜~・\s]+|[〜~・\s]+$|[の\s]*[NAV]$', '', base).strip()
                    if len(c) >= 2:
                        all_gp.append({'pattern': c, 'title': g['title'], 'level': g.get('level', 'JLPT'), 'category': '文型', 'grammar_id': g.get('id')})

        all_gp.sort(key=lambda x: len(x['pattern']), reverse=True)

        for gp in all_gp:
            pat = gp['pattern']
            start = 0
            while True:
                pos = text.find(pat, start)
                if pos == -1:
                    break
                end = pos + len(pat)
                if not any(occupied[pos:end]):
                    for k in range(pos, end):
                        occupied[k] = True
                    p_info = self.particle_data.get(pat, {})
                    elements.append({
                        'surface': pat,
                        'start': pos,
                        'end': end,
                        'category': '文型',
                        'title': gp['title'],
                        'level': gp.get('level', 'JLPT'),
                        'grammar_id': gp.get('grammar_id'),
                        'role': p_info.get('default_role', f"文型・{gp['title']}"),
                        'desc': p_info.get('usages', [{}])[0].get('desc', '') if p_info.get('usages') else '',
                        'distractors': p_info.get('distractors', ['ながらも', 'つつも', 'ものの', 'わりに']),
                        'substitutes': self._format_substitutes(p_info)
                    })
                start = pos + 1

        # 2. 複合助詞 (第二優先)
        for cp in COMPOUND_PARTICLES:
            pat = cp['pattern']
            start = 0
            while True:
                pos = text.find(pat, start)
                if pos == -1:
                    break
                end = pos + len(pat)
                if not any(occupied[pos:end]):
                    for k in range(pos, end):
                        occupied[k] = True
                    base_pat = cp.get('base', pat)
                    p_info = self.particle_data.get(base_pat, self.particle_data.get(pat, {}))
                    elements.append({
                        'surface': pat,
                        'start': pos,
                        'end': end,
                        'category': '複合助詞',
                        'title': cp['title'],
                        'level': '複合助詞',
                        'role': p_info.get('default_role', f"複合助詞・{pat}"),
                        'desc': p_info.get('usages', [{}])[0].get('desc', '') if p_info.get('usages') else cp.get('desc', ''),
                        'distractors': p_info.get('distractors', ['について', 'に対して', 'にとって', 'として']),
                        'substitutes': self._format_substitutes(p_info)
                    })
                start = pos + 1

        # 3. 接續助詞 (第三優先)
        for cj in CONJUNCTIVE_PARTICLES:
            pat = cj['pattern']
            start = 0
            while True:
                pos = text.find(pat, start)
                if pos == -1:
                    break
                end = pos + len(pat)
                if not any(occupied[pos:end]):
                    for k in range(pos, end):
                        occupied[k] = True
                    p_info = self.particle_data.get(pat, {})
                    elements.append({
                        'surface': pat,
                        'start': pos,
                        'end': end,
                        'category': '接續助詞',
                        'title': cj['title'],
                        'level': '接續助詞',
                        'role': p_info.get('default_role', f"接續助詞・{pat}"),
                        'desc': p_info.get('usages', [{}])[0].get('desc', '') if p_info.get('usages') else '',
                        'distractors': p_info.get('distractors', ['ので', 'のに', 'ても', 'ながら']),
                        'substitutes': self._format_substitutes(p_info)
                    })
                start = pos + 1

        # 4. 副助詞 (第四優先)
        for ap in ADVERBIAL_PARTICLES:
            pat = ap['pattern']
            start = 0
            while True:
                pos = text.find(pat, start)
                if pos == -1:
                    break
                end = pos + len(pat)
                if not any(occupied[pos:end]):
                    for k in range(pos, end):
                        occupied[k] = True
                    p_info = self.particle_data.get(pat, {})
                    elements.append({
                        'surface': pat,
                        'start': pos,
                        'end': end,
                        'category': '副助詞',
                        'title': ap['title'],
                        'level': '副助詞',
                        'role': p_info.get('default_role', f"副助詞・{pat}"),
                        'desc': p_info.get('usages', [{}])[0].get('desc', '') if p_info.get('usages') else '',
                        'distractors': p_info.get('distractors', ['は', 'も', 'だけ', 'さえ']),
                        'substitutes': self._format_substitutes(p_info)
                    })
                start = pos + 1

        # 5. 格助詞 (第五優先，並防範でした、です等誤判)
        for kp in CASE_PARTICLES:
            pat = kp['pattern']
            start = 0
            while True:
                pos = text.find(pat, start)
                if pos == -1:
                    break
                end = pos + len(pat)
                if not any(occupied[pos:end]):
                    sub_snippet = text[pos:pos+4]
                    if pat == 'で' and (sub_snippet.startswith('でした') or sub_snippet.startswith('です')):
                        start = pos + 1
                        continue
                    for k in range(pos, end):
                        occupied[k] = True
                    p_info = self.particle_data.get(pat, {})
                    elements.append({
                        'surface': pat,
                        'start': pos,
                        'end': end,
                        'category': '格助詞',
                        'title': kp['title'],
                        'level': '格助詞',
                        'role': p_info.get('default_role', f"格助詞・{pat}"),
                        'desc': p_info.get('usages', [{}])[0].get('desc', '') if p_info.get('usages') else '',
                        'distractors': p_info.get('distractors', ['が', 'を', 'に', 'で', 'へ']),
                        'substitutes': self._format_substitutes(p_info)
                    })
                start = pos + 1

        elements.sort(key=lambda x: x['start'])
        return elements

    def _format_substitutes(self, p_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化助詞或文型推薦之 941 代用庫"""
        subs = []
        if not p_info:
            return subs
        for u in p_info.get('usages', []):
            for sub in u.get('substitutes', []):
                gid = sub.get('grammarId')
                g_data = self.grammar_id_map.get(gid) if gid else None
                subs.append({
                    "type": sub.get("type"),
                    "title": sub.get("title"),
                    "level": sub.get("level"),
                    "desc": sub.get("desc"),
                    "grammarId": gid,
                    "paraphrase_demo": sub.get("paraphrase_demo"),
                    "grammar_data": {
                        "id": g_data.get("id"),
                        "title": g_data.get("title"),
                        "level": g_data.get("level"),
                        "meaningZh": g_data.get("meaningZh"),
                        "form": g_data.get("form"),
                        "example": g_data.get("example"),
                        "translation": g_data.get("translation")
                    } if g_data else None
                })
        return subs

    def analyze_text(self, text: str, auto_translate: bool = True) -> Dict[str, Any]:
        """
        對日文文章進行完整解析：
        1. 逐句形態素分詞與假名生成
        2. JLPT 級數著色分析
        3. 941 條文法規則標註
        4. 助詞運用解析與代用換句話說
        5. 逐句繁中翻譯
        6. 全文統計數據
        """
        sentences_raw = self.split_sentences(text)
        analyzed_sentences = []
        
        jlpt_counts = {"N1": 0, "N2": 0, "N3": 0, "N4": 0, "N5": 0, "Other": 0}
        total_words = 0
        total_particles = 0
        matched_grammar_set = set()

        for s_idx, s_text in enumerate(sentences_raw):
            tokens = list(self.tokenizer.tokenize(s_text))
            sentence_words = []
            
            for t in tokens:
                surface = t.surface
                base_form = t.base_form if t.base_form != '*' else surface
                reading_kata = t.reading if t.reading != '*' else ''
                reading_hira = kata_to_hira(reading_kata)
                pos_parts = t.part_of_speech.split(',')
                primary_pos = self.pos_map.get(pos_parts[0], pos_parts[0])
                sub_pos = pos_parts[1] if len(pos_parts) > 1 and pos_parts[1] != '*' else ''
                
                # JLPT 等級判定
                jlpt_lvl = self.get_jlpt_level(base_form, surface, reading_hira)
                if jlpt_lvl:
                    jlpt_counts[jlpt_lvl] += 1
                else:
                    if re.search(r'[\u4e00-\u9faf\u3040-\u309f\u30a0-\u30ff]', surface):
                        jlpt_counts["Other"] += 1
                        
                ruby_html = make_ruby(surface, reading_kata)
                has_kanji = bool(re.search(r'[\u4e00-\u9faf]', surface))
                
                total_words += 1
                is_particle = ('助詞' in primary_pos) or (surface in self.particle_data)
                sentence_words.append({
                    "surface": surface,
                    "base_form": base_form,
                    "reading": reading_hira,
                    "reading_kata": reading_kata,
                    "ruby_html": ruby_html,
                    "pos": f"{primary_pos}{'・' + sub_pos if sub_pos else ''}",
                    "pos_raw": pos_parts[0],
                    "jlpt": jlpt_lvl,
                    "is_kanji": has_kanji,
                    "is_particle": is_particle
                })
                
            # 搜尋本句命中的 941 文法
            grammars = self.find_grammars(s_text)
            for g in grammars:
                matched_grammar_set.add(g["id"])

            # 階層鎖定分詞：分析格助詞、副助詞、複合助詞、接續助詞與文型（嚴禁拆解文型）
            sentence_particles = self.analyze_sentence_hierarchy(s_text)
            total_particles += len(sentence_particles)

            # 防誤判保護：若詞彙落在複合文型（如「ながらも」「に伴い」）區間內，不得單獨視為零散助詞
            occupied_spans = [(el['start'], el['end']) for el in sentence_particles if len(el['surface']) > 1]
            char_cursor = 0
            for w in sentence_words:
                w_len = len(w['surface'])
                w_start = s_text.find(w['surface'], char_cursor)
                if w_start != -1:
                    w_end = w_start + w_len
                    char_cursor = w_end
                    # 若本單字落在長度大於1之複合助詞或文型中，且本身小於該區間，取消其獨立助詞標籤
                    is_in_compound = any(s <= w_start and w_end <= e and (e - s) > w_len for s, e in occupied_spans)
                    if is_in_compound:
                        w['is_particle'] = False
                        w['pos'] = '文型成分'
                
            # 句子中文翻譯
            translation = ""
            if auto_translate:
                translation = self.translate_to_traditional_chinese(s_text)
                
            analyzed_sentences.append({
                "sentence_id": s_idx,
                "text": s_text,
                "words": sentence_words,
                "grammars": grammars,
                "particles": sentence_particles,
                "translation": translation
            })

        # 全文統計數據
        stats = {
            "sentence_count": len(analyzed_sentences),
            "word_count": total_words,
            "grammar_count": len(matched_grammar_set),
            "particle_count": total_particles,
            "jlpt_distribution": jlpt_counts
        }

        return {
            "sentences": analyzed_sentences,
            "stats": stats
        }

    async def extract_url_content(self, url: str) -> Dict[str, Any]:
        """抓取指定日文網址之文章標題與純文字內容"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8,zh-TW;q=0.7"
        }
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=12.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            
            content_type = resp.headers.get("content-type", "").lower()
            if "euc-jp" in content_type:
                html = resp.content.decode("euc-jp", errors="ignore")
            elif "shift_jis" in content_type or "sjis" in content_type:
                html = resp.content.decode("shift_jis", errors="ignore")
            else:
                html = resp.text
                
        soup = BeautifulSoup(html, "html.parser")
        
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "iframe", "svg"]):
            tag.extract()
            
        title = soup.title.string.strip() if soup.title and soup.title.string else "未命名日文網頁"
        
        article_elem = None
        selectors = [
            "article",
            "main",
            ".article-body",
            ".article-main",
            "#article-main",
            ".entry-content",
            ".post-content",
            ".content",
            "#content",
            ".news-text",
            ".text",
            ".honbun"
        ]
        for sel in selectors:
            elem = soup.select_one(sel)
            if elem and len(elem.get_text().strip()) > 100:
                article_elem = elem
                break
                
        if not article_elem:
            article_elem = soup.body if soup.body else soup
            
        paragraphs = []
        for p in article_elem.find_all(["p", "h1", "h2", "h3", "h4", "li"]):
            p_text = p.get_text().strip()
            if len(p_text) > 8:
                paragraphs.append(p_text)
                
        if not paragraphs:
            raw_text = article_elem.get_text(separator="\n")
            paragraphs = [line.strip() for line in raw_text.splitlines() if len(line.strip()) > 8]
            
        clean_text = "\n\n".join(paragraphs)
        return {
            "title": title,
            "url": url,
            "content": clean_text
        }
