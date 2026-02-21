using System.Collections;
using UnityEngine;

namespace FeedMe.Enemies
{
    /// <summary>
    /// Stage 3-1: Total Eclipse.
    /// Void Tendrils emerge from reality tears in the space-flesh environment.
    /// Low-gravity space level: tendril grabs player and holds them in place.
    /// </summary>
    public class VoidTendril : EnemyBase
    {
        [SerializeField] private float grabDuration   = 2.5f;
        [SerializeField] private float grabRange      = 2f;
        [SerializeField] private float emergeDuration = 1f;

        private bool isGrabbing;
        private Player.PlayerController grabbedPlayer;

        protected override void Awake()
        {
            base.Awake();
            maxHP = 25;
            contactDamage = 1;
            moveSpeed = 0f;       // Tendrils don't move, they emerge from a spot
            aggroRange = 5f;
            attackRange = 2f;
            attackCooldown = 4f;
            weaknessDescription = "Nitrous Dash phases through grab";
        }

        protected override void Start()
        {
            base.Start();
            StartCoroutine(EmergeFromTear());
        }

        private IEnumerator EmergeFromTear()
        {
            // Animate emerging from void
            float t = 0;
            Vector3 hiddenPos = transform.position + Vector3.down * 2f;
            Vector3 targetPos = transform.position;
            transform.position = hiddenPos;

            while (t < emergeDuration)
            {
                t += Time.deltaTime;
                transform.position = Vector3.Lerp(hiddenPos, targetPos, t / emergeDuration);
                yield return null;
            }
        }

        protected override void PatrolBehaviour()
        {
            // Tendrils wait in place and pulse
            float pulse = Mathf.Sin(Time.time * 2f) * 0.1f + 1f;
            transform.localScale = new Vector3(pulse, pulse, 1f);
        }

        protected override void AggroBehaviour()
        {
            if (isGrabbing) return;
            float dist = Vector2.Distance(transform.position, player.position);
            if (dist <= attackRange && attackTimer <= 0)
            {
                PerformAttack();
                attackTimer = attackCooldown;
            }
        }

        protected override void PerformAttack()
        {
            if (player == null) return;
            float dist = Vector2.Distance(transform.position, player.position);
            if (dist <= grabRange)
                StartCoroutine(GrabPlayer());
        }

        private IEnumerator GrabPlayer()
        {
            isGrabbing = true;
            grabbedPlayer = player.GetComponent<Player.PlayerController>();

            // Freeze player position (disable their input movement temporarily)
            // Player's Nitrous Dash breaks free
            float elapsed = 0;
            while (elapsed < grabDuration && grabbedPlayer != null)
            {
                player.position = Vector2.MoveTowards(
                    player.position, transform.position, Time.deltaTime * 3f);
                player.GetComponent<Player.PlayerHealth>()?.TakeDamage(1);
                elapsed += Time.deltaTime;
                yield return new WaitForSeconds(0.5f);
            }
            isGrabbing = false;
        }
    }
}
