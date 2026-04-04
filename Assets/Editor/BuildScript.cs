using System;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

// NOTE: This file must live under Assets/Editor/ so Unity excludes it from
//       runtime builds automatically (Editor-only assembly).

namespace FeedMe.Editor
{
    /// <summary>
    /// Headless build script for Little Shop of Horrors: The Creepypasta Chronicles.
    ///
    /// Invoke from command line:
    ///   Unity -quit -batchmode -projectPath . \
    ///         -executeMethod FeedMe.Editor.BuildScript.BuildGame \
    ///         -buildTarget StandaloneWindows64 \
    ///         -buildMode Release
    ///
    /// Supported -buildTarget values:
    ///   StandaloneWindows64 | StandaloneOSX | StandaloneLinux64 | WebGL | Android | iOS
    ///
    /// Supported -buildMode values:
    ///   Development | Release  (defaults to Release)
    /// </summary>
    public static class BuildScript
    {
        // ── Scene List ─────────────────────────────────────────────────────────
        // Mirrors GameManager.StageScenes (Assets/Scripts/Systems/GameManager.cs).
        // IMPORTANT: Keep this list in sync with GameManager.StageScenes.
        // Scene names must match the filenames in Assets/Scenes/ exactly.
        private static readonly string[] GameScenes =
        {
            // ── Stage 1 ──────────────────────────────────────────────────────
            "Assets/Scenes/Stage1_1_MushnksCursedGreenhouse.unity",   // NOTE: "Mushnks" is canonical
            "Assets/Scenes/Stage1_2_UndergroundRootSystem.unity",
            "Assets/Scenes/Stage1_3_SkidRowAfterDark.unity",
            "Assets/Scenes/Boss1_OrinScrivello.unity",
            // ── Stage 2 ──────────────────────────────────────────────────────
            "Assets/Scenes/Stage2_1_FeedingFloor.unity",
            "Assets/Scenes/Stage2_2_ClientCorridors.unity",
            "Assets/Scenes/Stage2_3_SuccessIllusion.unity",
            "Assets/Scenes/Boss2_PatrickMartin.unity",
            // ── Stage 3 ──────────────────────────────────────────────────────
            "Assets/Scenes/Stage3_1_TotalEclipse.unity",
            "Assets/Scenes/Stage3_2_GardenPlanet.unity",
            "Assets/Scenes/Stage3_3_SingingVoid.unity",
            "Assets/Scenes/Boss3_AudreyII.unity",
            // ── Special / Endings ─────────────────────────────────────────────
            "Assets/Scenes/SomewhereThatSGreen.unity",
            "Assets/Scenes/LostEpisode_VHS.unity",
            "Assets/Scenes/TrueEndingCutscene.unity",
            "Assets/Scenes/DarkEndingCutscene.unity",
            "Assets/Scenes/GoldenEndingCutscene.unity",
            // ── Boot ──────────────────────────────────────────────────────────
            "Assets/Scenes/MainMenu.unity",
        };

        // ── Entry Point ────────────────────────────────────────────────────────
        /// <summary>
        /// Called by Unity in batch mode via -executeMethod FeedMe.Editor.BuildScript.BuildGame.
        /// Reads build parameters from command-line arguments.
        /// </summary>
        public static void BuildGame()
        {
            try
            {
                BuildTarget target    = ParseBuildTarget();
                bool        isDev     = ParseBuildMode();
                string      output    = BuildOutputPath(target);
                string[]    scenes    = ResolveScenes();

                BuildPlayerOptions options = new BuildPlayerOptions
                {
                    scenes           = scenes,
                    locationPathName = output,
                    target           = target,
                    targetGroup      = BuildPipeline.GetBuildTargetGroup(target),
                    options          = isDev
                        ? BuildOptions.Development | BuildOptions.AllowDebugging
                        : BuildOptions.None,
                };

                Log($"[BuildScript] Starting {(isDev ? "Development" : "Release")} build");
                Log($"[BuildScript] Platform : {target}");
                Log($"[BuildScript] Output   : {output}");
                Log($"[BuildScript] Scenes   : {scenes.Length}");

                BuildReport  report  = BuildPipeline.BuildPlayer(options);
                BuildSummary summary = report.summary;

                if (summary.result == BuildResult.Succeeded)
                {
                    Log($"[BuildScript] Build succeeded in {summary.totalTime.TotalSeconds:F1}s " +
                        $"({summary.totalSize / 1_048_576f:F1} MB)");
                    EditorApplication.Exit(0);
                }
                else
                {
                    LogError($"[BuildScript] Build FAILED: {summary.result}  Errors={summary.totalErrors}");
                    EditorApplication.Exit(1);
                }
            }
            catch (Exception ex)
            {
                LogError($"[BuildScript] Unhandled exception: {ex}");
                EditorApplication.Exit(1);
            }
        }

        // ── Platform Entry Points (usable as -executeMethod directly) ──────────
        /// <summary>Builds a Windows 64-bit release.</summary>
        public static void BuildWindows() => RunBuild(BuildTarget.StandaloneWindows64, false);

        /// <summary>Builds a macOS release.</summary>
        public static void BuildMacOS()   => RunBuild(BuildTarget.StandaloneOSX, false);

