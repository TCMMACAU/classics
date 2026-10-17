# 經典原文（經索）

由 https://tcmclassics.grok.me 遷移嘅中醫經典原文檢索站，GitHub Pages 版本。

- 原文來源檔：`books/<書號>/` 每篇一個 Markdown 檔，條文編號穩定，唔會重新編號。
- 書目與底本：`books.json`
- 建站：`python3 build.py`（只用 Python 標準庫），輸出到 `docs/`
- 「我嘅加減」：只存喺用家瀏覽器 localStorage，可喺首頁匯出／匯入 JSON 備份，唔會上傳。
- 所有原文供閱讀檢索，不是處方依據。

完整遷移前備份另存喺本機 `/workspace/classics-backup-20261017/`（含 manifest 同原站 JS 數據檔）。

## 索引（build.py 自動生成）
- 方劑總目 `docs/fangji/`：傷寒論、金匱要略、溫病條辨、金匱要略心典以「方名＋主之」句式抽取，醫學衷中參西錄以方名篇題抽取，同名合併連回條文；不錄組成／主治。
- 藥物總目 `docs/yao/`：以神農本草經條首藥名（351藥）為綱，連本經疏證同名篇與臨證指南醫案同名出現條文；一字藥名不作醫案連結。
- 病門索引 `docs/bingmen/`：以臨證指南醫案 112 門為綱，其他書只按篇題包含門名作相關連結。

## 新增書（2026-10-17）
難經、溫熱論、濕熱病篇、脈經、針灸大成、本草備要，來源皆為維基文庫公有領域古籍頁，逐本底本／作者／來源連結記喺 books.json 各書條目。溫熱論只錄原頁編號條文一至三十七（現代編者「總論」不錄）；本草備要來源為簡體轉錄，入站時以 OpenCC 機械轉繁；針灸大成原頁若干生僻字為 Unicode 私用區碼（原站標示未能識別），轉錄以「□」標示。

## 臨床入口與可安裝版（2026-10-17）
- `docs/clinical/`：醫師診症查原文用；病門頁聚合原篇、相關篇目、方劑／藥物總目命中（只係索引比對）。加減升級為「證型／判斷／覆診」三欄＋修改時間，只存 localStorage（KEY 不變，舊純文字筆記同舊匯出檔相容，新匯出含結構欄位）。
- `docs/patient.html?id=<條文編號>`：病人閱讀頁，只顯示原文同出處，列印時隱藏導航／按鈕。
- PWA：`manifest.webmanifest`＋`sw.js`（版本 classics-v3）。只預載 app 殼、首頁、三索引、臨床入口、搜尋／病人頁同圖標；15,836 條頁面唔會一次過預載，睇過嘅頁面 runtime cache，離線可再開；search-index.json 行 network-first 保持更新。

## 網站地圖
每次 build 喺 build.py 自動生成：`docs/sitemap.xml`（2,831 條絕對網址，已排除需要 ?id= 嘅病人閱讀頁 utility）、`docs/robots.txt`（指去 sitemap）、人睇嘅 `docs/sitemap/index.html`（書目＋索引，頁尾「網站地圖」連結）。冇加 lastmod，保證重複 build 輸出一致。
