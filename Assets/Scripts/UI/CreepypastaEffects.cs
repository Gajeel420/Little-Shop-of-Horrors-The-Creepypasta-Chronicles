using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace FeedMe.UI
{
    /// <summary>
    /// Implements all persistent creepypasta ambient effects that play
    /// throughout the game independent of specific events:
    ///
    /// - The Watcher: shadow figure in backgrounds, never acknowledged
    /// - Glitched NPCs: T-poses, reversed speech
    /// - Save Corruption messages: "Your save file is hungry"
    /// - Lost Episode: secret VHS-style corrupted level aesthetic
    /// - Numbers Station: ambient radio broadcasts coordinates in teeth
    /// - HUD Thorn Growth: health bar thorns at high corruption
    /// </summary>
    public class CreepypastaEffects : MonoBehaviour
    {
        public static CreepypastaEffects Instance { get; private set; }

        [Header("The Watcher")]
        [SerializeField] private GameObject watcherShadowPrefab;
        [SerializeField] private float watcherSpawnChance = 0.05f;  // per scene load
        [SerializeField] private Vector2[] watcherSpawnRegions;

        [Header("VHS / Lost Episode Filter")]
        [SerializeField] private Material vhsMaterial;
        [SerializeField] private float vhsIntensity = 0f;
        [SerializeField] private Camera mainCamera;

        [Header("Numbers Station")]
        [SerializeField] private AudioSource radioSource;
        [SerializeField] private AudioClip[] staticClips;
        [SerializeField] private AudioClip[] toothCoordinateClips;
        [SerializeField] private float stationTriggerChance = 0.02f;  // per minute

        [Header("Color Desaturation")]
        [SerializeField] private Material saturationMaterial;
        private float currentSaturation = 1f;
        private float targetSaturation = 1f;

        // Per-stage target saturations: Stage 1 = vibrant, Stage 3 = near monochrome
        private static readonly float[] StageSaturations = { 1f, 0.65f, 0.3f, 0.0f };

        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        private void Start()
        {
            TrySpawnWatcher();
            StartCoroutine(NumbersStationLoop());
        }

        private void Update()
        {
            // Smoothly desaturate world as player progresses
            currentSaturation = Mathf.MoveTowards(currentSaturation, targetSaturation, Time.deltaTime * 0.02f);
            if (saturationMaterial != null)
                saturationMaterial.SetFloat("_Saturation", currentSaturation);
        }

        // ── The Watcher ────────────────────────────────────────────────────────
        private void TrySpawnWatcher()
        {
            if (Random.value > watcherSpawnChance) return;
            if (watcherShadowPrefab == null || watcherSpawnRegions.Length == 0) return;

            Vector2 region = watcherSpawnRegions[Random.Range(0, watcherSpawnRegions.Length)];
            Vector3 spawnPos = new Vector3(region.x, region.y, 0);

            GameObject watcher = Instantiate(watcherShadowPrefab, spawnPos, Quaternion.identity);
            // Watcher never moves, never reacts - just watches
            // It disappears if the player gets within 3 units (no acknowledgement)
            watcher.AddComponent<WatcherBehaviour>();
        }

        // ── Stage Desaturation ─────────────────────────────────────────────────
        public void SetStage(int stageIndex)
        {
            targetSaturation = stageIndex < StageSaturations.Length
                ? StageSaturations[stageIndex] : 0f;
        }

        // ── VHS / Lost Episode ─────────────────────────────────────────────────
        public void ActivateVHSFilter(float intensity)
        {
            vhsIntensity = intensity;
            if (vhsMaterial != null)
                vhsMaterial.SetFloat("_VHSIntensity", vhsIntensity);
        }

        // ── Numbers Station ────────────────────────────────────────────────────
        private IEnumerator NumbersStationLoop()
        {
            while (true)
            {
                yield return new WaitForSeconds(60f);
                if (Random.value < stationTriggerChance)
                    yield return StartCoroutine(BroadcastStation());
            }
        }

        private IEnumerator BroadcastStation()
        {
            if (radioSource == null) yield break;

            // Static burst
            if (staticClips.Length > 0)
                radioSource.PlayOneShot(staticClips[Random.Range(0, staticClips.Length)]);

            yield return new WaitForSeconds(1f);

            // "Coordinates in human teeth" broadcast
            if (toothCoordinateClips.Length > 0)
                radioSource.PlayOneShot(toothCoordinateClips[Random.Range(0, toothCoordinateClips.Length)]);

            yield return new WaitForSeconds(3f);

            if (staticClips.Length > 0)
                radioSource.PlayOneShot(staticClips[Random.Range(0, staticClips.Length)]);
        }

        // ── NPC Glitch ─────────────────────────────────────────────────────────
        public static void TriggerNPCGlitch(GameObject npc)
        {
            // Randomly T-pose or play reversed audio
            Animator anim = npc.GetComponent<Animator>();
            if (anim != null && Random.value < 0.5f)
                anim.SetTrigger("TPose");

            AudioSource audio = npc.GetComponent<AudioSource>();
            if (audio != null && audio.clip != null)
            {
                // Reverse the audio clip (requires reversing samples at runtime)
                // Simplified: just pitch-reverse flag on audio source
                audio.pitch = -1f;
                audio.time = audio.clip.length;
                audio.Play();
            }
        }
    }

    /// <summary>
    /// The Watcher shadow figure: stays in background, disappears silently
    /// if player comes close. Never acknowledged by any in-game system.
    /// </summary>
    public class WatcherBehaviour : MonoBehaviour
    {
        private const float DisappearRange = 3f;
        private Transform player;

        private void Start()
        {
            player = GameObject.FindGameObjectWithTag("Player")?.transform;
        }

        private void Update()
        {
            if (player == null) return;
            if (Vector2.Distance(transform.position, player.position) < DisappearRange)
                Destroy(gameObject); // No fanfare, no acknowledgement
        }
    }
}
