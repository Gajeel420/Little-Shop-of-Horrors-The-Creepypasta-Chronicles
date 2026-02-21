using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace FeedMe.Bosses
{
    /// <summary>
    /// STAGE 3 BOSS: Audrey II - "Mean Green Mother From Outer Space"
    ///
    /// Phase 1 (100-75%): Classic form - Bite, Vine Forest, Spore Cloud, Minions
    /// Phase 2 (75-40%):  Hydra - 5 heads with independent attack patterns.
    ///                     All must be damaged within 30 sec or they regenerate.
    ///                     Destroying each head shows a memory flashback.
    /// Phase 3 (40-0%):   Truth - Seymour/Plant amalgam. Memory weapons,
    ///                     mirror reflection weak point. Final choice.
    ///
    /// Reward: True Ending unlock / "Somewhere That's Green" NG+ ability.
    /// </summary>
    public class AudreyIIBoss : BossBase
    {
        // ── Inspector ──────────────────────────────────────────────────────────
        [Header("Phase 1 - Classic Form")]
        [SerializeField] private int vineCount = 12;
        [SerializeField] private float vineSpawnInterval = 0.3f;
        [SerializeField] private GameObject vinePrefab;
        [SerializeField] private GameObject sporePrefab;
        [SerializeField] private GameObject[] minion1Wave;  // Tooth Golems
        [SerializeField] private GameObject[] minion2Wave;  // Contract Wraiths

        [Header("Phase 2 - Hydra")]
        [SerializeField] private HydraHead[] hydraHeads;    // 5 head objects
        [SerializeField] private float headSyncWindow = 30f; // seconds to damage all

        [Header("Phase 3 - Truth")]
        [SerializeField] private GameObject mirrorWeakPointPrefab;
        [SerializeField] private Transform mirrorSpawnPoint;
        [SerializeField] private GameObject[] memoryAttackPrefabs;  // 4 memory attacks
        [SerializeField] private TMPro.TextMeshProUGUI revelationText;
        [SerializeField] private float finalChoiceTimer = 8f;

        [Header("Audio")]
        [SerializeField] private AudioClip biteClip;
        [SerializeField] private AudioClip vineClip;
        [SerializeField] private AudioClip hydraRoarClip;
        [SerializeField] private AudioClip truthRevealClip;
        [SerializeField] private AudioClip defeatOptionAClip;
        [SerializeField] private AudioClip defeatOptionBClip;

        // ── State ──────────────────────────────────────────────────────────────
        private HashSet<HydraHead> damagedHeadsThisWindow = new();
        private float hydraWindowTimer;
        private bool hydraWindowActive;
        private GameObject activeMirror;

        // ── Setup ──────────────────────────────────────────────────────────────
        protected override void Awake()
        {
            base.Awake();
            phaseThresholds = new float[] { 0.75f, 0.4f };
            // Reward depends on ending chosen - handled in DeathSequence
            rewardAbility = AbilityType.SomewhereThatSGreen;
        }

        protected override void OnBossStart()
        {
            NarrativeManager.Instance?.PlayCutscene("AudreyIIOpening");
            StartCoroutine(Phase1Behaviour());
        }

        // ── Phase 1 (100% → 75%) ─────────────────────────────────────────────
        protected override IEnumerator Phase1Behaviour()
        {
            while (currentPhase == 0 && !isDefeated)
            {
                yield return StartCoroutine(BiteLunge());
                yield return new WaitForSeconds(1.5f);
                yield return StartCoroutine(VineForest());
                yield return new WaitForSeconds(1f);
                yield return StartCoroutine(SporeCloud());
                yield return new WaitForSeconds(1f);
                yield return StartCoroutine(SummonMinions(minion1Wave));
                yield return new WaitForSeconds(3f);
                yield return StartCoroutine(SummonMinions(minion2Wave));
                yield return new WaitForSeconds(2f);
            }
        }

        private IEnumerator BiteLunge()
        {
            audioSource.PlayOneShot(biteClip);

            // Three tiers of bite range, each telegraphed
            float[] tiers = { 3f, 6f, 12f };
            float[] speeds = { 0.25f, 0.45f, 0.9f };

            for (int i = 0; i < tiers.Length; i++)
            {
                // Snap jaws at each range
                Collider2D hit = Physics2D.OverlapCircle(transform.position, tiers[i]);
                if (hit != null && hit.CompareTag("Player"))
                {
                    hit.GetComponent<Player.PlayerHealth>()?.TakeDamage(2);
                    break; // Only hit once
                }
                yield return new WaitForSeconds(speeds[i]);
            }
        }

        private IEnumerator VineForest()
        {
            audioSource.PlayOneShot(vineClip);
            List<Vector3> spawnPoints = GenerateVinePositions(vineCount);

            for (int i = 0; i < spawnPoints.Count; i++)
            {
                Instantiate(vinePrefab, spawnPoints[i], Quaternion.identity);
                yield return new WaitForSeconds(vineSpawnInterval);
            }
        }

        private List<Vector3> GenerateVinePositions(int count)
        {
            var positions = new List<Vector3>();
            float arenaWidth = 20f;
            float step = arenaWidth / count;
            for (int i = 0; i < count; i++)
            {
                float x = -arenaWidth / 2f + step * i;
                positions.Add(new Vector3(x, -4f, 0));
            }
            // Shuffle for memorization challenge
            for (int i = 0; i < positions.Count; i++)
            {
                int j = Random.Range(i, positions.Count);
                (positions[i], positions[j]) = (positions[j], positions[i]);
            }
            return positions;
        }

        private IEnumerator SporeCloud()
        {
            GameObject spore = Instantiate(sporePrefab, transform.position + Vector3.right * 2f,
                Quaternion.identity);
            // Photosynthesis converts this to health (SporeCloud component checks for ability)
            yield return new WaitForSeconds(0.8f);
        }

        private IEnumerator SummonMinions(GameObject[] prefabs)
        {
            foreach (var prefab in prefabs)
            {
                if (prefab == null) continue;
                Vector3 pos = transform.position + new Vector3(Random.Range(-5f, 5f), -2f, 0);
                Instantiate(prefab, pos, Quaternion.identity);
                yield return new WaitForSeconds(0.4f);
            }
        }

        // ── Phase 2 (75% → 40%): Hydra ────────────────────────────────────────
        protected override IEnumerator PhaseTransition(int newPhase)
        {
            if (newPhase == 1)
            {
                animator.SetTrigger("HydraBurst");
                audioSource.PlayOneShot(hydraRoarClip);
                NarrativeManager.Instance?.PlayDialogue("AudreyHydra",
                    "YOU WANT TO SEE WHAT I REALLY AM? FINE!");
                yield return new WaitForSeconds(3f);

                // Enable all 5 hydra heads
                foreach (var head in hydraHeads)
                    head?.Activate(this);
            }
            else if (newPhase == 2)
            {
                // All heads merge back, wrong amalgamation
                foreach (var head in hydraHeads)
                    head?.Deactivate();

                animator.SetTrigger("TruthMerge");
                audioSource.PlayOneShot(truthRevealClip);

                NarrativeManager.Instance?.PlayDialogue("AudreyTruth",
                    "Don't you get it yet? We're the same! WE'VE ALWAYS BEEN THE SAME!");

                // Boss health bar name changes to "YOURSELF"
                HUDManager.Instance?.SetBossName("YOURSELF");
                yield return new WaitForSeconds(4f);
            }
        }

        protected override void StartPhaseLoop(int phase)
        {
            if (phase == 1) StartCoroutine(Phase2Behaviour());
            else if (phase == 2) StartCoroutine(Phase3Behaviour());
        }

        private IEnumerator Phase2Behaviour()
        {
            // Hydra: heads attack independently via HydraHead components
            // Manager loop: enforce 30-second "damage all heads" window
            while (currentPhase == 1 && !isDefeated)
            {
                damagedHeadsThisWindow.Clear();
                hydraWindowActive = true;
                hydraWindowTimer = headSyncWindow;

                yield return new WaitForSeconds(headSyncWindow);

                // Check if all 5 heads were damaged
                if (damagedHeadsThisWindow.Count < hydraHeads.Length)
                    RegenerateAllHeads();

                hydraWindowActive = false;
                yield return new WaitForSeconds(2f);
            }
        }

        public void RegisterHeadDamaged(HydraHead head)
        {
            if (!hydraWindowActive) return;
            damagedHeadsThisWindow.Add(head);

            // Play memory flashback for this head
            NarrativeManager.Instance?.PlayMemoryFlash(head.MemoryKey);

            // If all heads damaged, trigger phase check
            if (damagedHeadsThisWindow.Count >= hydraHeads.Length)
                CheckPhaseChangeFromHydra();
        }

        private void RegenerateAllHeads()
        {
            // Heads feed on Seymour's memories - health regeneration animation
            foreach (var head in hydraHeads)
                head?.Regenerate();
        }

        private void CheckPhaseChangeFromHydra()
        {
            if (HPPercent <= phaseThresholds[currentPhase])
                StartCoroutine(PhaseTransition(2));
        }

        // ── Phase 3 (40% → 0%): The Truth ─────────────────────────────────────
        private IEnumerator Phase3Behaviour()
        {
            // Spawn mirror weak point
            activeMirror = Instantiate(mirrorWeakPointPrefab,
                mirrorSpawnPoint != null ? mirrorSpawnPoint.position : transform.position + Vector3.right * 5f,
                Quaternion.identity);
            activeMirror.GetComponent<MirrorWeakPoint>()?.Init(this);

            // Memory attacks cycle while player fights mirror
            StartCoroutine(MemoryAttackLoop());

            // Keep adding vines over mirror
            StartCoroutine(CoverMirrorRoutine());

            // Wait until defeated via mirror
            while (!isDefeated)
                yield return null;
        }

        private IEnumerator MemoryAttackLoop()
        {
            int index = 0;
            while (!isDefeated && currentPhase == 2)
            {
                if (memoryAttackPrefabs.Length > 0)
                {
                    Instantiate(memoryAttackPrefabs[index % memoryAttackPrefabs.Length],
                        Vector3.zero, Quaternion.identity);
                    index++;
                }
                yield return new WaitForSeconds(12f);
            }
        }

        private IEnumerator CoverMirrorRoutine()
        {
            while (!isDefeated && activeMirror != null)
            {
                Instantiate(vinePrefab, activeMirror.transform.position, Quaternion.identity);
                yield return new WaitForSeconds(5f);
            }
        }

        // Called by MirrorWeakPoint when player strikes it
        public void MirrorHit()
        {
            TakeDamage(20, transform.position);
            NarrativeManager.Instance?.GlitchContractText();
        }

        // ── Final Choice (triggered at <10% HP) ───────────────────────────────
        private bool finalChoiceTriggered;

        public override void TakeDamage(int amount, Vector2 hitPoint)
        {
            base.TakeDamage(amount, hitPoint);
            if (HPPercent < 0.1f && !finalChoiceTriggered)
                StartCoroutine(FinalChoice());
        }

        private IEnumerator FinalChoice()
        {
            finalChoiceTriggered = true;
            NarrativeManager.Instance?.PlayDialogue("AudreyFinalQuestion",
                "IF YOU KILL ME, YOU KILL YOURSELF! IS THAT WHAT YOU WANT?!");

            // Show choice UI - GameManager handles option selection
            GameManager.Instance?.ShowFinalChoice(OnOptionA, OnOptionB, OnOptionC);
            yield return null;
        }

        private void OnOptionA()   // "Yes" - True Ending
        {
            audioSource.PlayOneShot(defeatOptionAClip);
            StartCoroutine(Defeat());
        }

        private void OnOptionB()   // "No" - Dark Ending
        {
            audioSource.PlayOneShot(defeatOptionBClip);
            isDefeated = true;
            NarrativeManager.Instance?.PlayCutscene("DarkEnding");
            GameManager.Instance?.TriggerEnding(EndingType.Dark);
        }

        private void OnOptionC()   // Secret - Golden Ending (requires all collectibles)
        {
            if (!AbilityManager.Instance.HasAbility(AbilityType.AudreysLocket))
            {
                // Can't do golden ending, fall back to choice
                GameManager.Instance?.ShowFinalChoice(OnOptionA, OnOptionB, null);
                return;
            }
            isDefeated = true;
            NarrativeManager.Instance?.PlayCutscene("GoldenEndingRhythm");
            GameManager.Instance?.TriggerEnding(EndingType.Golden);
        }

        // ── Death (True Ending) ────────────────────────────────────────────────
        protected override IEnumerator DeathSequence()
        {
            if (activeMirror != null) Destroy(activeMirror);
            StopAllCoroutines();

            animator.SetTrigger("Death");

            NarrativeManager.Instance?.PlayDialogue("SeymourFinalWords",
                "I'd rather die human than live as a monster!");

            yield return new WaitForSeconds(2f);

            // Everything goes white
            HUDManager.Instance?.FadeToWhite(1.5f);
            yield return new WaitForSeconds(2f);

            GameManager.Instance?.TriggerEnding(EndingType.True);
        }
    }

    public enum EndingType { Bad, Normal, True, Dark, Golden }
}
