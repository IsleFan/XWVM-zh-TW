using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TextCore;
using UnityEngine.TextCore.LowLevel;

namespace XwvmChineseFont
{
    /// <summary>
    /// Adds dynamic CJK TextMeshPro fonts as fallbacks to every TMP font in XWVM, so text from
    /// non-Latin XLIFF files (zh-TW, zh-CN, ja, ko, ...) renders instead of boxes.
    ///
    /// Each locale has a font chain ("Fonts.&lt;locale&gt;" + "Fonts.coverage"): the first font decides
    /// the glyph style (e.g. Japanese vs. Chinese Han forms), later fonts cover other scripts.
    /// The chain is re-ordered whenever the game's selected locale changes (see <see cref="LocaleWatcher"/>).
    ///
    /// Unity calls <see cref="Init"/> because install_mac.sh (register_plugin.js) / install_windows.ps1 register it in
    /// RuntimeInitializeOnLoads.json and the DLL in ScriptingAssemblies.json.
    /// The DLL is platform independent: the same build works on macOS and Windows.
    ///
    /// Optional settings are read from XwvmChineseFont.ini next to this DLL, and any
    /// .ttf/.otf/.ttc placed in the XwvmChineseFont-fonts folder next to it is preferred
    /// over system fonts.
    /// </summary>
    public static class FallbackFontLoader
    {
        internal const string LogPrefix = "[XwvmChineseFont] ";
        private static readonly string[] FontExtensions = { ".ttf", ".otf", ".ttc", ".otc" };

        private static readonly Dictionary<string, string> Settings = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
        {
            ["FontFile"] = "",
            ["FaceIndex"] = "0",
            ["PreferredStyle"] = "Medium",
            ["SamplingPointSize"] = "64",
            ["Padding"] = "6",
            ["AtlasSize"] = "2048",
            ["Scale"] = "1.0",
            // Font families tried for a locale, in order. Lookup: exact locale, then language, then "default".
            ["Fonts.zh-TW"] = "PingFang TC;Heiti TC;Microsoft JhengHei;Noto Sans CJK TC;Noto Sans TC;PMingLiU",
            ["Fonts.zh-HK"] = "PingFang HK;PingFang TC;Microsoft JhengHei;Noto Sans CJK HK;Noto Sans CJK TC",
            ["Fonts.zh"] = "PingFang SC;Heiti SC;Microsoft YaHei;Noto Sans CJK SC;Noto Sans SC",
            ["Fonts.ja"] = "Hiragino Sans;Hiragino Kaku Gothic ProN;Yu Gothic;Meiryo;Noto Sans CJK JP;Noto Sans JP",
            ["Fonts.ko"] = "Apple SD Gothic Neo;Malgun Gothic;Noto Sans CJK KR;Noto Sans KR",
            ["Fonts.default"] = "PingFang TC;Microsoft JhengHei;Noto Sans CJK TC",
            // Appended to every chain so other scripts (Hangul, kana, Han) still render.
            ["Fonts.coverage"] = "Apple SD Gothic Neo;Malgun Gothic;Hiragino Sans;Yu Gothic;PingFang TC;Microsoft JhengHei;Noto Sans CJK KR;Arial Unicode MS",
        };

        private class FaceRef
        {
            public string Path;
            public int Face;
            public string Family;
            public string Style;
            public bool UserSupplied;
            public string Key => Path + "|" + Face;
            public override string ToString() => Family + " " + Style;
        }

