# CLAUDE.md — 生字練習簿產生器

給接手這個專案的 Claude 看的工作說明。使用者看的說明在 README.md。

## 專案是什麼

國小一年級國語生字練習簿產生器。輸入生字 → 即時預覽 A4 田字格練習頁（十字虛線、範字、描紅、注音欄、筆順）→ 下載 PDF 或直接列印。給家長在家幫孩子出作業用。

- 網站：https://kkccy1324.github.io/shengzi-workbook/（GitHub Pages，`main` 分支 `/docs`）
- 可安裝的 PWA：第一次連網開啟後，iPhone／Android／電腦都能離線使用
- 另有單一檔離線版 `docs/shengzi-offline.zip`，給電腦用（手機無法執行本機 HTML）

## 與使用者合作的方式

- 一律用**繁體中文**回覆。
- 回覆結構：**結論 → 底層邏輯與關鍵假設 → 潛在風險（觸發條件、影響、因應）**。
- 需要使用者提供資訊、做決定或操作時，把「待你確認／待你提供」清單放在回覆**最前面**。
- 需求不明確時不要猜：先寫出最合理的解讀與可能方向，請使用者確認。
- 較大的功能（新資料來源、架構變動）：**先提方案，確認後再做**。小修正可直接做。
- 程式原則：可維護性優先、架構簡單、註解精簡。符合這些原則的改善建議可以主動提出。
- 技術說明用生活化比喻，不要用硬體或 RTL 的比喻。
- 推送到 GitHub 前，涉及公開、授權、無法撤回的事項要先問。

## 檔案結構

```
src/shengzi.html        唯一的頁面原始碼。功能修改都在這裡
src/zhuyin-font.css     霞鶩文楷 TC 子集（注音符號＋頁首固定字），由 tools/data.py 產生
tools/data.py           產生 docs/strokes/ 與 src/zhuyin-font.css（需 npm）
tools/build.py          由 src/ 組出 docs/index.html、docs/sw.js、docs/shengzi-offline.zip
tools/check.py          端到端測試：網站連線、網站斷網（service worker）、單一檔離線版
.github/workflows/check.yml  每次 push／PR 自動組建、確認 docs/ 與 src/ 同步、跑 check.py
docs/data/              教育部《國語小字典》原始壓縮檔，不可修改
docs/strokes/s*.json    筆順資料，依字碼 % 200 分成 200 個檔
docs/vendor/            jsPDF 2.5.1（本地副本，不用 CDN）
docs/icons/, docs/manifest.webmanifest   PWA 圖示與設定
```

`docs/` 除了 `docs/data/` 之外都是產生出來的，不要手動修改。

## 修改流程

```bash
pip install openpyxl fonttools brotli playwright
# 1. 修改 src/shengzi.html
python3 tools/build.py      # 2. 重新組建
python3 tools/check.py      # 3. 三項測試都要 [OK]（需要 Chrome；路徑用 CHROME 環境變數指定）
# 4. commit、push
```

只有更新筆順或字型時才需要先跑 `python3 tools/data.py`。

- commit 作者使用 `kkccy1324 <kkccy1324@users.noreply.github.com>`，不要使用使用者的真實信箱。
- 每次 build 都會依檔案內容產生新的 service worker 快取版本。已開啟的頁面偵測到新版時，頁首會出現「更新」按鈕（邏輯在 `tools/build.py` 的 `PWA_SCRIPT`）。
- build 結果是固定的（離線版 zip 用固定時間戳），同一份原始碼重跑不會產生差異。忘了重新 build 就 push，CI 會失敗。

## 關鍵設計決策（不要在沒討論的情況下推翻）

