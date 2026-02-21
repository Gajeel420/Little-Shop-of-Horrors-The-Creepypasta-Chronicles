using System;
using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FeedMe
{
    /// <summary>
    /// Top-level game state machine.
    /// Tracks stage/level progress, corruption stage, ending logic,
    /// and coordinates between all manager singletons on scene load.
    /// </summary>
    public class GameManager : MonoBehaviour
    {
        public static GameManager Instance { get; private set; }

        // ── Scene Names ────────────────────────────────────────────────────────
        // Match these exactly to your Unity Scene names in Build Settings
        private static readonly string[] StageScenes =
        {
            // Stage 1
            "Stage1_1_MushnksCursedGreenhouse",
            "Stage1_2_UndergroundRootSystem",
            "Stage1_3_SkidRowAfterDark",
            "Boss1_OrinScrivello",
            // Stage 2
            "Stage2_1_FeedingFloor",
            "Stage2_2_ClientCorridors",
            "Stage2_3_SuccessIllusion",
            "Boss2_PatrickMartin",
            // Stage 3
            "Stage3_1_TotalEclipse",
            "Stage3_2_GardenPlanet",
            "Stage3_3_SingingVoid",
            "Boss3_AudreyII",
            // Special
            "SomewhereThatSGreen",
            "LostEpisode_VHS",
            "TrueEndingCutscene",
            "DarkEndingCutscene",
            "GoldenEndingCutscene",
            "MainMenu",
        };

        // ── State ──────────────────────────────────────────────────────────────
        private int corruptionStage; // 0-3, drives player visuals and world desaturation
        private bool isNewGamePlus;
        private EndingType? activeEnding;

        public bool IsNewGamePlus => isNewGamePlus;
        public int CorruptionStage => corruptionStage;

        // ── Lifecycle ──────────────────────────────────────────────────────────
        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        private void Start()
        {
            SaveSystem.InitStartDate();
            LoadSaveData();
            SceneManager.sceneLoaded += OnSceneLoaded;
        }

        private void OnDestroy()
        {
            SceneManager.sceneLoaded -= OnSceneLoaded;
        }

        // ── Save/Load ──────────────────────────────────────────────────────────
        private void LoadSaveData()
        {
            Player.PlayerHealth.LifetimeDeathCount.ToString(); // ensure static init
            corruptionStage = SaveSystem.LoadCorruptionStage();

            var abilities = SaveSystem.LoadAbilities();
            AbilityManager.Instance?.LoadAbilities(abilities);

            var (stage, level) = SaveSystem.LoadStage();
            // Don't auto-load stage; player selects from menu
        }

        // ── Scene Load ─────────────────────────────────────────────────────────
        private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            // Update world desaturation
            CreepypastaEffects.Instance?.SetStage(GetStageFromScene(scene.name));
            HUDManager.Instance?.SetCorruptionStage(corruptionStage);

            // Re-subscribe player events
            var ph = FindAnyObjectByType<Player.PlayerHealth>();
            if (ph != null)
            {
                ph.OnHealthChanged += HUDManager.Instance?.UpdateHearts;
                ph.OnPlayerDied += OnPlayerDied;
            }

            var playerCtrl = FindAnyObjectByType<Player.PlayerController>();
            playerCtrl?.ApplyTransformationStage(corruptionStage);
        }

        private int GetStageFromScene(string sceneName)
        {
            if (sceneName.StartsWith("Stage1") || sceneName.StartsWith("Boss1")) return 1;
            if (sceneName.StartsWith("Stage2") || sceneName.StartsWith("Boss2")) return 2;
            if (sceneName.StartsWith("Stage3") || sceneName.StartsWith("Boss3")) return 3;
            return 0;
        }

        // ── Stage Progression ──────────────────────────────────────────────────
        public void LoadNextScene()
        {
            string current = SceneManager.GetActiveScene().name;
            int idx = Array.IndexOf(StageScenes, current);
            if (idx < 0 || idx >= StageScenes.Length - 1) return;
            SaveSystem.SaveStage(idx / 4, idx % 4);
            StartCoroutine(TransitionToScene(StageScenes[idx + 1]));
        }

        public void LoadScene(string sceneName)
        {
            StartCoroutine(TransitionToScene(sceneName));
        }

        private IEnumerator TransitionToScene(string sceneName)
        {
            HUDManager.Instance?.FadeToBlack(0.5f);
            yield return new WaitForSeconds(0.6f);
            SceneManager.LoadScene(sceneName);
        }

        // ── Corruption ─────────────────────────────────────────────────────────
        public void IncrementCorruption()
        {
            corruptionStage = Mathf.Min(3, corruptionStage + 1);
            SaveSystem.SaveCorruptionStage(corruptionStage);
            FindAnyObjectByType<Player.PlayerController>()?.ApplyTransformationStage(corruptionStage);
            HUDManager.Instance?.SetCorruptionStage(corruptionStage);
        }

        // ── Final Choice (called by AudreyIIBoss) ──────────────────────────────
        public void ShowFinalChoice(Action onOptionA, Action onOptionB, Action onOptionC)
        {
            string[] labels = onOptionC != null
                ? new[] { "\"Yes.\"", "\"No.\"", "\"There's another way.\"" }
                : new[] { "\"Yes.\"", "\"No.\"" };

            HUDManager.Instance?.ShowChoiceWheel(labels, idx =>
            {
                switch (idx)
                {
                    case 0: onOptionA?.Invoke(); break;
                    case 1: onOptionB?.Invoke(); break;
                    case 2: onOptionC?.Invoke(); break;
                }
            });
        }

        // ── Endings ────────────────────────────────────────────────────────────
        public void TriggerEnding(EndingType ending)
        {
            activeEnding = ending;
            SaveSystem.UnlockEnding(ending);

            if (ending == EndingType.True || ending == EndingType.Normal)
            {
                // Unlock New Game+
                isNewGamePlus = true;
                AbilityManager.Instance?.UnlockAbility(AbilityType.SomewhereThatSGreen);
            }

            string scene = ending switch
            {
                EndingType.True   => "TrueEndingCutscene",
                EndingType.Dark   => "DarkEndingCutscene",
                EndingType.Golden => "GoldenEndingCutscene",
                _                 => "TrueEndingCutscene"
            };
            StartCoroutine(TransitionToScene(scene));
        }

        // ── Player Death ───────────────────────────────────────────────────────
        private void OnPlayerDied()
        {
            // Corruption increases slightly on death (plant gets stronger)
            if (corruptionStage < 3 && Player.PlayerHealth.LifetimeDeathCount % 10 == 0)
                IncrementCorruption();
        }

        // ── Combat Manager ─────────────────────────────────────────────────────
        // Lightweight inline combat manager - handles damage boost stack
        public void PushDamageBoost(DamageBoostToken token)
            => CombatManager.Instance?.PushDamageBoost(token);
        public void RemoveDamageBoost(DamageBoostToken token)
            => CombatManager.Instance?.RemoveDamageBoost(token);
    }
}
