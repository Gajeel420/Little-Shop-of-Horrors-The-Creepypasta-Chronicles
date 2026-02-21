using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;

namespace FeedMe.Player
{
    /// <summary>
    /// Core Seymour player controller.
    /// Handles movement, jumping, dashing, vine-swinging,
    /// and delegates ability activation to AbilityManager.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D), typeof(Collider2D))]
    public class PlayerController : MonoBehaviour
    {
        // ── Inspector ──────────────────────────────────────────────────────────
        [Header("Movement")]
        [SerializeField] private float moveSpeed = 6f;
        [SerializeField] private float jumpForce = 14f;
        [SerializeField] private float coyoteTime = 0.12f;
        [SerializeField] private float jumpBufferTime = 0.15f;

        [Header("Ground Check")]
        [SerializeField] private Transform groundCheck;
        [SerializeField] private float groundCheckRadius = 0.15f;
        [SerializeField] private LayerMask groundLayer;

        [Header("References")]
        [SerializeField] private AbilityManager abilityManager;
        [SerializeField] private PlayerHealth health;
        [SerializeField] private PlayerAnimator playerAnimator;

        // ── State ──────────────────────────────────────────────────────────────
        private Rigidbody2D rb;
        private Vector2 moveInput;

        private bool isGrounded;
        private float coyoteTimer;
        private float jumpBufferTimer;

        private bool isControlsReversed;   // Laughing Gas effect
        private float reverseControlsTimer;

        private bool isDashing;
        private bool isFacingRight = true;

        // ── Unity Lifecycle ────────────────────────────────────────────────────
        private void Awake()
        {
            rb = GetComponent<Rigidbody2D>();
        }

        private void Update()
        {
            HandleGroundCheck();
            HandleCoyoteTime();
            HandleJumpBuffer();
            HandleControlReverse();
            HandleFacing();
            playerAnimator?.UpdateAnimations(moveInput.x, isGrounded, isDashing);
        }

        private void FixedUpdate()
        {
            if (!isDashing)
                ApplyMovement();
        }

        // ── Input System Callbacks ─────────────────────────────────────────────
        public void OnMove(InputValue value)
        {
            moveInput = value.Get<Vector2>();
        }

        public void OnJump(InputValue value)
        {
            if (value.isPressed)
                jumpBufferTimer = jumpBufferTime;
        }

        public void OnDash(InputValue value)
        {
            if (value.isPressed && abilityManager.HasAbility(AbilityType.NitrousDash))
                StartCoroutine(PerformDash());
        }

        public void OnAttack(InputValue value)
        {
            if (value.isPressed && abilityManager.HasAbility(AbilityType.PruningShears))
                playerAnimator?.TriggerAttack();
        }

        public void OnAbility1(InputValue value)  // Blood Contract
        {
            if (value.isPressed && abilityManager.HasAbility(AbilityType.BloodContract))
                abilityManager.UseBloodContract();
        }

        public void OnAbility2(InputValue value)  // Photosynthesis
        {
            if (value.isPressed && abilityManager.HasAbility(AbilityType.Photosynthesis))
                abilityManager.UsePhotosynthesis();
        }

        // ── Movement ──────────────────────────────────────────────────────────
        private void ApplyMovement()
        {
            float input = isControlsReversed ? -moveInput.x : moveInput.x;
            rb.linearVelocity = new Vector2(input * moveSpeed, rb.linearVelocity.y);

            if (jumpBufferTimer > 0 && (isGrounded || coyoteTimer > 0))
            {
                rb.linearVelocity = new Vector2(rb.linearVelocity.x, jumpForce);
                jumpBufferTimer = 0;
                coyoteTimer = 0;

                // Double-jump via Vine Swing ability
                if (!isGrounded && abilityManager.HasAbility(AbilityType.VineSwing))
                    rb.linearVelocity = new Vector2(rb.linearVelocity.x, jumpForce * 0.85f);
            }
        }

        private void HandleGroundCheck()
        {
            isGrounded = Physics2D.OverlapCircle(groundCheck.position, groundCheckRadius, groundLayer);
        }

        private void HandleCoyoteTime()
        {
            if (isGrounded)
                coyoteTimer = coyoteTime;
            else
                coyoteTimer -= Time.deltaTime;
        }

        private void HandleJumpBuffer()
        {
            jumpBufferTimer -= Time.deltaTime;
        }

        private void HandleFacing()
        {
            if (moveInput.x > 0 && !isFacingRight) Flip();
            else if (moveInput.x < 0 && isFacingRight) Flip();
        }

        private void Flip()
        {
            isFacingRight = !isFacingRight;
            Vector3 scale = transform.localScale;
            scale.x *= -1;
            transform.localScale = scale;
        }

        // ── Nitrous Dash ───────────────────────────────────────────────────────
        private IEnumerator PerformDash()
        {
            isDashing = true;
            float dir = isFacingRight ? 1f : -1f;
            rb.linearVelocity = new Vector2(dir * 20f, 0f);
            rb.gravityScale = 0f;

            Physics2D.IgnoreLayerCollision(LayerMask.NameToLayer("Player"),
                                           LayerMask.NameToLayer("Enemy"), true);

            yield return new WaitForSeconds(0.22f);

            Physics2D.IgnoreLayerCollision(LayerMask.NameToLayer("Player"),
                                           LayerMask.NameToLayer("Enemy"), false);
            rb.gravityScale = 1f;
            isDashing = false;
        }

        // ── Status Effects ─────────────────────────────────────────────────────
        /// <summary>Laughing Gas: reverse controls for <paramref name="duration"/> seconds.</summary>
        public void ApplyControlReversal(float duration)
        {
            isControlsReversed = true;
            reverseControlsTimer = duration;
        }

        private void HandleControlReverse()
        {
            if (!isControlsReversed) return;
            reverseControlsTimer -= Time.deltaTime;
            if (reverseControlsTimer <= 0)
                isControlsReversed = false;
        }

        // ── Vine Swing Grapple ─────────────────────────────────────────────────
        public void LaunchToHook(Vector2 hookPosition)
        {
            if (!abilityManager.HasAbility(AbilityType.VineSwing)) return;
            StartCoroutine(SwingToHook(hookPosition));
        }

        private IEnumerator SwingToHook(Vector2 hookPosition)
        {
            Vector2 startPos = transform.position;
            float t = 0;
            float swingTime = 0.5f;
            while (t < swingTime)
            {
                t += Time.deltaTime;
                transform.position = Vector2.Lerp(startPos, hookPosition, t / swingTime);
                yield return null;
            }
            rb.linearVelocity = new Vector2(rb.linearVelocity.x, jumpForce * 1.1f);
        }

        // ── Transformation State ───────────────────────────────────────────────
        /// <summary>Visual/gameplay changes as Seymour's corruption increases.</summary>
        public void ApplyTransformationStage(int stage)
        {
            // Stage 0: human, 1: slight green veins, 2: partial, 3: near-full
            playerAnimator?.SetCorruptionStage(stage);
            if (stage >= 3)
                moveSpeed = 8f; // plant-speed boost at high corruption
        }
    }
}
