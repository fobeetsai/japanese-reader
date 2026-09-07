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

    def analyze_sentence_particles(self, words: List[Dict[str, Any]], sentence_text: str) -> List[Dict[str, Any]]:
        """識別句子中的所有助詞、分析語法角色、並推薦 941 文法庫之代用文型與換句話說"""
        particles = []
        for w_idx, w in enumerate(words):
            if '助詞' not in w.get('pos', ''):
                continue
            p_surface = w.get('surface', '')
            p_info = self.particle_data.get(p_surface)
            if not p_info:
                continue
            
            # 取得前後文語境切片
            prev_word = words[w_idx - 1]['surface'] if w_idx > 0 else ''
            next_word = words[w_idx + 1]['surface'] if w_idx + 1 < len(words) else ''
            context_snippet = f"{prev_word}【{p_surface}】{next_word}"

            # 依上下文特徵線索選定最匹配的用法
            matched_usage = p_info['usages'][0] if p_info.get('usages') else None
            for u in p_info.get('usages', []):
                clues = u.get('context_clue', [])
                if any(c in sentence_text for c in clues):
                    matched_usage = u
                    break
            
            # 格式化代用助詞與 941 文法庫推薦
            substitutes_formatted = []
            if matched_usage:
                for sub in matched_usage.get('substitutes', []):
                    gid = sub.get('grammarId')
                    g_data = self.grammar_id_map.get(gid) if gid else None
                    substitutes_formatted.append({
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

            particles.append({
                "surface": p_surface,
                "role": matched_usage.get("role") if matched_usage else p_info.get("default_role", "助詞"),
                "desc": matched_usage.get("desc") if matched_usage else "",
                "context_snippet": context_snippet,
                "distractors": p_info.get("distractors", ['は', 'が', 'を', 'に', 'で']),
                "substitutes": substitutes_formatted
            })
        return particles

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

            # 搜尋本句命中的助詞運用與代用文型換句話說
            sentence_particles = self.analyze_sentence_particles(sentence_words, s_text)
            total_particles += len(sentence_particles)
                
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
