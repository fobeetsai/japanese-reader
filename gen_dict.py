import os
import json
import re

root = os.path.dirname(os.path.abspath(__file__))
kanji_path = os.path.join(root, 'kanji_single_map.json')
vocab_path = os.path.join(root, 'jlpt_vocab_all.json')
out_path = os.path.join(root, 'trancy_extension', 'furigana_dict.js')

with open(kanji_path, 'r', encoding='utf-8') as f:
    kanji_map = json.load(f)

with open(vocab_path, 'r', encoding='utf-8') as f:
    vocab_raw = json.load(f)

vocab_map = {}
kanji_regex = re.compile(r'[\u4e00-\u9faf]')

for word, entries in vocab_raw.items():
    if kanji_regex.search(word) and entries:
        # Sort by level descending so N5 (most common everyday) comes before N1
        sorted_entries = sorted(entries, key=lambda x: x.get('level', 0), reverse=True)
        reading = sorted_entries[0].get('reading', '')
        if reading and reading != word:
            vocab_map[word] = reading

extra_common = {
    '私': 'わたし', '僕': 'ぼく', '俺': 'おれ', '貴方': 'あなた',
    '今日': 'きょう', '明日': 'あした', '昨日': 'きのう', '今週': 'こんしゅう', '来週': 'らいしゅう',
    '今年': 'ことし', '来年': 'らいねん', '去年': 'きょねん', '時間': 'じかん', '分': 'ふん',
    '日本': 'にほん', '日本語': 'にほんご', '東京': 'とうきょう', '会社': 'かいしゃ', '仕事': 'しごと',
    '電話': 'でんわ', '映画': 'えいが', '音楽': 'おんがく', '旅行': 'りょこう', '友達': 'ともだち',
    '家族': 'かぞく', '学校': 'がっこう', '先生': 'せんせい', '学生': 'がくせい', '勉強': 'べんきょう',
    '質問': 'しつもん', '問題': 'もんだい', '理由': 'りゆう', '意味': 'いみ', '漢字': 'かんじ',
    '仮名': 'かな', '平仮名': 'ひらがな', '片仮名': 'かたかな', '振仮名': 'ふりがな', '翻訳': 'ほんやく',
    '沉浸': 'ちんしん', '音声': 'おんせい', '発音': 'はつおん', '朗読': 'ろうどく', '自測': 'じそく',
    '遮蔽': 'しゃへい', '辞書': 'じしょ', '辞典': 'じてん', '単語': 'たんご', '文法': 'ぶんぽう',
    '復習': 'ふくしゅう', '練習': 'れんしゅう', '段落': 'だんらく', '選択': 'せんたく'
}
for k, v in extra_common.items():
    vocab_map[k] = v

kanji_json = json.dumps(kanji_map, ensure_ascii=False)
vocab_json = json.dumps(vocab_map, ensure_ascii=False)

