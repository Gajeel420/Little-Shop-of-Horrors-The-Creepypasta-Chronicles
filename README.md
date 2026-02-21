# Little Shop of Horrors: The Creepypasta Chronicles

A Metroidvania-style horror game built in **Unity (2D)** that blends the dark comedy of *Little Shop of Horrors* with creepypasta horror aesthetics.

---

## Game Overview

You play as Seymour Krelborn. After feeding Audrey II, her influence warps reality itself, pulling you through three interconnected nightmare realms — each representing a deeper stage of your own corruption.

### Stages
| Stage | Theme | Boss |
|-------|-------|------|
| 1 – The Withering Garden | Botanical Horror & Decay | Orin Scrivello, DDS (Reanimated) |
| 2 – The Consumption District | Body Horror & Transformation | Patrick Martin (The Salesman Entity) |
| 3 – The Outer Darkness | Cosmic Horror & The Origin | Audrey II – "Mean Green Mother" |

### Endings
- **Bad End**: Feed the plant, become fertilizer
- **Normal End**: Destroy Audrey II, but spores escape
- **True End**: Realize you're the plant — choose self-destruction to save reality
- **Secret/Golden End**: Use Audrey's Locket to find balance — become the Guardian

---

## Engine

**Unity 2022+ (2D)**

Recommended packages:
- Universal Render Pipeline (URP) — for post-processing corruption effects
- Cinemachine — for smooth 2D camera & boss arena transitions
- Input System (new) — for remappable controls & dialogue advance
- TextMeshPro — for dialogue box and creepypasta overlay text
- Unity Tilemaps — for all level layout
- Unity Timeline / Playables — for cutscenes

---

## Project Structure

```
Assets/
├── Scripts/
│   ├── Player/
│   │   ├── PlayerController.cs     # Movement, dash, vine swing, transformation
│   │   ├── PlayerHealth.cs         # Hearts, DOT, death & Mushnik death counter
│   │   └── PlayerAnimator.cs       # Animator bridge + corruption tint stages
│   │
│   ├── Abilities/
│   │   ├── AbilityType.cs          # Enum of all 11 abilities
│   │   ├── AbilityManager.cs       # Unlock registry, cooldowns, active ability effects
│   │   └── AbilityGate.cs          # World barriers requiring specific abilities
│   │
│   ├── Bosses/
│   │   ├── BossBase.cs             # HP, phase transitions, death sequence base
│   │   ├── Orin/
│   │   │   ├── OrinBoss.cs         # 3-phase Orin fight (Drill→Amalgamation)
│   │   │   ├── DrillApparatus.cs   # Rotating laser drill (Phase 2 arena hazard)
│   │   │   └── GasCanister.cs      # Throwable laughing gas bomb
│   │   ├── Patrick/
│   │   │   ├── PatrickBoss.cs      # 3-phase Patrick fight (Salesman→Hybrid)
│   │   │   ├── PatrickClone.cs     # Mirror-floor clone mechanic
│   │   │   └── ContractBriefcase.cs # Projectile that spawns contract traps
│   │   └── AudreyII/
│   │       ├── AudreyIIBoss.cs     # 3-phase + final choice (Pod→Hydra→Truth)
│   │       ├── HydraHead.cs        # 5 independent heads (Fire/Ice/Poison/Lightning/Center)
│   │       └── MirrorWeakPoint.cs  # Phase 3 mirror that shows true Seymour
│   │
│   ├── Enemies/
│   │   ├── EnemyBase.cs            # Patrol, aggro, damage, Mushnik's Ledger support
│   │   ├── ToothGolem.cs           # Orin summon — merges if ignored
│   │   ├── Stage1/
│   │   │   ├── CorruptedSucculent.cs  # Thorn-burst turret, 1-hit by Pruning Shears
│   │   │   └── ShadowStalker.cs       # Near-invisible, teleports behind player
│   │   ├── Stage2/
│   │   │   └── ContractWraith.cs   # Loops endlessly, grows more distorted each loop
│   │   └── Stage3/
│   │       └── VoidTendril.cs      # Grab enemy, Nitrous Dash breaks free
│   │
│   ├── Environment/
│   │   ├── AcidPool.cs             # DOT hazard, Photosynthesis freezes it
│   │   ├── LightZone.cs            # Photosynthesis heal zones
│   │   ├── OxygenTank.cs           # Orin Phase 3 — break 4 in 15s or die
│   │   └── Collectible.cs          # Memory Fragments (x8), Lore Items, Heart Containers
│   │
│   ├── Narrative/
│   │   ├── NarrativeManager.cs     # Cutscenes, dialogue, death lines, memory flashbacks
│   │   ├── DialogueBox.cs          # Typewriter dialogue, reversed text support
│   │   ├── CutscenePlayer.cs       # VideoClip / Playable Timeline cutscene router
│   │   └── SpeakerPortraitLibrary.cs  # ScriptableObject: speaker name → portrait sprite
│   │
│   ├── UI/
│   │   ├── HUDManager.cs           # Hearts, boss bar, ability icons, creepypasta overlays
│   │   └── CreepypastaEffects.cs   # The Watcher, world desaturation, Numbers Station, NPC glitch
│   │
│   ├── Audio/
│   │   └── AudioManager.cs         # Crossfade, doo-wop → horror corruption, boss themes
│   │
│   └── Systems/
│       ├── GameManager.cs          # Stage progression, corruption tracking, endings
│       ├── CombatManager.cs        # Attack hitbox, damage stack, crit blood FX
│       └── SaveSystem.cs           # PlayerPrefs save: deaths, abilities, collectibles, start date
│
├── Prefabs/          # Enemy, hazard, FX, UI element prefabs
├── Scenes/           # One scene per level + boss arenas + ending cutscenes
├── Animations/       # Animator controllers for player, enemies, bosses
├── Audio/            # Music tracks, SFX clips
└── Art/
    ├── Sprites/      # Character, enemy, tile sprites
    └── Tilemaps/     # Tilemap palettes per stage
```

