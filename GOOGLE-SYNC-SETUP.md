# 閱讀高手：啟用每位學生各自的 Google Drive 同步

程式包含完整備份／合併匯入及 Google Drive 同步，但必須先提供正式 OAuth Web Client ID 才能啟用 Google 登入。學生不需要填入 Client ID、API Key 或密碼。不要把 Client Secret 放入前端程式。

## 管理者一次設定

1. 登入 https://console.cloud.google.com/ ，選擇或建立你管理的專案，不需為本功能啟用計費。
2. 在 API 程式庫啟用 Google Drive API。
3. 在 Google Auth Platform 設定 Branding、Audience 與聯絡電子郵件。應用程式名稱使用「閱讀高手」。公開使用時 Audience 選 External；Testing 階段只有加入 Test users 的帳號能登入。
4. Data Access 僅要求 `openid`、`email` 及 `https://www.googleapis.com/auth/drive.appdata`。不要加入完整 Drive 讀寫權限。
5. 建立「Web application」OAuth Client。Authorized JavaScript origins 加入 `https://fobeetsai.github.io`（不要加 `/japanese-reader` 路徑）。本機測試可另加 `http://127.0.0.1:8765`。本功能用彈出式 token flow，不使用 Client Secret 或自建回呼後端。
6. 網站首頁為 `https://fobeetsai.github.io/japanese-reader/master.html`；隱私說明為 `https://fobeetsai.github.io/japanese-reader/reader-privacy.html`。若 Google 要求網域驗證或其他發布審查，依控制台要求完成，不要宣稱 Testing 已能供所有學生使用。
7. 將 Web Client ID 填入 `static/master/google-config.js` 的 `window.READER_GOOGLE_CLIENT_ID`。這是可公開的識別碼。更新该檔案及 HTML、sw.js 中的 config 版本號，再提交發布。
8. 用兩個測試 Google 帳號分別登入：驗證各帳號只看到自己的收藏，再以同一帳號在電腦和手機互相新增／刪除收藏。確認頁面顯示「本次同步完成」，且重新清除網站資料登入後可还原。
9. 在 Google Auth Platform 將 Audience 正式發布為 Production，依 Google 顯示的驗證要求處理後，再開放全班使用。

## 同步行為與限制

- 每位使用者資料存於該帳號的 appDataFolder，無教師跨帳號閱讀介面。
- OAuth token 僅在記憶體，過期或重新開啟頁面後須由使用者再次按登入。不宣稱關閉 APP 後仍背景同步。
- 每個開啟的頁面使用獨立 writer，發佈不可變的完整快照；同步讀取各 writer 最新版本並逐筆合併。邏輯版本及刪除標記可避免舊裝置把刪除資料加回來。相同收藏的同時編輯採確定性的版本順序，雲端歷史仍保留。
- 匯入是新增合併，相同 ID 保留目前版本，舊備份的刪除標記不會刪掉現有收藏。套用前保留本機復原快照，儲存失敗會回滾。
- 尚未做雲端歷史清理；長期使用將累積備份並占用 Drive 空間。大量資料／歷史檔案會停止同步並報錯，不會悄悄略過。每個備份限制 10 MB，每分類最多 10,000 筆。
- 各裝置必須使用同一個正式 Client ID／Google Cloud 專案，才會存取相同的應用程式資料空間。

參考：
- https://developers.google.com/identity/oauth2/web/guides/use-token-model
- https://developers.google.com/workspace/drive/api/guides/appdata
- https://developers.google.com/workspace/drive/api/guides/manage-uploads
