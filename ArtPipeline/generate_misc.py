"""
generate_misc.py
================
Generates all non-sprite, non-background assets:

Categories
----------
  cutscene   — Story beat illustration panels (16:9, used in CutscenePlayer)
  memory     — Memory flashback images (1:1, Hydra head kills / collectibles)
  collectible — Lore item portrait art (1:1, inventory / dialogue box portraits)
  ui         — Title card, main menu art, HUD decorations
  vhs        — Lost Episode corrupted VHS frames
  portrait   — Speaker portraits for DialogueBox (each character headshot)

Run:
    python generate_misc.py --host http://<vast-ip>:8188
    python generate_misc.py --host http://<vast-ip>:8188 --category memory
    python generate_misc.py --host http://<vast-ip>:8188 --id memory_audrey_love
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

STYLE = (
    "dark fantasy illustration, 1960s pop art meets horror, "
    "strong graphic novel linework, bold shadows, "
    "Little Shop of Horrors aesthetic, expressive"
)
NEG = "blurry, low quality, watermark, text, modern, 3d render, anime"

# ── Asset Definitions ─────────────────────────────────────────────────────────

MISC_ASSETS: list[dict] = [

    # ── CUTSCENE PANELS ───────────────────────────────────────────────────────
    {
        "id": "cutscene_orin_opening",
        "category": "cutscene",
        "w": 1920, "h": 1080,
        "prompt": (
            "Orin Scrivello's corpse convulsing in a dental chair, Audrey II vines "
            "retracting from his body, black eyes snapping open, horror moment, "
            "dramatic lighting from a single surgical lamp"
        ),
    },
    {
        "id": "cutscene_stage1_to_2",
        "category": "cutscene",
        "w": 1920, "h": 1080,
        "prompt": (
            "Seymour sitting alone holding a dental license, Audrey II looming 6 feet tall "
            "behind him, small green veins visible on Seymour's hands, dim shop interior, "
            "Patrick Martin entering through door in background"
        ),
    },
    {
        "id": "cutscene_void_fall",
        "category": "cutscene",
        "w": 1920, "h": 1080,
        "prompt": (
            "Seymour falling through void darkness, memory photographs floating around him: "
            "Audrey smiling, Mushnik yelling, blood on hands, cosmic horror scale"
        ),
    },
    {
        "id": "cutscene_truth_reveal",
        "category": "cutscene",
        "w": 1920, "h": 1080,
        "prompt": (
            "Seymour looking at completely green plant-like hands, Audrey's ghost standing "
            "before him in a garden laboratory, scientists in hazmat suits in background, "
            "infant pod with green-veined baby inside on examination table, horror revelation"
        ),
    },
    {
        "id": "cutscene_true_ending",
        "category": "cutscene",
        "w": 1920, "h": 1080,
        "prompt": (
            "peaceful 1960s garden, Seymour and Audrey sitting on a bench together, "
            "warm golden hour sunlight, white picket fence, flowers, "
            "small house in background, hope and peace, emotional"
        ),
    },
    {
        "id": "cutscene_dark_ending",
        "category": "cutscene",
        "w": 1920, "h": 1080,
        "prompt": (
            "Seymour transformed into plant-human hybrid on throne of vines, "
            "crown of thorns, surrounded by mind-controlled smiling humans, "
            "city overgrown in background, reversed triumph, disturbing"
        ),
    },
    {
        "id": "cutscene_golden_ending",
        "category": "cutscene",
        "w": 1920, "h": 1080,
        "prompt": (
            "Seymour holding tiny Audrey II pod in a glass terrarium, Audrey human standing "
            "beside him, flower shop rebuilt, Seymour's hands still slightly green glowing, "
            "bittersweet warmth, sunset through shop windows"
        ),
    },

    # ── MEMORY FLASHBACKS (8 fragments — Audrey's memory) ─────────────────────
    {
        "id": "memory_first_meeting",
        "category": "memory",
        "w": 512, "h": 512,
        "prompt": (
            "Seymour first seeing Audrey, she has a black eye and a sad smile, "
            "flower shop, warm and heartbreaking, memory photograph style, "
            "soft focus edges, nostalgic"
        ),
    },
    {
        "id": "memory_audrey_love",
        "category": "memory",
        "w": 512, "h": 512,
        "prompt": (
            "Audrey saying 'I love you' to Seymour, Seymour not saying it back, "
            "her expression hopeful and vulnerable, his expression distracted and guilty, "
            "memory photograph style"
        ),
    },
    {
        "id": "memory_first_blood",
        "category": "memory",
        "w": 512, "h": 512,
        "prompt": (
            "close up of Seymour's finger bleeding onto Audrey II's leaf, "
            "the plant visibly shuddering with pleasure, "
            "Seymour's expression half-disgusted half-entranced, memory sepia tone"
        ),
    },
    {
        "id": "memory_mushnik_worthless",
        "category": "memory",
        "w": 512, "h": 512,
        "prompt": (
            "Mushnik screaming at young Seymour, finger pointing, Seymour cowering, "
            "the flower shop messy around them, memory photograph style, childhood hurt"
        ),
    },
    {
        "id": "memory_orin_smiling",
        "category": "memory",
        "w": 512, "h": 512,
        "prompt": (
            "Orin's death but Seymour is smiling — disturbing memory corruption, "
            "green tint on Seymour's face, the smile wrong and alien, "
            "horror realization memory"
        ),
    },
    {
        "id": "memory_mushnik_purchase",
        "category": "memory",
        "w": 512, "h": 512,
        "prompt": (
            "document being signed in a dingy office, Mushnik purchasing young Seymour "
            "like a product not adopting a child, notary present, deeply wrong"
        ),
    },
    {
        "id": "memory_pod_birth",
        "category": "memory",
        "w": 512, "h": 512,
        "prompt": (
            "alien seedpod landing on Earth at night, cracking open to reveal infant, "
            "green veins, black eyes, not quite human, cosmic horror scale reduction"
        ),
    },
    {
        "id": "memory_somewhere_green",
        "category": "memory",
        "w": 512, "h": 512,
        "prompt": (
            "Audrey's dream — idyllic small town American home, white picket fence, "
            "garden, safe and warm, the place that was promised, "
            "pure and uncorrupted, emotional"
        ),
    },

    # ── COLLECTIBLE LORE ITEMS ─────────────────────────────────────────────────
    {
        "id": "lore_orin_license",
        "category": "collectible",
        "w": 256, "h": 256,
        "prompt": (
            "tattered 1960s dental license certificate framed behind cracked glass, "
            "Orin Scrivello DDS, slightly blood-stained, collectible item portrait"
        ),
    },
    {
        "id": "lore_mushnik_ledger",
        "category": "collectible",
        "w": 256, "h": 256,
        "prompt": (
            "old leather-bound accounting ledger, Mushnik's Flower Shop, "
            "columns of numbers in cramped handwriting, a few suspicious entries, "
            "collectible item portrait"
        ),
    },
    {
        "id": "lore_audreys_ribbon",
        "category": "collectible",
        "w": 256, "h": 256,
        "prompt": (
            "pale blue hair ribbon on a dirty floor, delicate and sad, "
            "single item portrait, implies loss"
        ),
    },
    {
        "id": "lore_dentist_key",
        "category": "collectible",
        "w": 256, "h": 256,
        "prompt": (
            "old ornate brass key with a tooth-shaped bow, "
            "hanging on a hook, slightly corroded, collectible portrait"
        ),
    },
    {
        "id": "lore_audrey_locket",
        "category": "collectible",
        "w": 256, "h": 256,
        "prompt": (
            "gold heart locket on a chain, open to reveal tiny photograph of Audrey "
            "looking directly at camera, warm and haunting, glowing faintly"
        ),
    },
    {
        "id": "lore_patrick_card",
        "category": "collectible",
        "w": 256, "h": 256,
        "prompt": (
            "business card for Patrick Martin: Exclusive Botanic Ventures Inc, "
            "the ink is shifting and moving, slightly cursed looking"
        ),
    },
    {
        "id": "lore_fertilizer_bag",
        "category": "collectible",
        "w": 256, "h": 256,
        "prompt": (
            "torn bag of fertilizer labelled with a face-like brand logo, "
            "dark liquid seeping from tear, collectible item portrait"
        ),
    },
    {
        "id": "lore_alien_pod",
        "category": "collectible",
        "w": 256, "h": 256,
        "prompt": (
            "small metallic alien crash pod, cracked open, interior shows organic "
            "nest material, clearly not from Earth, collectible portrait"
        ),
    },

    # ── SPEAKER PORTRAITS ──────────────────────────────────────────────────────
    {
        "id": "portrait_seymour",
        "category": "portrait",
        "w": 128, "h": 128,
        "prompt": (
            "Seymour Krelborn headshot portrait, 1960s young man, thick glasses, "
            "nervous expression, green apron, pixel art style, dialogue box portrait"
        ),
    },
    {
        "id": "portrait_seymour_corrupt",
        "category": "portrait",
        "w": 128, "h": 128,
        "prompt": (
            "Seymour Krelborn headshot corrupted, green-tinted skin, black-edged eyes, "
            "disturbing expression, plant veins, dialogue box portrait"
        ),
    },
    {
        "id": "portrait_audrey",
        "category": "portrait",
        "w": 128, "h": 128,
        "prompt": (
            "Audrey headshot portrait, 1960s blonde woman, kind smile, slight bruise, "
            "floral dress, pixel art, dialogue box portrait"
        ),
    },
    {
        "id": "portrait_audrey_ghost",
        "category": "portrait",
        "w": 128, "h": 128,
        "prompt": (
            "Audrey as ghost portrait, translucent, fading at edges, sad but warm smile, "
            "pixel art, dialogue box portrait"
        ),
    },
    {
        "id": "portrait_mushnik",
        "category": "portrait",
        "w": 128, "h": 128,
        "prompt": (
            "Mushnik headshot portrait, elderly florist, reading glasses, suspicious scowl, "
            "apron, pixel art, dialogue box portrait"
        ),
    },
    {
        "id": "portrait_audreyii",
        "category": "portrait",
        "w": 128, "h": 128,
        "prompt": (
            "Audrey II face portrait, enormous alien plant, huge toothy maw, "
            "green and menacing, bioluminescent veins, pixel art, dialogue box portrait"
        ),
    },
    {
        "id": "portrait_orin",
        "category": "portrait",
        "w": 128, "h": 128,
        "prompt": (
            "Orin Scrivello headshot reanimated, motorcycle jacket, cracked gas mask, "
            "black dead eyes, sinister grin, pixel art, dialogue box portrait"
        ),
    },
    {
        "id": "portrait_patrick",
        "category": "portrait",
        "w": 128, "h": 128,
        "prompt": (
            "Patrick Martin headshot, slick grey suit, too-many-teeth smile, "
            "eyes blinking independently, pixel art, dialogue box portrait"
        ),
    },

    # ── UI ART ────────────────────────────────────────────────────────────────
    {
        "id": "ui_title_card",
        "category": "ui",
        "w": 1920, "h": 1080,
        "prompt": (
            "title screen art for 'Little Shop of Horrors: The Creepypasta Chronicles', "
            "Audrey II looming over a tiny Mushnik's flower shop, "
            "1960s horror movie poster aesthetic, bold colours, night scene"
        ),
    },
    {
        "id": "ui_hud_heart",
        "category": "ui",
        "w": 32, "h": 32,
        "prompt": (
            "pixel art heart icon, slightly botanical, leaf texture, "
            "vibrant red-green, HUD element, clean transparent background"
        ),
    },
    {
        "id": "ui_hud_heart_thorn",
        "category": "ui",
        "w": 32, "h": 32,
        "prompt": (
            "pixel art heart icon covered in thorns, corruption stage 3, "
            "dark green, HUD element, transparent background"
        ),
    },
    {
        "id": "ui_hud_thorn_overlay",
        "category": "ui",
        "w": 32, "h": 32,
        "prompt": (
            "pixel art thorn branch overlay, grows over health bar, "
            "dark green with small barbs, transparent background"
        ),
    },

    # ── VHS LOST EPISODE OVERLAYS ─────────────────────────────────────────────
    {
        "id": "vhs_tracking_error",
        "category": "vhs",
        "w": 1920, "h": 1080,
        "prompt": (
            "heavy VHS tape tracking error, horizontal scan lines, colour bleed, "
            "off-track vertical hold, snow static bands, pure distortion overlay"
        ),
    },
    {
        "id": "vhs_timestamp",
        "category": "vhs",
        "w": 256, "h": 64,
        "prompt": (
            "VHS tape timestamp display, REC indicator blinking, "
            "orange LED-style digits showing corrupted date like 00:00:00, "
            "transparent background"
        ),
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",     default="http://127.0.0.1:8188")
    parser.add_argument("--category", default=None,
                        help="Filter by category: cutscene|memory|collectible|ui|vhs|portrait")
    parser.add_argument("--id",       default=None, help="Single asset ID")
    parser.add_argument("--out",      default="../Assets/Art")
    parser.add_argument("--seed",     type=int, default=55555)
    args = parser.parse_args()

    targets = MISC_ASSETS
    if args.id:
        targets = [a for a in MISC_ASSETS if a["id"] == args.id]
        if not targets:
            console.print(f"[red]Unknown asset id: {args.id}[/red]")
            sys.exit(1)
    elif args.category:
        targets = [a for a in MISC_ASSETS if a["category"] == args.category]

    console.rule(f"[bold green]Generating {len(targets)} misc assets[/bold green]")

    workflow_path = Path(__file__).parent / "workflows" / "misc_workflow.json"
    workflow_text = workflow_path.read_text()
    # Replace integer placeholders (will be overridden per job)
    for ph, val in [("TARGET_WIDTH", "512"), ("TARGET_HEIGHT", "512")]:
        workflow_text = workflow_text.replace(ph, val)
    workflow_template = json.loads(workflow_text)

    client   = ComfyUIClient(args.host)
    out_base = Path(__file__).parent / args.out

    jobs = []
    for i, asset in enumerate(targets):
        wf = copy.deepcopy(workflow_template)

        positive = f"{STYLE}, {asset['prompt']}"
        negative = NEG
        wf["3_positive"]["inputs"]["text"] = positive
        wf["4_negative"]["inputs"]["text"] = negative
        wf["10_resize"]["inputs"]["width"]  = asset["w"]
        wf["10_resize"]["inputs"]["height"] = asset["h"]
        # Aspect ratio: set generation latent to match
        wf["5_latent"]["inputs"]["width"]  = min(asset["w"], 1024)
        wf["5_latent"]["inputs"]["height"] = min(asset["h"], 1024)

        cat_dir = {
            "cutscene":   "Cutscenes",
            "memory":     "Memories",
            "collectible":"Collectibles",
            "ui":         "UI",
            "vhs":        "VHS",
            "portrait":   "Portraits",
        }.get(asset["category"], "Misc")

        jobs.append({
            "workflow":    wf,
            "seed":        args.seed + i * 7,
            "filename":    f"{asset['id']}.png",
            "output_subdir": cat_dir,
        })

    # Group by subdirectory
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
    console.print(f"Saved {len(all_saved)} assets to [cyan]{out_base}[/cyan]")


if __name__ == "__main__":
    main()
