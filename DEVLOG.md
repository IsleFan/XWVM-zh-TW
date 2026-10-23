# DEVLOG

## 2026-10-23

### 修改內容（Changes）
- `font-plugin/ChineseFontLoader.cs`：啟動時以系統繁中字型（PingFang TC／微軟正黑體）建立動態 TMP 字型，掛為全域與各字型 fallback。
- `font-plugin/UiTextLocalizer.cs` ＋ `XwvmChineseFont-zh-TW.json`：中文語系時替換 Rewired 按鍵設定畫面、動作名稱、滑鼠按鍵名稱（276 條），切換語言時還原。
- `font-plugin/patch_xwvm.py`、`install_mac.sh`：註冊 DLL 到 `ScriptingAssemblies.json`／`RuntimeInitializeOnLoads.json`；macOS 以 APFS clone 產生 `xwvm-zhTW.app` 並重新 ad-hoc 簽章。
- `translation/translate/`：8,940 條全部翻譯；`exports/zh-TW-v1/` 語言包。
- `translation/glossary/`：台灣星戰術語表（296 條，含來源分級）、遊戲新增專有名詞（477 條）、翻譯規範。
- `translation/tools/localization_tool.py`：驗證器允許中文複數分支內 `{}` 數量不同；條件文字含冒號時不再誤判為格式器名稱。
- `translation/tools/pipeline/`：分批、檢查（含簡體字偵測）、合併腳本。
- 多語系支援（分支 `feature/multilingual-fonts`）：
  - `font-plugin/FallbackFontLoader.cs`（原 ChineseFontLoader.cs）：依語系組字型鏈（`Fonts.<語系>` ＋ `Fonts.coverage`），可掛多個 fallback，切換語言時重排；內建 zh-TW／zh-HK／zh／ja／ko 字型鏈。
  - `font-plugin/LocaleWatcher.cs`：輪詢遊戲語系，通知字型與介面文字模組。
  - `font-plugin/UiTextLocalizer.cs`：改讀所有 `XwvmChineseFont-<語系>.json`，依語系套用。
  - `font-plugin/patch_xwvm.py`：入口改為 `FallbackFontLoader.Init`，複製所有語系的 json。
  - `translation/tools/localization_tool.py`：新增 `--locale`；欄位名 `target_<語系>`、trgLang、匯出路徑與檔名依語系；複數分支數依 Unity SmartFormat 規則檢查（單一複數形語言另有警告）。zh-TW 重新建置與 zh-TW-v1 逐位元相同。
  - `translation/tools/test_localization_tool.py`：新增 5 個測試（共 19 個）。
  - `translation/tools/pipeline/`：check_batch／merge_outputs 依語系運作。
  - `translation/install_zh-TW_mac.sh` → `install_language_mac.sh`：自動判斷語言包語系。
- 公開前清理：移除 ChatGPT 流程檔（CLOUD-HANDOFF／CLOUD-CONTENTS）與本機路徑；commit 改用 GitHub noreply 信箱；README 加非官方聲明；倉庫改為公開。

### 問題與解法（Problems & Solutions）
- 中文顯示方框：遊戲 TMP 字型無 CJK 字形 → 執行期動態字型 fallback。
- BepInEx 5.4.23.5 doorstop 在 Unity 6000.3.7f1（macOS arm64／Rosetta）無法啟動 → 改用 Unity 的 RuntimeInitializeOnLoad 清單載入外掛。
- `/Applications/XWVM/xwvm.app` 屬 root → 修改 APFS clone 副本，不動原版。
- SmartFormat 對 `zh` 永遠取第一個複數分支 → 所有複數分支寫成通用形（`{} 款遊戲|{} 款遊戲`）。
- 按鍵設定畫面不在 XLIFF → 外掛執行期替換文字。
- SmartFormat 的俄文等規則不看分支數就回傳 0–2 等索引，分支不足會丟出例外 → 驗證器依語言要求分支數（ru 3、pl 4、ar 6…）。
- 機種 CSV 的迴圈變數 `field` 遮蔽了新加的同名變數，導致驗證全錯 → 改名 `target_key`，靠既有測試抓到。

### 待辦事項（TODO）
- 在遊戲中逐畫面確認排版（任務說明框換行、HUD／CMD 長度、任務目標組句）。
- 以遊戲內「Export Original Game Strings」匯出的原文比對並更新任務文字。
- Windows 版實測（字型：msjh.ttc）。
- 視需要檢討「本遊戲建議」譯名。
- 日文／韓文字型鏈只驗證了字型偵測（log 已列出 Hiragino、Apple SD Gothic Neo），尚未以實際 ja／ko 語言包在遊戲中測試。
