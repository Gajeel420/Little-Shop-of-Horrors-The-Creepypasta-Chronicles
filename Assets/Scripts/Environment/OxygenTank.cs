using UnityEngine;

namespace FeedMe.Environment
{
    /// <summary>
    /// Placed around the edge of Orin's Phase 3 arena.
    /// During the Laughing Gas Flood attack, 4 of these must be
    /// destroyed within 15 seconds to prevent player death.
    /// </summary>
    public class OxygenTank : MonoBehaviour
    {
        [SerializeField] private int hitsToDestroy = 1;
        [SerializeField] private ParticleSystem breakFX;
        [SerializeField] private AudioClip breakClip;

        private int hitCount;
        private int tanksBroken;  // reference to OrinBoss counter

        public void Enable(ref int brokeCounter)
        {
            hitCount = 0;
            gameObject.SetActive(true);
        }

        private void OnTriggerEnter2D(Collider2D other)
        {
            if (!other.CompareTag("PlayerAttack")) return;
            hitCount++;
            if (hitCount >= hitsToDestroy)
                BreakTank();
        }

        private void BreakTank()
        {
            breakFX?.Play();
            AudioSource.PlayClipAtPoint(breakClip, transform.position);
            // The gas flood routine in OrinBoss polls for tank destruction
            gameObject.SetActive(false);
        }
    }
}
