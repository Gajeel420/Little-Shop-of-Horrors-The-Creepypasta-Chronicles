using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace FeedMe
{
    /// <summary>
    /// Central ability registry.  Tracks unlocked abilities, enforces cooldowns,
    /// and drives the active-ability effects for Blood Contract and Photosynthesis.
    /// </summary>
    public class AbilityManager : MonoBehaviour
    {
        // ── Singleton ──────────────────────────────────────────────────────────
        public static AbilityManager Instance { get; private set; }

        // ── Inspector ──────────────────────────────────────────────────────────
        [Header("Blood Contract")]
        [SerializeField] private float bloodContractDuration    = 5f;
        [SerializeField] private float bloodContractCooldown    = 20f;
        [SerializeField] private int   bloodContractHPCost      = 2;
        [SerializeField] private LayerMask hiddenPlatformLayer;

        [Header("Photosynthesis")]
        [SerializeField] private float photosynthesisDuration   = 8f;
        [SerializeField] private float photosynthesisCooldown   = 15f;
        [SerializeField] private GameObject tempPlatformPrefab;

        [Header("Feed Me Seymour")]
        [SerializeField] private int   feedMeHPCost             = 3;
        [SerializeField] private int   feedMeDamageMultiplier   = 5;

        [Header("Somewhere That's Green (NG+)")]
        [SerializeField] private float ngpSlowTimeScale         = 0.4f;
        [SerializeField] private float ngpDuration              = 6f;

        // ── Private state ──────────────────────────────────────────────────────
        private HashSet<AbilityType> unlockedAbilities = new();
        private Dictionary<AbilityType, float> cooldownTimers = new();
        private Player.PlayerHealth health;
        private GameObject activeTempPlatform;

        public event Action<AbilityType> OnAbilityUnlocked;

        // ── Lifecycle ──────────────────────────────────────────────────────────
        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);

            health = GetComponent<Player.PlayerHealth>();
        }

        private void Update()
        {
            // Tick all active cooldowns
            var keys = new List<AbilityType>(cooldownTimers.Keys);
            foreach (var key in keys)
            {
                cooldownTimers[key] -= Time.deltaTime;
                if (cooldownTimers[key] <= 0)
                    cooldownTimers.Remove(key);
            }
        }

        // ── Query ──────────────────────────────────────────────────────────────
        public bool HasAbility(AbilityType ability) => unlockedAbilities.Contains(ability);

        public bool IsOnCooldown(AbilityType ability) => cooldownTimers.ContainsKey(ability);

        public float GetCooldownRemaining(AbilityType ability) =>
            cooldownTimers.TryGetValue(ability, out float t) ? t : 0f;

        // ── Unlock ─────────────────────────────────────────────────────────────
        public void UnlockAbility(AbilityType ability)
        {
            if (unlockedAbilities.Add(ability))
            {
                OnAbilityUnlocked?.Invoke(ability);
                SaveSystem.SaveAbilities(unlockedAbilities);
                HUDManager.Instance?.ShowAbilityUnlockNotification(ability);
            }
        }

        /// <summary>Restore abilities from a loaded save file.</summary>
        public void LoadAbilities(IEnumerable<AbilityType> saved)
        {
            foreach (var a in saved)
                unlockedAbilities.Add(a);
        }

        // ── Active Ability: Blood Contract ─────────────────────────────────────
        public void UseBloodContract()
        {
            if (IsOnCooldown(AbilityType.BloodContract)) return;
            if (!health.SpendHealth(bloodContractHPCost)) return;

            StartCoroutine(BloodContractRoutine());
        }

        private IEnumerator BloodContractRoutine()
        {
            SetCooldown(AbilityType.BloodContract, bloodContractCooldown);

            // Reveal hidden platforms
            int originalMask = Camera.main.cullingMask;
            Camera.main.cullingMask |= hiddenPlatformLayer.value;
            HUDManager.Instance?.ShowBloodContractFX(true);

            // Player is briefly invincible and deals bonus damage
            GetComponent<Player.PlayerController>()?.ApplyControlReversal(0); // clears reversed
            DamageBoostToken boost = new DamageBoostToken(2f); // x2 damage
            CombatManager.Instance?.PushDamageBoost(boost);

            yield return new WaitForSeconds(bloodContractDuration);

            Camera.main.cullingMask = originalMask;
            HUDManager.Instance?.ShowBloodContractFX(false);
            CombatManager.Instance?.RemoveDamageBoost(boost);
        }

        // ── Active Ability: Photosynthesis ─────────────────────────────────────
        public void UsePhotosynthesis()
        {
            if (IsOnCooldown(AbilityType.Photosynthesis)) return;

            StartCoroutine(PhotosynthesisRoutine());
        }

        private IEnumerator PhotosynthesisRoutine()
        {
            SetCooldown(AbilityType.Photosynthesis, photosynthesisCooldown);
            HUDManager.Instance?.ShowPhotosynthesisFX(true);

            // Spawn a temporary platform beneath the player
            if (tempPlatformPrefab != null)
            {
                Vector3 spawnPos = transform.position + Vector3.down * 0.5f;
                activeTempPlatform = Instantiate(tempPlatformPrefab, spawnPos, Quaternion.identity);
            }

            // Convert nearby acid pools to safe ground (acid pools listen to this event)
            AcidPool.ConvertNearby(transform.position, 4f);

            yield return new WaitForSeconds(photosynthesisDuration);

            if (activeTempPlatform != null)
                Destroy(activeTempPlatform);

            HUDManager.Instance?.ShowPhotosynthesisFX(false);
        }

        // ── Active Ability: Feed Me Seymour ────────────────────────────────────
        public bool UseFeedMeSeymour(out int damageMultiplier)
        {
            damageMultiplier = 0;
            if (!HasAbility(AbilityType.FeedMeSeymour)) return false;
            if (!health.SpendHealth(feedMeHPCost)) return false;

            damageMultiplier = feedMeDamageMultiplier;
            return true;
        }

        // ── Active Ability: Somewhere That's Green (NG+) ───────────────────────
        public void UseSomewhereThatSGreen()
        {
            if (!HasAbility(AbilityType.SomewhereThatSGreen)) return;
            if (IsOnCooldown(AbilityType.SomewhereThatSGreen)) return;

            StartCoroutine(NGPRoutine());
        }

        private IEnumerator NGPRoutine()
        {
            SetCooldown(AbilityType.SomewhereThatSGreen, 30f);
            Time.timeScale = ngpSlowTimeScale;
            HUDManager.Instance?.ShowNGPFX(true);

            yield return new WaitForSecondsRealtime(ngpDuration);

            Time.timeScale = 1f;
            HUDManager.Instance?.ShowNGPFX(false);
        }

        // ── Helpers ────────────────────────────────────────────────────────────
        private void SetCooldown(AbilityType ability, float duration)
        {
            cooldownTimers[ability] = duration;
        }
    }

    /// <summary>Token used to stack and remove temporary damage boosts.</summary>
    public class DamageBoostToken
    {
        public float Multiplier { get; }
        public DamageBoostToken(float multiplier) => Multiplier = multiplier;
    }
}
