# XWVM CJK 字型外掛（XwvmChineseFont）

讓 XWVM 的 TextMeshPro 介面正確顯示中文、日文、韓文等非拉丁文字（解決文字變成方框）。
實測版本：XWVM 1.0.20260923.2004（Unity 6000.3.7f1，Mono）。
（組件名稱沿用 XwvmChineseFont，以便與已安裝的版本相容。）

## 原理

XWVM 的字型（Eurostile、News Gothic 等）只有拉丁字元。外掛在遊戲啟動時用系統字型建立
**動態 TextMeshPro 字型**，依序掛到每一個 TMP 字型的 fallback 清單；找不到的字由這串字型補上，
用到時才產生字形，不需要事先做字型圖集，沒用到的字型也幾乎不佔記憶體。

**依語系選字型**：每個語系有一條字型鏈（`Fonts.<語系>` ＋ `Fonts.coverage`）。排在最前面的字型決定字形風格
（例如日文用 Hiragino、繁中用蘋方-繁，漢字寫法才會正確），後面的字型負責其他文字（韓文、假名…）。
遊戲切換語言時，外掛會自動重排 fallback 順序。

| 語系 | 預設字型鏈（macOS／Windows 中先找到者優先） |
| --- | --- |
| zh-TW | 蘋方-繁、黑體-繁／微軟正黑體 |
| zh-HK | 蘋方-港、蘋方-繁／微軟正黑體 |
| zh（含 zh-CN） | 蘋方-簡、黑體-簡／微軟雅黑 |
| ja | Hiragino Sans、Hiragino Kaku Gothic ProN／Yu Gothic、Meiryo |
| ko | Apple SD Gothic Neo／Malgun Gothic |
| 其他（英、德、俄…） | 蘋方-繁／微軟正黑體 |
| 全部語系最後再加 | Apple SD Gothic Neo、Malgun Gothic、Hiragino Sans、Yu Gothic、蘋方-繁、微軟正黑體、Arial Unicode MS |

Linux 版會找 Noto Sans CJK。字型鏈中找不到的字型會自動略過。

Unity 會依 `RuntimeInitializeOnLoads.json` 在啟動時呼叫外掛（`FallbackFontLoader.Init`），所以不需要 BepInEx
（BepInEx 5.4.23.5 的 doorstop 在這版 Unity 無法啟動，已測試過）。

**限制**：TextMeshPro 不處理由右往左（阿拉伯文、希伯來文）與需要字形組合（泰文、印地文）的文字，這些語言即使有字型也無法正確排版。

## 不在 XLIFF 裡的介面文字

按鍵設定視窗（Rewired 控制對應器）、輸入動作名稱、滑鼠按鍵名稱寫死在遊戲資料裡，XLIFF 翻不到。
外掛會讀取 DLL 旁所有 `XwvmChineseFont-<語系>.json`（英文原文 → 譯文），在遊戲選到該語系時於執行期替換
（先比對完整語系代碼，例如 `zh-TW`，再比對語言，例如 `ja`）；切回其他語言會還原英文。

- 目前提供：`XwvmChineseFont-zh-TW.json`（276 條）。
- 新增語言：複製一份改名為 `XwvmChineseFont-ja.json` 等，把值改成該語言的譯文，重跑安裝即可。

## macOS 安裝

```sh
./install_mac.sh
```

- 會在 `/Applications/XWVM/` 產生 `xwvm-zhTW.app`（原版 `xwvm.app` 不會被修改）。
  使用 APFS 複製，幾乎不佔額外空間。
- 之後用 `xwvm-zhTW.app` 開遊戲。存檔與設定和原版共用。
- **XWVM 每次更新後要重跑一次** `install_mac.sh`。

## Windows 安裝（之後用）

同一個 `XwvmChineseFont.dll` 可直接用在 Windows，不需要重新編譯。

1. 安裝 Python 3。
2. 找到 XWVM 安裝資料夾裡的 `XWVM_Data`（名稱為「執行檔名稱_Data」）。
3. 執行（會一併複製同資料夾內所有 `XwvmChineseFont-*.json`）：
   ```
   python patch_xwvm.py "C:\路徑\XWVM\XWVM_Data" XwvmChineseFont.dll
   ```
4. 移除：`python patch_xwvm.py "C:\路徑\XWVM\XWVM_Data" --uninstall`（第一次修改前的原始檔也會另存為 `*.orig`）。

## 自訂字型與大小（選用）

在 `XwvmChineseFont.dll` 旁放 `XwvmChineseFont.ini`（macOS 版放在本資料夾後重跑 `install_mac.sh`）：

```ini
# 指定字型檔；空白 = 自動找系統字型。也可以把 .ttf/.otf/.ttc 放進 XwvmChineseFont-fonts 資料夾。
# 使用者提供的字型永遠排在字型鏈最前面（.ttc 會選符合該語系字型鏈的字面，否則用 FaceIndex）。
FontFile=
FaceIndex=0
# 覆寫某個語系的字型鏈（字型家族名稱，以分號分隔）
Fonts.ja=Hiragino Sans;Yu Gothic;Noto Sans CJK JP
# 所有語系最後都會加上的補字字型
Fonts.coverage=Apple SD Gothic Neo;Malgun Gothic;Arial Unicode MS
PreferredStyle=Medium
# 這些字相對遊戲字型的大小倍率
Scale=1.0
```

## 翻譯檔放哪裡

遊戲會從檔名自動註冊語系：檔名須為 `*_<語系>.xliff`，語系代碼格式為 `xx` 或 `xx-YY`（例如 `ja`、`ko`、`zh-TW`），放進

- macOS：`/Library/Application Support/XWVM Team/XWVM/StreamingAssets/Localization/XLIFF/<語系>/`
- Windows：XWVM 的 `StreamingAssets/Localization/XLIFF/<語系>/`

可用 `translation/install_language_mac.sh` 安裝。建議不要直接改 `en` 資料夾的英文原檔。

## 檢查是否生效

看 `~/Library/Logs/XWVM Team/XWVM/Player.log`（Windows：`%USERPROFILE%\AppData\LocalLow\XWVM Team\XWVM\Player.log`）：

```
[XwvmChineseFont] Found font families: PingFang HK, PingFang TC, PingFang SC, ..., Hiragino Sans, Apple SD Gothic Neo, Arial Unicode MS
[XwvmChineseFont] Font chain for locale 'zh-tw': PingFang TC Medium > Heiti TC Medium > Apple SD Gothic Neo Medium > Hiragino Sans W5 > Arial Unicode MS Regular
[XwvmChineseFont] Applied 5 fallback font(s) to 5 TextMeshPro font(s).
[XwvmChineseFont] Loaded 276 UI translations for 'zh-TW' from ...
[XwvmChineseFont] Session rendered N glyph(s) through XWVM Fallback (PingFang TC Medium): ...
```

## 重新編譯

```sh
dotnet build -c Release            # macOS，參照 /Applications/XWVM 內的遊戲 DLL
dotnet build -c Release -p:GameManaged="C:\...\XWVM_Data\Managed"   # Windows
```
