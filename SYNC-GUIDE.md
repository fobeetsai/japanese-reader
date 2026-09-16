# 跨裝置同步與手機學習

資料原本儲存在每一台裝置、每一個瀏覽器自己的 localStorage。因此 A、B 電腦、手機、不同瀏覽器甚至主畫面 App 可能呈現不同內容；重新整理網站不會傳送個人資料。

## 本人：GitHub 同步

1. 在 A 點「🔄 同步」，使用自己的 GitHub 帳號建立只有 gist 權限的 Personal Access Token (classic)，設定有效期限。
2. 貼上 Token，第一次讓 Gist ID 留空，按「立即同步」，確認建立雲端資料。
3. 到 B，貼上同一帳號的 Token（可另建一枚只有 gist 權限的 Token）及 A 畫面顯示的 Gist ID。先匯出 B 的 JSON 備份，再按「以雲端為準」。
4. 每次在 A 學習完按一次「立即同步」；改用 B 前也按一次。可選擇開啟時同步，勾選後需成功同步一次以儲存設定。

同步範圍：抽認卡牌組、卡片內容、SRS 複習排程及學習紀錄。不同裝置的介面與語音設定保留本機；閱讀助手、漢字道場的原始筆記不在此同步範圍。

若兩端都有修改，系統會停止，需選擇以本機或雲端為準，**不會合併兩份資料**。覆蓋前在此瀏覽器保留最近一組本機及雲端復原備份，可在「選擇資料來源／復原備份」匯出。覆蓋可能捨棄另一端獨有的修改，請先備份。首次連結既有 Gist 也需選擇資料來源。

GitHub Gist 沒有跨裝置交易鎖；系統在寫入前再次檢查版本，但請輪流同步，不要兩台同時上傳。上傳若逾時，GitHub 仍可能已收到資料；先檢查 Gist，再決定重試，避免建立重複 Gist。無網路時可繼續本機複習，連線後再同步。

Token 只儲存在設定它的瀏覽器，不會放入備份或 Gist。不要把老師的 Token 給學生，也不要在共用電腦設定。停用時可到 GitHub 撤銷 Token。Secret Gist 並非加密或真正的私人資料庫，知道網址的人可以讀取，請勿存放學生個資、機密教材。

## 學生：不需帳號的檔案移轉

A：同步 → 匯出 JSON 備份檔 → 透過自己的雲端硬碟、AirDrop 或其他檔案傳送方式交給 B。

B：同步 → 還原 JSON 備份 → 選取檔案 → 確認取代本機內容。

這是手動移轉，不是背景同步。備份包含卡片與進度，不包含 Token。不要清除瀏覽器資料後才備份。

## 手機網頁 App 與 App Store

- iPhone／iPad：用 Safari 開啟 flashcard.html → 分享 → 加入主畫面。
- Android：用 Chrome 開啟 → 選單 → 安裝應用程式或加到主畫面，名稱依瀏覽器版本而異。
- 首次連網開啟後，已快取的卡片可離線複習；雲端同步與線上查詢需要網路。裝置可清除網站儲存，仍需定期備份。

目前是 PWA 網頁 App，沒有上架 App Store。未來可製作 iOS App，但須有 Apple Developer Program 帳號（官方標準每會員年 USD 99，依地區計價），完成 iOS 建置、實機測試、隱私揭露及 App Review。單純把網站套殼可能不符合 4.2 最低功能要求。可先把離線學習、手機操作及資料移轉做穩，再規劃上架。

官方參考：
- https://developer.apple.com/programs/enroll/
- https://developer.apple.com/app-store/review/guidelines/#minimum-functionality
- https://docs.github.com/en/rest/gists/gists

## 驗證

執行 `node tests/sync.cjs`。測試使用模擬 GitHub 回應與隔離儲存，不呼叫使用者帳號、不建立真正 Gist，也不使用付費 AI。仍需使用者在 A、B 裝置輸入自己的 Token 完成首次連結。
