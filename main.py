# -*- coding: utf-8 -*-
"""
日文閱讀助手 (Japanese Reading Assistant) - FastAPI 後端應用服務
仿 句解霸 (en998.com/iread) 核心架構
深度整合 《絵でわかる日本語》 941 條繁體中文文法資料庫
"""

import os
import json
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from analyzer import JapaneseAnalyzer

app = FastAPI(
    title="日文閱讀助手 (Japanese Reading Assistant)",
    description="智慧日語閱讀學習系統，支援文章與網址分析、JLPT 單字分級著色、941條文法標註、假名遮蔽與逐句繁中翻譯",
    version="2.0.0"
)

# 啟用 CORS 跨域支援
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化解析器
analyzer = JapaneseAnalyzer(
    grammar_path="grammar_data.json",
    jlpt_path="jlpt_vocab_all.json"
)

# 資料模型
class AnalyzeRequest(BaseModel):
    text: str
    auto_translate: bool = True

class ExtractUrlRequest(BaseModel):
    url: str

class TranslateWordRequest(BaseModel):
    text: str

# 內建精選日語閱讀範例
SAMPLE_ARTICLES = [
    {
        "id": "nhk_ai_news",
        "title": "【時事科技】AI技術の進化と私たちの生活 (NHK 風格新聞)",
        "level": "N3 ~ N2",
        "content": """日本では、AI（人工知能）を使った新しいサービスが次々と始まっています。
病院では、医師が診察する時にAIを使って、病気を見つける手助けをしています。
また、外国人の観光客が増えているため、ホテルや駅では自動で翻訳するロボットが活躍しています。
専門家は「これからは生活のあらゆる場面でAIが使われる一方、正しい情報をどう見分けるかが大切になる」と話しています。
新しい技術を恐れることなく、上手に付き合っていくことが求められています。"""
    },
    {
        "id": "jlpt_n2_essay",
        "title": "【JLPT N2/N1 讀解】便利さと心の豊かさ（多項文法精選論說文）",
        "level": "N2 ~ N1",
        "content": """科学技術の急速な発展に伴い、私たちの生活は便利になる一方である。
しかし、いくら生活が便利になったからといっても、人間の心が豊かになったとは言えないのではないだろうか。
現代人は利便性を追求するあまり、自然との触れ合いや人との絆を忘れがちである。
１時間悩んだあげく、余計な物を買ってしまう消費者心理も問題視されている。
豊かな社会を築くためには、物質的な豊かさのみならず、心のゆとりを大切にする姿勢こそが欠かせないものにほかならない。"""
    },
    {
        "id": "momotaro_story",
        "title": "【經典故事】桃太郎（基礎讀物與初中階文型）",
        "level": "N5 ~ N3",
        "content": """むかしむかし、ある所に、おじいさんとおばあさんが住んでいました。
おじいさんは山へ柴刈りに、おばあさんは川へ洗濯に行きました。
おばあさんが川で洗濯をしていると、川上から大きな桃が、どんぶらこ、どんぶらこと流れてきました。
「おや、これは大きな桃だこと。家に持って帰って、おじいさんと一緒に食べよう」とおばあさんは桃を拾い上げて、家に持ち帰りました。
夕方、おじいさんが山から帰ってきて、桃を割ってみると、中から元気な男の子が生まれました。
二人は大喜びで、男の子に「桃太郎」と名付けました。"""
    }
]

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "grammars_loaded": len(analyzer.grammars),
        "particles_loaded": len(analyzer.particle_data),
        "jlpt_words_loaded": len(analyzer.jlpt_vocab)
    }

@app.get("/api/particles")
async def get_particles():
    """獲取日文助詞運用與代用換句話說資料庫"""
    return analyzer.particle_data

@app.get("/api/examples")
async def get_sample_articles():
    """獲取精選日語閱讀範例列表"""
    return SAMPLE_ARTICLES

@app.post("/api/extract-url")
async def extract_url(req: ExtractUrlRequest):
    """自網址抓取日文網頁正文"""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="請提供有效的網址")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
        
    try:
        data = await analyzer.extract_url_content(url)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"網址正文擷取失敗: {str(e)}")

@app.post("/api/analyze")
async def analyze_article(req: AnalyzeRequest):
    """解析日文文章全文"""
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="文章內容不可為空")
        
    try:
        result = analyzer.analyze_text(text, auto_translate=req.auto_translate)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文章解析過程出錯: {str(e)}")

@app.post("/api/translate-word")
async def translate_word(req: TranslateWordRequest):
    """即時單字或片語繁體中文翻譯"""
    w = req.text.strip()
    if not w:
        return {"translation": ""}
    tr = analyzer.translate_to_traditional_chinese(w)
    return {"translation": tr}

@app.get("/api/grammar/{grammar_id}")
async def get_grammar_detail(grammar_id: int):
    """獲取特定文法項目完整詳解"""
    for g in analyzer.grammars:
        if g.get("id") == grammar_id:
            return g
    raise HTTPException(status_code=404, detail="找不到此文法項目")

# MOJi 辭書直連查詢 API
from moji_client import search_moji

@app.get("/api/moji/search")
async def moji_search_get(word: str):
    """自 MOJi 辭書查詢日語單字讀音、釋義與權威例句"""
    if not word.strip():
        raise HTTPException(status_code=400, detail="請提供欲查詢的單字")
    result = search_moji(word)
    return result

@app.post("/api/moji/search")
async def moji_search_post(req: TranslateWordRequest):
    """自 MOJi 辭書查詢日語單字讀音、釋義與權威例句 (POST)"""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="請提供欲查詢的單字")
    result = search_moji(req.text)
    return result


# 掛載靜態網頁前端
os.makedirs("static", exist_ok=True)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