        private static readonly List<FaceRef> Faces = new List<FaceRef>();
        private static readonly Dictionary<string, TMP_FontAsset> Assets = new Dictionary<string, TMP_FontAsset>();
        private static readonly HashSet<int> PatchedFonts = new HashSet<int>();
        private static List<TMP_FontAsset> _chain = new List<TMP_FontAsset>();
        private static string _chainLocale;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        public static void Init()
        {
            try
            {
                string dir = Path.GetDirectoryName(typeof(FallbackFontLoader).Assembly.Location);
                LoadSettings(Path.Combine(dir, "XwvmChineseFont.ini"));

                IndexFonts(Path.Combine(dir, "XwvmChineseFont-fonts"));
                if (Faces.Count == 0)
                {
                    Debug.LogError(LogPrefix + "No usable CJK font found. Put a .ttf/.otf into XwvmChineseFont-fonts or set FontFile in XwvmChineseFont.ini.");
                    return;
                }

                // The game's locale is not known yet; use the default chain until LocaleWatcher reports it.
                ApplyLocale("");
                SceneManager.sceneLoaded += (_, __) => PatchFonts(onlyNew: true);
                UiTextLocalizer.Init(dir);
                LocaleWatcher.Create();
                Application.quitting += LogRenderedGlyphs;
            }
            catch (Exception e)
            {
                Debug.LogError(LogPrefix + "Initialisation failed: " + e);
            }
        }

        private static void LoadSettings(string path)
        {
            if (!File.Exists(path))
            {
                return;
            }
            foreach (string raw in File.ReadAllLines(path))
            {
                string line = raw.Trim();
                int eq = line.IndexOf('=');
                if (line.Length == 0 || line[0] == '#' || line[0] == ';' || line[0] == '[' || eq <= 0)
                {
                    continue;
                }
                Settings[line.Substring(0, eq).Trim()] = line.Substring(eq + 1).Trim();
            }
            Debug.Log(LogPrefix + "Loaded settings from " + path);
        }

        private static int IntSetting(string key) => int.Parse(Settings[key]);

        private static List<string> SplitList(string value) =>
            value.Split(';').Select(f => f.Trim()).Where(f => f.Length > 0).ToList();

        /// <summary>Records every face of the candidate font files; collections (.ttc) hold several families.</summary>
        private static void IndexFonts(string fontsDir)
        {
            var userFiles = new List<string>();
            string fontFile = Settings["FontFile"];
            if (fontFile.Length > 0 && File.Exists(fontFile))
            {
                userFiles.Add(fontFile);
            }
            if (Directory.Exists(fontsDir))
            {
                userFiles.AddRange(Directory.GetFiles(fontsDir)
                    .Where(f => FontExtensions.Contains(Path.GetExtension(f).ToLowerInvariant()))
                    .OrderBy(f => f, StringComparer.OrdinalIgnoreCase));
            }

            foreach (string file in userFiles)
            {
                IndexFile(file, userSupplied: true);
            }
            foreach (string file in SystemFontFiles().Where(File.Exists).Distinct())
            {
                IndexFile(file, userSupplied: false);
            }
            Debug.Log(LogPrefix + "Found font families: " + string.Join(", ", Faces.Select(f => f.Family).Distinct()));
        }

        private static void IndexFile(string path, bool userSupplied)
        {
            for (int face = 0; face < 64; face++)
            {
                if (FontEngine.LoadFontFace(path, 32f, face) != FontEngineError.Success)
                {
                    break;
                }
                FaceInfo info = FontEngine.GetFaceInfo();
                Faces.Add(new FaceRef { Path = path, Face = face, Family = info.familyName, Style = info.styleName, UserSupplied = userSupplied });
            }
        }

