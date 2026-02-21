using UnityEngine;

namespace FeedMe.Player
{
    /// <summary>
    /// Bridges PlayerController to Unity Animator.
    /// Handles all animation parameter updates including
    /// HUD corruption stage visuals as the game progresses.
    /// </summary>
    [RequireComponent(typeof(Animator), typeof(SpriteRenderer))]
    public class PlayerAnimator : MonoBehaviour
    {
        private static readonly int SpeedHash      = Animator.StringToHash("Speed");
        private static readonly int IsGroundedHash = Animator.StringToHash("IsGrounded");
        private static readonly int IsDashingHash  = Animator.StringToHash("IsDashing");
        private static readonly int AttackHash     = Animator.StringToHash("Attack");
        private static readonly int CorruptionHash = Animator.StringToHash("CorruptionStage");

        [Header("Flash Effect")]
        [SerializeField] private float flashInterval = 0.1f;
        [SerializeField] private int flashCount = 5;

        [Header("Corruption Color Tints")]
        [SerializeField] private Color[] corruptionTints = new Color[]
        {
            Color.white,                           // Stage 0 - human
            new Color(0.85f, 1f, 0.85f),           // Stage 1 - slight green
            new Color(0.6f, 1f, 0.6f),             // Stage 2 - obvious green
            new Color(0.2f, 0.9f, 0.2f)            // Stage 3 - nearly plant
        };

        private Animator animator;
        private SpriteRenderer spriteRenderer;
        private int currentCorruptionStage;

        private void Awake()
        {
            animator = GetComponent<Animator>();
            spriteRenderer = GetComponent<SpriteRenderer>();
        }

        public void UpdateAnimations(float horizontalSpeed, bool grounded, bool dashing)
        {
            animator.SetFloat(SpeedHash, Mathf.Abs(horizontalSpeed));
            animator.SetBool(IsGroundedHash, grounded);
            animator.SetBool(IsDashingHash, dashing);
        }

        public void TriggerAttack()
        {
            animator.SetTrigger(AttackHash);
        }

        public void SetCorruptionStage(int stage)
        {
            currentCorruptionStage = Mathf.Clamp(stage, 0, corruptionTints.Length - 1);
            animator.SetInteger(CorruptionHash, currentCorruptionStage);
            spriteRenderer.color = corruptionTints[currentCorruptionStage];
        }

        public void TriggerInvincibilityFlash()
        {
            StartCoroutine(FlashCoroutine());
        }

        private System.Collections.IEnumerator FlashCoroutine()
        {
            for (int i = 0; i < flashCount; i++)
            {
                spriteRenderer.enabled = false;
                yield return new WaitForSeconds(flashInterval);
                spriteRenderer.enabled = true;
                yield return new WaitForSeconds(flashInterval);
            }
        }
    }
}
