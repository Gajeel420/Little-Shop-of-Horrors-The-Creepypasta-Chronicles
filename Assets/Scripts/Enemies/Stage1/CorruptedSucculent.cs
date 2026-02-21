using UnityEngine;

namespace FeedMe.Enemies
{
    /// <summary>
    /// Stage 1-1 enemy: Corrupted Succulent.
    /// Stays stationary, fires thorn projectiles in a burst when player enters range.
    /// Dies in one hit from Pruning Shears (ability weakness).
    /// </summary>
    public class CorruptedSucculent : EnemyBase
    {
        [SerializeField] private GameObject thornPrefab;
        [SerializeField] private int thornBurstCount = 3;
        [SerializeField] private float thornSpeed = 8f;

        protected override void Awake()
        {
            base.Awake();
            maxHP = 20;
            contactDamage = 1;
            moveSpeed = 0;
            aggroRange = 6f;
            attackRange = 6f;
            attackCooldown = 2.5f;
            weaknessDescription = "Pruning Shears - one hit kill";
            weaknessAbility = AbilityType.PruningShears;
        }

        protected override void PatrolBehaviour()
        {
            // Stationary - no patrol
        }

        protected override void PerformAttack()
        {
            if (thornPrefab == null || player == null) return;

            // Burst of thorns spread around player's position
            for (int i = 0; i < thornBurstCount; i++)
            {
                float angle = (360f / thornBurstCount) * i;
                Vector2 dir = new Vector2(
                    Mathf.Cos(angle * Mathf.Deg2Rad),
                    Mathf.Sin(angle * Mathf.Deg2Rad));

                GameObject thorn = Instantiate(thornPrefab, transform.position, Quaternion.identity);
                thorn.GetComponent<Rigidbody2D>()?.AddForce(dir * thornSpeed, ForceMode2D.Impulse);
                Destroy(thorn, 3f);
            }
        }

        public override void TakeDamage(int amount)
        {
            // Instant kill when hit with Pruning Shears
            bool hasPruning = AbilityManager.Instance?.HasAbility(AbilityType.PruningShears) ?? false;
            base.TakeDamage(hasPruning ? maxHP : amount);
        }
    }
}
