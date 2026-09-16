# -*- coding: utf-8 -*-
"""Legacy compatibility; MOJi membership stays on the official platform."""

def search_moji(word: str):
    return {"status": "disabled", "message": "請使用 MOJi 官方查詞入口或個人詞表匯入", "word": word.strip()}
