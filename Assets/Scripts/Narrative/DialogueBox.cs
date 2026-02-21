using System.Collections;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FeedMe
{
    /// <summary>
    /// Typewriter-style dialogue box.
    /// Supports reversed dialogue (creepypasta glitched NPCs),
    /// speaker portrait swaps, and "skip" on confirm input.
    /// </summary>
    public class DialogueBox : MonoBehaviour
    {
        [SerializeField] private GameObject panel;
        [SerializeField] private TextMeshProUGUI speakerLabel;
        [SerializeField] private TextMeshProUGUI bodyText;
        [SerializeField] private Image speakerPortrait;
        [SerializeField] private float typeSpeed = 0.04f;  // seconds per character
        [SerializeField] private SpeakerPortraitLibrary portraitLibrary;

        public bool IsShowing { get; private set; }
        private bool skipRequested;

        public void Show(string speaker, string text, bool reversed = false)
        {
            StartCoroutine(ShowRoutine(speaker, text, reversed));
        }

        private IEnumerator ShowRoutine(string speaker, string text, bool reversed)
        {
            IsShowing = true;
            skipRequested = false;
            panel?.SetActive(true);

            if (speakerLabel != null) speakerLabel.text = speaker;
            if (bodyText != null)    bodyText.text = string.Empty;

            // Portrait
            Sprite portrait = portraitLibrary?.Get(speaker);
            if (speakerPortrait != null)
                speakerPortrait.sprite = portrait;

            string displayText = reversed ? Reverse(text) : text;

            // Typewriter
            for (int i = 0; i <= displayText.Length; i++)
            {
                if (skipRequested) { bodyText.text = displayText; break; }
                if (bodyText != null)
                    bodyText.text = displayText.Substring(0, i);
                yield return new WaitForSeconds(typeSpeed);
            }

            // Wait for player to press confirm or auto-advance
            yield return new WaitUntil(() => skipRequested);
            skipRequested = false;
            panel?.SetActive(false);
            IsShowing = false;
        }

        // Called by input system or button
        public void Advance() => skipRequested = true;

        private static string Reverse(string s)
        {
            char[] arr = s.ToCharArray();
            System.Array.Reverse(arr);
            return new string(arr);
        }
    }
}
