using System.Collections.Generic;
using TMPro;
using UnityEngine;

namespace XwvmChineseFont
{
    /// <summary>
    /// 3D TextMeshPro objects draw fallback-font glyphs with child TMP_SubMesh renderers.
    /// When an Animator animates the text's material (e.g. XWVM's opening crawl fading in via _FaceColor),
    /// Unity applies it as a MaterialPropertyBlock on the main renderer only, so CJK glyphs stay invisible.
    /// This copies the main renderer's property block to the sub-meshes that use our fallback fonts.
    /// </summary>
    internal static class SubMeshPropertySync
    {
        private static readonly List<(Renderer main, Renderer[] subs)> Targets = new List<(Renderer, Renderer[])>();
        private static readonly HashSet<int> Logged = new HashSet<int>();
        private static readonly MaterialPropertyBlock Block = new MaterialPropertyBlock();

        /// <summary>Finds 3D texts with fallback-font sub-meshes; called a few times per second.</summary>
        public static void Refresh()
        {
            Targets.Clear();
            foreach (TextMeshPro text in Object.FindObjectsByType<TextMeshPro>(FindObjectsSortMode.None))
            {
                var subs = new List<Renderer>();
                foreach (TMP_SubMesh sub in text.GetComponentsInChildren<TMP_SubMesh>())
                {
                    if (FallbackFontLoader.IsFallbackFont(sub.fontAsset))
                    {
                        subs.Add(sub.renderer);
                    }
                }
                if (subs.Count > 0)
                {
                    Targets.Add((text.renderer, subs.ToArray()));
                }
            }
        }

        /// <summary>Runs every frame after animation has written this frame's property blocks.</summary>
        public static void Sync()
        {
            foreach (var (main, subs) in Targets)
            {
                if (main == null || !main.HasPropertyBlock())
                {
                    continue;
                }
                main.GetPropertyBlock(Block);
                foreach (Renderer sub in subs)
                {
                    if (sub != null)
                    {
                        sub.SetPropertyBlock(Block);
                    }
                }
                if (Logged.Add(main.GetInstanceID()))
                {
                    Debug.Log(FallbackFontLoader.LogPrefix + "Syncing animated material properties to " + subs.Length
                        + " fallback sub-mesh(es) of '" + main.name + "'.");
                }
            }
        }
    }
}
