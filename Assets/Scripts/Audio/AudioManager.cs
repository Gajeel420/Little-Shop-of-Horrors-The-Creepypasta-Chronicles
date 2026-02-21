using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace FeedMe.Audio
{
    /// <summary>
    /// Manages background music, doo-wop corruption, and audio transitions.
    ///
    /// Music design per game design doc:
    ///   - Starts as vibrant 1960s doo-wop
    ///   - Gradually distorts to horror ambience as corruption increases
    ///   - Boss themes: film songs corrupted (pitch-shifted, reversed, degraded)
    ///   - Stage 3: full cosmic horror soundscape
    /// </summary>
    public class AudioManager : MonoBehaviour
    {
        public static AudioManager Instance { get; private set; }

        [Header("Music Tracks")]
        [SerializeField] private AudioClip[] stageMusic;   // Index 0-3 = stage 0-3 (0=clean, 3=horror)
        [SerializeField] private AudioClip[] bossThemes;   // Orin, Patrick, AudreyII
        [SerializeField] private float crossfadeDuration = 2f;

        [Header("Corruption Audio")]
        [SerializeField] private float[] corruptionPitchShifts = { 1f, 0.97f, 0.9f, 0.75f };
        [SerializeField] private float[] corruptionReverbMix   = { 0f, 0.2f, 0.5f, 0.9f };

        [Header("Sources")]
        [SerializeField] private AudioSource musicSource1;
        [SerializeField] private AudioSource musicSource2;

        private int currentCorruption;
        private AudioSource activeSource;
        private AudioSource inactiveSource;

        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            activeSource = musicSource1;
            inactiveSource = musicSource2;
        }

        // ── Public API ──────────────────────────────────────────────────────────
        public void PlayStageMusic(int stageIndex)
        {
            if (stageIndex >= stageMusic.Length) return;
            CrossfadeTo(stageMusic[stageIndex]);
        }

        public void PlayBossTheme(int bossIndex)
        {
            if (bossIndex >= bossThemes.Length) return;
            CrossfadeTo(bossThemes[bossIndex]);
        }

        public void SetCorruptionLevel(int level)
        {
            currentCorruption = Mathf.Clamp(level, 0, 3);
            float pitch  = corruptionPitchShifts[currentCorruption];
            float reverb = corruptionReverbMix[currentCorruption];

            activeSource.pitch = pitch;
            // AudioMixer parameters would be set here for reverb
        }

        public void StopMusic(float fadeTime = 1f)
        {
            StartCoroutine(FadeOut(activeSource, fadeTime));
        }

        // ── Crossfade ──────────────────────────────────────────────────────────
        private void CrossfadeTo(AudioClip clip)
        {
            if (activeSource.clip == clip) return;
            StartCoroutine(CrossfadeRoutine(clip));
        }

        private IEnumerator CrossfadeRoutine(AudioClip newClip)
        {
            inactiveSource.clip = newClip;
            inactiveSource.pitch = corruptionPitchShifts[currentCorruption];
            inactiveSource.volume = 0;
            inactiveSource.Play();

            float t = 0;
            while (t < crossfadeDuration)
            {
                t += Time.deltaTime;
                float pct = t / crossfadeDuration;
                activeSource.volume = 1f - pct;
                inactiveSource.volume = pct;
                yield return null;
            }
            activeSource.Stop();

            // Swap
            (activeSource, inactiveSource) = (inactiveSource, activeSource);
        }

        private IEnumerator FadeOut(AudioSource source, float duration)
        {
            float startVol = source.volume;
            float t = 0;
            while (t < duration)
            {
                t += Time.deltaTime;
                source.volume = Mathf.Lerp(startVol, 0, t / duration);
                yield return null;
            }
            source.Stop();
            source.volume = startVol;
        }
    }
}
