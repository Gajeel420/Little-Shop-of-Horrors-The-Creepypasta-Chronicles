using System.Collections;
using UnityEngine;

namespace FeedMe.Bosses
{
    /// <summary>
    /// The central rotating drill in Orin's arena.
    /// Activates at Phase 2, creating a sweeping light-laser beam
    /// that forces the player to time jumps.
    /// </summary>
    public class DrillApparatus : MonoBehaviour
    {
        [SerializeField] private float rotationSpeed = 60f;   // degrees/sec
        [SerializeField] private LineRenderer laserRenderer;
        [SerializeField] private float laserLength = 15f;
        [SerializeField] private int laserDamage = 1;
        [SerializeField] private LayerMask playerLayer;

        private bool isActive;
        private float currentAngle;

        public void Activate() => isActive = true;
        public void Deactivate() => isActive = false;

        private void Update()
        {
            if (!isActive) return;

            currentAngle += rotationSpeed * Time.deltaTime;
            transform.rotation = Quaternion.Euler(0, 0, currentAngle);
            UpdateLaser();
        }

        private void UpdateLaser()
        {
            if (laserRenderer == null) return;

            Vector2 dir = transform.right;
            laserRenderer.SetPosition(0, transform.position);
            laserRenderer.SetPosition(1, (Vector2)transform.position + dir * laserLength);

            // Damage player if laser hits
            RaycastHit2D hit = Physics2D.Raycast(transform.position, dir, laserLength, playerLayer);
            if (hit.collider != null)
            {
                hit.collider.GetComponent<Player.PlayerHealth>()
                    ?.TakeDamage(laserDamage);
            }
        }
    }
}
