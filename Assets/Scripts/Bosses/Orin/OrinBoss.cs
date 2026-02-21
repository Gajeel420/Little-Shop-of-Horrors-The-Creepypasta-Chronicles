using System.Collections;
using UnityEngine;

namespace FeedMe.Bosses
{
    /// <summary>
    /// STAGE 1 BOSS: Orin Scrivello, DDS (Reanimated)
    ///
    /// Phase 1 (100-70%): Drill Lunge, Laughing Gas Bombs, Tool Toss
    /// Phase 2 (70-40%):  Spiral Drill, Gas Mask weak point, Tooth Golem summons
    /// Phase 3 (40-0%):   Amalgamation - Quadruple Vine Whip, Gas Flood, Debris
    ///
    /// Weakness: Hit the gas mask to stagger. Reward: Nitrous Dash.
    /// </summary>
    public class OrinBoss : BossBase
    {
        // ── Inspector ──────────────────────────────────────────────────────────
        [Header("Phase 1 - Attacks")]
        [SerializeField] private float drillLungeSpeed    = 18f;
        [SerializeField] private float drillLungeWarnTime = 2f;
        [SerializeField] private GameObject gasCanisterPrefab;
        [SerializeField] private GameObject dentalToolPrefab;
        [SerializeField] private int toolTossCount        = 5;

        [Header("Phase 2 - Drill Apparatus")]
        [SerializeField] private Transform centralDrill;
        [SerializeField] private GameObject toothGolemPrefab;
        [SerializeField] private int golemSummonCount     = 3;
        [SerializeField] private Transform[] golemSpawnPoints;
        [SerializeField] private Collider2D gasMaskWeakPoint;  // Hit this to crack mask
        [SerializeField] private int maskCracksNeeded         = 3;
        [SerializeField] private float dizzyDuration          = 4f;

        [Header("Phase 3 - Amalgamation")]
        [SerializeField] private Transform[] vineArmPoints;     // 4 arm spawn anchors
        [SerializeField] private GameObject dentalDebrisPrefab;
        [SerializeField] private int oxygenTankCount           = 4;
        [SerializeField] private GameObject oxygenTankPrefab;
        [SerializeField] private float gasfloorduration        = 15f;
        [SerializeField] private GameObject gasFloorPrefab;

        [Header("Audio")]
        [SerializeField] private AudioClip laughClip;
        [SerializeField] private AudioClip drillClip;
        [SerializeField] private AudioClip gasBombClip;
        [SerializeField] private AudioClip maskCrackClip;
        [SerializeField] private AudioClip amalgamationRoarClip;

        // ── Private state ──────────────────────────────────────────────────────
        private Rigidbody2D rb;
        private int maskCrackCount;
        private bool isDizzy;
        private bool mergedWithDrill;

        private static readonly int DrillLungeAnim   = Animator.StringToHash("DrillLunge");
        private static readonly int DizyAnim         = Animator.StringToHash("Dizzy");
        private static readonly int MaskCrackAnim    = Animator.StringToHash("MaskCrack");
        private static readonly int AmalgamateAnim   = Animator.StringToHash("Amalgamate");

        // ── Setup ──────────────────────────────────────────────────────────────
        protected override void Awake()
        {
            base.Awake();
            rb = GetComponent<Rigidbody2D>();
            // Boss reward is Nitrous Dash
            rewardAbility = AbilityType.NitrousDash;
            phaseThresholds = new float[] { 0.7f, 0.4f };
        }

        protected override void OnBossStart()
        {
            NarrativeManager.Instance?.PlayCutscene("OrinOpening");
            StartCoroutine(Phase1Behaviour());
        }

        // ── Phase 1 (100% → 70%) ──────────────────────────────────────────────
        protected override IEnumerator Phase1Behaviour()
        {
            while (currentPhase == 0 && !isDefeated)
            {
                yield return StartCoroutine(DrillLunge());
                yield return new WaitForSeconds(1.5f);
                yield return StartCoroutine(LaughingGasBomb());
                yield return new WaitForSeconds(1f);
                yield return StartCoroutine(ToolToss());
                yield return new WaitForSeconds(2f);
            }
        }

