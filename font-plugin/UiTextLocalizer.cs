using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using Newtonsoft.Json;
using TMPro;
using UnityEngine;
using UnityEngine.Localization.Settings;

namespace XwvmChineseFont
{
    /// <summary>
    /// Translates UI text that XWVM does not take from its XLIFF files: the Rewired control-mapping
    /// window (its LanguageData asset), input action names and mouse element names shown in TMP texts.
    /// Translations come from XwvmChineseFont-zh-TW.json (exact English text -> Chinese) next to this DLL
    /// and are only applied while the selected locale is Chinese; switching language restores the English.
    /// </summary>
    internal class UiTextLocalizer : MonoBehaviour
    {
        private const string LogPrefix = "[XwvmChineseFont] ";
        private const float ScanInterval = 0.25f;

        private Dictionary<string, string> _translations;
        private readonly Dictionary<TMP_Text, KeyValuePair<string, string>> _changedTexts = new Dictionary<TMP_Text, KeyValuePair<string, string>>();
        private readonly List<(object owner, FieldInfo field, string original)> _changedFields = new List<(object, FieldInfo, string)>();
        private readonly HashSet<int> _patchedAssets = new HashSet<int>();
        private bool _active;
        private float _nextScan;

        public static void Create(string dllDirectory)
        {
            string path = Path.Combine(dllDirectory, "XwvmChineseFont-zh-TW.json");
            if (!File.Exists(path))
            {
                return;
            }
            var translations = JsonConvert.DeserializeObject<Dictionary<string, string>>(File.ReadAllText(path));
            translations.Remove("_comment");

            var go = new GameObject("XwvmChineseFont.UiTextLocalizer") { hideFlags = HideFlags.HideAndDontSave };
            DontDestroyOnLoad(go);
            go.AddComponent<UiTextLocalizer>()._translations = translations;
            Debug.Log(LogPrefix + "Loaded " + translations.Count + " extra UI translations from " + path);
        }

        private void Update()
        {
            if (Time.unscaledTime < _nextScan)
            {
                return;
            }
            _nextScan = Time.unscaledTime + ScanInterval;

            bool chinese = IsChineseSelected();
            if (chinese)
            {
                PatchLanguageDataAssets();
                TranslateVisibleTexts();
            }
            else if (_active)
            {
                Restore();
            }
            _active = chinese;
        }

        private static bool IsChineseSelected()
        {
            if (!LocalizationSettings.HasSettings || !LocalizationSettings.InitializationOperation.IsDone)
            {
                return false;
            }
            string code = LocalizationSettings.SelectedLocale?.Identifier.Code;
            return code != null && code.StartsWith("zh", StringComparison.OrdinalIgnoreCase);
        }

        private bool TryTranslate(string text, out string translated)
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
        private void PatchLanguageDataAssets()
        {
            Type type = Type.GetType("Rewired.UI.ControlMapper.LanguageData, Assembly-CSharp");
            if (type == null)
            {
                return;
            }
            foreach (UnityEngine.Object asset in Resources.FindObjectsOfTypeAll(type))
            {
                if (!_patchedAssets.Add(asset.GetInstanceID()))
                {
                    continue;
                }
                foreach (FieldInfo field in type.GetFields(BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public))
                {
                    if (field.FieldType == typeof(string) && TryTranslate((string)field.GetValue(asset), out string zh))
                    {
                        _changedFields.Add((asset, field, (string)field.GetValue(asset)));
                        field.SetValue(asset, zh);
                    }
                }
            }
        }

        private void TranslateVisibleTexts()
        {
            if (_changedTexts.Count > 2000)
            {
                var destroyed = new List<TMP_Text>();
                foreach (TMP_Text key in _changedTexts.Keys)
                {
                    if (key == null)
                    {
                        destroyed.Add(key);
                    }
                }
                destroyed.ForEach(k => _changedTexts.Remove(k));
            }
            foreach (TMP_Text text in FindObjectsByType<TMP_Text>(FindObjectsSortMode.None))
            {
                string current = text.text;
                if (TryTranslate(current, out string zh))
                {
                    _changedTexts[text] = new KeyValuePair<string, string>(current, zh);
                    text.text = zh;
                }
            }
        }

        private void Restore()
        {
            foreach (var (owner, field, original) in _changedFields)
            {
                if (owner is UnityEngine.Object o && o != null)
                {
                    field.SetValue(owner, original);
                }
            }
            _changedFields.Clear();
            _patchedAssets.Clear();

            foreach (var pair in _changedTexts)
            {
                // Only undo our own change; the game may have replaced the text since.
                if (pair.Key != null && pair.Key.text == pair.Value.Value)
                {
                    pair.Key.text = pair.Value.Key;
                }
            }
            _changedTexts.Clear();
        }
    }
}
