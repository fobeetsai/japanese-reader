# -*- coding: utf-8 -*-
"""
MOJi 辭書 (MOJi Dictionary) 資料即時提取模組
直接調用 MOJi 原生 Parse 雲端 API，抓取官方日文讀音、音調(Accent)、繁中/中文詞性與釋義、原生權威例句
"""

import urllib.request
import json
from typing import Dict, Any, Optional

# 簡轉繁對照字典（涵蓋營造工程、商務與日常生活高頻詞彙）
S2T_MAP = {
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
}

def to_traditional_chinese(text: str) -> str:
    """轉換文字為繁體中文"""
    if not text:
        return ""
    res = text
    for s, t in S2T_MAP.items():
        res = res.replace(s, t)
    return res

def search_moji(word: str) -> Dict[str, Any]:
    """
    自 MOJi 辭書直接導入單字的讀音、中文釋義與例句
    """
    clean_word = word.strip()
    if not clean_word:
        return {"status": "error", "message": "單字不能為空"}

    url = "https://api.mojidict.com/parse/functions/search-all"
    payload = json.dumps({
        "text": clean_word,
        "types": [102, 103, 106]
    }).encode("utf-8")

    headers = {
        "X-Parse-Application-Id": "E62VyFVLMiW7kvbtVq3p",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {
            "status": "error",
            "message": f"MOJi 網路連線錯誤: {str(e)}",
            "word": clean_word
        }

    res_obj = data.get("result", {}).get("result", {})
    w_list = res_obj.get("word", {}).get("searchResult", [])
    ex_list = res_obj.get("example", {}).get("searchResult", [])

    if not w_list:
        return {
            "status": "not_found",
            "message": "MOJi 辭書中未找到完全匹配的單字",
            "word": clean_word
        }

    # 優先精確匹配目標單字
    best_word = None
    for item in w_list:
        title = item.get("title", "")
        parts = [p.strip() for p in title.split("|")]
        if parts[0] == clean_word:
            best_word = item
            break
    if not best_word and w_list:
        best_word = w_list[0]

    # 解析標題 (通常為 "漢字 | 讀音 音調")
    title_parts = [p.strip() for p in best_word.get("title", "").split("|")]
    spell = title_parts[0] if title_parts else clean_word
    reading = title_parts[1] if len(title_parts) > 1 else ""
    raw_meaning = best_word.get("excerpt", "")
    meaning = to_traditional_chinese(raw_meaning)

    # 提取原生權威例句
    example_text = ""
    if ex_list:
        first_ex = ex_list[0]
        jp_sent = first_ex.get("title", "").strip()
        zh_sent = to_traditional_chinese(first_ex.get("excerpt", "").strip())
        if jp_sent and zh_sent:
            example_text = f"{jp_sent} ({zh_sent})"
        elif jp_sent:
            example_text = jp_sent

    target_id = best_word.get("targetId")

    # 若 searchResult 中無例句，嘗試調用 detailInfo
    if target_id and not example_text:
        try:
            d_url = f"https://api.mojidict.com/app/mojidict/api/v1/word/detailInfo?wordId={target_id}"
            d_req = urllib.request.Request(d_url, headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.mojidict.com/"
            })
            with urllib.request.urlopen(d_req, timeout=4) as d_resp:
                d_data = json.loads(d_resp.read().decode("utf-8"))
                examples = d_data.get("examples", [])
                jp_e = next((e["title"] for e in examples if e.get("lang") == "ja"), "")
                zh_e = next((to_traditional_chinese(e["title"]) for e in examples if e.get("lang") in ("zh-CN", "zh-TW")), "")
                if jp_e and zh_e:
                    example_text = f"{jp_e} ({zh_e})"
                elif jp_e:
                    example_text = jp_e
        except Exception:
            pass

    return {
        "status": "success",
        "source": "MOJi 辭書 (官方直接導出)",
        "word": spell,
        "reading": reading,
        "meaning": meaning,
        "example": example_text,
        "targetId": target_id,
        "all_words": [
            {
                "title": w.get("title"),
                "meaning": to_traditional_chinese(w.get("excerpt", "")),
                "targetId": w.get("targetId")
            }
            for w in w_list[:5]
        ]
    }
