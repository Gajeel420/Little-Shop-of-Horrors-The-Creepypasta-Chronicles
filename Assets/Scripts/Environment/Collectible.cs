using UnityEngine;

namespace FeedMe.Environment
{
    public enum CollectibleType
    {
        MemoryFragment,     // 8 Audrey fragments - unlock Audrey's Locket + true ending
        LoreItem,           // Narrative collectibles (Orin's dental license, Mushnik's ledger)
        HeartContainer,     // +1 max heart
        AbilityToken,       // Optional ability pickups
    }

    /// <summary>
    /// Collectible item placed in the world.
    /// On pickup: saves to SaveSystem, triggers narrative flash if memory fragment,
    /// checks for Audrey's Locket completion (8/8 memory fragments).
    /// </summary>
    public class Collectible : MonoBehaviour
    {
        [SerializeField] private CollectibleType type;
        [SerializeField] private string collectibleID;   // Unique ID, e.g. "MemoryFrag_01"
        [SerializeField] private AbilityType abilityToGrant;  // For AbilityToken type
        [SerializeField] private Sprite memorySprite;
        [SerializeField] [TextArea(2, 4)] private string memoryNarration;
        [SerializeField] private AudioClip pickupSound;

        private void Start()
        {
            // Already collected in a previous session?
            if (SaveSystem.HasCollectible(collectibleID))
                Destroy(gameObject);
        }

        private void OnTriggerEnter2D(Collider2D other)
        {
            if (!other.CompareTag("Player")) return;
            Collect(other);
        }

        private void Collect(Collider2D player)
        {
            AudioSource.PlayClipAtPoint(pickupSound, transform.position);
            SaveSystem.SaveCollectible(collectibleID);

            switch (type)
            {
                case CollectibleType.MemoryFragment:
                    NarrativeManager.Instance?.PlayMemoryFlash(collectibleID);
                    CheckLocketCompletion();
                    break;

                case CollectibleType.HeartContainer:
                    player.GetComponent<Player.PlayerHealth>()?.AddMaxHeart();
                    break;

                case CollectibleType.AbilityToken:
                    AbilityManager.Instance?.UnlockAbility(abilityToGrant);
                    break;

                case CollectibleType.LoreItem:
                    HUDManager.Instance?.ShowCreepypastaMessage($"Found: {collectibleID}", 3f);
                    break;
            }

            Destroy(gameObject);
        }

        private void CheckLocketCompletion()
        {
            int count = SaveSystem.GetCollectibleCount("MemoryFrag_");
            if (count >= 8)
            {
                AbilityManager.Instance?.UnlockAbility(AbilityType.AudreysLocket);
                NarrativeManager.Instance?.PlayDialogue("AUDREY",
                    "Find me, Seymour. I'm in somewhere that's green. The REAL green.");
            }
        }
    }
}
