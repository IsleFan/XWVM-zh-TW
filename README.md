# XWVM 繁體中文化（zh-TW）

讓 [XWVM](https://www.moddb.com/mods/xwvm)（*Star Wars: X-Wing* 1993 的現代重製引擎）完整顯示**繁體中文（台灣）**。

> **非官方粉絲翻譯。** 本專案與 Lucasfilm、Disney、LucasArts 及 XWVM Team 均無關聯，亦未獲其認可。
> 僅供非商業用途；使用者需自行擁有正版 *Star Wars: X-Wing* 及 XWVM。
> 若權利人要求，將立即移除相關內容。

- 對應版本：XWVM `1.0.20260923.2004`（Unity 6000.3.7f1，Mono）
- 翻譯量：**8,940 條字串全部翻完**（介面、設定、中央大廳、HUD、任務目標、Tour 1–5 全部任務簡報、歷史／額外任務、過場字幕、製作群名單、機種名稱），另加 276 條按鍵設定畫面字串
- 術語：以台灣官方／授權出版的星際大戰譯名為準（路克·天行者、韓·索羅、達斯·維達、X翼戰機、鈦戰機、滅星者、死星、雅文…）
- 已在 macOS（Apple Silicon）實機確認可顯示中文；Windows 版做法相同但尚未實測

---

## 快速安裝（macOS）

需要先裝好 XWVM（`/Applications/XWVM/xwvm.app`）並在遊戲中加入原版 X-Wing。

```bash
# 1. 中文字型外掛：建立 /Applications/XWVM/xwvm-zhTW.app（原版 app 不會被修改）
./font-plugin/install_mac.sh

# 2. 中文語言包：複製到 XWVM 的 StreamingAssets（會要求輸入 Mac 密碼）
./translation/install_zh-TW_mac.sh zh-TW-v1
```

3. 用 **`/Applications/XWVM/xwvm-zhTW.app`** 開遊戲。
4. `Settings > Audio and Language > Subtitles and Language > Language` 選 **Chinese (Traditional)**。

> XWVM 每次更新後要重跑第 1 步（重建 xwvm-zhTW.app）；語言包若被更新覆蓋，重跑第 2 步。
> 移除語言包：`./translation/install_zh-TW_mac.sh --uninstall`；移除外掛：刪掉 `xwvm-zhTW.app` 即可。

## Windows（之後使用）

同一個 `XwvmChineseFont.dll` 不必重新編譯即可用於 Windows：

```
python font-plugin\patch_xwvm.py "C:\路徑\XWVM\XWVM_Data" font-plugin\XwvmChineseFont.dll
```

- `XWVM_Data` 是「執行檔名稱_Data」資料夾；原始 JSON 會備份成 `*.orig`，移除時加 `--uninstall`。
- 預設字型為微軟正黑體（`msjh.ttc`）。
- 語言包：把 `translation/exports/zh-TW-v1/Localization/` 裡的 `XLIFF/zh-TW/` 與 `CSV/*_zh-TW.csv` 複製到 XWVM 的 `StreamingAssets/Localization/` 對應位置。

---

## 做了什麼、怎麼做的

### 1. 問題：中文變成方框

XWVM 本身會讀取 `StreamingAssets/Localization/XLIFF/<語系>/*.xliff`，檔名是 `*_zh-TW.xliff` 時會自動註冊「Chinese (Traditional)」語系，所以**翻譯檔載得進去**。但介面用的 TextMeshPro 字型（Eurostile、News Gothic、Franklin Gothic…）都只有拉丁字元，中文字找不到字形就顯示成方框，而且遊戲沒有提供外掛字型的入口。

### 2. 解法：XwvmChineseFont 字型外掛（`font-plugin/`）

一個約 450 行的 C# 外掛，在遊戲啟動時：

1. 從系統找繁中字型（macOS：蘋方-繁 PingFang TC Medium → 黑體-繁 → Arial Unicode；Windows：微軟正黑體 → 新細明體）。`.ttc` 字型集會逐一比對字型家族名稱，避免選到簡體或日文字面。
2. 用 TextMeshPro 的 `TMP_FontAsset.CreateFontAsset` 建立**動態 SDF 字型**（用到哪個字才畫哪個字，不需要事先做字型圖集）。
3. 把它加到 `TMP_Settings` 的全域 fallback，以及每個已載入 TMP 字型的 `fallbackFontAssetTable`；每次切換場景再補一次。

**載入方式**：最初嘗試 BepInEx 5.4.23.5，但它的 doorstop 在這版 Unity 6 上無法啟動（arm64 與 Rosetta 都試過）。改用 Unity 內建機制：

- 把 DLL 放進遊戲的 `Managed/`，並登記到 `ScriptingAssemblies.json`；
- 在 `RuntimeInitializeOnLoads.json` 加一筆，讓 Unity 在第一個場景載入前呼叫 `ChineseFontLoader.Init`。

macOS 的 XWVM 安裝在 root 擁有的資料夾，所以 `install_mac.sh` 用 APFS clone 複製出 `xwvm-zhTW.app`（幾乎不佔空間），修改副本後重新做 ad-hoc 簽章，**原版 app 完全不動**。存檔與設定兩者共用。

**按鍵設定畫面**：這個畫面是第三方輸入套件 Rewired 的 ControlMapper，文字寫死在遊戲資料裡、不經過 XLIFF（西、義、德文版這頁也都是英文）。外掛的 `UiTextLocalizer` 在語系為中文時，依 `XwvmChineseFont-zh-TW.json`（英文原文 → 中文，276 條）替換 ControlMapper 的 LanguageData 字串與畫面上的 TMP 文字；切回其他語言會還原。鍵盤按鍵名（ESC、Ctrl + F1）刻意保留英文。

驗證方式：外掛會在 `Player.log` 寫下使用的字型、掛上 fallback 的字型數，以及離開遊戲時實際經由中文字型畫出的字（例如 `…開始遊戲`）。全部譯文用到的 1,774 個字元都已用 CoreText 確認在 PingFang TC 內有字形。

### 3. 翻譯流程（`translation/`）

1. **抽取**：以 XWVM 隨附的 XLIFF（31 份）與機種 CSV 為來源，轉成可編輯 JSON（`translate/`），保留穩定 ID、英文原文、情境與開發者註記。
2. **權威術語表**（`translation/glossary/glossary_zh-TW.csv`，296 條）：查證台灣 Disney+、樂高台灣、EA 台灣、台灣媒體與中文 Wookieepedia 等來源，每條標註來源等級——官方 28、授權出版 24、社群慣用 33、本遊戲建議 211（台灣無既有譯名的遊戲專有名詞）。特別處理台灣與中國用語差異（滅星者／歼星舰、武技族／伍基人、雅文、飛彈、雷射、砲）。
3. **翻譯規範**（`translation/glossary/STYLE_GUIDE.zh-TW.md`）：標點、語氣、HUD 長度限制、艦名加「號」規則、希臘字母呼號與型別縮寫（CRV、X-W、T/F）保留英文、反抗軍／叛軍依說話者立場等。
4. **分批翻譯**：任務文字中重複的短標籤（呼號、艦名、貨物）先去重統一翻譯（5,985 次出現 → 1,748 條），產出的名稱表再交給長篇簡報翻譯使用，讓 HUD 與簡報名稱一致。共 10 批，翻譯中新增的 477 個遊戲專有名詞記錄在 `glossary/game_terms_coined.tsv`。
5. **驗證**：`tools/localization_tool.py validate --complete` 檢查每條譯文的 SmartString 變數、`choose(...)` 選項、分支數、富文字標籤、`[[ ]]`／`(( ))`／`(* *)` 標記、換行數，並另外檢查簡體字。結果 0 錯誤、0 未翻。
6. **匯出**：`build` 產生遊戲原生格式的 `exports/zh-TW-v1/`（31 個 XLIFF ＋ 機種 CSV）。

**一個重要的技術細節**：Unity Localization 的 SmartFormat 對中文（`zh`）的複數規則永遠只取**第一個**分支，所以 `{n:plural:1 game|{} games}` 必須翻成 `{n:plural:{} 款遊戲|{} 款遊戲}`，否則 3 款會顯示成「1 款」。驗證器已為此調整（允許複數分支內的 `{}` 數量不同），也修正了條件文字含冒號時的誤判。

---

## 修改翻譯

```bash
cd translation
# 編輯 translate/**/*.json 的 target_zh_TW 欄位
python3 tools/localization_tool.py validate            # 檢查格式
python3 tools/localization_tool.py build --name zh-TW-v2
./install_zh-TW_mac.sh zh-TW-v2
```

按鍵設定畫面等「不在 XLIFF 裡」的字串：編輯 `font-plugin/XwvmChineseFont-zh-TW.json` 後重跑 `font-plugin/install_mac.sh`。

## 重新編譯外掛

需要 .NET SDK（任何 8.0 以上版本即可），編譯時參照本機 XWVM 的遊戲 DLL：

```bash
cd font-plugin
dotnet build -c Release && cp bin/Release/XwvmChineseFont.dll .
# Windows：dotnet build -c Release -p:GameManaged="C:\...\XWVM_Data\Managed"
```

設定（選用）：在 DLL 旁放 `XwvmChineseFont.ini` 可指定字型檔、字型家族、字重與大小倍率；或把 `.ttf/.otf` 放進 `XwvmChineseFont-fonts/` 資料夾。詳見 [font-plugin/README.zh-TW.md](font-plugin/README.zh-TW.md)。

---

## 目錄

| 路徑 | 內容 |
| --- | --- |
| `font-plugin/` | 字型＋介面文字外掛原始碼、預先編譯的 DLL、按鍵畫面對照表、macOS 安裝腳本、跨平台修補腳本 |
| `translation/translate/` | 可編輯的翻譯 JSON（唯一日常編輯區） |
| `translation/exports/zh-TW-v1/` | 可直接安裝的語言包 |
| `translation/glossary/` | 台灣星戰術語表、遊戲新增專有名詞、翻譯規範 |
| `translation/tools/` | 抽取／驗證／匯出工具與測試；`pipeline/` 為分批翻譯用的切分、檢查、合併腳本 |
| `translation/reference/` | XWVM 原始 XLIFF／CSV 快照（勿編輯） |
| `translation/reports/` | 盤點與驗證報告 |
| `DEVLOG.md` | 開發紀錄 |

## 已知限制

- 尚未逐畫面確認中文排版：任務說明框的換行、HUD 目標框與 CMD 的長度、由片段組合的任務目標句子。
- 翻譯來源是 XWVM 隨附的樣板文字，未使用遊戲內「Export Original Game Strings」匯出的版本，與你註冊的原版遊戲版本可能有少數差異。
- 未涵蓋：TIE Fighter 專用文字、自訂任務、圖片內嵌文字、配音。
- 「本遊戲建議」的譯名（例如 韋奇·安提利斯、畢格斯·達克萊特、護衛艦／巡防艦）是本專案自訂，並非台灣官方譯名。

## 著作權與授權

- `font-plugin/` 與 `translation/tools/` 為本專案原創程式碼。
- XWVM 語系來源檔（`translation/reference/` 及譯文的英文原文）來自 XWVM Team，MIT 授權，見 `translation/LICENSE-XWVM-localization.txt`。
- 任務簡報、過場等原版遊戲文字及其譯文涉及 Lucasfilm／LucasArts 的著作權；*Star Wars* 及相關名稱與商標為 Lucasfilm Ltd. 所有。本專案以非商業粉絲翻譯形式提供，不主張上述內容的任何權利；權利人如有疑慮請開 issue 聯絡，將立即處理下架。
- 不得將本專案用於任何商業用途或販售。
- 不包含任何遊戲執行檔、遊戲 DLL、反編譯程式碼或字型檔（字型使用系統內建）。
