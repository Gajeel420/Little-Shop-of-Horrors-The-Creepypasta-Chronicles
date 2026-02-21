using System;
using System.Collections;
using UnityEngine;

namespace FeedMe.Bosses
{
    /// <summary>
    /// Shared base for all three bosses.
    /// Handles HP, phase transitions, invincibility windows,
    /// death animation sequencing, and reward granting.
    /// </summary>
    public abstract class BossBase : MonoBehaviour
    {
        [Header("Boss Stats")]
        [SerializeField] protected int maxHP = 500;
        [SerializeField] protected float[] phaseThresholds;   // e.g. {0.7f, 0.4f} = 70%, 40%
        [SerializeField] protected float hitInvincibilityTime = 0.08f;

        [Header("Reward")]
        [SerializeField] protected AbilityType rewardAbility;
        [SerializeField] protected AudioClip defeatSting;

        protected int currentHP;
        protected int currentPhase;
        protected bool isDefeated;
        protected bool isTransitioning;

        protected Transform player;
        protected Animator animator;
        protected AudioSource audioSource;

        public event Action<BossBase> OnBossDefeated;
        public event Action<int>      OnPhaseChanged;   // passes new phase index

        // ── Lifecycle ──────────────────────────────────────────────────────────
        protected virtual void Awake()
        {
            animator    = GetComponent<Animator>();
            audioSource = GetComponent<AudioSource>();
        }

        protected virtual void Start()
        {
            currentHP    = maxHP;
            currentPhase = 0;
            player       = GameObject.FindGameObjectWithTag("Player")?.transform;

            HUDManager.Instance?.ShowBossHealthBar(this);
            OnBossStart();
        }

        // ── Abstract interface ─────────────────────────────────────────────────
        protected abstract void OnBossStart();
        protected abstract IEnumerator Phase1Behaviour();
        protected abstract IEnumerator PhaseTransition(int newPhase);
        protected abstract IEnumerator DeathSequence();

        // ── Damage ─────────────────────────────────────────────────────────────
        public virtual void TakeDamage(int amount, Vector2 hitPoint)
        {
            if (isDefeated || isTransitioning) return;

            currentHP = Mathf.Max(0, currentHP - amount);
            HUDManager.Instance?.UpdateBossHP(currentHP, maxHP);
            PlayHitEffect(hitPoint);

            CheckPhaseTransition();

            if (currentHP <= 0)
                StartCoroutine(Defeat());
        }

        protected virtual void PlayHitEffect(Vector2 hitPoint)
        {
            // Override in subclasses for specific hit particles/sounds
        }

        // ── Phase Logic ────────────────────────────────────────────────────────
        private void CheckPhaseTransition()
        {
            if (phaseThresholds == null) return;
            if (currentPhase >= phaseThresholds.Length) return;

            float hpPercent = (float)currentHP / maxHP;
            if (hpPercent <= phaseThresholds[currentPhase])
            {
                int nextPhase = currentPhase + 1;
                StartCoroutine(TransitionToPhase(nextPhase));
            }
        }

        private IEnumerator TransitionToPhase(int newPhase)
        {
            isTransitioning = true;
            currentPhase = newPhase;
            OnPhaseChanged?.Invoke(newPhase);
            StopAllAttackCoroutines();

            yield return StartCoroutine(PhaseTransition(newPhase));

            isTransitioning = false;
            StartPhaseLoop(newPhase);
        }

        protected virtual void StartPhaseLoop(int phase)
        {
            // Override in subclasses to start correct coroutine per phase
        }

        protected virtual void StopAllAttackCoroutines()
        {
            StopAllCoroutines();
        }

        // ── Defeat ─────────────────────────────────────────────────────────────
        protected IEnumerator Defeat()
        {
            if (isDefeated) yield break;
            isDefeated = true;

            StopAllAttackCoroutines();
            audioSource?.PlayOneShot(defeatSting);

            yield return StartCoroutine(DeathSequence());

            AbilityManager.Instance?.UnlockAbility(rewardAbility);
            NarrativeManager.Instance?.TriggerBossDefeated(GetType().Name);
            OnBossDefeated?.Invoke(this);

            HUDManager.Instance?.HideBossHealthBar();
            Destroy(gameObject, 0.5f);
        }

        // ── Utilities ──────────────────────────────────────────────────────────
        protected bool IsPlayerInRange(float range) =>
            player != null && Vector2.Distance(transform.position, player.position) <= range;

        protected Vector2 DirectionToPlayer() =>
            player != null
                ? (player.position - transform.position).normalized
                : Vector2.right;

        protected float HPPercent => (float)currentHP / maxHP;
    }
}
