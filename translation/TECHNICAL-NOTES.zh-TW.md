# 實際盤點與匯回限制（2026-10-22）

## 已存取的範圍

- 原版：原版 X-Wing 安裝資料夾（floppy 與 Collector's CD 版），成功唯讀存取，507 檔、121,032,250 bytes（總量含未讀取內容的私人存檔類檔案）。
- XWVM 本體：`/Applications/XWVM/xwvm.app`，Info.plist 顯示 `1.0.20260923.2004`、bundle version `190414`。
- XWVM 額外資料：`/Library/Application Support/XWVM Team/XWVM/`；文字來源為 `StreamingAssets/Localization/`，HD 模組在 `Resources/Mods/`。
- 輸出只放在本次任務工作區。沒有提出或遭到檔案權限升級拒絕；沒有寫入遊戲目錄旁。未讀取存檔內容、玩家紀錄、憑證或使用者偏好檔。

原版 `classic` 內可見 DOS floppy 時期資源與 B-Wing 擴充；程式內靜態版本標記分別為 `XWING.EXE` 1.1、`BWING.EXE` 1.2。`collectors_cd/BWING.EXE` 標記 1.5，README 指明 X-Wing CD。這些是檔案內容證據，沒有啟動程式確認。指定目錄未見 1998 Remastered。

`classic/MISSION` 有 119 個 XWI 與 112 個 BRF，合計 978,059 bytes；`classic/RESOURCE` 有 112 個 LFD 與 1 個 CFT。唯讀解析幾份 LFD 的區塊表，可確認 `BRIEF.LFD`、`MISSIONS.LFD`、`CREDITS.LFD` 有 TEXT 區塊。這次未將原版二進位文字抽入翻譯檔。

`collectors_cd/game.fil` 為 89,526,528 bytes；`game.ins` 宣告 MODE1/2352 光碟軌。未掛載、解包或複製光碟內容。原版三個 FNT 只有約 0.7–1.7 KB，屬舊式小字型資源，非已驗證的中文字型介面；原版文字碼頁尚未確定，不能直接把 BRF／XWI／LFD 當 UTF-8 改寫。

## 抽取方法與最小來源

依開發者建議，以已安裝的 `XLIFF/es` 作為新語系起點。31 份 XLIFF 取英文 `<source>`、原始 `unit id` 與 notes；西班牙文 `<target>` 只留在參考快照，不當成繁中譯文。另取 4,873-byte 的 `CSV/XWVM.xwing.Species_en.csv`。32 份檔案共 1,991,873 bytes，另保留 1,066-byte 的來源 LICENSE。逐檔用途分類、大小與筆數見 `FILE-LIST.txt`，SHA-256 見 `manifest.json`。

來源目錄有 `en/de/es/it`，本次未見已安裝 `zh-TW`。英語資料夾沒有 OriginalStrings 任務分割檔，西班牙與義大利資料夾有；因此使用西班牙樣板中的英文原文，可涵蓋 Tour 1–5、四類戰機歷史任務、bonus、PPG、intro、cutscenes、credits，共 7,166 項。

已比較 en/es 共用表：除了 en 的 `SYSTEM_Misc` 重複一次，ID 集合一致；兩個獎項敘述及 Clone Pilot 的空白格式有來源文字差異。本次不合併或猜測哪一版較新，保留 es 模板的來源與出處。所有輸出候選的 `trgLang` 正規化為 `zh-TW`，原始來源快照不動。

`source_format=xml_fragment` 的 Clone Pilot 項目含真正 XML `<b>` 子元素；工具保留結構，不會直接攤平成文字。其他多數富文字是一般字串。來源的 Revive Pilot 文案本身有多餘 `</b>`，工具忠實保留並記錄，沒有自動修正上游內容。XLIFF 語言屬性與 file ID 也有上游差異；本次保留其非語系欄位，不宣稱通過完整 XLIFF XSD 或遊戲解析器驗證。

## 可用介面與中文限制

官方版本說明確認 XLIFF／CSV 語系系統。UI 文字顯示 `Settings > Audio and Language > Subtitles and Language > Language`，並有 `Export Original Game Strings`，說明可將已註冊遊戲的原文匯出到使用者資料區 `XWVM/Localization`。這次沒有啟動遊戲或按匯出，因此目前的任務文字是 XWVM 隨附樣板，不能保證與使用者目前註冊的 classic／CD 版本逐字一致。日後應由該功能產生版本相符的原文，再以穩定 ID 比對更新。

安裝目錄找到 `Unity.TextMeshPro.dll`、`Unity.Localization.dll`。沒有找到 `.cs`、`.sln`／`.csproj` 或獨立 TTF／OTF。`Assembly-CSharp.dll` 的靜態識別字可見 `RuntimeLocalizationLoader`、`DiscoverAndRegisterLocales`、`ParseXliff2`、`LoadLocalizedSpeciesCsvFileAsync`；這只是可能的原始碼協作入口，不是可承諾的外掛 API，也沒有取得核心原始碼。現有公開翻譯 repository 的線索不等於核心遊戲已開源。

開發者 10 月 13 日表示 TextMeshPro 字型需要預先處理，非拉丁字型還要額外支援；10 月 20 日仍提及未來可測試自訂字型版本。因此中文顯示、中文字元輸入、字型 fallback、字型圖集、換行禁則、字寬與 HUD 排版全部仍未驗證。現有「替換互動字幕字體」設定也不能當作載入中文 TTF 的證據。

後續最小技術合作：確認 zh-TW 語系註冊與 XLIFF 分割檔載入；取得可載入的繁中字型資產或開發者新增字型介面；確認機種 CSV 的分類詞與 SmartString 複數規則；使用少量已翻譯 UI／任務／HUD 文字做實機測試。工具只建立本機候選輸出，不會自動安裝。

## 缺漏、授權與網路研究

未納入 TIE Fighter 專屬 5 份表與 tf Species CSV、選裝飛行對話 mod、自訂任務、圖片內嵌文字、配音、以及尚未暴露到上述本機語系檔的字串。共用表內若有其他遊戲共用概念仍予保留。這不是全遊戲文字完整性保證。

只保留本機語系資料與隨附 MIT LICENSE；不推論它授權散布原版遊戲完整素材。沒有複製 EXE／DLL／LFD／FNT／光碟映像、HD 圖像聲音、存檔、log、`.git` 或原作者 PowerShell 腳本，也沒有執行那些程式。

參考的官方頁面：

- [官方 20260923 發行說明](https://www.moddb.com/mods/xwvm/news/xwvm-alpha-20260923-download-links)
- [官方 First Steps](https://www.moddb.com/mods/xwvm/news/xwvm-your-first-steps)
- [開發者 10/13：新增語系與字型仍待支援](https://www.moddb.com/mods/xwvm#9290785)
- [第三方 10/20：自述完成 zh-TW XLIFF](https://www.moddb.com/mods/xwvm#9296084)
- [開發者 10/20：仍缺 CSV](https://www.moddb.com/mods/xwvm#9296103)
- [第三方 10/21：將未翻譯 CSV 加入壓縮檔](https://www.moddb.com/mods/xwvm#9296639)

上述第三方翻譯與目前 20260923 公開版本的語系工作有關，但沒有獨立驗證其檔案內容、精確版本、品質或授權；未下載、未合併、未重新發布。可先確認貢獻者授權與來源，再依 ID 比對重用，以避免重工。上傳目的地仍待確認，這次沒有對任何外部網站上傳。
