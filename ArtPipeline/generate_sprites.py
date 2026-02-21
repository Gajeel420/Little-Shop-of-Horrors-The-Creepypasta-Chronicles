"""
generate_sprites.py
===================
Generates character sprite sheets for Feed Me: Descent into Madness.

Each character has a list of animations, each animation has N frames.
Frames are generated individually (ComfyUI batched KSampler) then assembled
into a Unity-ready sprite sheet PNG using Pillow.

Output layout per character:
  Assets/Art/Sprites/<CharacterName>/<CharacterName>_<animation>.png
  Assets/Art/Sprites/<CharacterName>/<CharacterName>_meta.json   ← frame rects for Unity slicer

Run:
    python generate_sprites.py --host http://<vast-ip>:8188
    python generate_sprites.py --host http://<vast-ip>:8188 --char Seymour
    python generate_sprites.py --host http://<vast-ip>:8188 --char Orin --anim attack
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image
from comfyui_client import ComfyUIClient
from rich.console import Console

console = Console()

# ── Shared style ──────────────────────────────────────────────────────────────
STYLE = (
    "pixel art character sprite, 16-bit SNES style, dark fantasy, "
    "clean black outline, full body visible, centered, "
    "transparent background, single character, no background scenery, "
    "Little Shop of Horrors aesthetic"
)
NEG = (
    "background, scenery, multiple characters, cropped, blurry, "
    "low quality, text, watermark, ui, hud, photorealistic"
)

# ── Frame sizes (at generation resolution, then 4x upscaled) ─────────────────
GEN_FRAME_W = 256
GEN_FRAME_H = 256
OUT_FRAME_W = 128    # Unity import size after downscaling 4x output
OUT_FRAME_H = 128

# ── Character & Animation definitions ────────────────────────────────────────
CHARACTERS: list[dict] = [

    # ── PLAYER ────────────────────────────────────────────────────────────────
    {
        "id": "Seymour",
        "description": "young awkward 1960s florist shop assistant, thick glasses, messy brown hair, "
                       "green apron over white shirt, slightly hunched posture",
        "corruption_variants": True,   # Generate stage 0-3 variants (green skin tint increases)
        "animations": [
            {"id": "idle",          "frames": 4,  "desc": "breathing idle, slight sway"},
            {"id": "run",           "frames": 8,  "desc": "running side view, side-scroller run cycle"},
            {"id": "jump",          "frames": 4,  "desc": "jump arc: crouch, leap, peak, fall"},
            {"id": "fall",          "frames": 2,  "desc": "falling downward"},
            {"id": "attack_shears", "frames": 6,  "desc": "slashing forward with large pruning shears"},
            {"id": "dash",          "frames": 4,  "desc": "lunging forward dash, motion blur"},
            {"id": "vine_swing",    "frames": 4,  "desc": "swinging on vine grapple hook"},
            {"id": "hurt",          "frames": 3,  "desc": "recoiling from hit, pain expression"},
            {"id": "death",         "frames": 8,  "desc": "collapsing and dissolving into plant matter"},
            {"id": "transform_1",   "frames": 6,  "desc": "green veins appearing on skin, grimacing"},
            {"id": "transform_2",   "frames": 6,  "desc": "skin turning green, body elongating"},
            {"id": "transform_3",   "frames": 8,  "desc": "near-complete plant transformation, horror"},
        ],
    },

    # ── MAIN BOSSES ───────────────────────────────────────────────────────────
    {
        "id": "OrinScrivello",
        "description": "1960s sadistic dentist, motorcycle jacket, black gloves, "
                       "reanimated corpse with plant roots visible through skin, "
                       "drill weapon, cracked gas mask, dead black eyes",
        "corruption_variants": False,
        "animations": [
            {"id": "idle",          "frames": 4,  "desc": "twitching reanimated idle, occasional laugh"},
            {"id": "drill_lunge",   "frames": 8,  "desc": "winding up then lunging forward with drill"},
            {"id": "gas_throw",     "frames": 4,  "desc": "hurling laughing gas canister overhead"},
            {"id": "tool_toss",     "frames": 6,  "desc": "rapid-fire dental tool throwing"},
            {"id": "spiral_drill",  "frames": 8,  "desc": "spinning in place with drill extended"},
            {"id": "dizzy",         "frames": 6,  "desc": "staggering, dizzy, mask cracking"},
            {"id": "amalgamate",    "frames": 10, "desc": "body merging with drill apparatus, horror"},
            {"id": "death",         "frames": 8,  "desc": "crumbling to plant fertilizer"},
        ],
    },
    {
        "id": "PatrickMartin",
        "description": "slick 1960s corporate salesman, sharp grey suit, briefcase, "
                       "too-wide smile showing too many teeth, eyes that blink independently, "
                       "plant hybrid form: suit torn revealing Audrey II pod structure beneath",
        "corruption_variants": False,
        "animations": [
            {"id": "idle",           "frames": 4,  "desc": "smiling and gesturing, briefcase tapping"},
            {"id": "multiply",       "frames": 6,  "desc": "splitting into multiple copies"},
            {"id": "contract_throw", "frames": 4,  "desc": "hurling giant contract papers"},
            {"id": "megaphone",      "frames": 4,  "desc": "producing megaphone and blasting shockwave"},
            {"id": "glitch_reveal",  "frames": 8,  "desc": "suit glitching, plant matter underneath"},
            {"id": "vine_tie",       "frames": 6,  "desc": "necktie becoming vine whip"},
            {"id": "consume",        "frames": 8,  "desc": "opening massive plant maw, suction"},
            {"id": "death",          "frames": 8,  "desc": "body dissolving into spores"},
        ],
    },
    {
        "id": "AudreyII",
        "description": "enormous carnivorous alien plant, bright green with red-pink maw, "
                       "thick vines, multiple leaves, bioluminescent veins, "
                       "cosmic horror scale, expressive face, singing mouth",
        "corruption_variants": False,
        "animations": [
            {"id": "pod_idle",       "frames": 4,  "desc": "pod form pulsating, small and ominous"},
            {"id": "bite",           "frames": 6,  "desc": "lunging bite attack with massive jaws"},
            {"id": "vine_whip",      "frames": 6,  "desc": "vine arm slashing across arena"},
            {"id": "spore_exhale",   "frames": 4,  "desc": "exhaling toxic spore cloud from maw"},
            {"id": "hydra_burst",    "frames": 10, "desc": "exploding into 5-head hydra form"},
            {"id": "hydra_idle",     "frames": 4,  "desc": "all 5 heads swaying independently"},
            {"id": "truth_form",     "frames": 8,  "desc": "amalgamating with Seymour, glitching"},
            {"id": "death",          "frames": 12, "desc": "massive explosion of vines and light"},
        ],
    },

    # ── ENEMIES ───────────────────────────────────────────────────────────────
    {
        "id": "CorruptedSucculent",
        "description": "oversized cactus-like plant, pulsating with green veins, "
                       "thorns like hypodermic needles, glowing eyes",
        "corruption_variants": False,
        "animations": [
            {"id": "idle",   "frames": 3, "desc": "slow pulse, thorns extending and retracting"},
            {"id": "attack", "frames": 4, "desc": "burst-firing thorn projectiles in arc"},
            {"id": "death",  "frames": 4, "desc": "wilting and collapsing"},
        ],
    },
    {
        "id": "ShadowStalker",
        "description": "near-invisible shadow humanoid, only outline and white eyes visible, "
                       "wearing tattered 1960s vagrant clothes, clawed hands",
        "corruption_variants": False,
        "animations": [
            {"id": "idle",      "frames": 3, "desc": "barely-visible shimmer"},
            {"id": "teleport",  "frames": 4, "desc": "dissolving and reappearing"},
            {"id": "strike",    "frames": 4, "desc": "fast claw slash"},
            {"id": "death",     "frames": 4, "desc": "dissolving into shadow"},
        ],
    },
    {
        "id": "ContractWraith",
        "description": "floating translucent figure in 1960s business suit, "
                       "face distorted beyond recognition, surrounded by drifting contract papers",
        "corruption_variants": False,
        "animations": [
            {"id": "idle",   "frames": 4, "desc": "floating, papers drifting around"},
            {"id": "attack", "frames": 4, "desc": "hurling binding contract paper"},
            {"id": "death",  "frames": 4, "desc": "papers scattering, body fading"},
        ],
    },
    {
        "id": "ToothGolem",
        "description": "humanoid figure made of compacted teeth and dental tools, "
                       "roughly 4 feet tall, stumbling gait, drills for hands",
        "corruption_variants": False,
        "animations": [
            {"id": "idle",   "frames": 3, "desc": "shuffling in place"},
            {"id": "run",    "frames": 4, "desc": "lurching charge"},
            {"id": "merge",  "frames": 6, "desc": "two golems combining into larger form"},
            {"id": "death",  "frames": 4, "desc": "shattering into tooth shower"},
        ],
    },

    # ── NPCs ──────────────────────────────────────────────────────────────────
    {
        "id": "Audrey_Human",
        "description": "sweet young woman 1960s style, blonde updo, floral dress, "
                       "occasional bruise (Orin's victim), warm kind expression, "
                       "later: ghost/memory version fading at edges",
        "corruption_variants": False,
        "animations": [
            {"id": "idle",     "frames": 4, "desc": "gentle breathing idle, slight smile"},
            {"id": "talk",     "frames": 6, "desc": "speaking, expressive gestures"},
            {"id": "scared",   "frames": 3, "desc": "cowering, fearful"},
            {"id": "ghost",    "frames": 4, "desc": "translucent ghost form, fading edges"},
        ],
    },
    {
        "id": "Mushnik",
        "description": "elderly Jewish florist shop owner, 1960s, "
                       "slightly hunched, apron, reading glasses on chain, "
                       "paranoid and greedy expression, later: puppet/zombie version",
        "corruption_variants": False,
        "animations": [
            {"id": "idle",    "frames": 3, "desc": "counting money, nervous"},
            {"id": "talk",    "frames": 4, "desc": "gesticulating complaint"},
            {"id": "zombie",  "frames": 4, "desc": "plant-controlled puppet, jerky movements"},
        ],
    },
]


def build_jobs(
    workflow_template: dict,
    characters: list[dict],
    base_seed: int = 99999,
) -> list[tuple[dict, list]]:
    """
    Returns list of (character_meta, job_list) tuples.
    Each job generates frames for one animation.
    """
    all_groups = []

    for char in characters:
        char_desc = char["description"]
        corruption_stages = range(4) if char.get("corruption_variants") else [0]

        for corruption in corruption_stages:
            corruption_suffix = f"_c{corruption}" if char["corruption_variants"] else ""
            corruption_mod = {
                0: "",
                1: ", slight green veins under skin",
                2: ", skin turning green, plant stems emerging from body",
                3: ", mostly plant creature, human features barely visible",
            }[corruption]

            jobs: list[dict] = []
            for anim in char["animations"]:
                wf = copy.deepcopy(workflow_template)

                positive = (
                    f"{STYLE}, {char_desc}{corruption_mod}, "
                    f"animation frame: {anim['desc']}, "
                    f"frame {'{frame_num}'} of {anim['frames']}"
                )
                negative = NEG

                # Inject into workflow
                wf["3_positive"]["inputs"]["text"] = positive
                wf["4_negative"]["inputs"]["text"] = negative
                wf["5_latent"]["inputs"]["batch_size"] = anim["frames"]
                wf["5_latent"]["inputs"]["width"]  = GEN_FRAME_W
                wf["5_latent"]["inputs"]["height"] = GEN_FRAME_H
                wf["14_resize"]["inputs"]["width"]  = OUT_FRAME_W * 4  # 4x for upscaler
                wf["14_resize"]["inputs"]["height"] = OUT_FRAME_H * 4

                # Pose reference
                pose_path = (
                    Path(__file__).parent / "pose_references" /
                    f"{char['id']}_{anim['id']}.png"
                )
                if pose_path.exists():
                    wf["7_pose_image"]["inputs"]["image"] = str(pose_path)
                    wf["9_ksampler"]["inputs"]["positive"] = ["8_controlnet_apply", 0]
                    wf["9_ksampler"]["inputs"]["negative"]  = ["8_controlnet_apply", 1]
                else:
                    # Bypass ControlNet — connect directly to CLIP outputs
                    wf["9_ksampler"]["inputs"]["positive"] = ["3_positive", 0]
                    wf["9_ksampler"]["inputs"]["negative"]  = ["4_negative", 0]

                seed = base_seed + hash(f"{char['id']}{anim['id']}{corruption}") % (2**20)

                jobs.append({
                    "workflow":   wf,
                    "seed":       seed & 0xFFFFFFFF,
                    "filename":   f"{char['id']}{corruption_suffix}_{anim['id']}.png",
                    "char_id":    char["id"],
                    "anim_id":    anim["id"],
                    "frame_count": anim["frames"],
                    "corruption": corruption,
                })

            all_groups.append((char, corruption, jobs))

    return all_groups


def assemble_sheet(frames: list[bytes], cols: int, frame_w: int, frame_h: int) -> bytes:
    """Arrange individual frame PNGs into a horizontal sprite sheet."""
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * frame_w, rows * frame_h), (0, 0, 0, 0))

    for idx, frame_bytes in enumerate(frames):
        img = Image.open(BytesIO(frame_bytes)).convert("RGBA")
        img = img.resize((frame_w, frame_h), Image.LANCZOS)
        col = idx % cols
        row = idx // cols
        sheet.paste(img, (col * frame_w, row * frame_h))

    buf = BytesIO()
    sheet.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def build_meta(char_id: str, anim_id: str, frames: int,
               frame_w: int, frame_h: int, cols: int) -> dict:
    """Unity-compatible frame metadata for the sprite sheet slicer."""
    rects = []
    for i in range(frames):
        col = i % cols
        row = i // cols
        rects.append({
            "name":   f"{char_id}_{anim_id}_{i:02d}",
            "x":      col * frame_w,
            "y":      row * frame_h,
            "width":  frame_w,
            "height": frame_h,
            "pivot":  {"x": 0.5, "y": 0.0},
        })
    return {"frames": rects, "frameWidth": frame_w, "frameHeight": frame_h}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",  default="http://127.0.0.1:8188")
    parser.add_argument("--char",  default=None, help="Character ID to generate")
    parser.add_argument("--anim",  default=None, help="Animation ID within character")
    parser.add_argument("--out",   default="../Assets/Art/Sprites")
    parser.add_argument("--seed",  type=int, default=99999)
    parser.add_argument("--cols",  type=int, default=8, help="Columns per sprite sheet")
    args = parser.parse_args()

    targets = CHARACTERS
    if args.char:
        targets = [c for c in CHARACTERS if c["id"] == args.char]
        if not targets:
            console.print(f"[red]Unknown character: {args.char}[/red]")
            sys.exit(1)

    workflow_path = Path(__file__).parent / "workflows" / "sprite_workflow.json"
    workflow_text = workflow_path.read_text()
    # Replace JSON integer placeholders before parsing
    for placeholder, value in [
        ("FRAME_WIDTH", str(GEN_FRAME_W)),
        ("FRAME_HEIGHT", str(GEN_FRAME_H)),
        ("FRAME_COUNT", "1"),          # will be overridden per job
        ("OUTPUT_FRAME_WIDTH",  str(OUT_FRAME_W * 4)),
        ("OUTPUT_FRAME_HEIGHT", str(OUT_FRAME_H * 4)),
        ('"POSE_IMAGE_PATH"', '"__placeholder__"'),
    ]:
        workflow_text = workflow_text.replace(placeholder, value)
    workflow = json.loads(workflow_text)

    all_groups = build_jobs(workflow, targets, base_seed=args.seed)

    client  = ComfyUIClient(args.host)
    out_base = Path(__file__).parent / args.out

    all_meta: dict[str, dict] = {}

    for char, corruption, jobs in all_groups:
        char_id = char["id"]
        c_suffix = f"_c{corruption}" if char.get("corruption_variants") else ""
        char_dir = out_base / char_id
        char_dir.mkdir(parents=True, exist_ok=True)

        for job in jobs:
            if args.anim and job["anim_id"] != args.anim:
                continue

            console.print(f"[cyan]{char_id}{c_suffix}[/cyan] → [yellow]{job['anim_id']}[/yellow] "
                          f"({job['frame_count']} frames)")

            # Generate all frames for this animation
            frame_images: list[bytes] = client.generate(
                job["workflow"],
                seed=job["seed"],
                output_node_ids=["15_save"],
            )

            # Pad to expected frame count if ComfyUI returns fewer
            while len(frame_images) < job["frame_count"]:
                frame_images.append(frame_images[-1])
            frame_images = frame_images[: job["frame_count"]]

            # Assemble sprite sheet
            sheet_bytes = assemble_sheet(
                frame_images, args.cols, OUT_FRAME_W, OUT_FRAME_H
            )

            sheet_path = char_dir / job["filename"]
            sheet_path.write_bytes(sheet_bytes)
            console.print(f"  → [green]{sheet_path}[/green]")

            # Collect metadata
            meta = build_meta(
                char_id, job["anim_id"], job["frame_count"],
                OUT_FRAME_W, OUT_FRAME_H, args.cols,
            )
            anim_key = f"{char_id}{c_suffix}_{job['anim_id']}"
            all_meta[anim_key] = meta

        # Write meta file for Unity sprite slicer
        meta_path = char_dir / f"{char_id}_meta.json"
        # Merge with existing if present
        if meta_path.exists():
            existing = json.loads(meta_path.read_text())
            existing.update(all_meta)
            all_meta = existing
        meta_path.write_text(json.dumps(all_meta, indent=2))

    console.rule("[bold green]Sprite generation complete[/bold green]")


if __name__ == "__main__":
    main()
