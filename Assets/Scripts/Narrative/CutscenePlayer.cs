using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Video;

namespace FeedMe
{
    /// <summary>
    /// Plays pre-authored cutscenes by key.
    /// Cutscenes can be VideoClip assets (pre-rendered) or
    /// in-engine timeline sequences (Unity Playables / Timeline).
    /// Each key maps to either a VideoClip or a PlayableDirector in the scene.
    /// </summary>
    public class CutscenePlayer : MonoBehaviour
    {
        [SerializeField] private List<CutsceneEntry> entries;
        [SerializeField] private VideoPlayer videoPlayer;
        [SerializeField] private UnityEngine.Playables.PlayableDirector director;
        [SerializeField] private CanvasGroup blackScreen;

        private Action pendingCallback;
        private bool isPlaying;

        public void Play(string key, Action onComplete = null)
        {
            foreach (var entry in entries)
            {
                if (entry.key == key)
                {
                    pendingCallback = onComplete;
                    StartCutscene(entry);
                    return;
                }
            }
            // Key not found - skip directly to callback
            onComplete?.Invoke();
        }

        private void StartCutscene(CutsceneEntry entry)
        {
            if (isPlaying) return;
            isPlaying = true;
            HUDManager.Instance?.FadeToBlack(0.3f);

            if (entry.videoClip != null && videoPlayer != null)
            {
                videoPlayer.clip = entry.videoClip;
                videoPlayer.Play();
                videoPlayer.loopPointReached += OnVideoEnd;
            }
            else if (entry.playableAsset != null && director != null)
            {
                director.playableAsset = entry.playableAsset;
                director.Play();
                director.stopped += OnDirectorStopped;
            }
            else
            {
                // No media - just a narrative beat, complete immediately
                isPlaying = false;
                pendingCallback?.Invoke();
            }
        }

        private void OnVideoEnd(VideoPlayer vp)
        {
            videoPlayer.loopPointReached -= OnVideoEnd;
            FinishCutscene();
        }

        private void OnDirectorStopped(UnityEngine.Playables.PlayableDirector d)
        {
            director.stopped -= OnDirectorStopped;
            FinishCutscene();
        }

        private void FinishCutscene()
        {
            isPlaying = false;
            HUDManager.Instance?.FadeFromBlack(0.3f);
            pendingCallback?.Invoke();
            pendingCallback = null;
        }
    }

    [Serializable]
    public class CutsceneEntry
    {
        public string key;
        public VideoClip videoClip;
        public UnityEngine.Playables.PlayableAsset playableAsset;
    }
}
