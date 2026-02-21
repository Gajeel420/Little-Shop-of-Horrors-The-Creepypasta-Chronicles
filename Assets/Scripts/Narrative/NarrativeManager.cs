using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;

namespace FeedMe
{
    /// <summary>
    /// Central hub for all story events: cutscenes, dialogue, voiceovers,
    /// memory flashbacks, and the creepypasta death-counter Mushnik lines.
    /// </summary>
    public class NarrativeManager : MonoBehaviour
    {
        public static NarrativeManager Instance { get; private set; }

        [Header("Dialogue UI")]
        [SerializeField] private DialogueBox dialogueBox;
        [SerializeField] private CutscenePlayer cutscenePlayer;

        [Header("Mushnik Death Lines")]
        [SerializeField] private string[] mushnikDeathLines = new string[]
        {
            "You've died once, Seymour. Are you really trying?",
            "Three times now, Seymour. Three.",
            "You've died {n} times, Seymour... Audrey II is keeping count.",
            "I've watched you die {n} times. Are you even human anymore?",
            "Fifty-three deaths, Seymour. I stopped caring around thirty.",
            "You've died {n} times. The plant gets stronger each time, you know.",
            "{n} deaths. Somewhere That's Green is starting to sound better, isn't it.",
            "Your save file is hungry, Seymour. You've died {n} times.",
        };

        [Header("Memory Flashback Keys")]
        [SerializeField] private MemoryFlashEntry[] memoryFlashEntries;

        [Header("Events")]
        public UnityEvent<string> OnCutsceneComplete;
        public UnityEvent<string> OnBossDefeated;

        private bool dialogueActive;
        private Queue<(string speaker, string text)> dialogueQueue = new();

        // ── Lifecycle ──────────────────────────────────────────────────────────
        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        // ── Cutscenes ──────────────────────────────────────────────────────────
        public void PlayCutscene(string cutsceneKey)
        {
            cutscenePlayer?.Play(cutsceneKey, () => OnCutsceneComplete?.Invoke(cutsceneKey));
        }

        public void PlayQuickFlash(string imageKey)
        {
            HUDManager.Instance?.FlashImage(imageKey, 0.8f);
        }

        // ── Dialogue ───────────────────────────────────────────────────────────
        public void PlayDialogue(string speaker, string text)
        {
            dialogueQueue.Enqueue((speaker, text));
            if (!dialogueActive)
                StartCoroutine(ProcessDialogueQueue());
        }

        public void PlayVoiceover(string speaker, string text)
        {
            // Voiceover: no text box, just audio + subtitle
            HUDManager.Instance?.ShowSubtitle($"{speaker}: {text}", 4f);
        }

        private IEnumerator ProcessDialogueQueue()
        {
            dialogueActive = true;
            while (dialogueQueue.Count > 0)
            {
                var (speaker, text) = dialogueQueue.Dequeue();
                dialogueBox?.Show(speaker, text);
                yield return new WaitUntil(() => dialogueBox == null || !dialogueBox.IsShowing);
                yield return new WaitForSeconds(0.3f);
            }
            dialogueActive = false;
        }

        // ── Boss Defeated ──────────────────────────────────────────────────────
        public void TriggerBossDefeated(string bossName)
        {
            OnBossDefeated?.Invoke(bossName);
            StartCoroutine(PostBossNarrative(bossName));
        }

        private IEnumerator PostBossNarrative(string bossName)
        {
            yield return new WaitForSeconds(1f);
            switch (bossName)
            {
                case "OrinBoss":
                    PlayCutscene("Stage1ToStage2_Cutscene");
                    break;
                case "PatrickBoss":
                    PlayCutscene("Stage2ToStage3_Cutscene");
                    break;
            }
        }

        // ── Mushnik Death Counter ──────────────────────────────────────────────
        /// <summary>Called each time the player dies. Mushnik comments on death count.</summary>
        public void TriggerMushniklDeathLine(int deathCount)
        {
            string line = PickMushnikLine(deathCount);
            line = line.Replace("{n}", deathCount.ToString());

            // Creepypasta: show as persistent screen text, not a dialogue box
            HUDManager.Instance?.ShowCreepypastaMessage(line, 5f);

            // Additional creepypasta triggers
            if (deathCount == 27)
                HUDManager.Instance?.ShowCreepypastaMessage("Your save file is hungry.", 3f);
        }

        private string PickMushnikLine(int count)
        {
            if (count <= 1) return mushnikDeathLines[0];
            if (count == 3) return mushnikDeathLines[1];
            if (count < 50) return mushnikDeathLines[2];
            if (count < 100) return mushnikDeathLines[4];
            return mushnikDeathLines[6];
        }

        // ── Memory Flashbacks ──────────────────────────────────────────────────
        public void PlayMemoryFlash(string key)
        {
            foreach (var entry in memoryFlashEntries)
            {
                if (entry.key == key)
                {
                    StartCoroutine(ShowMemoryFlash(entry));
                    return;
                }
            }
        }

        private IEnumerator ShowMemoryFlash(MemoryFlashEntry entry)
        {
            HUDManager.Instance?.FadeToBlack(0.3f);
            yield return new WaitForSeconds(0.4f);
            HUDManager.Instance?.ShowMemoryImage(entry.sprite);
            PlayDialogue("MEMORY", entry.narrationText);
            yield return new WaitForSeconds(3f);
            HUDManager.Instance?.HideMemoryImage();
            HUDManager.Instance?.FadeFromBlack(0.3f);
        }

        // ── Contract Text Glitch ───────────────────────────────────────────────
        public void GlitchContractText()
        {
            HUDManager.Instance?.GlitchText(0.5f);
        }

        // ── Interlude Choice Moments ───────────────────────────────────────────
        public void ShowInterludeChoice(string[] options, Action<int> onChoice)
        {
            HUDManager.Instance?.ShowChoiceWheel(options, onChoice);
        }
    }

    [Serializable]
    public class MemoryFlashEntry
    {
        public string key;
        public Sprite sprite;
        [TextArea(2, 5)]
        public string narrationText;
    }
}
