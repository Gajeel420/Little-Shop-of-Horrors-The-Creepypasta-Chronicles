using System.Collections;
using UnityEngine;

namespace FeedMe.Enemies
{
    /// <summary>
    /// Stage 2-2: Client Corridors.
    /// Contract Wraith: floats toward player, throws binding contract papers.
    /// If player is hit, they are frozen briefly while text scrolls across the screen.
    /// One of the three customers that loops endlessly, becoming more distorted each loop.
    /// </summary>
    public class ContractWraith : EnemyBase
    {
        [SerializeField] private GameObject contractPaperPrefab;
        [SerializeField] private float floatAmplitude = 0.5f;
        [SerializeField] private float floatFrequency = 1.5f;
        [SerializeField] private int distortionLevel = 0;  // Increments each loop

        private float startY;
        private float loopTimer;

        // Creepypasta: 3 wraiths in infinite corridor loop
        public static int GlobalLoopCount = 0;

        protected override void Awake()
        {
            base.Awake();
            maxHP = 35;
            moveSpeed = 2f;
            aggroRange = 8f;
            attackRange = 5f;
            attackCooldown = 2f;
            weaknessDescription = "Audrey's Locket breaks their illusion loop";
            weaknessAbility = AbilityType.AudreysLocket;
        }

        protected override void Start()
        {
            base.Start();
            startY = transform.position.y;
            distortionLevel = GlobalLoopCount;
            ApplyDistortion();
        }

        private void ApplyDistortion()
        {
            if (spriteRenderer == null) return;
            // Each loop, wraith becomes more visually wrong
            float greenTint = Mathf.Clamp01(distortionLevel * 0.15f);
            spriteRenderer.color = new Color(1f - greenTint, 1f, 1f - greenTint);
            transform.localScale = Vector3.one * (1f + distortionLevel * 0.05f); // slowly grows
        }

        protected override void AggroBehaviour()
        {
            // Float toward player
            if (player == null) return;
            Vector2 dir = (player.position - transform.position).normalized;
            rb.linearVelocity = dir * moveSpeed;

            // Sinusoidal float
            Vector3 pos = transform.position;
            pos.y = startY + Mathf.Sin(Time.time * floatFrequency) * floatAmplitude;

            float dist = Vector2.Distance(transform.position, player.position);
            if (dist <= attackRange && attackTimer <= 0)
            {
                PerformAttack();
                attackTimer = attackCooldown;
            }
        }

        protected override void PerformAttack()
        {
            if (contractPaperPrefab == null || player == null) return;
            Vector2 dir = (player.position - transform.position).normalized;
            GameObject paper = Instantiate(contractPaperPrefab, transform.position, Quaternion.identity);
            paper.GetComponent<Rigidbody2D>()?.AddForce(dir * 9f, ForceMode2D.Impulse);
        }

        protected override IEnumerator Die()
        {
            // On death in the looping corridor, increment loop count and respawn
            GlobalLoopCount++;
            yield return StartCoroutine(base.Die());
        }

        public override void TakeDamage(int amount)
        {
            // Audrey's Locket: reveal true form and instant kill
            bool hasLocket = AbilityManager.Instance?.HasAbility(AbilityType.AudreysLocket) ?? false;
            base.TakeDamage(hasLocket ? maxHP : amount);
        }
    }
}
