using System.Collections;
using UnityEngine;

namespace FeedMe.Enemies
{
    /// <summary>
    /// Tooth Golem: summoned by Orin in Phase 2.
    /// Seeks the player; drops a temporary damage boost on death.
    /// Multiple golems can merge into a larger golem if left alone.
    /// </summary>
    public class ToothGolem : EnemyBase
    {
        [SerializeField] private GameObject damageBoostDropPrefab;
        [SerializeField] private float mergeCheckInterval = 5f;
        [SerializeField] private float mergeRange = 2f;
        [SerializeField] private GameObject mergedGolemPrefab;

        private float mergeTimer;

        protected override void Awake()
        {
            base.Awake();
            maxHP = 15;
            contactDamage = 1;
            moveSpeed = 4f;
            aggroRange = 20f;   // Always seeks player
            attackRange = 1f;
            attackCooldown = 1f;
            dropPrefab = damageBoostDropPrefab;
            dropChance = 1f; // Always drops
            weaknessDescription = "One hit - but they merge if ignored";
        }

        protected override void Update()
        {
            base.Update();

            mergeTimer -= Time.deltaTime;
            if (mergeTimer <= 0)
            {
                CheckMerge();
                mergeTimer = mergeCheckInterval;
            }
        }

        protected override void PerformAttack()
        {
            player?.GetComponent<Player.PlayerHealth>()?.TakeDamage(contactDamage);
        }

        private void CheckMerge()
        {
            Collider2D[] nearby = Physics2D.OverlapCircleAll(transform.position, mergeRange);
            ToothGolem partner = null;
            foreach (var col in nearby)
            {
                if (col.gameObject == gameObject) continue;
                ToothGolem g = col.GetComponent<ToothGolem>();
                if (g != null) { partner = g; break; }
            }

            if (partner != null)
            {
                // Merge into larger golem
                Vector3 midpoint = (transform.position + partner.transform.position) * 0.5f;
                Instantiate(mergedGolemPrefab, midpoint, Quaternion.identity);
                Destroy(partner.gameObject);
                Destroy(gameObject);
            }
        }

        public override void TakeDamage(int amount)
        {
            // Golems die in one hit always
            base.TakeDamage(maxHP);
        }
    }
}
