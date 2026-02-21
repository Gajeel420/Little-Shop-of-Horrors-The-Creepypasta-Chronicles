using UnityEngine;

namespace FeedMe.Bosses
{
    /// <summary>
    /// A Patrick Martin clone.  If real = false, attacks hit for no damage
    /// and the clone is only visible in the mirror floor reflection.
    /// </summary>
    public class PatrickClone : MonoBehaviour
    {
        [SerializeField] private SpriteRenderer spriteRenderer;
        [SerializeField] private float orbitSpeed = 90f;
        [SerializeField] private float throwInterval = 1.5f;
        [SerializeField] private GameObject briefcasePrefab;

        private bool isReal;
        private Transform player;
        private float throwTimer;

        public void Init(bool isReal)
        {
            this.isReal = isReal;
            // Non-real clones are transparent except in reflection
            if (!isReal && spriteRenderer != null)
                spriteRenderer.color = new Color(1, 1, 1, 0.15f);

            player = GameObject.FindGameObjectWithTag("Player")?.transform;
        }

        private void Update()
        {
            // Orbit the arena center
            transform.RotateAround(Vector3.zero, Vector3.forward, orbitSpeed * Time.deltaTime);

            // Throw briefcases periodically
            throwTimer -= Time.deltaTime;
            if (throwTimer <= 0)
            {
                ThrowBriefcase();
                throwTimer = throwInterval;
            }
        }

        private void ThrowBriefcase()
        {
            if (player == null || briefcasePrefab == null) return;
            Vector2 dir = (player.position - transform.position).normalized;
            GameObject bc = Instantiate(briefcasePrefab, transform.position, Quaternion.identity);
            bc.GetComponent<Rigidbody2D>()?.AddForce(dir * 10f, ForceMode2D.Impulse);

            // If clone is fake, mark briefcase as no-damage
            if (!isReal)
                bc.GetComponent<ContractBriefcase>()?.SetNoDamage();
        }
    }
}
