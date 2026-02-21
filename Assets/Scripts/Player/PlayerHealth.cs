using System;
using System.Collections;
using UnityEngine;

namespace FeedMe.Player
{
    /// <summary>
    /// Manages Seymour's health, damage, death, and the
    /// creepypasta "death counter" that Mushnik tracks.
    /// </summary>
    public class PlayerHealth : MonoBehaviour
    {
        [Header("Health")]
        [SerializeField] private int maxHearts = 6;
        [SerializeField] private float invincibilityDuration = 1.2f;

        [Header("Death / Loop")]
        [SerializeField] private string respawnSceneName = "MushniksShop";
        [SerializeField] private AudioClip deathSound;

        // Tracked across sessions - stored in save data
        public static int LifetimeDeathCount { get; private set; }

        private int currentHearts;
        private bool isInvincible;
        private float dotTimer;
        private float dotDamagePerSecond;
        private bool dotActive;

        public int CurrentHearts => currentHearts;
        public int MaxHearts => maxHearts;

        public event Action<int, int> OnHealthChanged;  // (current, max)
        public event Action OnPlayerDied;

        private void Start()
        {
            currentHearts = maxHearts;
            OnHealthChanged?.Invoke(currentHearts, maxHearts);
        }

        private void Update()
        {
            HandleDOT();
        }

        // ── Damage ─────────────────────────────────────────────────────────────
        public void TakeDamage(int amount)
        {
            if (isInvincible) return;

            currentHearts = Mathf.Max(0, currentHearts - amount);
            OnHealthChanged?.Invoke(currentHearts, maxHearts);

            if (currentHearts <= 0)
                StartCoroutine(Die());
            else
                StartCoroutine(InvincibilityFrames());
        }

        public void Heal(int amount)
        {
            currentHearts = Mathf.Min(maxHearts, currentHearts + amount);
            OnHealthChanged?.Invoke(currentHearts, maxHearts);
        }

        /// <summary>Blood Contract: spend health to activate effect.</summary>
        public bool SpendHealth(int amount)
        {
            if (currentHearts <= amount) return false;
            currentHearts -= amount;
            OnHealthChanged?.Invoke(currentHearts, maxHearts);
            return true;
        }

        public void AddMaxHeart()
        {
            maxHearts++;
            currentHearts++;
            OnHealthChanged?.Invoke(currentHearts, maxHearts);
        }

        // ── Damage Over Time ───────────────────────────────────────────────────
        /// <summary>Toxic pollen, acid pools, spore clouds.</summary>
        public void ApplyDOT(float damagePerSecond, float duration)
        {
            dotDamagePerSecond = damagePerSecond;
            dotTimer = duration;
            dotActive = true;
        }

        private void HandleDOT()
        {
            if (!dotActive) return;
            dotTimer -= Time.deltaTime;
            if (dotTimer <= 0)
            {
                dotActive = false;
                return;
            }
            // Apply fractional damage, floor to hearts
            if (Time.frameCount % 60 == 0)
                TakeDamage(Mathf.FloorToInt(dotDamagePerSecond));
        }

        // ── Death & Loop ───────────────────────────────────────────────────────
        private IEnumerator Die()
        {
            LifetimeDeathCount++;
            SaveSystem.SaveDeathCount(LifetimeDeathCount);

            OnPlayerDied?.Invoke();
            AudioSource.PlayClipAtPoint(deathSound, transform.position);

            // Creepypasta Mushnik dialogue triggers via NarrativeManager
            NarrativeManager.Instance?.TriggerMushniklDeathLine(LifetimeDeathCount);

            yield return new WaitForSeconds(2f);
            UnityEngine.SceneManagement.SceneManager.LoadScene(respawnSceneName);
        }

        private IEnumerator InvincibilityFrames()
        {
            isInvincible = true;
            // Flash effect handled by PlayerAnimator
            yield return new WaitForSeconds(invincibilityDuration);
            isInvincible = false;
        }

        // ── Photosynthesis Heal Zone ───────────────────────────────────────────
        private bool inLightZone;

        public void EnterLightZone() => inLightZone = true;
        public void ExitLightZone() => inLightZone = false;

        private void LateUpdate()
        {
            // Photosynthesis: heal 1 heart every 5 seconds in light
            if (inLightZone && Time.frameCount % 300 == 0)
                Heal(1);
        }
    }
}
