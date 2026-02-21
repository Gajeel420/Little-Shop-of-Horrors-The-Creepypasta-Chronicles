using System.Collections.Generic;
using UnityEngine;

namespace FeedMe
{
    /// <summary>
    /// Handles attack collision detection, damage calculations,
    /// and the damage boost stack (Blood Contract, Feed Me Seymour, etc.).
    /// Attach to the Player's attack hitbox GameObject.
    /// </summary>
    public class CombatManager : MonoBehaviour
    {
        public static CombatManager Instance { get; private set; }

        [Header("Base Attack")]
        [SerializeField] private int baseAttackDamage = 10;
        [SerializeField] private LayerMask enemyLayer;
        [SerializeField] private LayerMask bossLayer;
        [SerializeField] private float attackHitboxRadius = 0.8f;
        [SerializeField] private Transform attackPoint;

        [Header("Hyperrealistic Blood (Critical Hit)")]
        [SerializeField] private ParticleSystem critBloodFX;  // "Hyperrealistic Blood" effect
        [SerializeField] private float critChance = 0.1f;
        [SerializeField] private int critMultiplier = 3;

        private List<DamageBoostToken> damageBoosts = new();
        private AbilityManager abilityManager;

        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
        }

        private void Start()
        {
            abilityManager = AbilityManager.Instance;
        }

        // ── Attack Execution ───────────────────────────────────────────────────
        /// <summary>Called by PlayerAnimator animation event at hit frame.</summary>
        public void ExecuteAttack()
        {
            if (attackPoint == null) return;

            Collider2D[] hits = Physics2D.OverlapCircleAll(
                attackPoint.position, attackHitboxRadius, enemyLayer | bossLayer);

            int damage = CalculateDamage();
            bool isCrit = Random.value < critChance;
            if (isCrit)
            {
                damage *= critMultiplier;
                critBloodFX?.Play(); // Creepypasta: "Hyperrealistic Blood"
            }

            foreach (var hit in hits)
            {
                // Enemies
                hit.GetComponent<Enemies.EnemyBase>()?.TakeDamage(damage);
                // Bosses
                hit.GetComponent<Bosses.BossBase>()?.TakeDamage(damage, hit.ClosestPoint(attackPoint.position));
                // Specific boss weak points
                hit.GetComponent<Bosses.OrinBoss>()?.HitMask();
                hit.GetComponent<Bosses.Patrick.PatrickBoss>()?.HitBulb();
                hit.GetComponent<Bosses.AudreyII.MirrorWeakPoint>()?.GetComponent<Bosses.AudreyII.MirrorWeakPoint>();
                // Destructibles (gas canisters, etc.)
                hit.GetComponent<Bosses.IDestructible>()?.Destroy();
            }
        }

        private int CalculateDamage()
        {
            int dmg = baseAttackDamage;

            // Apply boost stack
            foreach (var boost in damageBoosts)
                dmg = Mathf.RoundToInt(dmg * boost.Multiplier);

            // Feed Me Seymour one-shot boost
            if (abilityManager != null)
            {
                bool feedMe = abilityManager.UseFeedMeSeymour(out int mult);
                if (feedMe) dmg *= mult;
            }

            // New Game+ half cost
            if (GameManager.Instance?.IsNewGamePlus == true)
                dmg = Mathf.RoundToInt(dmg * 1.5f);

            return dmg;
        }

        // ── Damage Boost Stack ─────────────────────────────────────────────────
        public void PushDamageBoost(DamageBoostToken token)  => damageBoosts.Add(token);
        public void RemoveDamageBoost(DamageBoostToken token) => damageBoosts.Remove(token);

        // ── Gizmos ────────────────────────────────────────────────────────────
        private void OnDrawGizmosSelected()
        {
            if (attackPoint == null) return;
            Gizmos.color = Color.red;
            Gizmos.DrawWireSphere(attackPoint.position, attackHitboxRadius);
        }
    }
}
