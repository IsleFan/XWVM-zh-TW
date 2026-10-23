# XWVM 繁體中文翻譯工作目錄

## 目前狀態（2026-10-23）

- **8,940 個欄位全部翻譯完成**，`validate --complete` 通過。語言包：`exports/zh-TW-v1/`（31 個 XLIFF ＋ 機種 CSV）。
- 安裝：`./install_zh-TW_mac.sh zh-TW-v1`（需輸入密碼）；移除：`./install_zh-TW_mac.sh --uninstall`。
- 中文字型需搭配 XwvmChineseFont 外掛，從 `/Applications/XWVM/xwvm-zhTW.app` 啟動。
- 術語：`glossary/glossary_zh-TW.csv`（台灣星戰權威譯名，含來源分級）、`glossary/game_terms_coined.tsv`（翻譯時新增的遊戲專有名詞）、`glossary/STYLE_GUIDE.zh-TW.md`（翻譯規範）。
- 驗證器調整：允許複數分支內的 `{}` 數量不同（Unity SmartFormat 對中文永遠取第一個複數分支），並修正條件文字含冒號時的誤判。
- 尚未在遊戲中逐畫面確認排版。下方原始說明中「目前所有繁中翻譯欄都留白」已不適用。

這是**可翻譯資源與離線工具**，不是已驗證可載入遊戲的中文語言包。對應本機 XWVM `1.0.20260923.2004`。原版遊戲、XWVM 安裝檔、存檔與設定都未修改。

## 從這裡開始

1. 用可儲存 UTF-8 的文字編輯器開啟 `translate/` 下的 JSON。
2. **只填 `target_zh_TW`**；需要筆記時填 `translator_note`。保留 `id`、`source`、情境與其他欄位。
3. `source` 是英文原文。空白 `target_zh_TW` 表示未翻譯，匯出時會使用英文原文。
4. 建議先做 `01_ui_and_xwing`，再做 `02_common`、`03_original_game`；`04_smart_strings` 的格式較複雜，可留後面。`05_species` 是機種名稱、縮寫與語法欄位。

例如原文 `Page {pIndex} / {pCount}` 的翻譯欄可填：

```json
"target_zh_TW": "第 {pIndex} 頁，共 {pCount} 頁"
```

JSON 字串中的雙引號寫成 `\"`，換行寫成 `\n`，反斜線寫成 `\\`。不要把這些檔案當作遊戲可直接載入的 JSON 語言包。

## 內容

| 分類 | 編輯檔數 | 欄位總數 | 有英文原文的欄位 |
| --- | ---: | ---: | ---: |
| UI 與 X-Wing 介面 | 8 | 864 | 843 |
| 共用文字 | 5 | 208 | 206 |
| 原版任務、簡報、過場等既有翻譯表 | 14 | 7,166 | 7,166 |
| 戰鬥詞彙與 SmartString 等 | 4 | 439 | 439 |
| 102 種機種的 7 個可編輯欄位 | 1 | 714 | 286 |
| **合計** | **32** | **9,391** | **8,940** |

另外 451 欄原文為空白，包括 23 個 XLIFF 項目與 428 個機種可選欄位，不必為了完成度強行填字。目前所有繁中翻譯欄都留白。

- `translate/`：唯一日常編輯區，保留穩定 ID、原文、繁中欄位、情境與原作者註記。
- `reference/`：32 份原生來源快照，請勿編輯。來源共 1,991,873 bytes。
- `tools/`：本次撰寫的 Python 抽取、驗證與匯出工具；只用標準函式庫。
- `manifest.json`、`FILE-LIST.txt`：逐檔來源、大小、筆數與 SHA-256。
- `reports/`：實際盤點、驗證及測試紀錄。
- `exports/`：自行產生的 XLIFF／分號 CSV **候選輸出**，不會自動安裝。

## 驗證與匯出

在終端機進入本目錄後執行：

```sh
python3 tools/localization_tool.py validate
python3 tools/localization_tool.py build --name candidate-001
```

`validate` 允許未完成翻譯，會檢查原文與 ID 不變、JSON／XML 結構、SmartString 變數與分支、富文字與強調標記；進度寫入 `reports/validation.json`。若要檢查是否全部填完，使用 `validate --complete`。

`build` 會新增 `exports/candidate-001/Localization/XLIFF/zh-TW/` 與 `Localization/CSV/`，保留原生檔名、分割表、ID 與 CSV 欄位；已存在的匯出目錄會拒絕覆寫。重建請換名稱。它不複製到遊戲，也不啟動遊戲。

重跑本次測試：

```sh
python3 -m unittest discover -s tools -p 'test_*.py' -v
```

## 翻譯規則與目前限制

保留 `{name}`、`{species.ONE}` 等變數、`choose(...)` 的英文選項值、分支分隔符 `|`、`<b>`／`<color=...>` 等標籤，以及 `[[...]]`、`((...))`、`(*...*)` 標記。可以翻譯標記內的顯示文字。選擇式、複數式中的顯示文字可翻譯，但不可任意改動分支數。驗證採保守比對，並不等於 Unity SmartFormat 執行測試。

機種 CSV 的 `SPECIES_ID`、欄名與 `GENDER` 是識別／語法資料，工具保留不變；只開放 7 個顯示或語法文字欄位。CSV 的空白原文欄位可保留空白，`CLASSIFIER` 等用法仍需與開發者確認。空白翻譯欄無法表達「刻意清空非空原文」。

XWVM 開發者於 2026-10-13 說明 TextMeshPro 的非拉丁字型尚需支援，不能假設放入 TTF 就能顯示中文。這次沒有安裝字型、載入語言包或測試遊戲畫面。`build` 產生的 `font-characters.txt` 可供日後字型涵蓋檢查，但不會建立字型圖集。

詳見 [技術盤點與缺漏](TECHNICAL-NOTES.zh-TW.md)。此目錄適合先開始翻譯；真正匯入仍需確認字型、語系識別、原版版本差異、SmartString 行為與畫面排版。
