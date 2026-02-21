namespace FeedMe
{
    /// <summary>
    /// All abilities Seymour can unlock throughout the game.
    /// Ordered roughly by acquisition order.
    /// </summary>
    public enum AbilityType
    {
        // ── Core (story-required) ──────────────────────────────────────────────
        PruningShears,      // Stage 1 start: cut vines, basic melee attack
        NitrousDash,        // Orin boss reward: invincible dash
        BloodContract,      // Patrick boss reward: reveal secrets, invincibility at HP cost
        VineSwing,          // Stage 2-2: grapple hooks / double jump
        Photosynthesis,     // Stage 2-3: heal in lit areas, grow temp platforms
        DentistTools,       // Dropped by Orin's Tooth Golems: break metal barriers
        AudreysLocket,      // Collectible (need all 8 memory fragments): see illusions

        // ── Optional / Secret ──────────────────────────────────────────────────
        MushniksLedger,     // Show enemy HP and weaknesses
        SkidRowBlues,       // Charm vagrant NPCs for hints / shortcuts
        FeedMeSeymour,      // Sacrifice HP for powerful single attack

        // ── New Game+ ──────────────────────────────────────────────────────────
        SomewhereThatSGreen // NG+ power: brief slow-time + all ability costs halved
    }
}
