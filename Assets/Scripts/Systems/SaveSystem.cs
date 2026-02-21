using System;
using System.Collections.Generic;
using UnityEngine;

namespace FeedMe
{
    /// <summary>
    /// Persistent save system using PlayerPrefs (swap for JSON file system for production).
    /// Saves: death count, unlocked abilities, collectibles, stage progress, start date.
    /// Creepypasta element: "Your save file is hungry" messaging handled by NarrativeManager.
    /// </summary>
    public static class SaveSystem
    {
        private const string KEY_DEATHS       = "DeathCount";
        private const string KEY_ABILITIES    = "Abilities";
        private const string KEY_STAGE        = "CurrentStage";
        private const string KEY_COLLECTIBLES = "Collectibles";
        private const string KEY_START_DATE   = "SaveStartDate";
        private const string KEY_ENDINGS      = "UnlockedEndings";
        private const string KEY_CORRUPTION   = "CorruptionStage";

        // ── Death Counter ──────────────────────────────────────────────────────
        public static void SaveDeathCount(int count)
        {
            PlayerPrefs.SetInt(KEY_DEATHS, count);
            PlayerPrefs.Save();
        }

        public static int LoadDeathCount() => PlayerPrefs.GetInt(KEY_DEATHS, 0);

        // ── Abilities ──────────────────────────────────────────────────────────
        public static void SaveAbilities(IEnumerable<AbilityType> abilities)
        {
            var list = new List<int>();
            foreach (var a in abilities)
                list.Add((int)a);
            PlayerPrefs.SetString(KEY_ABILITIES, string.Join(",", list));
            PlayerPrefs.Save();
        }

        public static List<AbilityType> LoadAbilities()
        {
            var result = new List<AbilityType>();
            string raw = PlayerPrefs.GetString(KEY_ABILITIES, "");
            if (string.IsNullOrEmpty(raw)) return result;
            foreach (var part in raw.Split(','))
            {
                if (int.TryParse(part, out int v))
                    result.Add((AbilityType)v);
            }
            return result;
        }

        // ── Stage Progress ─────────────────────────────────────────────────────
        public static void SaveStage(int stageIndex, int levelIndex)
        {
            PlayerPrefs.SetInt(KEY_STAGE, stageIndex * 10 + levelIndex);
            PlayerPrefs.Save();
        }

        public static (int stage, int level) LoadStage()
        {
            int packed = PlayerPrefs.GetInt(KEY_STAGE, 0);
            return (packed / 10, packed % 10);
        }

        // ── Collectibles (Memory Fragments, Lore Items) ────────────────────────
        public static void SaveCollectible(string id)
        {
            string current = PlayerPrefs.GetString(KEY_COLLECTIBLES, "");
            if (!current.Contains(id))
            {
                current += (string.IsNullOrEmpty(current) ? "" : ",") + id;
                PlayerPrefs.SetString(KEY_COLLECTIBLES, current);
                PlayerPrefs.Save();
            }
        }

        public static bool HasCollectible(string id)
        {
            string current = PlayerPrefs.GetString(KEY_COLLECTIBLES, "");
            return current.Contains(id);
        }

        public static int GetCollectibleCount(string prefix)
        {
            string current = PlayerPrefs.GetString(KEY_COLLECTIBLES, "");
            if (string.IsNullOrEmpty(current)) return 0;
            int count = 0;
            foreach (var part in current.Split(','))
                if (part.StartsWith(prefix)) count++;
            return count;
        }

        // ── Save Start Date (used in Patrick's predatory contract) ─────────────
        public static void InitStartDate()
        {
            if (!PlayerPrefs.HasKey(KEY_START_DATE))
            {
                PlayerPrefs.SetString(KEY_START_DATE, DateTime.Now.ToString("o"));
                PlayerPrefs.Save();
            }
        }

        public static DateTime GetSaveStartDate()
        {
            string raw = PlayerPrefs.GetString(KEY_START_DATE, DateTime.Now.ToString("o"));
            return DateTime.Parse(raw);
        }

        // ── Endings ────────────────────────────────────────────────────────────
        public static void UnlockEnding(EndingType ending)
        {
            string current = PlayerPrefs.GetString(KEY_ENDINGS, "");
            string key = ending.ToString();
            if (!current.Contains(key))
            {
                current += (string.IsNullOrEmpty(current) ? "" : ",") + key;
                PlayerPrefs.SetString(KEY_ENDINGS, current);
                PlayerPrefs.Save();
            }
        }

        public static bool HasEnding(EndingType ending) =>
            PlayerPrefs.GetString(KEY_ENDINGS, "").Contains(ending.ToString());

        // ── Corruption Stage ───────────────────────────────────────────────────
        public static void SaveCorruptionStage(int stage)
        {
            PlayerPrefs.SetInt(KEY_CORRUPTION, stage);
            PlayerPrefs.Save();
        }

        public static int LoadCorruptionStage() => PlayerPrefs.GetInt(KEY_CORRUPTION, 0);

        // ── Full Reset ─────────────────────────────────────────────────────────
        public static void DeleteSave()
        {
            PlayerPrefs.DeleteAll();
            PlayerPrefs.Save();
        }
    }
}