        private IEnumerator DrillLunge()
        {
            // Telegraph: maniacal laughter then charge
            audioSource.PlayOneShot(laughClip);
            animator.SetTrigger(DrillLungeAnim);
            yield return new WaitForSeconds(drillLungeWarnTime);

            if (player == null) yield break;
            Vector2 dir = (player.position - transform.position).normalized;

            audioSource.PlayOneShot(drillClip);
            float elapsed = 0;
            float lungeTime = 0.35f;
            while (elapsed < lungeTime)
            {
                rb.linearVelocity = dir * drillLungeSpeed;
                elapsed += Time.deltaTime;
                yield return null;
            }
            rb.linearVelocity = Vector2.zero;
            yield return new WaitForSeconds(0.5f); // recovery
        }

        private IEnumerator LaughingGasBomb()
        {
            audioSource.PlayOneShot(gasBombClip);
            Vector3 throwPos = player != null
                ? player.position + Vector3.up * 2f
                : transform.position + Vector3.right * 3f;

            Instantiate(gasCanisterPrefab, throwPos, Quaternion.identity);
            // GasCanister component on that prefab handles explosion + control reversal
            yield return new WaitForSeconds(0.8f);
        }

        private IEnumerator ToolToss()
        {
            float arcSpread = 60f;
            float startAngle = -arcSpread / 2f;
            float step = arcSpread / (toolTossCount - 1);

            for (int i = 0; i < toolTossCount; i++)
            {
                float angle = startAngle + step * i;
                Vector2 dir = Quaternion.Euler(0, 0, angle) * DirectionToPlayer();
                GameObject tool = Instantiate(dentalToolPrefab, transform.position, Quaternion.identity);
                tool.GetComponent<Rigidbody2D>()?.AddForce(dir * 12f, ForceMode2D.Impulse);
                yield return new WaitForSeconds(0.1f);
            }
        }

        // ── Phase 2 (70% → 40%) ──────────────────────────────────────────────
        protected override IEnumerator PhaseTransition(int newPhase)
        {
            if (newPhase == 1)
            {
                // Stagger to central drill
                audioSource.PlayOneShot(drillClip);
                yield return new WaitForSeconds(1.5f);
                // Central drill starts rotating (handled by DrillApparatus component)
                centralDrill?.GetComponent<DrillApparatus>()?.Activate();
            }
            else if (newPhase == 2)
            {
                // Orin impales himself on drill; amalgamation begins
                audioSource.PlayOneShot(amalgamationRoarClip);
                animator.SetTrigger(AmalgamateAnim);
                mergedWithDrill = true;
                yield return new WaitForSeconds(2f);
            }
        }

        protected override void StartPhaseLoop(int phase)
        {
            if (phase == 1) StartCoroutine(Phase2Behaviour());
            else if (phase == 2) StartCoroutine(Phase3Behaviour());
        }

        private IEnumerator Phase2Behaviour()
        {
            while (currentPhase == 1 && !isDefeated)
            {
                yield return StartCoroutine(SpiralDrill());
                yield return new WaitForSeconds(1f);
                yield return StartCoroutine(SummonToothGolems());
                yield return new WaitForSeconds(2f);

                // Expose mask weak point periodically
                if (!isDizzy)
                    gasMaskWeakPoint.enabled = true;
                yield return new WaitForSeconds(3f);
                gasMaskWeakPoint.enabled = false;
            }
        }

        private IEnumerator SpiralDrill()
        {
            // 3 expanding shockwave rings
            for (int wave = 0; wave < 3; wave++)
            {
                SpawnShockwaveRing(wave * 0.4f + 0.8f); // increasing radius
                yield return new WaitForSeconds(0.4f);
            }
            // Dizzy after 3rd wave
            StartCoroutine(Dizziness());
        }

        private void SpawnShockwaveRing(float radius)
        {
            int segments = 12;
            for (int i = 0; i < segments; i++)
            {
                float angle = (360f / segments) * i;
                Vector2 dir = new Vector2(Mathf.Cos(angle * Mathf.Deg2Rad), Mathf.Sin(angle * Mathf.Deg2Rad));
                GameObject tool = Instantiate(dentalToolPrefab, transform.position, Quaternion.identity);
                tool.GetComponent<Rigidbody2D>()?.AddForce(dir * (radius * 6f), ForceMode2D.Impulse);
            }
        }

