using System;
using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FeedMe
{
    /// <summary>
    /// Central HUD controller.
    /// Manages: heart containers, boss health bar, ability cooldowns,
    /// creepypasta overlay messages, hint toasts, screen fades,
    /// and the progressive HUD corruption (thorns growing on health bar).
    /// </summary>
    public class HUDManager : MonoBehaviour
    {
        public static HUDManager Instance { get; private set; }

        // ── Player Hearts ──────────────────────────────────────────────────────
        [Header("Hearts")]
        [SerializeField] private Transform heartContainer;
        [SerializeField] private GameObject heartFullPrefab;
        [SerializeField] private GameObject heartEmptyPrefab;
        [SerializeField] private GameObject thornOverlayPrefab;  // Appears over hearts at corruption
        [SerializeField] private int[] thornThresholds = { 2, 4, 6 }; // Corruption stages to add thorns

        // ── Boss Health Bar ────────────────────────────────────────────────────
        [Header("Boss HP")]
        [SerializeField] private GameObject bossHPPanel;
        [SerializeField] private Slider bossHPSlider;
        [SerializeField] private TextMeshProUGUI bossNameLabel;
        [SerializeField] private Image bossHPFill;
        [SerializeField] private Color bossHP1Color = Color.green;
        [SerializeField] private Color bossHP2Color = Color.yellow;
        [SerializeField] private Color bossHP3Color = Color.red;

        // ── Ability Cooldowns ──────────────────────────────────────────────────
        [Header("Ability Icons")]
        [SerializeField] private AbilityIconSlot[] abilitySlots;

        // ── Creepypasta Overlays ───────────────────────────────────────────────
        [Header("Creepypasta Effects")]
        [SerializeField] private TextMeshProUGUI creepypastaMessageText;
        [SerializeField] private CanvasGroup creepypastaCanvasGroup;
        [SerializeField] private TextMeshProUGUI subtitleText;
        [SerializeField] private TextMeshProUGUI hintText;

        // ── Memory / Image Flash ───────────────────────────────────────────────
        [Header("Memory Flash")]
        [SerializeField] private Image memoryImage;
        [SerializeField] private CanvasGroup memoryCanvasGroup;

        // ── Screen Fades ───────────────────────────────────────────────────────
        [Header("Fades")]
        [SerializeField] private CanvasGroup fadePanel;

        // ── Choice Wheel ───────────────────────────────────────────────────────
        [Header("Choice")]
        [SerializeField] private GameObject choicePanel;
        [SerializeField] private Button[] choiceButtons;
        [SerializeField] private TextMeshProUGUI[] choiceLabels;

        // ── Enemy HP bars (Mushnik's Ledger) ───────────────────────────────────
        [Header("Enemy HP")]
        [SerializeField] private GameObject enemyHPBarPrefab;
        private Dictionary<object, GameObject> enemyHPBars = new();

        // ── Lifecycle ──────────────────────────────────────────────────────────
        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        private void Start()
        {
            bossHPPanel?.SetActive(false);
            memoryCanvasGroup?.gameObject.SetActive(false);
            choicePanel?.SetActive(false);
        }

        private void Update()
        {
            UpdateAbilityCooldowns();
        }

        // ── Hearts ─────────────────────────────────────────────────────────────
        public void UpdateHearts(int current, int max)
        {
            if (heartContainer == null) return;

            // Clear existing
            foreach (Transform child in heartContainer)
                Destroy(child.gameObject);

            for (int i = 0; i < max; i++)
            {
                GameObject heart = Instantiate(i < current ? heartFullPrefab : heartEmptyPrefab,
                    heartContainer);
            }
        }

        /// <summary>Add thorn overlays as corruption progresses.</summary>
        public void SetCorruptionStage(int stage)
        {
            // Remove existing thorns
            foreach (Transform child in heartContainer)
            {
                if (child.gameObject.name.Contains("Thorn"))
                    Destroy(child.gameObject);
            }

            // Add thorns based on stage
            int thornCount = Mathf.Min(stage, thornThresholds.Length);
            for (int i = 0; i < thornCount; i++)
            {
                if (thornOverlayPrefab != null)
                    Instantiate(thornOverlayPrefab, heartContainer).name = $"Thorn_{i}";
            }
        }

        // ── Boss Health Bar ────────────────────────────────────────────────────
        public void ShowBossHealthBar(Bosses.BossBase boss)
        {
            bossHPPanel?.SetActive(true);
            bossHPSlider.value = 1f;
            bossNameLabel.text = boss.name.Replace("Boss", "").ToUpper();
        }

        public void UpdateBossHP(int current, int max)
        {
            if (bossHPSlider == null) return;
            float t = (float)current / max;
            bossHPSlider.value = t;
            if (bossHPFill != null)
                bossHPFill.color = Color.Lerp(bossHP3Color, bossHP1Color, t);
        }

        public void SetBossName(string name)
        {
            if (bossNameLabel != null)
                bossNameLabel.text = name;
        }

        public void HideBossHealthBar()
        {
            StartCoroutine(FadeOutBossBar());
        }

        private IEnumerator FadeOutBossBar()
        {
            yield return new WaitForSeconds(1f);
            bossHPPanel?.SetActive(false);
        }

        // ── Ability Cooldown Icons ─────────────────────────────────────────────
        private void UpdateAbilityCooldowns()
        {
            if (AbilityManager.Instance == null) return;
            foreach (var slot in abilitySlots)
                slot?.Update(AbilityManager.Instance);
        }

        public void ShowAbilityUnlockNotification(AbilityType ability)
        {
            StartCoroutine(ShowToast($"Ability Unlocked: {ability}", 3f));
        }

        // ── Creepypasta Messages ───────────────────────────────────────────────
        public void ShowCreepypastaMessage(string message, float duration)
        {
            StartCoroutine(CreepypastaMessageRoutine(message, duration));
        }

        private IEnumerator CreepypastaMessageRoutine(string message, float duration)
        {
            if (creepypastaMessageText != null)
                creepypastaMessageText.text = message;

            if (creepypastaCanvasGroup != null)
            {
                creepypastaCanvasGroup.alpha = 0;
                float t = 0;
                while (t < 0.5f) { t += Time.deltaTime; creepypastaCanvasGroup.alpha = t / 0.5f; yield return null; }
                yield return new WaitForSeconds(duration);
                t = 0;
                while (t < 0.5f) { t += Time.deltaTime; creepypastaCanvasGroup.alpha = 1f - t / 0.5f; yield return null; }
                creepypastaCanvasGroup.alpha = 0;
            }
        }

        public void ShowHint(string hint, float duration)
        {
            StartCoroutine(ShowToast(hint, duration, hintText));
        }

        public void ShowSubtitle(string text, float duration)
        {
            StartCoroutine(ShowToast(text, duration, subtitleText));
        }

        private IEnumerator ShowToast(string text, float duration, TextMeshProUGUI target = null)
        {
            var label = target ?? hintText;
            if (label == null) yield break;
            label.text = text;
            label.gameObject.SetActive(true);
            yield return new WaitForSeconds(duration);
            label.gameObject.SetActive(false);
        }

        // ── Ability-specific FX ────────────────────────────────────────────────
        public void ShowBloodContractFX(bool active)
        {
            // Red screen vignette (post-processing volume via script)
            // Implementation: enable/disable a CanvasGroup overlay
        }

        public void ShowPhotosynthesisFX(bool active)
        {
            // Green screen pulse
        }

        public void ShowNGPFX(bool active)
        {
            // Golden slow-time effect
        }

        // ── Memory Flash ───────────────────────────────────────────────────────
        public void ShowMemoryImage(Sprite sprite)
        {
            if (memoryImage == null) return;
            memoryImage.sprite = sprite;
            memoryCanvasGroup?.gameObject.SetActive(true);
            if (memoryCanvasGroup != null) memoryCanvasGroup.alpha = 1;
        }

        public void HideMemoryImage()
        {
            memoryCanvasGroup?.gameObject.SetActive(false);
        }

        public void FlashImage(string key, float duration)
        {
            StartCoroutine(QuickFlash(duration));
        }

        private IEnumerator QuickFlash(float duration)
        {
            if (memoryCanvasGroup != null)
            {
                memoryCanvasGroup.gameObject.SetActive(true);
                memoryCanvasGroup.alpha = 1;
                yield return new WaitForSeconds(duration);
                memoryCanvasGroup.alpha = 0;
                memoryCanvasGroup.gameObject.SetActive(false);
            }
        }

        // ── Screen Fades ───────────────────────────────────────────────────────
        public void FadeToBlack(float duration)  => StartCoroutine(Fade(0, 1, duration));
        public void FadeFromBlack(float duration) => StartCoroutine(Fade(1, 0, duration));
        public void FadeToWhite(float duration)
        {
            if (fadePanel != null)
                fadePanel.GetComponent<Image>().color = Color.white;
            FadeToBlack(duration);
        }

        private IEnumerator Fade(float from, float to, float duration)
        {
            if (fadePanel == null) yield break;
            fadePanel.gameObject.SetActive(true);
            float t = 0;
            while (t < duration)
            {
                t += Time.deltaTime;
                fadePanel.alpha = Mathf.Lerp(from, to, t / duration);
                yield return null;
            }
            fadePanel.alpha = to;
            if (to == 0) fadePanel.gameObject.SetActive(false);
        }

        // ── Glitch Effect ──────────────────────────────────────────────────────
        public void GlitchText(float duration)
        {
            StartCoroutine(TextGlitch(duration));
        }

        private IEnumerator TextGlitch(float duration)
        {
            float elapsed = 0;
            while (elapsed < duration)
            {
                // Random offset on UI elements - handled via CanvasGroup offset
                float x = UnityEngine.Random.Range(-5f, 5f);
                float y = UnityEngine.Random.Range(-3f, 3f);
                creepypastaCanvasGroup.GetComponent<RectTransform>().anchoredPosition
                    += new Vector2(x, y);
                elapsed += Time.deltaTime;
                yield return new WaitForSeconds(0.05f);
            }
        }

        // ── Choice Wheel ───────────────────────────────────────────────────────
        public void ShowChoiceWheel(string[] options, Action<int> onChoice)
        {
            choicePanel?.SetActive(true);
            for (int i = 0; i < choiceButtons.Length; i++)
            {
                if (i < options.Length)
                {
                    choiceButtons[i].gameObject.SetActive(true);
                    if (choiceLabels.Length > i)
                        choiceLabels[i].text = options[i];
                    int captured = i;
                    choiceButtons[i].onClick.RemoveAllListeners();
                    choiceButtons[i].onClick.AddListener(() =>
                    {
                        choicePanel.SetActive(false);
                        onChoice?.Invoke(captured);
                    });
                }
                else
                {
                    choiceButtons[i].gameObject.SetActive(false);
                }
            }
        }

        // ── Enemy HP Bars (Mushnik's Ledger) ───────────────────────────────────
        public void ShowEnemyHPBar(object enemy, int current, int max, string weakness)
        {
            // Implementation: world-space canvas bar above enemy
            // Managed by dictionary to avoid duplicate bars
        }
    }

    /// <summary>Serializable slot pairing an AbilityType to a UI icon+cooldown fill.</summary>
    [Serializable]
    public class AbilityIconSlot
    {
        public AbilityType ability;
        public Image cooldownFill;
        public Image icon;
        public CanvasGroup lockedOverlay;

        public void Update(AbilityManager am)
        {
            bool has = am.HasAbility(ability);
            if (lockedOverlay != null) lockedOverlay.alpha = has ? 0 : 1;
            if (!has || cooldownFill == null) return;

            float remaining = am.GetCooldownRemaining(ability);
            // This requires knowing the max cooldown per ability - simplified here
            cooldownFill.fillAmount = remaining > 0 ? remaining / 20f : 0;
        }
    }
}