        private static IEnumerable<string> SystemFontFiles()
        {
            switch (Application.platform)
            {
                case RuntimePlatform.OSXPlayer:
                    // PingFang ships as a downloadable system asset on recent macOS versions.
                    const string assets = "/System/Library/AssetsV2";
                    if (Directory.Exists(assets))
                    {
                        foreach (string dir in Directory.GetDirectories(assets, "com_apple_MobileAsset_Font*"))
                        {
                            foreach (string file in Directory.GetFiles(dir, "PingFang.ttc", SearchOption.AllDirectories))
                            {
                                yield return file;
                            }
                        }
                    }
                    yield return "/System/Library/Fonts/PingFang.ttc";
                    yield return "/System/Library/Fonts/STHeiti Medium.ttc";
                    yield return "/System/Library/Fonts/STHeiti Light.ttc";
                    // Hiragino weights: W5 first so it wins when no "Medium"/"Regular" style exists.
                    foreach (string weight in new[] { "W5", "W4", "W3", "W6" })
                    {
                        yield return "/System/Library/Fonts/ヒラギノ角ゴシック " + weight + ".ttc";
                    }
                    yield return "/System/Library/Fonts/AppleSDGothicNeo.ttc";
                    yield return "/Library/Fonts/Arial Unicode.ttf";
                    break;

                case RuntimePlatform.WindowsPlayer:
                    string winFonts = Environment.GetFolderPath(Environment.SpecialFolder.Fonts);
                    foreach (string name in new[] { "msjh.ttc", "msjhbd.ttc", "msyh.ttc", "YuGothM.ttc", "YuGothR.ttc", "meiryo.ttc",
                                                    "malgun.ttf", "NotoSansTC-VF.ttf", "mingliu.ttc", "mingliub.ttc" })
                    {
                        yield return Path.Combine(winFonts, name);
                    }
                    break;

                case RuntimePlatform.LinuxPlayer:
                    yield return "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc";
                    yield return "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc";
                    break;
            }
        }

        /// <summary>Font families for a locale code such as "zh-tw": exact entry, then language, then default; plus coverage.</summary>
        private static List<string> ChainFamilies(string locale)
        {
            string language = locale.Split('-')[0];
            string key = Settings.ContainsKey("Fonts." + locale) && locale.Length > 0 ? "Fonts." + locale
                : Settings.ContainsKey("Fonts." + language) && language.Length > 0 ? "Fonts." + language
                : "Fonts.default";
            return SplitList(Settings[key]).Concat(SplitList(Settings["Fonts.coverage"]))
                .Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        }

        private static int StyleRank(FaceRef face)
        {
            return string.Equals(face.Style, Settings["PreferredStyle"], StringComparison.OrdinalIgnoreCase) ? 0
                : string.Equals(face.Style, "Regular", StringComparison.OrdinalIgnoreCase) ? 1
                : 2;
        }

        private static FaceRef BestFace(IEnumerable<FaceRef> candidates, string family)
        {
            // OrderBy is stable, so equal style ranks keep discovery order.
            return candidates.Where(f => string.Equals(f.Family, family, StringComparison.OrdinalIgnoreCase))
                .OrderBy(StyleRank).FirstOrDefault();
        }

        private static List<FaceRef> ResolveChain(string locale)
        {
            List<string> families = ChainFamilies(locale);
            var chosen = new List<FaceRef>();

            // User-supplied fonts always come first: the face of each file matching the chain, else FaceIndex.
            foreach (var file in Faces.Where(f => f.UserSupplied).GroupBy(f => f.Path))
            {
                FaceRef face = families.Select(fam => BestFace(file, fam)).FirstOrDefault(f => f != null)
                    ?? file.FirstOrDefault(f => f.Face == IntSetting("FaceIndex"));
                if (face != null)
                {
                    chosen.Add(face);
                }
            }
            foreach (string family in families)
            {
                FaceRef face = BestFace(Faces.Where(f => !f.UserSupplied), family);
                if (face != null && chosen.All(c => c.Key != face.Key))
                {
                    chosen.Add(face);
                }
            }
            return chosen;
        }

        internal static bool IsFallbackFont(TMP_FontAsset font) => font != null && Assets.ContainsValue(font);

        private static TMP_FontAsset GetOrCreateAsset(FaceRef face)
        {
            if (Assets.TryGetValue(face.Key, out TMP_FontAsset existing))
            {
                return existing;
            }
            int atlasSize = IntSetting("AtlasSize");
            // The atlas texture stays 1x1 until the first glyph is needed, so unused fonts cost almost nothing.
            TMP_FontAsset font = TMP_FontAsset.CreateFontAsset(face.Path, face.Face, IntSetting("SamplingPointSize"),
                IntSetting("Padding"), GlyphRenderMode.SDFAA, atlasSize, atlasSize);
            if (font == null)
            {
                Debug.LogWarning(LogPrefix + "TextMeshPro could not create a font asset from " + face.Path);
                return null;
            }
            font.name = "XWVM Fallback (" + face + ")";
            FaceInfo faceInfo = font.faceInfo;
            faceInfo.scale = float.Parse(Settings["Scale"], System.Globalization.CultureInfo.InvariantCulture);
            font.faceInfo = faceInfo;
            font.hideFlags = HideFlags.DontUnloadUnusedAsset;
            Assets[face.Key] = font;
            return font;
        }