        private IEnumerator Dizziness()
        {
            isDizzy = true;
            animator.SetBool(DizyAnim, true);
            yield return new WaitForSeconds(dizzyDuration);
            animator.SetBool(DizyAnim, false);
            isDizzy = false;
        }

        // Called by damage system when gas mask hit point is struck
        public void HitMask()
        {
            if (!isDizzy) return;
            maskCrackCount++;
            audioSource.PlayOneShot(maskCrackClip);
            animator.SetInteger(MaskCrackAnim, maskCrackCount);

            if (maskCrackCount >= maskCracksNeeded)
            {
                // Mask fully shattered: Orin inhales own gas, longer stagger
                StartCoroutine(MaskShatter());
            }
        }

        private IEnumerator MaskShatter()
        {
            // Reveal plant roots growing through skull
            // Plays mask-shatter animation variant
            yield return StartCoroutine(Dizziness());
            yield return StartCoroutine(Dizziness()); // double duration
        }

        private IEnumerator SummonToothGolems()
        {
            for (int i = 0; i < golemSummonCount && i < golemSpawnPoints.Length; i++)
            {
                Instantiate(toothGolemPrefab, golemSpawnPoints[i].position, Quaternion.identity);
                yield return new WaitForSeconds(0.3f);
            }
        }

        // ── Phase 3 (40% → 0%) ───────────────────────────────────────────────
        private IEnumerator Phase3Behaviour()
        {
            while (!isDefeated)
            {
                yield return StartCoroutine(QuadrupleVineWhip());
                yield return new WaitForSeconds(1.5f);

                if (HPPercent < 0.15f)
                    yield return StartCoroutine(DespérationChairThrow());
                else
                    yield return StartCoroutine(LaughingGasFlood());
            }
        }

        private IEnumerator QuadrupleVineWhip()
        {
            // Arms slam clockwise
            for (int i = 0; i < vineArmPoints.Length; i++)
            {
                GameObject slam = Instantiate(dentalDebrisPrefab, vineArmPoints[i].position, Quaternion.identity);
                slam.GetComponent<Rigidbody2D>()?.AddForce(Vector2.down * 20f, ForceMode2D.Impulse);
                yield return new WaitForSeconds(0.25f);
            }
            // Expose drill-core weak point after all four slams
            yield return new WaitForSeconds(0.5f);
        }

        private IEnumerator LaughingGasFlood()
        {
            // Spawn gas floor; player must destroy 4 oxygen tanks
            GameObject gasFloor = Instantiate(gasFloorPrefab, transform.position, Quaternion.identity);

            int tanksDestroyed = 0;
            GameObject[] tanks = new GameObject[oxygenTankCount];
            // Oxygen tank positions should be pre-placed in scene; we enable them here
            OxygenTank[] sceneTanks = FindObjectsByType<OxygenTank>(FindObjectsSortMode.None);
            foreach (var t in sceneTanks) t.Enable(ref tanksDestroyed);

            float elapsed = 0;
            while (elapsed < gasfloorduration && tanksDestroyed < oxygenTankCount)
            {
                elapsed += Time.deltaTime;
                yield return null;
            }
            Destroy(gasFloor);
        }

        private IEnumerator DespérationChairThrow()
        {
            // Rip chairs from ground, throw at player
            for (int i = 0; i < 4; i++)
            {
                Vector3 throwTarget = player != null ? player.position : transform.position;
                GameObject chair = Instantiate(dentalDebrisPrefab,
                    transform.position + Vector3.up * 2f, Quaternion.identity);
                Vector2 dir = (throwTarget - chair.transform.position).normalized;
                chair.GetComponent<Rigidbody2D>()?.AddForce(dir * 16f, ForceMode2D.Impulse);
                yield return new WaitForSeconds(0.3f);
            }
        }

        // ── Death ──────────────────────────────────────────────────────────────
        protected override IEnumerator DeathSequence()
        {
            rb.linearVelocity = Vector2.zero;
            animator.SetTrigger("Death");

            // Orin's final words
            NarrativeManager.Instance?.PlayDialogue("OrinDeath", "It didn't hurt... why didn't it hurt?");
            yield return new WaitForSeconds(3f);

            // Body crumbles; vines retract toward shop
            // (Particle system on child GameObject handles this visually)
            GetComponentInChildren<ParticleSystem>()?.Play();
            yield return new WaitForSeconds(2f);
        }
    }
}