1. **字典直接用教育部原始檔**：教育部《國語小字典》授權是 CC BY-ND 3.0 TW（禁止改作）。使用者明確要求 repo 只放未修改的原始壓縮檔，不散布轉換後的資料。頁面在瀏覽器裡解析原始檔：自己寫的 zip 讀取器＋`DecompressionStream('deflate-raw')`＋`DOMParser` 讀 xlsx，邏輯在 `buildDict()`。需要 iOS 16.4 以上。
2. **多音字判讀**：預設讀音取字典解釋文字中附注音用例最多的讀音。詞語判讀是相鄰兩字在用例中的讀音多數決（最高票 ≥ 第二名 2 倍才採用）。
3. **注音校對四種狀態**：綠＝確認（含依詞語判讀的多音字）、藍＝單獨出現的多音字待選、黃＝輸入的注音與字典不符（仍印使用者輸入的注音）、紅＝字典查無此字。
4. **範字用筆順外框繪製，不用字型**：讓筆順序號和字形對齊，同時符合教育部標準字形。沒有筆順資料的字（《國語小字典》4,311 字中有 260 個罕用字）才用字型。
5. **筆順呈現四選一**：不顯示／標序號／分解格／兩者（預設兩者）。分解格高度依「這次輸入中筆畫最多的字」決定。
   - 整個筆順功能由 `src/shengzi.html` 的 `STROKE_ORDER` 常數開關。目前為 `false`（使用者要求先關閉，筆順改好後再開）：隱藏筆順設定、輸出不標序號也不加分解格，範字仍用筆順外框畫。改成 `true` 後重新 build 即上線。
6. **PDF**：把每頁畫在 9 px/mm 的 canvas 上，再用 jsPDF 轉成 PDF。不在 PDF 裡內嵌中文字型。
7. **一份原始碼產出三種版本**：claude.ai 版（使用 `downloads` 能力下載）、GitHub Pages PWA、單一檔離線版（所有資料內嵌在 `<script type="application/json">` 和 base64 的原始 zip）。頁面用 `OFFLINE`（有沒有內嵌資料）和 `CAN_PRINT`（不在 iframe 裡）判斷執行環境。
8. **手機版面**：寬度小於 900px 時用「設定／預覽」切換分頁。早期使用者回報「看不到預覽」，原因是預覽排在很長的設定面板下方。

## 資料來源與授權

| 資料 | 來源 | 授權 |
|---|---|---|
| 注音、例詞 | 教育部《國語小字典》2026-09-29 版（辭典公眾授權網） | CC BY-ND 3.0 TW，原檔不改 |
| 筆順 | npm `zh-stroke-data@0.0.75`（g0v，取自教育部常用國字標準字體筆順學習網） | CC0 |
| 字型 | npm `lxgw-wenkai-tc-webfont@1.2.0` | OFL 1.1 |
| jsPDF | npm `jspdf@2.5.1` | MIT |
| 本專案程式碼 | | MIT |

## 目前狀態與待辦

- [x] repo 為 public，GitHub Pages 已開啟（2026-11-08 由 GitHub API `has_pages: true` 確認；沙箱連不到 github.io，網站內容未實際開啟驗證）。
- [ ] **iPhone 實測未做**：加入主畫面後「下載 PDF」與「直接列印」是否可用。若不行，考慮改成開啟 PDF 預覽，再用分享選單列印。
- [ ] **筆畫多的字序號擁擠**：例如「學」16 畫配 20 mm 格。曾提議筆畫超過約 12 畫時自動放大範字格，使用者尚未決定。
- [ ] claude.ai 上有一份舊的 artifact 版本（字典仍用轉換後的 JSON），以 GitHub 網站為主。使用者尚未決定是否同步或刪除。
- 已知限制：沙箱環境無法測試 Safari/WebKit，只能測 Chrome。iOS 相容性要靠使用者回報。

## 開發歷程摘要

1. 田字格＋十字虛線、範字＋描紅、直式／橫式、PDF 輸出
2. 描紅方式：自訂格數／一半描紅／全部描紅
3. 注音依《國語小字典》自動帶入與校對，加上顏色圖例
4. 筆順：序號＋分解格，可切換
5. 單一檔離線版
6. 手機「設定／預覽」切換分頁、載入失敗與錯誤的診斷訊息
7. 為了讓 iPhone 也能離線，改成 GitHub Pages PWA
8. 字典改為瀏覽器直接讀取教育部原始檔（授權考量）
