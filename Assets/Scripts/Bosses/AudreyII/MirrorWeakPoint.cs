using System.Collections;
using UnityEngine;

namespace FeedMe.Bosses
{
    /// <summary>
    /// The giant mirror in Phase 3 of the Audrey II fight.
    /// Shows Seymour's "true" untransformed self.
    /// Attacking it damages the boss; Audrey II tries to cover it with vines.
    /// </summary>
    public class MirrorWeakPoint : MonoBehaviour
    {
        [SerializeField] private SpriteRenderer reflectionSprite;  // Shows human Seymour
        [SerializeField] private ParticleSystem shatterParticles;
        [SerializeField] private AudioClip mirrorHitClip;
        [SerializeField] private AudioClip mirrorCoverClip;
        [SerializeField] private int hitsToShatter = 20;

        private AudreyIIBoss boss;
        private int hitCount;
        private bool isActive;

        public void Init(AudreyIIBoss parentBoss)
        {
            boss = parentBoss;
            isActive = true;
        }

        private void OnTriggerEnter2D(Collider2D other)
        {
            if (!isActive) return;
            // Only Pruning Shears attack registers (tagged "PlayerAttack")
            if (!other.CompareTag("PlayerAttack")) return;

            hitCount++;
            AudioSource.PlayClipAtPoint(mirrorHitClip, transform.position);

            // Glitch the reflection image to show corruption progress
            float corruptionT = (float)hitCount / hitsToShatter;
            if (reflectionSprite != null)
                reflectionSprite.color = Color.Lerp(Color.white,
                    new Color(0.2f, 0.9f, 0.2f), corruptionT);

            boss?.MirrorHit();

            if (hitCount >= hitsToShatter)
                StartCoroutine(Shatter());
        }

        // Called by AudreyIIBoss vine cover routine
        public void CoverWithVine()
        {
            if (!isActive) return;
            AudioSource.PlayClipAtPoint(mirrorCoverClip, transform.position);
            StartCoroutine(TemporaryBlock());
        }

        private IEnumerator TemporaryBlock()
        {
            isActive = false;
            // Tint mirror green to indicate blockage
            if (reflectionSprite != null)
                reflectionSprite.color = Color.green;

            yield return new WaitForSeconds(4f);  // Player must cut vine to restore

            if (reflectionSprite != null)
                reflectionSprite.color = Color.white;
            isActive = true;
        }

        private IEnumerator Shatter()
        {
            isActive = false;
            shatterParticles?.Play();
            yield return new WaitForSeconds(0.5f);
            Destroy(gameObject);
        }
    }
}
