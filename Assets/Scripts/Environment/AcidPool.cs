using System.Collections.Generic;
using UnityEngine;

namespace FeedMe.Environment
{
    /// <summary>
    /// Stage 2-1: Feeding Floor.
    /// Stomach acid pools that deal DOT to the player.
    /// Frozen/neutralized by Photosynthesis ability.
    /// </summary>
    public class AcidPool : MonoBehaviour
    {
        [SerializeField] private float damagePerSecond = 1f;
        [SerializeField] private ParticleSystem bubbleParticles;
        [SerializeField] private SpriteRenderer poolSprite;
        [SerializeField] private Color activeColor   = new Color(0.6f, 1f, 0.2f, 0.8f);
        [SerializeField] private Color frozenColor   = new Color(0.2f, 0.6f, 1f, 0.5f);

        private bool isFrozen;
        private List<Player.PlayerHealth> playersInside = new();

        private static List<AcidPool> allPools = new();

        private void OnEnable()  => allPools.Add(this);
        private void OnDisable() => allPools.Remove(this);

        private void Update()
        {
            if (isFrozen) return;
            foreach (var ph in playersInside)
                ph?.ApplyDOT(damagePerSecond, 0.5f);
        }

        private void OnTriggerEnter2D(Collider2D other)
        {
            var ph = other.GetComponent<Player.PlayerHealth>();
            if (ph != null && !playersInside.Contains(ph))
                playersInside.Add(ph);
        }

        private void OnTriggerExit2D(Collider2D other)
        {
            var ph = other.GetComponent<Player.PlayerHealth>();
            if (ph != null)
                playersInside.Remove(ph);
        }

        public void Freeze()
        {
            isFrozen = true;
            bubbleParticles?.Stop();
            if (poolSprite != null)
                poolSprite.color = frozenColor;
            // Frozen acid becomes a walkable platform
            GetComponent<Collider2D>().isTrigger = false;
        }

        public void Unfreeze()
        {
            isFrozen = false;
            bubbleParticles?.Play();
            if (poolSprite != null)
                poolSprite.color = activeColor;
            GetComponent<Collider2D>().isTrigger = true;
        }

        /// <summary>Called by Photosynthesis ability to neutralize nearby pools.</summary>
        public static void ConvertNearby(Vector3 origin, float radius)
        {
            foreach (var pool in allPools)
            {
                if (Vector3.Distance(pool.transform.position, origin) <= radius)
                    pool.Freeze();
            }
        }
    }
}
