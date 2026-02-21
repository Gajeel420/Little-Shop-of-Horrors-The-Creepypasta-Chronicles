using System.Collections;
using UnityEngine;

namespace FeedMe.Bosses
{
    /// <summary>
    /// Laughing gas canister thrown by Orin.
    /// Explodes after a delay, creating an AOE that reverses player controls.
    /// The Pruning Shears attack can destroy it mid-air.
    /// </summary>
    public class GasCanister : MonoBehaviour, IDestructible
    {
        [SerializeField] private float fuseTime       = 3f;
        [SerializeField] private float explosionRadius = 3.5f;
        [SerializeField] private float controlReverseDuration = 8f;
        [SerializeField] private GameObject explosionFXPrefab;
        [SerializeField] private AudioClip explosionClip;

        private bool exploded;

        private void Start() => StartCoroutine(FuseCountdown());

        private IEnumerator FuseCountdown()
        {
            yield return new WaitForSeconds(fuseTime);
            Explode();
        }

        private void Explode()
        {
            if (exploded) return;
            exploded = true;

            AudioSource.PlayClipAtPoint(explosionClip, transform.position);
            Instantiate(explosionFXPrefab, transform.position, Quaternion.identity);

            // Find all players in radius and reverse their controls
            Collider2D[] hits = Physics2D.OverlapCircleAll(transform.position, explosionRadius);
            foreach (var hit in hits)
            {
                hit.GetComponent<Player.PlayerController>()
                    ?.ApplyControlReversal(controlReverseDuration);
            }

            Destroy(gameObject);
        }

        // Called when Pruning Shears hits it
        public void Destroy()
        {
            exploded = true; // cancel fuse
            Destroy(gameObject);
        }
    }

    public interface IDestructible
    {
        void Destroy();
    }
}
