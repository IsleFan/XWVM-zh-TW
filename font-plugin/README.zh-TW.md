# XWVM 中文字型外掛（XwvmChineseFont）

讓 XWVM 的 TextMeshPro 介面正確顯示繁體中文（解決中文變成方框）。
實測版本：XWVM 1.0.20260923.2004（Unity 6000.3.7f1，Mono）。

## 原理

XWVM 的字型（Eurostile、News Gothic 等）只有拉丁字元。外掛在遊戲啟動時用系統中文字型
建立一個 **動態 TextMeshPro 字型**，並把它掛到每一個 TMP 字型的 fallback 清單，
找不到的字就由中文字型補上，用到時才產生字形，不需要事先做字型圖集。

Unity 會依 `RuntimeInitializeOnLoads.json` 在啟動時呼叫外掛，所以不需要 BepInEx
（BepInEx 5.4.23.5 的 doorstop 在這版 Unity 無法啟動，已測試過）。

## 不在 XLIFF 裡的介面文字

按鍵設定視窗（Rewired 控制對應器）、輸入動作名稱、滑鼠按鍵名稱寫死在遊戲資料裡，XLIFF 翻不到。
外掛會讀取 `XwvmChineseFont-zh-TW.json`（英文原文 → 中文），在語言選為中文時於執行期替換；
切回其他語言會還原英文。要補翻其他寫死的介面字串，把英文原文與譯文加進這個 JSON 後重跑安裝即可。

## macOS 安裝

```sh
./install_mac.sh
```

- 會在 `/Applications/XWVM/` 產生 `xwvm-zhTW.app`（原版 `xwvm.app` 不會被修改）。
  使用 APFS 複製，幾乎不佔額外空間。
- 之後用 `xwvm-zhTW.app` 開遊戲。存檔與設定和原版共用。
- **XWVM 每次更新後要重跑一次** `install_mac.sh`。
- 預設字型：PingFang TC（蘋方-繁）Medium；找不到時依序改用黑體-繁、Arial Unicode。

## Windows 安裝（之後用）

同一個 `XwvmChineseFont.dll` 可直接用在 Windows，不需要重新編譯。

1. 安裝 Python 3。
2. 找到 XWVM 安裝資料夾裡的 `XWVM_Data`（名稱為「執行檔名稱_Data」）。
3. 執行：
   ```
   python patch_xwvm.py "C:\路徑\XWVM\XWVM_Data" XwvmChineseFont.dll
   ```
4. 預設字型：微軟正黑體（msjh.ttc）。
5. 移除：`python patch_xwvm.py "C:\路徑\XWVM\XWVM_Data" --uninstall`（第一次修改前的原始檔也會另存為 `*.orig`）。

## 自訂字型與大小（選用）

在 `XwvmChineseFont.dll` 旁放 `XwvmChineseFont.ini`（macOS 版放在本資料夾後重跑 `install_mac.sh`）：

```ini
# 指定字型檔；空白 = 自動找系統字型
FontFile=
# 也可以把 .ttf/.otf 放進 XwvmChineseFont-fonts 資料夾（例如 Noto Sans TC）
PreferredFamilies=PingFang TC;Heiti TC;Microsoft JhengHei;Noto Sans TC
PreferredStyle=Medium
# 中文字相對遊戲字型的大小倍率
Scale=1.0
```

## 中文翻譯檔放哪裡

遊戲會從檔名自動註冊語系：把翻譯好的 XLIFF 命名為 `*_zh-TW.xliff`，放進

- macOS：`/Library/Application Support/XWVM Team/XWVM/StreamingAssets/Localization/XLIFF/zh-TW/`
- Windows：XWVM 的 `StreamingAssets/Localization/XLIFF/zh-TW/`

然後在 `Settings > Audio and Language > Subtitles and Language > Language` 選 Chinese (Traditional)。
macOS 的這個資料夾屬於 root，需要用 Finder（會要求密碼）或 `sudo` 複製。
建議不要直接改 `en` 資料夾的英文原檔。

## 檢查是否生效

看 `~/Library/Logs/XWVM Team/XWVM/Player.log`（Windows：`%USERPROFILE%\AppData\LocalLow\XWVM Team\XWVM\Player.log`）：

```
[XwvmChineseFont] Using Chinese font ... [PingFang TC Medium]
[XwvmChineseFont] Added Chinese fallback to 5 TextMeshPro font(s).
[XwvmChineseFont] Session rendered N glyph(s) through the Chinese fallback: ...
```

## 重新編譯

```sh
dotnet build -c Release            # macOS，參照 /Applications/XWVM 內的遊戲 DLL
dotnet build -c Release -p:GameManaged="C:\...\XWVM_Data\Managed"   # Windows
```
