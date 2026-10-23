# XWVM Traditional Chinese Localization (zh-TW)

[繁體中文](README.md) | **English**

Makes [XWVM](https://www.moddb.com/mods/xwvm) — the modern remake engine for *Star Wars: X-Wing* (1993) — fully display **Traditional Chinese (Taiwan)**.

> **Unofficial fan translation.** This project is not affiliated with or endorsed by Lucasfilm, Disney, LucasArts or the XWVM Team.
> Non-commercial use only; you need your own legal copies of *Star Wars: X-Wing* and XWVM.
> Content will be removed promptly at the request of the rights holders.

- Target version: XWVM `1.0.20260923.2004` (Unity 6000.3.7f1, Mono)
- Coverage: **all 8,940 strings translated** (UI, settings, concourse, HUD, mission goals, every Tour 1–5 briefing, historical/bonus missions, cutscene subtitles, credits, craft names), plus 276 strings of the key-binding screen
- Terminology follows the official/licensed Taiwanese Star Wars names (路克·天行者 Luke Skywalker, 韓·索羅 Han Solo, 達斯·維達 Darth Vader, X翼戰機 X-wing, 鈦戰機 TIE fighter, 滅星者 Star Destroyer, 死星 Death Star, 雅文 Yavin…)
- Verified in game on macOS (Apple Silicon); the Windows installer uses the same approach but has not been tested on Windows yet

---

## For players: download and run

Download the zip for your system from [**Releases**](https://github.com/IsleFan/XWVM-zh-TW/releases), extract it and double-click the installer. Nothing else needs to be installed:

| System | Download | Install |
| --- | --- | --- |
| macOS | `XWVM-zh-TW-<version>-macOS.zip` | double-click `安裝中文化.command` ("Install") |
| Windows | `XWVM-zh-TW-<version>-Windows.zip` | extract, then double-click `安裝中文化.bat` ("Install") |

Each zip contains `使用說明.txt` (instructions, in Chinese) explaining the security prompts macOS and Windows show the first time. After installing, start the game and pick **Chinese (Traditional)** under
`Settings > Audio and Language > Subtitles and Language > Language`.

- Install XWVM first and add your legal copy of X-Wing in XWVM.
- On macOS the installer creates a separate `xwvm-zhTW.app` (the original app is not modified) — start the game with it from then on. On Windows you keep using the normal XWVM.
- Run the installer again after every XWVM update. Use `移除中文化` ("Uninstall") to remove everything.
- **The Windows build is a beta**: its installer has not been verified on a real Windows machine yet. Please report problems in [Issues](https://github.com/IsleFan/XWVM-zh-TW/issues).

## Installing from source (developers)

macOS (no Python needed):

```bash
./font-plugin/install_mac.sh                          # creates /Applications/XWVM/xwvm-zhTW.app
./translation/install_language_mac.sh zh-TW-v1        # installs the language pack (asks for your Mac password)
```

- Uninstall: `./font-plugin/install_mac.sh --uninstall` and `./translation/install_language_mac.sh --uninstall zh-TW`.

Windows (PowerShell 5.1, built into Windows 10/11):

```powershell
powershell -ExecutionPolicy Bypass -File font-plugin\install_windows.ps1 -LanguagePack translation\exports\zh-TW-v1
```

- Finds XWVM automatically (or pass `-GameDir`), asks for administrator rights only when needed, backs up the original JSON files as `*.orig`; add `-Uninstall` to remove.
- The default font is Microsoft JhengHei (`msjh.ttc`).

Build the release zips: `python3 release/build_release.py v0.9.0-beta` (output in `release/dist/`).

---

## What was done and how

### 1. The problem: Chinese shows up as boxes

XWVM reads `StreamingAssets/Localization/XLIFF/<locale>/*.xliff` and registers a new language automatically when the files are named `*_zh-TW.xliff`, so **translations do load**. But the TextMeshPro fonts used by the UI (Eurostile, News Gothic, Franklin Gothic…) only contain Latin glyphs, so Chinese characters render as boxes — and the game offers no way to add fonts.

### 2. The fix: the XwvmChineseFont plugin (`font-plugin/`)

A C# plugin of about 450 lines that, at game start:

1. Builds a font chain for the current game locale (zh-TW: PingFang TC → Heiti TC on macOS, Microsoft JhengHei on Windows), followed by coverage fonts for Japanese, Korean, etc. (Hiragino, Apple SD Gothic Neo, Arial Unicode). Faces inside `.ttc` collections are matched by family name, so the Simplified Chinese or Japanese faces are never picked by mistake.
2. Creates **dynamic SDF fonts** with TextMeshPro's `TMP_FontAsset.CreateFontAsset` (glyphs are rendered on first use; no pre-built font atlas needed).
3. Appends them in order to the global `TMP_Settings` fallback list and to each loaded TMP font's `fallbackFontAssetTable`; this is repeated on every scene load, and the order is rebuilt when the player switches language (e.g. Hiragino goes first for Japanese so Han characters use Japanese glyph forms).

**How it is loaded:** BepInEx 5.4.23.5 was tried first, but its doorstop does not start on this Unity 6 build (tested with arm64 and Rosetta). The plugin uses Unity's own mechanism instead:

- the DLL is placed in the game's `Managed/` folder and listed in `ScriptingAssemblies.json`;
- an entry in `RuntimeInitializeOnLoads.json` makes Unity call `FallbackFontLoader.Init` before the first scene loads.

On macOS XWVM is installed in a root-owned folder, so `install_mac.sh` makes an APFS clone `xwvm-zhTW.app` (uses almost no disk space), patches the copy and re-applies an ad-hoc signature; **the original app is never touched**. Saves and settings are shared. The registration is done with macOS's built-in JavaScript (`register_plugin.js`), so no Python is needed; on Windows `install_windows.ps1` does the same with the built-in PowerShell.

**Key-binding screen:** this screen is the ControlMapper of the third-party input library Rewired. Its text is baked into the game data and does not go through XLIFF (it stays English in the Spanish/Italian/German versions too). While a language with a table is selected, the plugin's `UiTextLocalizer` replaces the ControlMapper's LanguageData strings and the on-screen TMP texts using `XwvmChineseFont-<locale>.json` (English → translation; 276 entries for zh-TW), and restores English when the language changes. Keyboard key names (ESC, Ctrl + F1) intentionally stay in English.

**Verification:** the plugin writes the fonts it found, the font chain per locale, and — when the game quits — the glyphs actually rendered through each fallback font (e.g. `…開始遊戲`) to `Player.log`. All 1,774 characters used by the translation were checked with CoreText to exist in PingFang TC.

### 3. Translation workflow (`translation/`)

1. **Extraction:** the 31 XLIFF files and the craft CSV shipped with XWVM are converted to editable JSON (`translate/`), keeping the stable IDs, English source, context and developer notes.
2. **Authoritative glossary** (`translation/glossary/glossary_zh-TW.csv`, 296 entries): checked against Disney+ Taiwan, LEGO Taiwan, EA Taiwan, Taiwanese media and the Chinese Wookieepedia, with each entry graded by source — official 28, licensed publication 24, established community usage 33, proposed for this game 211 (game-specific names with no existing Taiwanese translation). Taiwanese and Mainland Chinese usage are kept apart (滅星者 vs 歼星舰, 武技族 vs 伍基人, 雅文, 飛彈, 雷射, 砲).
3. **Style guide** (`translation/glossary/STYLE_GUIDE.zh-TW.md`): punctuation, tone, HUD length limits, the "號" suffix for ship names, Greek-letter callsigns and type codes (CRV, X-W, T/F) kept in English, 反抗軍/叛軍 depending on the speaker's side, and more.
4. **Batch translation:** repeated short mission labels (callsigns, ship names, cargo) were deduplicated and translated once (5,985 occurrences → 1,748 strings); the resulting name table was then used for the long briefings so HUD and briefing names match. 10 batches in total; the 477 game-specific names coined along the way are recorded in `glossary/game_terms_coined.tsv`.
5. **Validation:** `tools/localization_tool.py validate --complete` checks every translation's SmartString variables, `choose(...)` options, branch counts, rich-text tags, `[[ ]]` / `(( ))` / `(* *)` markers and line breaks, plus a Simplified-character check. Result: 0 errors, 0 untranslated.
6. **Export:** `build` produces the game's native format in `exports/zh-TW-v1/` (31 XLIFF files + the craft CSV).

**An important technical detail:** Unity Localization's SmartFormat plural rule for Chinese (`zh`) always picks the **first** branch, so `{n:plural:1 game|{} games}` must become `{n:plural:{} 款遊戲|{} 款遊戲}` — otherwise 3 games would be shown as "1". The validator accounts for this (extra `{}` inside plural branches are allowed) and no longer misreads conditional text that contains a colon.

---

## Editing the translation

```bash
cd translation
# edit the target_zh_TW fields in translate/**/*.json
python3 tools/localization_tool.py validate            # check the format
python3 tools/localization_tool.py build --name zh-TW-v2
./install_language_mac.sh zh-TW-v2
```

Strings that are not in XLIFF (key-binding screen etc.): edit `font-plugin/XwvmChineseFont-zh-TW.json` and run `font-plugin/install_mac.sh` again.

## Adding other languages (Japanese, Korean…)

The plugin and the tools take the locale as a parameter, so adding a language needs no code changes:

```bash
# 1. create a workspace for the language (extracts the English sources from your XWVM install; the field is target_ja)
python3 translation/tools/localization_tool.py extract --locale ja --out translation-ja

# 2. translate target_ja in translation-ja/translate/**/*.json, then validate and export
python3 translation/tools/localization_tool.py validate --root translation-ja
python3 translation/tools/localization_tool.py build --root translation-ja --name ja-v1

# 3. install (the locale is detected from the pack)
./translation/install_language_mac.sh translation-ja/exports/ja-v1
```

- Locale codes must be `xx` or `xx-YY` (the only file names XWVM recognises).
- **Plural rules are checked per language:** Chinese, Japanese, Korean, Vietnamese, Thai and others have a single plural form, so all branches should be the same general form (a warning is shown otherwise); Russian, Ukrainian, Czech and others need 3 branches, Polish and Slovenian 4, Arabic 6 (following Unity SmartFormat's rules — a wrong branch count makes the game throw an error).
- Fonts: the plugin has built-in chains for zh-TW / zh-HK / zh-CN / ja / ko and uses the default chain for other languages; override with `Fonts.<locale>` in `XwvmChineseFont.ini`.
- Key-binding screen: copy `font-plugin/XwvmChineseFont-zh-TW.json` to `XwvmChineseFont-ja.json`, translate it and run `font-plugin/install_mac.sh` again.
- The batch checker also takes a locale: `python3 translation/tools/pipeline/check_batch.py <batch> <out> ja`.
- Not possible: right-to-left scripts (Arabic, Hebrew) and scripts that need glyph shaping (Thai, Hindi) — TextMeshPro does not support that layout.

## Rebuilding the plugin

Requires the .NET SDK (8.0 or later); it compiles against the game DLLs of your local XWVM:

```bash
cd font-plugin
dotnet build -c Release && cp bin/Release/XwvmChineseFont.dll .
# Windows: dotnet build -c Release -p:GameManaged="C:\...\XWVM_Data\Managed"
```

Settings (optional): an `XwvmChineseFont.ini` next to the DLL can set a font file, per-locale font chains (`Fonts.<locale>`), the weight and a size multiplier; or put `.ttf/.otf` files in an `XwvmChineseFont-fonts/` folder. See [font-plugin/README.zh-TW.md](font-plugin/README.zh-TW.md) (Chinese).

---

## Repository layout

| Path | Contents |
| --- | --- |
| `font-plugin/` | Font + UI text plugin source, prebuilt DLL, key-binding table, macOS / Windows installer scripts |
| `release/` | Double-click install / uninstall scripts and instructions for players, and the packaging script |
| `translation/translate/` | Editable translation JSON (the only place to edit) |
| `translation/exports/zh-TW-v1/` | Ready-to-install language pack |
| `translation/glossary/` | Taiwanese Star Wars glossary, coined game names, style guide |
| `translation/tools/` | Extraction / validation / export tool and tests; `pipeline/` holds the batch split, check and merge scripts |
| `translation/reference/` | Snapshot of XWVM's original XLIFF / CSV (do not edit) |
| `translation/reports/` | Inventory and validation reports |
| `DEVLOG.md` | Development log (Chinese) |

## Known limitations

- The Windows installer has not been tested on real Windows; it searches for XWVM's language folder automatically.
- The Chinese layout has not been checked screen by screen yet: line breaks in mission description boxes, text length in the HUD target box and CMD, and mission goal sentences assembled from fragments.
- The sources are the template texts shipped with XWVM, not the output of the in-game "Export Original Game Strings", so there may be small differences from the original game version you registered.
- Not covered: TIE Fighter-specific text, custom missions, text inside images, voice.
- Names marked "proposed for this game" (e.g. 韋奇·安提利斯 Wedge Antilles, 畢格斯·達克萊特 Biggs Darklighter, 護衛艦 corvette / 巡防艦 frigate) are this project's choices, not official Taiwanese names.

## Copyright and licensing

- `font-plugin/`, `release/` and `translation/tools/` are original code of this project.
- The XWVM localization sources (`translation/reference/` and the English source text of the translations) come from the XWVM Team under the MIT license; see `translation/LICENSE-XWVM-localization.txt`.
- The original game text (mission briefings, cutscenes, etc.) and its translation involve copyrights of Lucasfilm / LucasArts; *Star Wars* and related names and marks are owned by Lucasfilm Ltd. This project is provided as a non-commercial fan translation and claims no rights to that content; rights holders can open an issue and it will be taken down promptly.
- This project may not be used commercially or sold.
- No game executables, game DLLs, decompiled code or font files are included (the plugin uses fonts already installed on the system).
