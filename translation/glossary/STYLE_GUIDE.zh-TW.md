# XWVM《星際大戰：X 翼戰機》繁體中文（台灣）翻譯規範

對象：1993 年 LucasArts 飛行模擬遊戲 *Star Wars: X-Wing*（XWVM 重製引擎）。玩家是台灣的星戰迷。

## 1. 術語
- **一律以 `glossary_zh-TW.csv` 為準**（english → zh_TW）。表中有的詞不得自創其他譯法；複數、所有格、縮寫也套用同一譯名（TIE Fighters → 鈦戰機）。
- 表中沒有的專有名詞：人名、星球用音譯並用「·」分隔姓名；遊戲獨有名詞給自然、一致的譯法，並把你新增的譯法列在回報裡。
- 使用台灣用語：軟體→「設定、檔案、儲存、載入、螢幕、滑鼠、搖桿、鍵盤、預設值、解析度」，不用「设置、文件、保存、加载、屏幕、鼠标」。不可出現簡體字。

## 2. 語氣
- 任務簡報、劇情：軍事簡報口吻，簡潔有力，像反抗軍指揮部對飛行員下令。
- 介面：短、直接。按鈕用動詞（儲存、取消、套用）。
- 全大寫英文（如 `DESTROY ALL TIE FIGHTERS`）照一般中文翻，不需要特別處理大小寫。

## 3. 標點與格式
- 中文句子用全形標點：，。：；！？「」（）……。引號用「」，書名用《》。
- 數字、變數、英文代號旁不用加空格以外的符號；中英文之間可留半形空格（例如「X 翼戰機」依術語表為準）。
- 保留原文的換行 `\n` 數量與段落結構；保留行首/行尾的空白或 Tab。
- 標籤後面接數值的（`Score:`、`PASSED:`）用全形冒號「：」。

## 4. 不可改動的標記（驗證器會擋）
- 大括號變數 `{name}`、`{species.ONE}`、`{minutes}` 原樣保留，可移動位置以符合中文語序。
- `choose(...)` 括號內的英文選項值**完全不動**；只翻譯冒號後面以 `|` 分隔的顯示文字，**分支數量不可變**。
  例：`{skill:choose(Rookie|Officer|Veteran|Ace|TopAce|Jedi):Rookie|Officer|Veteran|Ace|Top Ace|Jedi}` →
  `{skill:choose(Rookie|Officer|Veteran|Ace|TopAce|Jedi):新手|軍官|老手|王牌|頂尖王牌|絕地}`
- 條件式 `{x:A|B}`：翻譯 A、B，分支數不變。
- **複數 `{n:plural:單數|複數}`：遊戲的中文複數規則永遠只取第一個分支**，所以每個分支都要寫成同一個「通用形」，分支數量仍保持不變：
  - 原文 `{gameCount:plural:1 game|{} games}` → `{gameCount:plural:{} 款遊戲|{} 款遊戲}`。
    錯誤示範：`{gameCount:plural:1 款遊戲|{} 款遊戲}`（有 3 款時會顯示「1 款遊戲」）。
    `{}` 代表該數值；驗證器允許分支內的 `{}` 數量與原文不同。
  - 原文 `{count:plural:Laser|Lasers}` → `{count:plural:雷射砲|雷射砲}`。
- 富文字標籤 `<b>…</b>`、`<color=…>…</color>`、`<i>` 等：數量與種類相同，包住對應的中文。
- 強調標記 `[[…]]`、`((…))`、`(*…*)`：數量相同，包住對應的中文詞，例如 `[[Red Squadron]]` → `[[紅色中隊]]`。
- `\{`、`\}` 等跳脫字元原樣保留。

## 5. 版面長度
- HUD、目標框、貨物（Cargo）、飛行群組代號（Designation）、按鈕等短字串會顯示在窄欄位，**中文盡量 ≤ 原文字元數的一半到同長**。
- 飛行群組代號（Designation）：依術語表規則；表中沒規定的希臘字母代號（ALPHA、BETA…）保留英文原文。

## 6. 輸出
- 只輸出 JSON 物件：`{"<key>": "<中文>", ...}`，每個輸入項目一個 key，不可遺漏、不可新增。
- 用 `check_batch.py` 自我檢查，直到 0 錯誤、0 遺漏。

## 7. 星戰專用規則（依術語研究）
1. 人名用「·」：路克·天行者。頭銜放名字後：阿克巴上將、多唐納將軍、塔金總督、法蘭德中尉。
2. 具名艦船：英文一般詞意譯＋「號」（Independence → 獨立號）；人名/專名音譯＋「號」（Maria → 瑪莉亞號）。原文有艦種才加艦種：Frigate Priam → 巡防艦普萊姆號。
3. 名稱衝突：Intrepid = 勇猛號（「無畏」保留給 Dreadnaught 級）；Interdictor = 禁制者級；穿梭機 Falcon = 獵鷹號（不是千年鷹號）。
4. 羅馬數字行星 → 「X號星」（Kalla VII → 卡拉七號星）；Sector 星區、System 星系、Cluster 星團。
5. 中隊呼號：Red Squadron 紅色中隊、Red One 紅色一號、Red Leader 紅色隊長；無線電急促語句可用「紅一」。
6. 希臘字母飛行群組（ALPHA、BETA、Mu、Rho…）保留英文。Designation 欄位與 HUD 標籤維持原大寫；句子中寫「Alpha 編隊」、「Mu 砲艇」。
7. **型別縮寫保留英文**：CRV、FRG、FRT、TRN、SHU、CON、GUN、STD、CRS、X-W、Y-W、A-W、B-W、T/F、T/I、T/B、T/A 等在 HUD、CMD、短標籤（例如 `X-W Red`、`T/F Alpha`）一律保留英文原樣；在簡報/敘述句中才展開成中文（CRVs → 護衛艦）。艦種表 Species 的 **ABBR 欄位一律保留原文**。
8. 軍階 vs 職稱：Captain = 上尉（飛行員）／艦長（艦船指揮官）；Commander = 中校（軍階）／指揮官（職務）；Admiral 上將、General 將軍。生涯：飛行學員 → 飛行准尉 → 中尉 → 上尉 → 中校 → 將軍。
9. 台灣用語：飛彈（非導彈）、雷射（非激光）、砲（非炮）、貨櫃（非集裝箱）、穿梭機、護盾。
10. 立場：敘述與反抗軍方用「反抗軍」；只有帝國方台詞可用「叛軍」。「帝國」作形容詞，「帝國軍」指帝國部隊或人員。
11. Emperor = 皇帝（不是帝皇）；對白中的 Lord Vader = 維達大人。
12. Tour of Duty = 服役期（第一～第五服役期）。任務動詞統一：登艦（boarding）、癱瘓（disable）、護航（escort）、偵察／識別（inspect/identify）、摧毀（destroy）、俘獲（capture）、保護（protect）。
13. 貨物（Cargo）欄位多為全大寫英文短語（MILITARY EQPT.、FOODSTUFFS）：翻成簡短中文（軍用裝備、糧食），縮寫自然展開。