        /// <summary>Builds the fallback chain for <paramref name="locale"/> ("" = not known yet) and applies it to all TMP fonts.</summary>
        internal static void ApplyLocale(string locale)
        {
            locale = (locale ?? "").ToLowerInvariant();
            if (locale == _chainLocale)
            {
                return;
            }
            List<FaceRef> faces = ResolveChain(locale);
            List<TMP_FontAsset> chain = faces.Select(GetOrCreateAsset).Where(a => a != null).ToList();
            _chainLocale = locale;
            if (chain.SequenceEqual(_chain))
            {
                return;
            }
            _chain = chain;
            Debug.Log(LogPrefix + "Font chain for locale '" + (locale.Length > 0 ? locale : "default") + "': "
                + string.Join(" > ", faces.Where(f => Assets.ContainsKey(f.Key))));
            PatchFonts(onlyNew: false);
        }

        /// <summary>
        /// Puts the current chain at the end of the global TMP fallback list and of each TMP font's own
        /// fallback list (replacing any earlier chain), then asks text using those fonts to rebuild.
        /// </summary>
        private static void PatchFonts(bool onlyNew)
        {
            var ours = new HashSet<TMP_FontAsset>(Assets.Values);
            if (!onlyNew)
            {
                ReplaceChain(GlobalFallbacks(), ours);
            }

            int patched = 0;
            foreach (TMP_FontAsset font in Resources.FindObjectsOfTypeAll<TMP_FontAsset>())
            {
                if (ours.Contains(font) || (!PatchedFonts.Add(font.GetInstanceID()) && onlyNew))
                {
                    continue;
                }
                if (font.fallbackFontAssetTable == null)
                {
                    font.fallbackFontAssetTable = new List<TMP_FontAsset>();
                }
                ReplaceChain(font.fallbackFontAssetTable, ours);
                TMPro_EventManager.ON_FONT_PROPERTY_CHANGED(true, font);
                patched++;
            }
            if (patched > 0)
            {
                Debug.Log(LogPrefix + "Applied " + _chain.Count + " fallback font(s) to " + patched + " TextMeshPro font(s).");
            }
        }

        private static void ReplaceChain(List<TMP_FontAsset> fallbacks, HashSet<TMP_FontAsset> ours)
        {
            if (fallbacks == null)
            {
                return;
            }
            fallbacks.RemoveAll(ours.Contains);
            fallbacks.AddRange(_chain);
        }

        private static List<TMP_FontAsset> GlobalFallbacks()
        {
            try
            {
                if (TMP_Settings.instance == null)
                {
                    Debug.LogWarning(LogPrefix + "TMP Settings asset not found; relying on per-font fallbacks only.");
                    return null;
                }
                if (TMP_Settings.fallbackFontAssets == null)
                {
                    TMP_Settings.fallbackFontAssets = new List<TMP_FontAsset>();
                }
                return TMP_Settings.fallbackFontAssets;
            }
            catch (Exception e)
            {
                Debug.LogWarning(LogPrefix + "Could not access global TMP fallbacks: " + e.Message);
                return null;
            }
        }

        private static void LogRenderedGlyphs()
        {
            foreach (TMP_FontAsset font in Assets.Values.Where(a => a.characterTable.Count > 0))
            {
                Debug.Log(LogPrefix + "Session rendered " + font.characterTable.Count + " glyph(s) through " + font.name + ": "
                    + new string(font.characterTable.Take(80).Select(c => (char)c.unicode).ToArray()));
            }
        }
    }
}
