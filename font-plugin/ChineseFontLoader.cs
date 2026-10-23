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
    /// Adds a dynamic CJK TextMeshPro font as a fallback to every TMP font in XWVM,
    /// so Traditional Chinese text from the zh-TW XLIFF files renders instead of boxes.
    ///
    /// Unity calls <see cref="Init"/> because patch_xwvm.py registers it in
    /// RuntimeInitializeOnLoads.json and the DLL in ScriptingAssemblies.json.
    /// The DLL is platform independent: the same build works on macOS and Windows.
    ///
    /// Optional settings are read from XwvmChineseFont.ini next to this DLL, and any
    /// .ttf/.otf/.ttc placed in the XwvmChineseFont-fonts folder next to it is preferred
    /// over system fonts.
    /// </summary>
    public static class ChineseFontLoader
    {
        private const string LogPrefix = "[XwvmChineseFont] ";
        private static readonly string[] FontExtensions = { ".ttf", ".otf", ".ttc", ".otc" };

        private static readonly Dictionary<string, string> Settings = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
        {
            ["FontFile"] = "",
            ["FaceIndex"] = "0",
            ["PreferredFamilies"] = "PingFang TC;Heiti TC;Microsoft JhengHei;Noto Sans TC;Noto Sans CJK TC;Source Han Sans TC;PMingLiU;Arial Unicode MS",
            ["PreferredStyle"] = "Medium",
            ["SamplingPointSize"] = "64",
            ["Padding"] = "6",
            ["AtlasSize"] = "2048",
            ["Scale"] = "1.0",
        };

        private static TMP_FontAsset _fallback;
        private static readonly HashSet<int> PatchedFonts = new HashSet<int>();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        public static void Init()
        {
            try
            {
                string dir = Path.GetDirectoryName(typeof(ChineseFontLoader).Assembly.Location);
                LoadSettings(Path.Combine(dir, "XwvmChineseFont.ini"));

                _fallback = CreateFallbackFont(Path.Combine(dir, "XwvmChineseFont-fonts"));
                if (_fallback == null)
                {
                    Debug.LogError(LogPrefix + "No usable Chinese font found. Put a .ttf/.otf into XwvmChineseFont-fonts or set FontFile in XwvmChineseFont.ini.");
                    return;
                }

                AddGlobalFallback();
                PatchLoadedFonts();
                UiTextLocalizer.Create(dir);
                SceneManager.sceneLoaded += (_, __) => PatchLoadedFonts();
                Application.quitting += () => Debug.Log(LogPrefix + "Session rendered " + _fallback.characterTable.Count
                    + " glyph(s) through the Chinese fallback: "
                    + new string(_fallback.characterTable.Take(80).Select(c => (char)c.unicode).ToArray()));
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

        private static TMP_FontAsset CreateFallbackFont(string fontsDir)
        {
            List<string> families = Settings["PreferredFamilies"]
                .Split(';').Select(f => f.Trim()).Where(f => f.Length > 0).ToList();

            foreach (var (path, userSupplied) in CandidateFontFiles(fontsDir))
            {
                int face = FindBestFace(path, families, out string description);
                if (face < 0 && userSupplied)
                {
                    face = IntSetting("FaceIndex");
                    description = "face " + face;
                }
                if (face < 0)
                {
                    continue;
                }

                int atlasSize = IntSetting("AtlasSize");
                TMP_FontAsset font = TMP_FontAsset.CreateFontAsset(path, face, IntSetting("SamplingPointSize"),
                    IntSetting("Padding"), GlyphRenderMode.SDFAA, atlasSize, atlasSize);
                if (font == null)
                {
                    Debug.LogWarning(LogPrefix + "TextMeshPro could not create a font asset from " + path);
                    continue;
                }

                font.name = "XWVM zh-TW Fallback (" + description + ")";
                FaceInfo faceInfo = font.faceInfo;
                faceInfo.scale = float.Parse(Settings["Scale"], System.Globalization.CultureInfo.InvariantCulture);
                font.faceInfo = faceInfo;
                font.hideFlags = HideFlags.DontUnloadUnusedAsset;
                Debug.Log(LogPrefix + "Using Chinese font " + path + " [" + description + "]");
                return font;
            }
            return null;
        }

        private static IEnumerable<(string path, bool userSupplied)> CandidateFontFiles(string fontsDir)
        {
            string fontFile = Settings["FontFile"];
            if (fontFile.Length > 0 && File.Exists(fontFile))
            {
                yield return (fontFile, true);
            }

            if (Directory.Exists(fontsDir))
            {
                foreach (string file in Directory.GetFiles(fontsDir).OrderBy(f => f, StringComparer.OrdinalIgnoreCase))
                {
                    if (FontExtensions.Contains(Path.GetExtension(file).ToLowerInvariant()))
                    {
                        yield return (file, true);
                    }
                }
            }

            foreach (string file in SystemFontFiles().Where(File.Exists))
            {
                yield return (file, false);
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
                    yield return "/Library/Fonts/Arial Unicode.ttf";
                    break;

                case RuntimePlatform.WindowsPlayer:
                    string winFonts = Environment.GetFolderPath(Environment.SpecialFolder.Fonts);
                    foreach (string name in new[] { "msjh.ttc", "msjhbd.ttc", "NotoSansTC-VF.ttf", "mingliu.ttc", "mingliub.ttc" })
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

        /// <summary>
        /// Returns the face index in <paramref name="path"/> whose family best matches the preference list,
        /// or -1 when no face matches. Collections (.ttc) hold SC/TC/JP variants, so the face must be chosen by name.
        /// </summary>
        private static int FindBestFace(string path, List<string> families, out string description)
        {
            description = null;
            int bestFace = -1;
            int bestScore = int.MaxValue;
            string preferredStyle = Settings["PreferredStyle"];

            for (int face = 0; face < 64; face++)
            {
                if (FontEngine.LoadFontFace(path, 32f, face) != FontEngineError.Success)
                {
                    break;
                }
                FaceInfo info = FontEngine.GetFaceInfo();
                int familyRank = families.FindIndex(f => string.Equals(f, info.familyName, StringComparison.OrdinalIgnoreCase));
                if (familyRank < 0)
                {
                    continue;
                }

                int styleRank = string.Equals(info.styleName, preferredStyle, StringComparison.OrdinalIgnoreCase) ? 0
                    : string.Equals(info.styleName, "Regular", StringComparison.OrdinalIgnoreCase) ? 1
                    : 2;
                int score = familyRank * 10 + styleRank;
                if (score < bestScore)
                {
                    bestScore = score;
                    bestFace = face;
                    description = info.familyName + " " + info.styleName;
                }
            }
            return bestFace;
        }

        private static void AddGlobalFallback()
        {
            try
            {
                if (TMP_Settings.instance == null)
                {
                    Debug.LogWarning(LogPrefix + "TMP Settings asset not found; relying on per-font fallbacks only.");
                    return;
                }
                if (TMP_Settings.fallbackFontAssets == null)
                {
                    TMP_Settings.fallbackFontAssets = new List<TMP_FontAsset>();
                }
                if (!TMP_Settings.fallbackFontAssets.Contains(_fallback))
                {
                    TMP_Settings.fallbackFontAssets.Add(_fallback);
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning(LogPrefix + "Could not add global TMP fallback: " + e.Message);
            }
        }

        /// <summary>
        /// Appends the Chinese font to the fallback list of every TMP font currently loaded
        /// and asks text objects using those fonts to rebuild.
        /// </summary>
        private static void PatchLoadedFonts()
        {
            int patched = 0;
            foreach (TMP_FontAsset font in Resources.FindObjectsOfTypeAll<TMP_FontAsset>())
            {
                if (font == _fallback || !PatchedFonts.Add(font.GetInstanceID()))
                {
                    continue;
                }
                if (font.fallbackFontAssetTable == null)
                {
                    font.fallbackFontAssetTable = new List<TMP_FontAsset>();
                }
                if (!font.fallbackFontAssetTable.Contains(_fallback))
                {
                    font.fallbackFontAssetTable.Add(_fallback);
                }
                TMPro_EventManager.ON_FONT_PROPERTY_CHANGED(true, font);
                patched++;
            }
            if (patched > 0)
            {
                Debug.Log(LogPrefix + "Added Chinese fallback to " + patched + " TextMeshPro font(s).");
            }
        }
    }
}
