using System.Collections;
using UnityEngine;

namespace FeedMe.Bosses
{
    public enum HydraHeadType { Red, Blue, Green, Yellow, Center }

    /// <summary>
    /// One of five Audrey II hydra heads, each with a unique attack.
    /// Red=Fire, Blue=Ice, Green=Poison, Yellow=Lightning, Center=Coordinator.
    /// Destroying each reveals a memory flashback.
    /// </summary>
    public class HydraHead : MonoBehaviour
    {
        [SerializeField] public HydraHeadType headType;
        [SerializeField] public string MemoryKey;  // Passed to NarrativeManager for flashback
        [SerializeField] private int headHP = 100;
        [SerializeField] private float attackInterval = 3f;

        [Header("Attack Prefabs")]
        [SerializeField] private GameObject projectilePrefab;   // Fire/Ice/Poison/Lightning bolt
        [SerializeField] private ParticleSystem breathParticles;

        private int currentHP;
        private bool isActive;
        private bool isDestroyed;
        private AudreyIIBoss boss;
        private Transform player;
        private Animator animator;

        private void Awake()
        {
            animator = GetComponent<Animator>();
        }

        public void Activate(AudreyIIBoss parentBoss)
        {
            boss = parentBoss;
            isActive = true;
            currentHP = headHP;
            player = GameObject.FindGameObjectWithTag("Player")?.transform;
            StartCoroutine(AttackLoop());
        }

        public void Deactivate()
        {
            isActive = false;
            StopAllCoroutines();
            gameObject.SetActive(false);
        }

        public void Regenerate()
        {
            currentHP = headHP;
            isDestroyed = false;
            animator?.SetTrigger("Regenerate");
        }

        public void TakeDamage(int amount)
        {
            if (isDestroyed) return;
            currentHP -= amount;
            boss?.RegisterHeadDamaged(this);

            if (currentHP <= 0)
                StartCoroutine(HeadDestroyed());
        }

        private IEnumerator HeadDestroyed()
        {
            isDestroyed = true;
            animator?.SetTrigger("Destroyed");
            yield return new WaitForSeconds(1f);
            gameObject.SetActive(false);
        }

        private IEnumerator AttackLoop()
        {
            while (isActive && !isDestroyed)
            {
                yield return new WaitForSeconds(attackInterval);
                if (!isDestroyed) PerformAttack();
            }
        }

        private void PerformAttack()
        {
            if (player == null) return;
            switch (headType)
            {
                case HydraHeadType.Red:     FireBreath(); break;
                case HydraHeadType.Blue:    FrostBreath(); break;
                case HydraHeadType.Green:   AcidSpit(); break;
                case HydraHeadType.Yellow:  ChainLightning(); break;
                case HydraHeadType.Center:  CoordinateAttack(); break;
            }
        }

        private void FireBreath()
        {
            breathParticles?.Play();
            // Spawn lava pool at player position
            if (projectilePrefab != null)
                Instantiate(projectilePrefab, player.position, Quaternion.identity);
        }

        private void FrostBreath()
        {
            breathParticles?.Play();
            player.GetComponent<Player.PlayerController>()?.ApplyControlReversal(3f); // freeze substitute
        }

        private void AcidSpit()
        {
            if (projectilePrefab == null || player == null) return;
            Vector2 dir = (player.position - transform.position).normalized;
            GameObject acid = Instantiate(projectilePrefab, transform.position, Quaternion.identity);
            acid.GetComponent<Rigidbody2D>()?.AddForce(dir * 14f, ForceMode2D.Impulse);
        }

        private void ChainLightning()
        {
            // Hits platform below player with lightning - physics impulse upward
            player?.GetComponent<Rigidbody2D>()
                ?.AddForce(Vector2.up * 12f, ForceMode2D.Impulse);
            player?.GetComponent<Player.PlayerHealth>()?.TakeDamage(1);
        }

        private void CoordinateAttack()
        {
            // Make all other active heads attack simultaneously
            HydraHead[] all = FindObjectsByType<HydraHead>(FindObjectsSortMode.None);
            foreach (var h in all)
                if (h != this && !h.isDestroyed)
                    h.PerformAttack();
        }
    }
}