---

## Ability Progression

| Ability | Source | Effect |
|---------|--------|--------|
| Pruning Shears | Stage 1 start | Cut vines, basic melee; 1-hit succulents |
| Nitrous Dash | Orin defeated | Invincible dash through enemies/hazards |
| Blood Contract | Patrick defeated | Reveal hidden platforms; invincibility at HP cost |
| Vine Swing | Stage 2-2 | Grapple hooks, double jump |
| Photosynthesis | Stage 2-3 | Heal in light zones; freeze acid pools; temp platforms |
| Dentist's Tools | Tooth Golem drop | Break metal barriers, open locked doors |
| Audrey's Locket | All 8 memory fragments | See through illusions; required for Golden Ending |
| Mushnik's Ledger | Optional | Show enemy HP and weaknesses |
| Skid Row Blues | Optional | Charm vagrant NPCs |
| Feed Me Seymour | Optional | Sacrifice HP for massive damage burst |
| Somewhere That's Green | NG+ | Slow time; all ability costs halved |

---

## Creepypasta Elements

- **The Loop**: Mushnik counts your deaths ("You've died 27 times, Seymour...")
- **The Watcher**: Shadow figure in backgrounds. Never acknowledged. Disappears silently if you get close.
- **Glitched NPCs**: T-poses, reversed dialogue
- **Save Corruption**: "Your save file is hungry" on death milestones
- **Desaturating World**: Starts in vibrant 1960s color palette, drains to monochrome by Stage 3
- **HUD Corruption**: Thorns grow over your health bar as corruption increases
- **Numbers Station**: Random ambient radio broadcasts coordinates in human teeth
- **Lost Episode**: Secret level styled as corrupted VHS footage
- **Hyperrealistic Blood**: Critical hits trigger disturbing particle effect
- **Patrick's Contract**: The predatory contract contains your actual real-world save-file start date

---

## Development Setup

1. Install **Unity 2022.3 LTS** or later
2. Open the project folder in Unity Hub
3. Install required packages via Package Manager (URP, Cinemachine, Input System, TextMeshPro)
4. Open `Assets/Scenes/MainMenu` as the start scene
5. Configure Build Settings: add all scenes from `Assets/Scenes/` in order matching `GameManager.StageScenes`
