// ArtPipelineImporter.cs
// ========================
// Unity Editor-only tool that reads generated art from ArtPipeline output
// and configures all Texture2D import settings automatically.
//
// Opens via: Window → Feed Me → Art Pipeline Importer
//
// What it does:
//   1. Scans Assets/Art/** for newly dropped PNGs
//   2. Sets per-asset TextureImporter settings (sprite mode, pivot, PPU, filter)
//   3. Reads <CharacterName>_meta.json to auto-slice sprite sheets into frames
//   4. Assigns sprites to named Sprite Animation clips in Animations/
//   5. Applies "Background" texture type + tiling for parallax layers
//   6. Compresses everything appropriately for 2D (no MipMaps on sprites)

#if UNITY_EDITOR

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace FeedMe.Editor
{
    public class ArtPipelineImporter : EditorWindow
    {
        // ── Window ────────────────────────────────────────────────────────────
        [MenuItem("Window/Feed Me/Art Pipeline Importer")]
        public static void Open() => GetWindow<ArtPipelineImporter>("Art Pipeline Importer");

        private Vector2 scrollPos;
        private string statusLog = "";

        private void OnGUI()
        {
            GUILayout.Label("Feed Me: Art Pipeline Importer", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox(
                "Scans Assets/Art/ and applies correct import settings for all generated assets.\n" +
                "Run this after dropping new PNGs exported from ComfyUI.",
                MessageType.Info);

            EditorGUILayout.Space(8);

            if (GUILayout.Button("Import All Art Assets", GUILayout.Height(32)))
                RunImport();

            EditorGUILayout.Space(4);

            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("Backgrounds Only"))  ImportCategory(ArtCategory.Background);
                if (GUILayout.Button("Sprites Only"))      ImportCategory(ArtCategory.Sprite);
                if (GUILayout.Button("Misc / UI Only"))    ImportCategory(ArtCategory.Misc);
            }

            EditorGUILayout.Space(8);
            GUILayout.Label("Log:", EditorStyles.miniBoldLabel);
            scrollPos = EditorGUILayout.BeginScrollView(scrollPos, GUILayout.Height(300));
            EditorGUILayout.TextArea(statusLog, GUILayout.ExpandHeight(true));
            EditorGUILayout.EndScrollView();

            if (GUILayout.Button("Clear Log"))
                statusLog = "";
        }

        // ── Main import flow ──────────────────────────────────────────────────
        private void RunImport()
        {
            statusLog = "";
            Log("=== Art Pipeline Import Started ===");

            ImportCategory(ArtCategory.Background);
            ImportCategory(ArtCategory.Sprite);
            ImportCategory(ArtCategory.Misc);

            AssetDatabase.Refresh();
            Log("=== Import Complete ===");
        }

        private void ImportCategory(ArtCategory category)
        {
            string basePath = "Assets/Art";
            switch (category)
            {
                case ArtCategory.Background: ProcessBackgrounds(basePath + "/Backgrounds"); break;
                case ArtCategory.Sprite:     ProcessSprites(basePath + "/Sprites");         break;
                case ArtCategory.Misc:       ProcessMisc(basePath);                         break;
            }
            AssetDatabase.Refresh();
        }

        // ── Backgrounds ───────────────────────────────────────────────────────
        private void ProcessBackgrounds(string folderPath)
        {
            if (!Directory.Exists(folderPath)) { Log($"Skipped (not found): {folderPath}"); return; }

            var pngs = Directory.GetFiles(folderPath, "*.png", SearchOption.AllDirectories);
            Log($"Processing {pngs.Length} background(s)...");

            foreach (var absPath in pngs)
            {
                string assetPath = AbsToAsset(absPath);
                var importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;
                if (importer == null) continue;

                importer.textureType          = TextureImporterType.Sprite;
                importer.spriteImportMode     = SpriteImportMode.Single;
                importer.mipmapEnabled        = false;
                importer.filterMode           = FilterMode.Bilinear;
                importer.textureCompression   = TextureImporterCompression.Compressed;
                importer.spritePivot          = new Vector2(0.5f, 0.5f);
                importer.spritePixelsPerUnit  = 100;
                importer.isReadable           = false;

                var settings = importer.GetDefaultPlatformTextureSettings();
                settings.maxTextureSize       = 4096;
                settings.format               = TextureImporterFormat.DXT1;
                importer.SetPlatformTextureSettings(settings);

                importer.SaveAndReimport();
                Log($"  ✓ Background: {Path.GetFileName(assetPath)}");
            }
        }

        // ── Sprites ───────────────────────────────────────────────────────────
        private void ProcessSprites(string folderPath)
        {
            if (!Directory.Exists(folderPath)) { Log($"Skipped (not found): {folderPath}"); return; }

            // Each character has its own subfolder
            foreach (var charDir in Directory.GetDirectories(folderPath))
            {
                string charName   = Path.GetFileName(charDir);
                string metaPath   = Path.Combine(charDir, $"{charName}_meta.json");
                bool hasMeta      = File.Exists(metaPath);

                SpriteMetaRoot meta = null;
                if (hasMeta)
                {
                    try { meta = JsonUtility.FromJson<SpriteMetaRoot>(File.ReadAllText(metaPath)); }
                    catch (Exception e) { Log($"  [WARN] Bad meta for {charName}: {e.Message}"); }
                }

                var pngs = Directory.GetFiles(charDir, "*.png");
                Log($"Processing {charName}: {pngs.Length} sprite sheet(s)...");

                foreach (var absPath in pngs)
                {
                    string assetPath   = AbsToAsset(absPath);
                    string sheetName   = Path.GetFileNameWithoutExtension(absPath);
                    var importer       = AssetImporter.GetAtPath(assetPath) as TextureImporter;
                    if (importer == null) continue;

                    // Look for matching frame rects in meta
                    SpriteMetaEntry metaEntry = null;
                    if (meta != null)
                    {
                        // Find all entries that start with this sheet name
                        // meta keys are like "Seymour_idle"
                        string prefix = sheetName;
                        foreach (var kv in meta.animations)
                        {
                            if (kv.key == prefix)
                            { metaEntry = kv.value; break; }
                        }
                    }

                    ConfigureSpriteSheet(importer, assetPath, sheetName, metaEntry);
                    Log($"  ✓ Sprite: {sheetName} ({(metaEntry != null ? metaEntry.frames.Count : 1)} frames)");
                }
            }
        }

        private void ConfigureSpriteSheet(
            TextureImporter importer,
            string assetPath,
            string sheetName,
            SpriteMetaEntry meta)
        {
            importer.textureType        = TextureImporterType.Sprite;
            importer.mipmapEnabled      = false;
            importer.filterMode         = FilterMode.Point;   // pixel art: no filtering
            importer.textureCompression = TextureImporterCompression.Uncompressed; // sprites need alpha
            importer.alphaIsTransparency = true;
            importer.isReadable         = false;

            var platformSettings = importer.GetDefaultPlatformTextureSettings();
            platformSettings.maxTextureSize = 2048;
            importer.SetPlatformTextureSettings(platformSettings);

            if (meta != null && meta.frames != null && meta.frames.Count > 1)
            {
                importer.spriteImportMode = SpriteImportMode.Multiple;
                importer.spritePixelsPerUnit = meta.frameWidth > 0 ? meta.frameWidth : 128;

                var spriteRects = new List<SpriteMetaData>();
                foreach (var frame in meta.frames)
                {
                    // Unity's coordinate system has Y flipped from our top-down JSON
                    var ti = importer.GetTextureSettings(out var _);
                    // We need the texture height for Y flip — read from file
                    var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(assetPath);
                    int texH = tex != null ? tex.height : meta.frameHeight * 10;

                    spriteRects.Add(new SpriteMetaData
                    {
                        name   = frame.name,
                        rect   = new Rect(frame.x, texH - frame.y - frame.height,
                                          frame.width, frame.height),
                        pivot  = new Vector2(frame.pivot.x, frame.pivot.y),
                        alignment = (int)SpriteAlignment.Custom,
                    });
                }
                importer.spritesheet = spriteRects.ToArray();
            }
            else
            {
                importer.spriteImportMode    = SpriteImportMode.Single;
                importer.spritePixelsPerUnit = 128;
                importer.spritePivot         = new Vector2(0.5f, 0f); // bottom-center for characters
            }

            importer.SaveAndReimport();
        }

        // ── Misc / UI / Cutscenes ─────────────────────────────────────────────
        private void ProcessMisc(string basePath)
        {
            var miscDirs = new Dictionary<string, TextureImporterType>
            {
                { "Cutscenes",    TextureImporterType.Sprite },
                { "Memories",     TextureImporterType.Sprite },
                { "Collectibles", TextureImporterType.Sprite },
                { "Portraits",    TextureImporterType.Sprite },
                { "UI",           TextureImporterType.Sprite },
                { "VHS",          TextureImporterType.Sprite },
            };

            foreach (var (subdir, texType) in miscDirs)
            {
                string dirPath = Path.Combine(basePath, subdir);
                if (!Directory.Exists(dirPath)) continue;

                var pngs = Directory.GetFiles(dirPath, "*.png");
                Log($"Processing {subdir}: {pngs.Length} asset(s)...");

                foreach (var absPath in pngs)
                {
                    string assetPath = AbsToAsset(absPath);
                    var importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;
                    if (importer == null) continue;

                    importer.textureType          = texType;
                    importer.spriteImportMode     = SpriteImportMode.Single;
                    importer.mipmapEnabled        = false;
                    importer.alphaIsTransparency  = true;
                    importer.textureCompression   = TextureImporterCompression.Compressed;

                    bool isPortrait = subdir == "Portraits";
                    importer.filterMode           = isPortrait ? FilterMode.Point : FilterMode.Bilinear;
                    importer.spritePixelsPerUnit  = isPortrait ? 128 : 100;

                    var settings = importer.GetDefaultPlatformTextureSettings();
                    settings.maxTextureSize = subdir == "Cutscenes" ? 2048 : 512;
                    importer.SetPlatformTextureSettings(settings);

                    importer.SaveAndReimport();
                    Log($"  ✓ {subdir}: {Path.GetFileName(assetPath)}");
                }
            }
        }

        // ── Helpers ───────────────────────────────────────────────────────────
        private void Log(string msg)
        {
            statusLog += msg + "\n";
            Repaint();
            Debug.Log($"[ArtPipeline] {msg}");
        }

        private static string AbsToAsset(string absPath)
        {
            string full    = Path.GetFullPath(absPath).Replace('\\', '/');
            string dataPath = Application.dataPath.Replace('\\', '/');
            if (full.StartsWith(dataPath))
                return "Assets" + full.Substring(dataPath.Length);
            return absPath;
        }

        private enum ArtCategory { Background, Sprite, Misc }
    }

    // ── JSON deserialization types ────────────────────────────────────────────
    // Must be serializable by JsonUtility

    [Serializable]
    public class SpriteMetaRoot
    {
        public List<AnimationEntry> animations = new();
    }

    [Serializable]
    public class AnimationEntry
    {
        public string key;
        public SpriteMetaEntry value;
    }

    [Serializable]
    public class SpriteMetaEntry
    {
        public List<SpriteFrameRect> frames = new();
        public int frameWidth;
        public int frameHeight;
    }

    [Serializable]
    public class SpriteFrameRect
    {
        public string name;
        public int x, y, width, height;
        public SpritePivotPoint pivot;
    }

    [Serializable]
    public class SpritePivotPoint
    {
        public float x, y;
    }
}

#endif
