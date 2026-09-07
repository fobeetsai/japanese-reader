@echo off
chcp 65001 >nul
title 日文閱讀助手 (Japanese Reading Assistant)
echo =======================================================
echo          日文閱讀助手 (Japanese Reading Assistant)
echo    仿 句解霸 (en998) 核心・整合《絵でわかる日本語》941文法
echo =======================================================
echo.
echo 正在啟動後端服務...
echo.

:: 稍候 2 秒後自動開啟瀏覽器
start "" cmd /c "timeout /t 2 >nul && start http://localhost:8000"

:: 啟動 FastAPI 後端服務
.\.venv\Scripts\python.exe main.py

pause
