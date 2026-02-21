using System;
using System.Collections.Generic;
using UnityEngine;

namespace FeedMe
{
    /// <summary>
    /// Maps speaker name strings to portrait sprites for the dialogue box.
    /// Add entries in the Inspector to support all characters.
    /// </summary>
    [CreateAssetMenu(fileName = "SpeakerPortraitLibrary", menuName = "FeedMe/Speaker Portrait Library")]
    public class SpeakerPortraitLibrary : ScriptableObject
    {
        [SerializeField] private List<SpeakerEntry> entries;

        private Dictionary<string, Sprite> lookup;

        private void OnEnable()
        {
            lookup = new Dictionary<string, Sprite>(StringComparer.OrdinalIgnoreCase);
            foreach (var e in entries)
                if (e.sprite != null)
                    lookup[e.speakerName] = e.sprite;
        }

        public Sprite Get(string speakerName)
        {
            if (lookup == null) OnEnable();
            return lookup.TryGetValue(speakerName, out Sprite s) ? s : null;
        }
    }

    [Serializable]
    public class SpeakerEntry
    {
        public string speakerName;
        public Sprite sprite;
    }
}
