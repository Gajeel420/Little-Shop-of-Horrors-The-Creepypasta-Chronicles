using UnityEngine;
using UnityEngine.Events;

namespace FeedMe
{
    /// <summary>
    /// Place on any barrier in the world (vine wall, locked door, high ledge hook, etc.).
    /// When the player enters the trigger zone, checks if they have the required ability.
    /// On success: fires OnGateOpened and disables/destroys the barrier.
    /// On fail: fires OnGateBlocked and shows a contextual hint.
    /// </summary>
    public class AbilityGate : MonoBehaviour
    {
        [Header("Requirement")]
        [SerializeField] private AbilityType requiredAbility;
        [SerializeField] private bool destroyOnOpen = true;
        [SerializeField] private GameObject barrierObject;  // Assign the visual barrier

        [Header("Hint")]
        [SerializeField] private string blockedHintText = "";  // Leave empty to auto-generate
        [SerializeField] private float hintDisplayTime = 2.5f;

        [Header("Events")]
        public UnityEvent OnGateOpened;
        public UnityEvent OnGateBlocked;

        private bool hasOpened;

        private static readonly System.Collections.Generic.Dictionary<AbilityType, string> DefaultHints =
            new()
            {
                { AbilityType.PruningShears,    "You need the Pruning Shears to cut through this." },
                { AbilityType.NitrousDash,      "Nitrous Dash lets you phase through this barrier." },
                { AbilityType.BloodContract,    "Blood Contract reveals what's hidden here." },
                { AbilityType.VineSwing,        "You need the Vine Swing to reach up there." },
                { AbilityType.Photosynthesis,   "Photosynthesis can bridge across this hazard." },
                { AbilityType.DentistTools,     "Dentist's Tools can break through this metal door." },
                { AbilityType.AudreysLocket,    "Audrey's Locket reveals the truth here." },
            };

        private void OnTriggerEnter2D(Collider2D other)
        {
            if (hasOpened) return;
            if (!other.CompareTag("Player")) return;

            AbilityManager am = AbilityManager.Instance;
            if (am == null) return;

            if (am.HasAbility(requiredAbility))
            {
                OpenGate();
            }
            else
            {
                ShowHint();
                OnGateBlocked?.Invoke();
            }
        }

        private void OpenGate()
        {
            hasOpened = true;
            OnGateOpened?.Invoke();

            if (barrierObject != null)
            {
                if (destroyOnOpen)
                    Destroy(barrierObject);
                else
                    barrierObject.SetActive(false);
            }

            // Disable this trigger so it doesn't fire again
            Destroy(this);
        }

        private void ShowHint()
        {
            string hint = string.IsNullOrEmpty(blockedHintText)
                ? (DefaultHints.TryGetValue(requiredAbility, out string h) ? h : $"Need: {requiredAbility}")
                : blockedHintText;

            HUDManager.Instance?.ShowHint(hint, hintDisplayTime);
        }
    }
}
