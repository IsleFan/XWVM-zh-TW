using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using Newtonsoft.Json;
using TMPro;
using UnityEngine;

namespace XwvmChineseFont
{
    /// <summary>
    /// Translates UI text that XWVM does not take from its XLIFF files: the Rewired control-mapping
    /// window (its LanguageData asset), input action names and mouse element names shown in TMP texts.
    /// Each XwvmChineseFont-&lt;locale&gt;.json next to this DLL (exact English text -> translation) is used
    /// while that locale is selected (exact code first, then language); switching locale restores English.
    /// </summary>
    internal static class UiTextLocalizer
    {
        private const string FilePrefix = "XwvmChineseFont-";

        private static readonly Dictionary<string, Dictionary<string, string>> Tables =
            new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase);
        private static readonly Dictionary<TMP_Text, KeyValuePair<string, string>> ChangedTexts = new Dictionary<TMP_Text, KeyValuePair<string, string>>();
        private static readonly List<(object owner, FieldInfo field, string original)> ChangedFields = new List<(object, FieldInfo, string)>();
        private static readonly HashSet<int> PatchedAssets = new HashSet<int>();
        private static Dictionary<string, string> _translations;

        public static void Init(string dllDirectory)
        {
            foreach (string path in Directory.GetFiles(dllDirectory, FilePrefix + "*.json"))
            {
                string locale = Path.GetFileNameWithoutExtension(path).Substring(FilePrefix.Length);
                var table = JsonConvert.DeserializeObject<Dictionary<string, string>>(File.ReadAllText(path));
                table.Remove("_comment");
                Tables[locale] = table;
                Debug.Log(FallbackFontLoader.LogPrefix + "Loaded " + table.Count + " UI translations for '" + locale + "' from " + path);
            }
        }

        public static void SetLocale(string locale)
        {
            Restore();
            string language = locale.Split('-')[0];
            if (!Tables.TryGetValue(locale, out _translations))
            {
                Tables.TryGetValue(language, out _translations);
            }
        }

        public static void Tick()
        {
            if (_translations == null)
            {
                return;
            }
            PatchLanguageDataAssets();
            TranslateVisibleTexts();
        }

        private static bool TryTranslate(string text, out string translated)
        {
            translated = null;
            if (string.IsNullOrEmpty(text))
            {
                return false;
            }
            string trimmed = text.Trim();
            if (_translations.TryGetValue(trimmed, out translated))
            {
                return true;
            }
            // Rewired shows axis halves as "<name> +" / "<name> -".
            if (trimmed.Length > 2 && (trimmed.EndsWith(" +") || trimmed.EndsWith(" -"))
                && _translations.TryGetValue(trimmed.Substring(0, trimmed.Length - 2), out translated))
            {
                translated += trimmed.Substring(trimmed.Length - 2);
                return true;
            }
            return false;
        }

        /// <summary>Rewired's ControlMapper reads its labels and dialog templates from LanguageData string fields.</summary>
        private static void PatchLanguageDataAssets()
        {
            Type type = Type.GetType("Rewired.UI.ControlMapper.LanguageData, Assembly-CSharp");
            if (type == null)
            {
                return;
            }
            foreach (UnityEngine.Object asset in Resources.FindObjectsOfTypeAll(type))
            {
                if (!PatchedAssets.Add(asset.GetInstanceID()))
                {
                    continue;
                }
                foreach (FieldInfo field in type.GetFields(BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public))
                {
                    if (field.FieldType == typeof(string) && TryTranslate((string)field.GetValue(asset), out string translated))
                    {
                        ChangedFields.Add((asset, field, (string)field.GetValue(asset)));
                        field.SetValue(asset, translated);
                    }
                }
            }
        }

        private static void TranslateVisibleTexts()
        {
            if (ChangedTexts.Count > 2000)
            {
                var destroyed = new List<TMP_Text>();
                foreach (TMP_Text key in ChangedTexts.Keys)
                {
                    if (key == null)
                    {
                        destroyed.Add(key);
                    }
                }
                destroyed.ForEach(k => ChangedTexts.Remove(k));
            }
            foreach (TMP_Text text in UnityEngine.Object.FindObjectsByType<TMP_Text>(FindObjectsSortMode.None))
            {
                string current = text.text;
                if (TryTranslate(current, out string translated))
                {
                    ChangedTexts[text] = new KeyValuePair<string, string>(current, translated);
                    text.text = translated;
                }
            }
        }

        private static void Restore()
        {
            foreach (var (owner, field, original) in ChangedFields)
            {
                if (owner is UnityEngine.Object o && o != null)
                {
                    field.SetValue(owner, original);
                }
            }
            ChangedFields.Clear();
            PatchedAssets.Clear();

            foreach (var pair in ChangedTexts)
            {
                // Only undo our own change; the game may have replaced the text since.
                if (pair.Key != null && pair.Key.text == pair.Value.Value)
                {
                    pair.Key.text = pair.Value.Key;
                }
            }
            ChangedTexts.Clear();
            _translations = null;
        }
    }
}
