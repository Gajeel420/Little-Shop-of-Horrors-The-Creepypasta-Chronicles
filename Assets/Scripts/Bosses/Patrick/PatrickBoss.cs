using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace FeedMe.Bosses
{
    /// <summary>
    /// STAGE 2 BOSS: Patrick Martin (The Salesman Entity)
    ///
    /// Phase 1 (100-75%): Mirror-floor deception, multiplication, contract traps
    /// Phase 2 (75-40%):  Contracts bleed, platform manipulation, briefcase bulb
    /// Phase 3 (40-0%):   Full plant-hybrid: vine-tie whip, corporate consumption,
    ///                     contract tornado. Forces player to read damning contract.
    ///
    /// Weakness: Real Patrick only visible in mirror floor reflection.
    /// Reward: Blood Contract ability.
    /// </summary>
    public class PatrickBoss : BossBase
    {
        // ── Inspector ──────────────────────────────────────────────────────────
        [Header("Clones")]
        [SerializeField] private GameObject patrickClonePrefab;
        [SerializeField] private int cloneCount = 3;
        [SerializeField] private Transform[] cloneSpawnPoints;

        [Header("Phase 1 - Contracts")]
        [SerializeField] private GameObject briefcasePrefab;
        [SerializeField] private GameObject contractTrapPrefab;
        [SerializeField] private float trapFreezeDuration = 3f;
        [SerializeField] private GameObject megaphonePrefab;
        [SerializeField] private float soundwaveKnockback = 8f;

        [Header("Phase 2 - Platform Manipulation")]
        [SerializeField] private Transform[] movingPlatforms;
        [SerializeField] private float platformAmplitude = 3f;
        [SerializeField] private float platformSpeed = 1.5f;
        [SerializeField] private Transform briefcaseBulbWeakPoint;
        [SerializeField] private int bulbHitsNeeded = 5;

        [Header("Phase 3 - Hybrid")]
        [SerializeField] private float vinetieReach = 15f;
        [SerializeField] private float suctionForce = 8f;
        [SerializeField] private GameObject contractTornadoPrefab;
        [SerializeField] private TMPro.TextMeshProUGUI contractScrollText;
        [SerializeField] private string[] contractLines;  // Fill in Inspector with contract text

        [Header("Audio")]
        [SerializeField] private AudioClip salespitchClip;
        [SerializeField] private AudioClip briefcaseOpenClip;
        [SerializeField] private AudioClip contractSignClip;
        [SerializeField] private AudioClip hybridRoarClip;

        // ── State ──────────────────────────────────────────────────────────────
        private List<GameObject> activeClones = new();
        private bool mirrorFloorActive;
        private int bulbHitCount;
        private float platformTimer;

        // ── Setup ──────────────────────────────────────────────────────────────
        protected override void Awake()
        {
            base.Awake();
            rewardAbility = AbilityType.BloodContract;
            phaseThresholds = new float[] { 0.75f, 0.4f };
        }

        protected override void OnBossStart()
        {
            NarrativeManager.Instance?.PlayCutscene("PatrickOpening");
            // Activate mirror floor
            mirrorFloorActive = true;
            StartCoroutine(Phase1Behaviour());
        }

        // ── Phase 1 ────────────────────────────────────────────────────────────
        protected override IEnumerator Phase1Behaviour()
        {
            while (currentPhase == 0 && !isDefeated)
            {
                yield return StartCoroutine(MultiplicationBarrage());
                yield return new WaitForSeconds(1.5f);
                yield return StartCoroutine(ContractCascade());
                yield return new WaitForSeconds(1f);
                yield return StartCoroutine(SalesPitchShockwave());
                yield return new WaitForSeconds(2f);
            }
        }

        private IEnumerator MultiplicationBarrage()
        {
            audioSource.PlayOneShot(salespitchClip);
            // Spawn clones
            ClearClones();
            for (int i = 0; i < cloneCount && i < cloneSpawnPoints.Length; i++)
            {
                GameObject clone = Instantiate(patrickClonePrefab,
                    cloneSpawnPoints[i].position, Quaternion.identity);
                activeClones.Add(clone);
                // PatrickClone component attacks but deals no damage; only real Patrick damages
                clone.GetComponent<PatrickClone>()?.Init(isReal: false);
            }

            // Mirror floor shows real position
            // PatrickReflection component on floor handles reflection rendering
            yield return new WaitForSeconds(4f);

            // Clones merge back
            foreach (var clone in activeClones)
                if (clone != null) Destroy(clone);
            activeClones.Clear();
        }

        private IEnumerator ContractCascade()
        {
            audioSource.PlayOneShot(briefcaseOpenClip);
            for (int i = 0; i < 6; i++)
            {
                Vector3 spawnPos = transform.position + new Vector3(
                    Random.Range(-5f, 5f), 4f, 0);
                Instantiate(briefcasePrefab, spawnPos, Quaternion.identity);
                yield return new WaitForSeconds(0.3f);
            }
        }

        private IEnumerator SalesPitchShockwave()
        {
            // Megaphone cartoon shockwave - 3 concentric circles
            for (int i = 0; i < 3; i++)
            {
                Vector2 dir = DirectionToPlayer();
                // Push player back with physics
                Collider2D hit = Physics2D.OverlapCircle(transform.position, 4f + i * 1.5f);
                if (hit != null && hit.CompareTag("Player"))
                {
                    hit.GetComponent<Rigidbody2D>()
                        ?.AddForce(-dir * soundwaveKnockback, ForceMode2D.Impulse);
                    hit.GetComponent<Player.PlayerHealth>()?.TakeDamage(1);
                }
                yield return new WaitForSeconds(0.2f);
            }
        }

        // ── Phase 2 ────────────────────────────────────────────────────────────
        protected override IEnumerator PhaseTransition(int newPhase)
        {
            if (newPhase == 1)
            {
                // Glitch - suit tears, plant matter visible
                animator.SetTrigger("GlitchReveal");
                yield return new WaitForSeconds(2f);
                // Start moving platforms
            }
            else if (newPhase == 2)
            {
                audioSource.PlayOneShot(hybridRoarClip);
                animator.SetTrigger("HybridTransform");
                NarrativeManager.Instance?.PlayDialogue("PatrickReveal",
                    "Alright, FINE! Let me show you the REAL product!");
                yield return new WaitForSeconds(3f);
            }
        }

        protected override void StartPhaseLoop(int phase)
        {
            if (phase == 1) StartCoroutine(Phase2Behaviour());
            else if (phase == 2) StartCoroutine(Phase3Behaviour());
        }

        private IEnumerator Phase2Behaviour()
        {
            // Animate platforms
            StartCoroutine(AnimatePlatforms());
            bulbHitCount = 0;

            while (currentPhase == 1 && !isDefeated)
            {
                yield return StartCoroutine(BindingAgreement());
                yield return new WaitForSeconds(1f);
                yield return StartCoroutine(SwarmPitch());
                yield return new WaitForSeconds(2f);

                // Expose briefcase bulb
                briefcaseBulbWeakPoint.gameObject.SetActive(true);
                yield return new WaitForSeconds(3f);
                briefcaseBulbWeakPoint.gameObject.SetActive(false);
            }
        }

        private IEnumerator AnimatePlatforms()
        {
            while (currentPhase == 1)
            {
                platformTimer += Time.deltaTime * platformSpeed;
                for (int i = 0; i < movingPlatforms.Length; i++)
                {
                    if (movingPlatforms[i] == null) continue;
                    float offset = i * Mathf.PI * 0.5f; // phase offset per platform
                    float y = Mathf.Sin(platformTimer + offset) * platformAmplitude;
                    Vector3 pos = movingPlatforms[i].localPosition;
                    pos.y = y;
                    movingPlatforms[i].localPosition = pos;
                }
                yield return null;
            }
        }

        private IEnumerator BindingAgreement()
        {
            // Throw giant contract
            Vector3 target = player != null ? player.position : transform.position;
            GameObject contract = Instantiate(contractTrapPrefab, target, Quaternion.identity);
            audioSource.PlayOneShot(contractSignClip);
            // ContractTrap component on that prefab handles freeze effect
            yield return new WaitForSeconds(1f);
        }

        private IEnumerator SwarmPitch()
        {
            // Multiple clones circle arena in bullet-hell pattern
            SpawnCircleClones(8);
            yield return new WaitForSeconds(5f);
            ClearClones();
        }

        private void SpawnCircleClones(int count)
        {
            float radius = 6f;
            for (int i = 0; i < count; i++)
            {
                float angle = (360f / count) * i;
                Vector3 pos = transform.position + new Vector3(
                    Mathf.Cos(angle * Mathf.Deg2Rad) * radius,
                    Mathf.Sin(angle * Mathf.Deg2Rad) * radius, 0);
                GameObject clone = Instantiate(patrickClonePrefab, pos, Quaternion.identity);
                activeClones.Add(clone);
                clone.GetComponent<PatrickClone>()?.Init(isReal: false);
            }
        }

        // Called by the briefcase bulb hit box
        public void HitBulb()
        {
            bulbHitCount++;
            audioSource.PlayOneShot(briefcaseOpenClip);
            NarrativeManager.Instance?.PlayDialogue("PatrickBulbHit",
                "QUARTERLY LOSSES! SHAREHOLDER REVOLT!");

            if (bulbHitCount >= bulbHitsNeeded)
                CheckPhaseThreshold();
        }

        // ── Phase 3 ────────────────────────────────────────────────────────────
        private IEnumerator Phase3Behaviour()
        {
            while (!isDefeated)
            {
                yield return StartCoroutine(VineTieStrangle());
                yield return new WaitForSeconds(1.5f);
                yield return StartCoroutine(CorporateConsumption());
                yield return new WaitForSeconds(1f);

                if (HPPercent < 0.3f)
                    yield return StartCoroutine(TheFinePrint());

                yield return new WaitForSeconds(2f);
            }
        }

        private IEnumerator VineTieStrangle()
        {
            // Tie whip: low → high → split pattern
            if (player == null) yield break;

            // Three sweeps
            float[] heights = { 0.5f, 1.2f, 0f }; // low, high, split(ground)
            foreach (float h in heights)
            {
                Vector2 sweepPos = (Vector2)player.position + Vector2.up * h;
                Collider2D hit = Physics2D.OverlapCircle(sweepPos, 0.5f);
                if (hit != null && hit.CompareTag("Player"))
                    hit.GetComponent<Player.PlayerHealth>()?.TakeDamage(1);
                yield return new WaitForSeconds(0.4f);
            }
        }

        private IEnumerator CorporateConsumption()
        {
            // Suction effect: pull player toward mouth
            float duration = 3f;
            float elapsed = 0;
            while (elapsed < duration && player != null)
            {
                Vector2 toward = (transform.position - player.position).normalized;
                player.GetComponent<Rigidbody2D>()
                    ?.AddForce(toward * suctionForce);
                elapsed += Time.deltaTime;
                yield return null;
            }

            // If player was consumed
            float dist = player != null ? Vector2.Distance(transform.position, player.position) : 99f;
            if (dist < 1.5f)
            {
                player?.GetComponent<Player.PlayerHealth>()?.TakeDamage(3);
                // Brief cutscene of inside of digestive system
                NarrativeManager.Instance?.PlayQuickFlash("DigestiveSystem");
            }
        }

        private IEnumerator TheFinePrint()
        {
            // Contract tornado environment hazard
            GameObject tornado = Instantiate(contractTornadoPrefab,
                transform.position + Vector3.right * 3f, Quaternion.identity);

            // Force player to read contract text
            if (contractScrollText != null)
            {
                contractScrollText.gameObject.SetActive(true);
                System.DateTime startDate = SaveSystem.GetSaveStartDate();
                string dateStr = startDate.ToString("MMMM d, yyyy");

                string fullContract = string.Join("\n", contractLines)
                    .Replace("[PLAYER_START_DATE]", dateStr);

                contractScrollText.text = fullContract;

                // Glitch text as boss takes hits
                yield return new WaitForSeconds(8f);
                contractScrollText.gameObject.SetActive(false);
            }

            Destroy(tornado, 8f);
        }

        // ── Helpers ────────────────────────────────────────────────────────────
        private void CheckPhaseThreshold()
        {
            // Manually trigger next phase check after bulb hits
            if (HPPercent <= phaseThresholds[currentPhase])
                StartCoroutine(TransitionRoutine(currentPhase + 1));
        }

        private IEnumerator TransitionRoutine(int newPhase)
        {
            yield return StartCoroutine(PhaseTransition(newPhase));
            currentPhase = newPhase;
            StartPhaseLoop(newPhase);
        }

        private void ClearClones()
        {
            foreach (var c in activeClones)
                if (c != null) Destroy(c);
            activeClones.Clear();
        }

        // ── Death ──────────────────────────────────────────────────────────────
        protected override IEnumerator DeathSequence()
        {
            ClearClones();
            animator.SetTrigger("Death");
            NarrativeManager.Instance?.PlayCutscene("PatrickDeath");

            // "YOU'RE ALREADY MINE! READ THE CONTRACT!" final voiceover
            NarrativeManager.Instance?.PlayDialogue("PatrickFinalWords",
                "YOU'RE ALREADY MINE! READ THE CONTRACT!");

            yield return new WaitForSeconds(2f);
            // Body dissolves into spores; boardroom shatters
            GetComponentInChildren<ParticleSystem>()?.Play();
            yield return new WaitForSeconds(2.5f);

            NarrativeManager.Instance?.PlayVoiceover("AudreyII",
                "Contracts can be renegotiated, Seymour. Let me show you what you REALLY signed up for.");
        }
    }
}
