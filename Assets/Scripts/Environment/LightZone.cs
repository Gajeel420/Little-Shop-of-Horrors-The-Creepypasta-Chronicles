using UnityEngine;

namespace FeedMe.Environment
{
    /// <summary>
    /// Light zones used by Photosynthesis ability.
    /// When the player stands in a light zone, healing ticks over time.
    /// Also used by Photosynthesis active ability to grow platforms.
    /// </summary>
    public class LightZone : MonoBehaviour
    {
        [SerializeField] private bool isAlwaysOn = true;
        [SerializeField] private Light2D zoneLight;  // UnityEngine.Rendering.Universal.Light2D
        private bool isActive;

        private void Start() => isActive = isAlwaysOn;

        public void SetActive(bool active)
        {
            isActive = active;
            if (zoneLight != null) zoneLight.enabled = active;
        }

        private void OnTriggerEnter2D(Collider2D other)
        {
            if (!isActive) return;
            other.GetComponent<Player.PlayerHealth>()?.EnterLightZone();
        }

        private void OnTriggerExit2D(Collider2D other)
        {
            other.GetComponent<Player.PlayerHealth>()?.ExitLightZone();
        }
    }
}
