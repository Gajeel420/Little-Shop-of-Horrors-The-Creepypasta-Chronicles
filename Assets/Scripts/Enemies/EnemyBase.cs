using System.Collections;
using UnityEngine;

namespace FeedMe.Enemies
{
    /// <summary>
    /// Base class for all non-boss enemies.
    /// Handles health, patrol, aggro range, damage dealing, and death drops.
    /// Mushnik's Ledger ability makes HP and weakness visible via HUD overlay.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public abstract class EnemyBase : MonoBehaviour
    {
        [Header("Stats")]
        [SerializeField] protected int maxHP = 30;
        [SerializeField] protected int contactDamage = 1;
        [SerializeField] protected float moveSpeed = 2.5f;
        [SerializeField] protected float aggroRange = 7f;
        [SerializeField] protected float attackRange = 1.5f;
        [SerializeField] protected float attackCooldown = 1.5f;

        [Header("Drops")]
        [SerializeField] protected GameObject dropPrefab;
        [SerializeField] [Range(0f, 1f)] protected float dropChance = 0.3f;

        [Header("Ledger (Mushnik's Ledger ability)")]
        [SerializeField] protected string weaknessDescription = "Strike from above";
        [SerializeField] protected AbilityType? weaknessAbility = null;

        protected int currentHP;
        protected bool isAggro;
        protected bool isDead;
        protected float attackTimer;
        protected Rigidbody2D rb;
        protected Transform player;
        protected Animator animator;
        protected SpriteRenderer spriteRenderer;

        protected static readonly int WalkAnim  = Animator.StringToHash("Walking");
        protected static readonly int AttackAnim = Animator.StringToHash("Attack");
        protected static readonly int DeathAnim = Animator.StringToHash("Death");

        // ── Lifecycle ──────────────────────────────────────────────────────────
        protected virtual void Awake()
        {
            rb = GetComponent<Rigidbody2D>();
            animator = GetComponent<Animator>();
            spriteRenderer = GetComponent<SpriteRenderer>();
        }

        protected virtual void Start()
        {
            currentHP = maxHP;
            player = GameObject.FindGameObjectWithTag("Player")?.transform;
        }

        protected virtual void Update()
        {
            if (isDead) return;

            attackTimer -= Time.deltaTime;
            UpdateAggro();

            if (isAggro)
                AggroBehaviour();
            else
                PatrolBehaviour();

            // Show HP bar if Mushnik's Ledger is active
            if (AbilityManager.Instance?.HasAbility(AbilityType.MushniksLedger) == true)
                HUDManager.Instance?.ShowEnemyHPBar(this, currentHP, maxHP, weaknessDescription);
        }

        // ── AI ─────────────────────────────────────────────────────────────────
        private void UpdateAggro()
        {
            if (player == null) return;
            float dist = Vector2.Distance(transform.position, player.position);
            isAggro = dist <= aggroRange;
        }

        protected virtual void PatrolBehaviour()
        {
            // Default: pace back and forth
            rb.linearVelocity = new Vector2(moveSpeed * (spriteRenderer.flipX ? -1 : 1), rb.linearVelocity.y);
        }

        protected virtual void AggroBehaviour()
        {
            if (player == null) return;
            float dist = Vector2.Distance(transform.position, player.position);

            // Move toward player
            float dir = player.position.x > transform.position.x ? 1 : -1;
            rb.linearVelocity = new Vector2(dir * moveSpeed * 1.5f, rb.linearVelocity.y);
            spriteRenderer.flipX = dir < 0;

            if (dist <= attackRange && attackTimer <= 0)
            {
                PerformAttack();
                attackTimer = attackCooldown;
            }

            animator?.SetBool(WalkAnim, true);
        }

        protected abstract void PerformAttack();

        // ── Damage ─────────────────────────────────────────────────────────────
        public virtual void TakeDamage(int amount)
        {
            if (isDead) return;
            currentHP -= amount;
            StartCoroutine(HitFlash());

            if (currentHP <= 0)
                StartCoroutine(Die());
        }

        private IEnumerator HitFlash()
        {
            if (spriteRenderer != null)
            {
                spriteRenderer.color = Color.red;
                yield return new WaitForSeconds(0.08f);
                spriteRenderer.color = Color.white;
            }
        }

        protected virtual IEnumerator Die()
        {
            isDead = true;
            rb.linearVelocity = Vector2.zero;
            animator?.SetTrigger(DeathAnim);

            // Drop loot
            if (dropPrefab != null && Random.value <= dropChance)
                Instantiate(dropPrefab, transform.position, Quaternion.identity);

            yield return new WaitForSeconds(0.8f);
            Destroy(gameObject);
        }

        // ── Contact Damage ─────────────────────────────────────────────────────
        protected virtual void OnCollisionEnter2D(Collision2D col)
        {
            if (isDead) return;
            col.gameObject.GetComponent<Player.PlayerHealth>()?.TakeDamage(contactDamage);
        }
    }
}
