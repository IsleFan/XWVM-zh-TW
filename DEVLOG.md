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

### 問題與解法（Problems & Solutions）
- 中文顯示方框：遊戲 TMP 字型無 CJK 字形 → 執行期動態字型 fallback。
- BepInEx 5.4.23.5 doorstop 在 Unity 6000.3.7f1（macOS arm64／Rosetta）無法啟動 → 改用 Unity 的 RuntimeInitializeOnLoad 清單載入外掛。
- `/Applications/XWVM/xwvm.app` 屬 root → 修改 APFS clone 副本，不動原版。
- SmartFormat 對 `zh` 永遠取第一個複數分支 → 所有複數分支寫成通用形（`{} 款遊戲|{} 款遊戲`）。
- 按鍵設定畫面不在 XLIFF → 外掛執行期替換文字。

- 公開前清理：移除 ChatGPT 流程檔（CLOUD-HANDOFF／CLOUD-CONTENTS）與本機路徑；commit 改用 GitHub noreply 信箱；README 加非官方聲明；倉庫改為公開。

### 待辦事項（TODO）
- 在遊戲中逐畫面確認排版（任務說明框換行、HUD／CMD 長度、任務目標組句）。
- 以遊戲內「Export Original Game Strings」匯出的原文比對並更新任務文字。
- Windows 版實測（字型：msjh.ttc）。
- 視需要檢討「本遊戲建議」譯名。