        /// <summary>Builds a Linux 64-bit release.</summary>
        public static void BuildLinux()   => RunBuild(BuildTarget.StandaloneLinux64, false);

        /// <summary>Builds a WebGL release.</summary>
        public static void BuildWebGL()   => RunBuild(BuildTarget.WebGL, false);

        /// <summary>Builds an Android APK release.</summary>
        public static void BuildAndroid() => RunBuild(BuildTarget.Android, false);

        // ── Editor Menu Shortcuts ──────────────────────────────────────────────
        [MenuItem("Feed Me/Build/Windows (Release)")]
        private static void MenuBuildWindows() => RunBuild(BuildTarget.StandaloneWindows64, false);

        [MenuItem("Feed Me/Build/Windows (Development)")]
        private static void MenuBuildWindowsDev() => RunBuild(BuildTarget.StandaloneWindows64, true);

        [MenuItem("Feed Me/Build/macOS (Release)")]
        private static void MenuBuildMac() => RunBuild(BuildTarget.StandaloneOSX, false);

        [MenuItem("Feed Me/Build/Linux (Release)")]
        private static void MenuBuildLinux() => RunBuild(BuildTarget.StandaloneLinux64, false);

        [MenuItem("Feed Me/Build/WebGL (Release)")]
        private static void MenuBuildWebGL() => RunBuild(BuildTarget.WebGL, false);

        [MenuItem("Feed Me/Build/Android (Release)")]
        private static void MenuBuildAndroid() => RunBuild(BuildTarget.Android, false);

        // ── Internal Runner ────────────────────────────────────────────────────
        private static void RunBuild(BuildTarget target, bool development)
        {
            string   output  = BuildOutputPath(target);
            string[] scenes  = ResolveScenes();

            BuildPlayerOptions options = new BuildPlayerOptions
            {
                scenes           = scenes,
                locationPathName = output,
                target           = target,
                targetGroup      = BuildPipeline.GetBuildTargetGroup(target),
                options          = development
                    ? BuildOptions.Development | BuildOptions.AllowDebugging
                    : BuildOptions.None,
            };

            BuildPipeline.BuildPlayer(options);
        }

        // ── Scene Resolution ───────────────────────────────────────────────────
        /// <summary>
        /// Returns scenes for the build.
        /// Prefers enabled scenes from Build Settings (EditorBuildSettings);
        /// falls back to the hardcoded GameScenes list for fresh CI checkouts.
        /// </summary>
        private static string[] ResolveScenes()
        {
            string[] settingsScenes = EditorBuildSettings.scenes
                .Where(s => s.enabled)
                .Select(s => s.path)
                .ToArray();

            if (settingsScenes.Length > 0)
            {
                Log($"[BuildScript] Using {settingsScenes.Length} scene(s) from Build Settings.");
                return settingsScenes;
            }

            Log("[BuildScript] Build Settings has no enabled scenes — using hardcoded GameScenes list.");
            return GameScenes;
        }

        // ── Output Path ────────────────────────────────────────────────────────
        private static string BuildOutputPath(BuildTarget target) => target switch
        {
            BuildTarget.StandaloneWindows64 => "Builds/Windows/LittleShopOfHorrors.exe",
            BuildTarget.StandaloneOSX       => "Builds/macOS/LittleShopOfHorrors.app",
            BuildTarget.StandaloneLinux64   => "Builds/Linux/LittleShopOfHorrors.x86_64",
            BuildTarget.WebGL               => "Builds/WebGL",
            BuildTarget.Android             => "Builds/Android/LittleShopOfHorrors.apk",
            BuildTarget.iOS                 => "Builds/iOS",
            _                               => throw new ArgumentException($"Unsupported build target: {target}"),
        };

        // ── CLI Argument Parsing ───────────────────────────────────────────────
        private static BuildTarget ParseBuildTarget()
        {
            string raw = GetArgValue("-buildTarget");
            if (string.IsNullOrEmpty(raw))
            {
                Log("[BuildScript] No -buildTarget specified. Defaulting to StandaloneWindows64.");
                return BuildTarget.StandaloneWindows64;
            }

            return raw.ToLowerInvariant() switch
            {
                "standalonewindows64" or "windows" or "win64" => BuildTarget.StandaloneWindows64,
                "standaloneosx"       or "macos"   or "osx"   => BuildTarget.StandaloneOSX,
                "standalonelinux64"   or "linux"   or "linux64" => BuildTarget.StandaloneLinux64,
                "webgl"                                        => BuildTarget.WebGL,
                "android"                                      => BuildTarget.Android,
                "ios"                                          => BuildTarget.iOS,
                _ => throw new ArgumentException($"Unknown build target: '{raw}'"),
            };
        }

        private static bool ParseBuildMode()
        {
            string raw = GetArgValue("-buildMode");
            return string.Equals(raw, "Development", StringComparison.OrdinalIgnoreCase);
        }

        private static string GetArgValue(string key)
        {
            string[] args = Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (string.Equals(args[i], key, StringComparison.OrdinalIgnoreCase))
                    return args[i + 1];
            }
            return null;
        }

        // ── Logging ────────────────────────────────────────────────────────────
        private static void Log(string msg)      => Debug.Log(msg);
        private static void LogError(string msg) => Debug.LogError(msg);
    }
}
