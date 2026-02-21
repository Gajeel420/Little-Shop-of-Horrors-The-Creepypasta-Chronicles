"""
generate_backgrounds.py
=======================
Generates all background art for Feed Me: Descent into Madness.

Every level has:
  - A FAR layer   (sky / deep background)  — parallax depth 0.1
  - A MID layer   (main set dressing)      — parallax depth 0.4
  - A NEAR layer  (foreground silhouettes) — parallax depth 0.8

All prompts share a unified style token so every stage looks cohesive.
Corruption level controls colour palette and horror intensity.

Run:
    python generate_backgrounds.py --host http://<vast-ip>:8188 --stage all
    python generate_backgrounds.py --host http://<vast-ip>:8188 --stage 1
    python generate_backgrounds.py --host http://<vast-ip>:8188 --level 1-2
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

from comfyui_client import ComfyUIClient
from rich.console import Console

console = Console()

# ── Style tokens ──────────────────────────────────────────────────────────────
# Injected into every prompt. Change once to reskin the whole game.
STYLE_BASE = (
    "pixel art, 16-bit SNES aesthetic, dark fantasy side-scroller background, "
    "hand-painted details, strong silhouette contrast, cel-shaded shadows, "
    "Little Shop of Horrors inspired, botanical horror"
)

NEGATIVE_BASE = (
    "blurry, low quality, jpeg artifacts, watermark, text, signature, "
    "modern photography, 3d render, overexposed, flat colours, anime"
)

# Stage palette modifiers — applied on top of STYLE_BASE
STAGE_PALETTES = {
    1: "vibrant 1960s Technicolor palette, warm amber and green tones, lush overgrown",
    2: "desaturated flesh-toned palette, sickly pink and bile yellow, body horror",
    3: "near-monochrome, deep space void black, sickly bioluminescent green, cosmic horror",
}

# ── Background definitions ────────────────────────────────────────────────────
# Keys match Unity scene names from GameManager.StageScenes
BACKGROUNDS: list[dict] = [

    # ── STAGE 1 ───────────────────────────────────────────────────────────────
    {
        "id": "S1L1_greenhouse",
        "scene": "Stage1_1_MushnksCursedGreenhouse",
        "stage": 1,
        "layers": {
            "far":  "back wall of a 1960s florist shop, cracked glass greenhouse roof, "
                    "vines creeping through ceiling, dim greenish light filtering in, empty",
            "mid":  "overgrown flower shop interior, pulsating glowing vines covering shelves, "
                    "wilted and corrupted succulents, dental-white fluorescent lights flickering",
            "near": "silhouette of massive thorned vines arching across bottom frame, "
                    "potted plant silhouettes, scattered fertilizer bags",
        },
    },
    {
        "id": "S1L2_roots",
        "scene": "Stage1_2_UndergroundRootSystem",
        "stage": 1,
        "layers": {
            "far":  "deep underground cavern, dim bioluminescent root veins glowing faint green, "
                    "compacted soil ceiling with exposed pipes",
            "mid":  "labyrinth of enormous twisted roots, hanging parasitic seedpods, "
                    "pockets of toxic yellow spores drifting in air",
            "near": "thick root silhouettes crossing bottom third of frame, puddles reflecting "
                    "green glow, scattered bones and old tools half-buried",
        },
    },
    {
        "id": "S1L3_skidrow",
        "scene": "Stage1_3_SkidRowAfterDark",
        "stage": 1,
        "layers": {
            "far":  "perpetual night sky, no stars, thick fog above rooftops, "
                    "distant flickering neon signs (Out of Business, dentist cross)",
            "mid":  "1960s Skid Row street at night, abandoned storefronts, rusted fire escapes, "
                    "broken streetlights, tendrils of fog, dumpsters overflowing with plants",
            "near": "cracked sidewalk silhouette, fire hydrant wrapped in vines, "
                    "newspaper scraps blowing, shadow puddles",
        },
    },
    {
        "id": "S1_boss_arena",
        "scene": "Boss1_OrinScrivello",
        "stage": 1,
        "layers": {
            "far":  "1960s dental office interior, mint-green wallpaper with faded tooth pattern, "
                    "framed dental licences on wall, diplomas, single window night outside",
            "mid":  "circular dental arena, 4 reclined dental chairs as cover, "
                    "central chrome drill apparatus, shattered mirrors on walls, "
                    "nitrous oxide tanks with cracked valves, blood splatter",
            "near": "dental tool silhouettes scattered on floor, broken mirror shards, "
                    "gas-stained ceiling tiles",
        },
    },

    # ── STAGE 2 ───────────────────────────────────────────────────────────────
    {
        "id": "S2L1_feeding_floor",
        "scene": "Stage2_1_FeedingFloor",
        "stage": 2,
        "layers": {
            "far":  "vaulted cathedral interior built entirely from organic flesh and plant matter, "
                    "ribbed arches of exposed root and bone, faint red bioluminescence",
            "mid":  "the Feeding Floor — stomach acid pools glowing green on stone floor, "
                    "half-digested victims embedded in walls, bile dripping from ceiling vines",
            "near": "acid pool silhouette foreground, digestive tract tube openings in floor",
        },
    },
    {
        "id": "S2L2_corridors",
        "scene": "Stage2_2_ClientCorridors",
        "stage": 2,
        "layers": {
            "far":  "infinite 1960s waiting room hallway vanishing into darkness, "
                    "identical doors repeating, wrong perspective, liminal horror",
            "mid":  "waiting room with plastic chairs, product advertisement posters "
                    "whose faces are smeared, a reception desk with tentacle reaching over",
            "near": "foreground chairs silhouette, worn linoleum floor tiles, "
                    "flickering fluorescent tube light",
        },
    },
    {
        "id": "S2L3_penthouse",
        "scene": "Stage2_3_SuccessIllusion",
        "stage": 2,
        "layers": {
            "far":  "luxury penthouse apartment skyline view, but buildings are slightly wrong, "
                    "reality glitch edges, sky tinted sickly yellow-green",
            "mid":  "penthouse interior, gold record frames on walls, "
                    "photo frames showing blurred faces, mirrors that show wrong reflection, "
                    "vines breaking through the parquet floor",
            "near": "plush carpet foreground, broken mirror shards, golden rose thorns",
        },
    },
    {
        "id": "S2_boss_arena",
        "scene": "Boss2_PatrickMartin",
        "stage": 2,
        "layers": {
            "far":  "infinite boardroom extending into darkness, walls covered in scrolling "
                    "contract fine print that bleeds, overhead projector light beam",
            "mid":  "long conference table stretching to infinity, walls bleeding contracts, "
                    "mirror-polished floor reflecting wrong versions of room",
            "near": "conference table surface silhouette, scattered briefcases, contract papers",
        },
    },

    # ── STAGE 3 ───────────────────────────────────────────────────────────────
    {
        "id": "S3L1_eclipse",
        "scene": "Stage3_1_TotalEclipse",
        "stage": 3,
        "layers": {
            "far":  "deep space, total solar eclipse dominating upper right, "
                    "flesh-textured planets orbiting, screaming star formations",
            "mid":  "asteroid field of giant seedpods tumbling in zero gravity, "
                    "reality tears showing void beneath, bioluminescent spore clouds",
            "near": "broken rock silhouettes floating, alien pod fragments, "
                    "void tendrils reaching up from bottom of frame",
        },
    },
    {
        "id": "S3L2_garden_planet",
        "scene": "Stage3_2_GardenPlanet",
        "stage": 3,
        "layers": {
            "far":  "alien planet surface, sky filled with rings of plant matter, "
                    "giant carnivorous plants like trees on horizon, "
                    "skeletal ruins of previous civilizations",
            "mid":  "endless field of adult-sized Audrey II variants, "
                    "root colossi in mid-ground, bones of consumed worlds half-buried",
            "near": "massive root silhouettes, alien soil ground, skeletal hand emerging",
        },
    },
    {
        "id": "S3L3_singing_void",
        "scene": "Stage3_3_SingingVoid",
        "stage": 3,
        "layers": {
            "far":  "inside the consciousness of the plant collective, "
                    "pure void with floating memories like photographs, "
                    "fragments of Seymour's past drifting in darkness",
            "mid":  "abstract mental landscape, corrupted VHS static patches, "
                    "glitched versions of Mushnik's shop floating in pieces, "
                    "guilt manifestations as dark amorphous shapes",
            "near": "ground dissolving into void, broken tile fragments floating",
        },
    },
    {
        "id": "S3_boss_arena",
        "scene": "Boss3_AudreyII",
        "stage": 3,
        "layers": {
            "far":  "spherical arena floating in space, Earth visible in background covered in vines, "
                    "giant Audrey II pods orbiting like green moons",
            "mid":  "arena platform surface, reality glitching between different timelines, "
                    "mirrors everywhere showing different versions of same moment",
            "near": "shattered mirror shards floating as platforms, vine shadows below",
        },
    },

    # ── SPECIAL SCENES ────────────────────────────────────────────────────────
    {
        "id": "ending_green",
        "scene": "SomewhereThatSGreen",
        "stage": 0,
        "layers": {
            "far":  "idyllic 1960s small-town America sky, warm golden hour sunlight, "
                    "fluffy white clouds, peaceful and uncorrupted",
            "mid":  "beautiful flower garden, white picket fence, small cottage house, "
                    "real flowers (not carnivorous), Audrey's dream come true",
            "near": "garden path foreground, flower bed silhouettes",
        },
    },
    {
        "id": "lost_episode",
        "scene": "LostEpisode_VHS",
        "stage": 2,
        "layers": {
            "far":  "corrupted VHS tape aesthetic, heavy scan-line distortion, "
                    "colour bleed, off-track vertical hold, 1980s public access TV",
            "mid":  "Mushnik's shop but wrong — furniture in wrong positions, "
                    "Audrey II in corner watching, everything slightly too dark",
            "near": "heavy VHS grain overlay, timestamp counter bottom-left",
        },
    },
]

# ── Main ──────────────────────────────────────────────────────────────────────

def build_prompt(bg: dict, layer: str) -> tuple[str, str]:
    stage = bg["stage"]
    palette = STAGE_PALETTES.get(stage, "")
    layer_desc = bg["layers"][layer]
    layer_tag = {"far": "distant background layer", "mid": "midground layer",
                 "near": "foreground silhouette layer"}[layer]

    positive = (
        f"{STYLE_BASE}, {palette}, "
        f"{layer_tag}, {layer_desc}, "
        f"seamlessly tileable horizontally, no characters, environment only"
    )
    negative = (
        f"{NEGATIVE_BASE}, characters, people, player sprite, "
        f"UI elements, foreground figures"
        if layer != "near" else
        f"{NEGATIVE_BASE}, characters, people, player sprite, UI elements"
    )
    return positive, negative


def build_jobs(
    workflow_template: dict,
    backgrounds: list[dict],
    base_seed: int = 12345,
) -> list[dict]:
    jobs = []
    for i, bg in enumerate(backgrounds):
        for layer in ["far", "mid", "near"]:
            wf = copy.deepcopy(workflow_template)
            positive, negative = build_prompt(bg, layer)

            # Inject prompts into CLIP nodes
            wf["3_positive_clip"]["inputs"]["text"] = positive
            wf["4_negative_clip"]["inputs"]["text"] = negative
            wf["8_refiner_pos"]["inputs"]["text"] = positive
            wf["9_refiner_neg"]["inputs"]["text"] = negative

            # Near-layer: skip upscale, output at native 1920x1088
            if layer == "near":
                wf["14_resize_output"]["inputs"]["width"] = 1920
                wf["14_resize_output"]["inputs"]["height"] = 1088

            seed = base_seed + i * 3 + {"far": 0, "mid": 1, "near": 2}[layer]
            stage_folder = f"Stage{bg['stage']}" if bg["stage"] > 0 else "Special"
            filename = f"{bg['id']}_{layer}.png"

            jobs.append({
                "workflow":    wf,
                "seed":        seed,
                "filename":    filename,
                "output_subdir": stage_folder,
                "bg_id":       bg["id"],
                "layer":       layer,
            })
    return jobs


def main():
    parser = argparse.ArgumentParser(description="Generate backgrounds for Feed Me")
    parser.add_argument("--host",  default="http://127.0.0.1:8188", help="ComfyUI API host")
    parser.add_argument("--stage", default="all",
                        help="Stage to generate: all | 1 | 2 | 3 | special")
    parser.add_argument("--level", default=None,
                        help="Single level ID, e.g. S1L1_greenhouse")
    parser.add_argument("--out",   default="../Assets/Art/Backgrounds",
                        help="Output directory (relative to ArtPipeline/)")
    parser.add_argument("--seed",  type=int, default=12345)
    args = parser.parse_args()

    # Filter backgrounds
    if args.level:
        targets = [b for b in BACKGROUNDS if b["id"] == args.level]
        if not targets:
            console.print(f"[red]Unknown level id: {args.level}[/red]")
            sys.exit(1)
    elif args.stage == "all":
        targets = BACKGROUNDS
    elif args.stage == "special":
        targets = [b for b in BACKGROUNDS if b["stage"] == 0]
    else:
        stage_num = int(args.stage)
        targets = [b for b in BACKGROUNDS if b["stage"] == stage_num]

    console.rule(f"[bold green]Generating {len(targets)} background sets[/bold green]")

    workflow_path = Path(__file__).parent / "workflows" / "background_workflow.json"
    workflow = json.loads(workflow_path.read_text())

    jobs = build_jobs(workflow, targets, base_seed=args.seed)

    client = ComfyUIClient(args.host)
    out_base = Path(__file__).parent / args.out

    # Group by output subdir
    from collections import defaultdict
    by_subdir: dict[str, list] = defaultdict(list)
    for job in jobs:
        by_subdir[job["output_subdir"]].append(job)

    all_saved = []
    for subdir, subdir_jobs in by_subdir.items():
        out_dir = out_base / subdir
        saved = client.queue_batch(subdir_jobs, out_dir)
        all_saved.extend(saved)

    console.rule("[bold green]Done[/bold green]")
    console.print(f"Saved {len(all_saved)} background layers to [cyan]{out_base}[/cyan]")


if __name__ == "__main__":
    main()
