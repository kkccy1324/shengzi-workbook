# 生字練習簿產生器

輸入國小生字，自動排出 A4 田字格練習頁：格子有十字虛線方便定位，注音依教育部《國語小字典》自動帶入並校對，範字依教育部標準字體標出筆順，可下載 PDF 或直接列印。

**線上使用：** https://kkccy1324.github.io/shengzi-workbook/

第一次連網開啟後會把資料存在裝置上，之後沒有網路也能用。

## 功能

- **田字格練習頁**：直式（由右而左）或橫式，格子大小 24／20／16 mm，格線可選綠、紅、灰。
- **範字與描紅**：每個字第一格是黑色範字，描紅方式可選「自訂格數」、「一半描紅」、「全部描紅」。
- **注音自動帶入與校對**：只打國字即可。連著打的字（如「長大」）會當成詞語判斷多音字讀音。
- **筆順**：可選「標序號」（範字上標紅色筆畫順序）、「分解格」（一筆一筆加上去）、兩者或不顯示。
- **頁首**：標題、姓名、日期、家長簽名欄。
- **輸出**：下載 A4 PDF，或用瀏覽器直接列印。

### 注音校對顏色

| 顏色 | 意思 |
|---|---|
| 綠 | 讀音已確認 |
| 藍 | 多音字，單獨一個字無法判斷，請點選正確讀音 |
| 黃 | 輸入的注音和字典不同 |
| 紅 | 字典查無此字，可能是簡體字、異體字或錯字 |

點一下字可以看所有讀音和例詞，點選讀音就會寫回輸入框。

## 使用方式

### iPhone

1. 用 Safari 開啟上方網址，等頁面下方出現「已可離線使用」。
2. 點「分享」→「加入主畫面」。
3. 之後從主畫面的圖示開啟，沒有網路也能用。

### Android

1. 用 Chrome 開啟上方網址，等頁面下方出現「已可離線使用」。
2. 點右上角「⋮」→「加到主畫面」或「安裝應用程式」。

### 電腦

直接用瀏覽器開啟上方網址即可，第一次開啟後同樣可以離線使用。

如果想要完全不經過網站，可以下載單一檔離線版：[shengzi-offline.zip](https://kkccy1324.github.io/shengzi-workbook/shengzi-offline.zip)。解壓縮後用 Chrome、Edge 或 Safari 打開 HTML 檔即可。手機無法使用這個檔案，請改用上面加入主畫面的方式。

### 列印設定

印表機設定請選 **A4、邊界「無」、縮放 100%（實際大小）**，格子尺寸才會正確。

## 專案結構

```
src/shengzi.html        頁面原始碼（唯一需要修改的程式）
src/zhuyin-font.css     注音用字型子集（由 tools/data.py 產生）
tools/data.py           產生筆順資料與字型子集
tools/build.py          組出網站與單一檔離線版
docs/data/              教育部《國語小字典》原始開放資料（未修改）
docs/                   GitHub Pages 網站（除 docs/data/ 外皆由 tools 產生，不要手動修改）
```

## 更新資料與重新建置

需要 Python 3（套件：`openpyxl`、`fonttools`、`brotli`）與 npm。

```bash
pip install openpyxl fonttools brotli
python3 tools/data.py    # 只有更新教育部資料或筆順資料時才需要
python3 tools/build.py   # 修改 src/shengzi.html 後執行
```

教育部更新《國語小字典》時，從[辭典公眾授權網](https://language.moe.gov.tw/001/Upload/Files/site_content/M0001/respub/dict_mini_download.html)下載新的壓縮檔，原封不動放進 `docs/data/`，並把 `src/shengzi.html`、`tools/data.py`、`tools/build.py` 裡的檔名改成新檔名，再依序執行上面兩個指令。

## 資料來源與授權

| 資料 | 來源 | 授權 |
|---|---|---|
| 注音與例詞 | 教育部《國語小字典》開放資料（2026-09-29 版），[辭典公眾授權網](https://language.moe.gov.tw/001/Upload/Files/site_content/M0001/respub/index.html) | [CC BY-ND 3.0 TW](https://creativecommons.org/licenses/by-nd/3.0/tw/) |
| 筆順 | [g0v/zh-stroke-data](https://github.com/g0v/zh-stroke-data)，取自教育部常用國字標準字體筆順學習網 | CC0 |
| 注音字型 | [霞鶩文楷 TC（LXGW WenKai TC）](https://github.com/lxgw/LxgwWenkaiTC) | SIL Open Font License 1.1 |
| PDF 產生 | [jsPDF](https://github.com/parallax/jsPDF) 2.5.1 | MIT |

注音與例詞直接使用教育部原始資料：`docs/data/dict_mini_2019_20260929.zip` 是從辭典公眾授權網下載的原始檔，未經任何修改。網頁開啟時在使用者的瀏覽器裡讀取這個檔案查詢讀音，本專案不另外散布轉換後的字典資料。

> 資料來源：教育部《國語小字典》，中華民國教育部，依 CC BY-ND 3.0 TW 授權使用。

本專案程式碼以 MIT 授權釋出，詳見 [LICENSE](LICENSE)。
