using UnityEngine;

namespace FeedMe.Bosses
{
    /// <summary>
    /// Projectile thrown by Patrick Martin and his clones.
    /// Opens mid-air and releases contract papers that create trap zones.
    /// If marked as no-damage (fake clone throw), passes through harmlessly.
    /// </summary>
    public class ContractBriefcase : MonoBehaviour
    {
        [SerializeField] private GameObject contractTrapPrefab;
        [SerializeField] private float openDelay = 0.5f;
        [SerializeField] private int paperCount = 4;
        [SerializeField] private AudioClip openClip;

        private bool noDamage;
        private float timer;

        private void Start() => timer = openDelay;

        private void Update()
        {
            timer -= Time.deltaTime;
            if (timer <= 0)
            {
                OpenBriefcase();
                Destroy(gameObject);
            }
        }

        public void SetNoDamage() => noDamage = true;

        private void OpenBriefcase()
        {
            if (noDamage || contractTrapPrefab == null) return;
            AudioSource.PlayClipAtPoint(openClip, transform.position);

            for (int i = 0; i < paperCount; i++)
            {
                float angle = (360f / paperCount) * i;
                Vector3 offset = new Vector3(
                    Mathf.Cos(angle * Mathf.Deg2Rad),
                    Mathf.Sin(angle * Mathf.Deg2Rad), 0) * 0.5f;
                Instantiate(contractTrapPrefab, transform.position + offset, Quaternion.identity);
            }
        }
    }
}