js_content = """// Trancy Furigana Engine & Japanese Tokenizer
// High performance Furigana annotation and Karaoke word segmenter
(function() {
  'use strict';

  const KANJI_SINGLE_MAP = """ + kanji_json + """;
  const VOCAB_MAP = """ + vocab_json + """;

  const KANJI_REGEX = /[\u4e00-\u9faf]/;
  const KANJI_ONLY_REGEX = /^[\u4e00-\u9faf]+$/;

  // Build smart ruby HTML for a word/kanji
  function makeRuby(surface, reading) {
    if (!reading || !KANJI_REGEX.test(surface)) return surface;
    if (KANJI_ONLY_REGEX.test(surface)) {
      return '<ruby class="trancy-ruby">' + surface + '<rt class="trancy-rt">' + reading + '</rt></ruby>';
    }

    // Match suffix okurigana
    let suffixLen = 0;
    while (
      suffixLen < surface.length &&
      suffixLen < reading.length &&
      surface[surface.length - 1 - suffixLen] === reading[reading.length - 1 - suffixLen]
    ) {
      suffixLen++;
    }

    // Match prefix
    let prefixLen = 0;
    while (
      prefixLen < (surface.length - suffixLen) &&
      prefixLen < (reading.length - suffixLen) &&
      surface[prefixLen] === reading[prefixLen]
    ) {
      prefixLen++;
    }

    const prefix = surface.slice(0, prefixLen);
    const kanjiPart = surface.slice(prefixLen, suffixLen > 0 ? -suffixLen : undefined);
    const suffix = suffixLen > 0 ? surface.slice(-suffixLen) : '';
    const readingKanji = reading.slice(prefixLen, suffixLen > 0 ? -suffixLen : undefined);

    if (kanjiPart && readingKanji) {
      return prefix + '<ruby class="trancy-ruby">' + kanjiPart + '<rt class="trancy-rt">' + readingKanji + '</rt></ruby>' + suffix;
    }
    return '<ruby class="trancy-ruby">' + surface + '<rt class="trancy-rt">' + reading + '</rt></ruby>';
  }

  // Tokenize text into words / ruby items
  function tokenizeText(text) {
    if (!text) return [];
    const tokens = [];
    let i = 0;
    const len = text.length;

    while (i < len) {
      const ch = text[i];
      if (KANJI_REGEX.test(ch)) {
        let matched = false;
        const maxCheck = Math.min(len - i, 8);
        for (let l = maxCheck; l >= 1; l--) {
          const sub = text.slice(i, i + l);
          if (VOCAB_MAP[sub]) {
            tokens.push({
              surface: sub,
              reading: VOCAB_MAP[sub],
              ruby: makeRuby(sub, VOCAB_MAP[sub]),
              isKanji: true
            });
            i += l;
            matched = true;
            break;
          }
        }

        if (!matched) {
          const reading = KANJI_SINGLE_MAP[ch] || '';
          tokens.push({
            surface: ch,
            reading: reading,
            ruby: reading ? '<ruby class="trancy-ruby">' + ch + '<rt class="trancy-rt">' + reading + '</rt></ruby>' : ch,
            isKanji: true
          });
          i++;
        }
      } else {
        let end = i + 1;
        while (end < len && !KANJI_REGEX.test(text[end])) {
          if (/[\\s、。！？,.!?:;\\n\\(\\)\\[\\]【】「」『』]/.test(text[end])) {
            if (end === i) end++;
            break;
          }
          end++;
        }
        const part = text.slice(i, end);
        tokens.push({
          surface: part,
          reading: part,
          ruby: part,
          isKanji: false
        });
        i = end;
      }
    }
    return tokens;
  }

  // Convert pure Japanese text into Furigana HTML
  function toRubyHtml(text) {
    if (!text) return '';
    const tokens = tokenizeText(text);
    return tokens.map(t => t.ruby).join('');
  }

  // Build Karaoke HTML: each token is a clickable span with data-word-idx
  function toKaraokeHtml(text) {
    if (!text) return '';
    const tokens = tokenizeText(text);
    return tokens.map((t, idx) => {
      const isPunct = /^[\\s、。！？,.!?:;\\n\\(\\)\\[\\]【】「」『』]+$/.test(t.surface);
      if (isPunct) {
        return '<span class="trancy-karaoke-punct">' + t.ruby + '</span>';
      }
      return '<span class="trancy-karaoke-word" data-word-idx="' + idx + '" data-surface="' + encodeURIComponent(t.surface) + '" title="' + (t.reading || t.surface) + '">' + t.ruby + '</span>';
    }).join('');
  }

  window.TrancyFurigana = {
    tokenizeText,
    toRubyHtml,
    toKaraokeHtml,
    makeRuby,
    hasKanji: (text) => KANJI_REGEX.test(text)
  };
})();
"""

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(js_content)

print(f"Generated {out_path} ({os.path.getsize(out_path)} bytes)")
