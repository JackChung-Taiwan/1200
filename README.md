# 英語單字花園｜English 1200

繁體中文英語發音學習網站，供國小學生與教師使用。

> **部署狀態：** 目前先建立 GitHub Pages 發布設定。網站完整檔案（尤其 MP3、GIF 與原始教材）尚需由專案壓縮檔同步到此儲存庫；在 `dist/` 上傳完成之前，網站無法完整使用。

## 網站功能

- A–Z 單字分類與搜尋
- 1,171 筆原教材單字／片語與 1,277 組例句
- 原教材單字、例句 MP3 播放與速度調整
- 收藏、已學會、聽音選字、看英文選中文
- 教師投影模式及手機響應式版型

## 資料完整性

原始教材名稱 `English1200-0514`。「1200」為原教材名稱，索引不是人工補成 1200 筆。完整專案含 5,360 個原始檔案，其中 MP3 共 2,468 個。音檔與原始內容須保留在 `dist/original/English1200-0514/`，請勿只提交網頁的 HTML。

## 專案預期結構

```text
dist/
  index.html
  style.css
  app.js
  data.js
  original/English1200-0514/...
data/
scripts/
.github/workflows/deploy-pages.yml
README.md
```

## GitHub Pages 發布

1. 將原始專案資料夾 **English1200_Website_Project** 的內容提交到此儲存庫根目錄，不要再包一層資料夾。
2. 確認 `dist/index.html` 與 `dist/original/` 存在，音檔圖片已一併提交。
3. 前往 **Settings → Pages → Build and deployment → Source → GitHub Actions**。
4. 推送到 `main` 後，網站將由工作流程自動發布 `dist/`。
5. 站點預計網址：https://jackchung-taiwan.github.io/1200/

## 本機測試

```bash
python -m http.server 8000 --directory dist
```

瀏覽器開啟 http://localhost:8000。

授權與公開發布前請確認原教材文字、圖片及錄音素材具有適當使用／散布權限。