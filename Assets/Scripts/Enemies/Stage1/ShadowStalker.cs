using System.Collections;
using UnityEngine;

namespace FeedMe.Enemies
{
    /// <summary>
    /// Stage 1-3: Skid Row After Dark.
    /// Shadow stalker: nearly invisible, teleports behind the player,
    /// then does a fast strike. Blood Contract ability reveals its true position.
    /// </summary>
    public class ShadowStalker : EnemyBase
    {
        [SerializeField] private float teleportInterval = 4f;
        [SerializeField] private float strikeSpeed = 15f;
        [SerializeField] private float normalAlpha = 0.15f;
        [SerializeField] private float revealedAlpha = 1f;

        private float teleportTimer;
        private bool isStriking;
        private bool isRevealed;

        protected override void Awake()
        {
            base.Awake();
            maxHP = 40;
            moveSpeed = 3f;
            aggroRange = 10f;
            attackRange = 1f;
            attackCooldown = 3f;
            weaknessDescription = "Blood Contract reveals true position";
            weaknessAbility = AbilityType.BloodContract;
        }

        protected override void Start()
        {
            base.Start();
            SetAlpha(normalAlpha);
            teleportTimer = teleportInterval;
        }

        protected override void Update()
        {
            base.Update();

            // Blood Contract reveals this enemy
            isRevealed = AbilityManager.Instance?.HasAbility(AbilityType.BloodContract) == true;
            SetAlpha(isRevealed ? revealedAlpha : normalAlpha);

            if (isAggro && !isStriking)
            {
                teleportTimer -= Time.deltaTime;
                if (teleportTimer <= 0)
                {
                    StartCoroutine(TeleportAndStrike());
                    teleportTimer = teleportInterval;
                }
            }
        }

        protected override void PatrolBehaviour()
        {
            rb.linearVelocity = Vector2.zero; // Stalkers don't patrol visibly
        }

        protected override void PerformAttack()
        {
            // Strike handled by TeleportAndStrike
        }

        private IEnumerator TeleportAndStrike()
        {
            isStriking = true;

            if (player == null) { isStriking = false; yield break; }

            // Teleport behind player
            float side = player.GetComponent<SpriteRenderer>()?.flipX == true ? 1 : -1;
            Vector3 behindPlayer = player.position + new Vector3(side * 1.5f, 0, 0);
            transform.position = behindPlayer;

            yield return new WaitForSeconds(0.2f);

            // Fast strike
            Vector2 dir = (player.position - transform.position).normalized;
            float elapsed = 0;
            while (elapsed < 0.25f)
            {
                rb.linearVelocity = dir * strikeSpeed;
                elapsed += Time.deltaTime;
                yield return null;
            }
            rb.linearVelocity = Vector2.zero;

            isStriking = false;
        }

        private void SetAlpha(float a)
        {
            if (spriteRenderer != null)
            {
                Color c = spriteRenderer.color;
                c.a = a;
                spriteRenderer.color = c;
            }
        }
    }
}
