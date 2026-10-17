# 經典原文（經索）

由 https://tcmclassics.grok.me 遷移嘅中醫經典原文檢索站，GitHub Pages 版本。

- 原文來源檔：`books/<書號>/` 每篇一個 Markdown 檔，條文編號穩定，唔會重新編號。
- 書目與底本：`books.json`
- 建站：`python3 build.py`（只用 Python 標準庫），輸出到 `docs/`
- 「我嘅加減」：只存喺用家瀏覽器 localStorage，可喺首頁匯出／匯入 JSON 備份，唔會上傳。
- 所有原文供閱讀檢索，不是處方依據。

完整遷移前備份另存喺本機 `/workspace/classics-backup-20261017/`（含 manifest 同原站 JS 數據檔）。
