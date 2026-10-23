using UnityEngine;
using UnityEngine.Localization.Settings;

namespace XwvmChineseFont
{
    /// <summary>
    /// Polls the game's selected locale and tells <see cref="FallbackFontLoader"/> and
    /// <see cref="UiTextLocalizer"/> when it changes; also drives the UI text replacement.
    /// </summary>
    internal class LocaleWatcher : MonoBehaviour
    {
        private const float Interval = 0.25f;

        private string _locale;
        private float _next;

        public static void Create()
        {
            var go = new GameObject("XwvmChineseFont.LocaleWatcher") { hideFlags = HideFlags.HideAndDontSave };
            DontDestroyOnLoad(go);
            go.AddComponent<LocaleWatcher>();
        }

        private void Update()
        {
            if (Time.unscaledTime < _next)
            {
                return;
            }
            _next = Time.unscaledTime + Interval;

            string locale = CurrentLocale();
            if (locale != null && locale != _locale)
            {
                _locale = locale;
                FallbackFontLoader.ApplyLocale(locale);
                UiTextLocalizer.SetLocale(locale);
            }
            UiTextLocalizer.Tick();
        }

        /// <summary>Lower-case locale code such as "zh-tw", or null while Unity Localization is still starting.</summary>
        private static string CurrentLocale()
        {
            if (!LocalizationSettings.HasSettings || !LocalizationSettings.InitializationOperation.IsDone)
            {
                return null;
            }
            return LocalizationSettings.SelectedLocale?.Identifier.Code?.ToLowerInvariant();
        }
    }
}
