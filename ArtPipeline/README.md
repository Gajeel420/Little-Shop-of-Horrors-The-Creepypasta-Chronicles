# Art Pipeline — Feed Me: Descent into Madness

Generates all game art via **ComfyUI on vast.ai** using Stable Diffusion XL.

---

## Quick Start

### 1. Spin up a vast.ai instance

| Setting | Value |
|---------|-------|
| Template | `pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime` |
| GPU | RTX 3090 / 4090 / A100 (24 GB+ VRAM) |
| Disk | 80 GB+ |
| Ports | `8188/tcp` (ComfyUI) |

### 2. SSH in and bootstrap

```bash
# Upload this whole ArtPipeline/ folder to the instance
scp -r ArtPipeline/ root@<vast-ip>:/workspace/feedme_pipeline

# SSH in
ssh root@<vast-ip>

# Run setup (downloads ComfyUI, models, custom nodes)
cd /workspace/feedme_pipeline
chmod +x vastai_setup.sh
./vastai_setup.sh
# Takes 15-30 min depending on bandwidth
```

### 3. Install Python deps

```bash
pip install -r /workspace/feedme_pipeline/requirements.txt
```

### 4. Generate everything

```bash
cd /workspace/feedme_pipeline
python generate_all.py --host http://127.0.0.1:8188
# Or target one stage at a time:
python generate_all.py --host http://127.0.0.1:8188 --stage 1
```

### 5. Download output back to your machine

```bash
# From your local machine
scp -r root@<vast-ip>:/workspace/feedme_pipeline/../Assets/Art ./Assets/
```

### 6. Import into Unity

Open Unity → **Window → Feed Me → Art Pipeline Importer** → **Import All Art Assets**

---

## Generators

| Script | What it generates | CLI flags |
|--------|------------------|-----------|
| `generate_backgrounds.py` | All level parallax layers (far/mid/near) | `--stage 1\|2\|3\|special\|all`, `--level <id>` |
| `generate_sprites.py` | Character sprite sheets + meta.json | `--char <id>`, `--anim <id>` |
| `generate_misc.py` | Cutscenes, memories, portraits, UI, VHS | `--category <cat>`, `--id <id>` |
| `generate_all.py` | Runs all three in order | `--only backgrounds\|sprites\|misc` |

---

## Output Structure

```
Assets/Art/
├── Backgrounds/
│   ├── Stage1/
│   │   ├── S1L1_greenhouse_far.png
│   │   ├── S1L1_greenhouse_mid.png
│   │   ├── S1L1_greenhouse_near.png
│   │   └── ...
│   ├── Stage2/
│   ├── Stage3/
│   └── Special/
│
├── Sprites/
│   ├── Seymour/
│   │   ├── Seymour_idle.png          ← 8-frame sprite sheet
│   │   ├── Seymour_run.png
│   │   ├── Seymour_c1_idle.png       ← corruption variant
│   │   ├── Seymour_meta.json         ← frame rects for Unity slicer
│   │   └── ...
│   ├── OrinScrivello/
│   ├── PatrickMartin/
│   ├── AudreyII/
│   └── ...
│
├── Cutscenes/
├── Memories/
├── Collectibles/
├── Portraits/
├── UI/
└── VHS/
```

---

## Workflows

| File | Used by | Resolution |
|------|---------|-----------|
| `workflows/background_workflow.json` | `generate_backgrounds.py` | 3840×2160 (4K parallax) |
| `workflows/sprite_workflow.json` | `generate_sprites.py` | 128×128 per frame, assembled into sheet |
| `workflows/misc_workflow.json` | `generate_misc.py` | Per-asset (32×32 → 1920×1080) |

All workflows use **SDXL Base 1.0 + Refiner + 4x-UltraSharp upscaler**.
Sprite sheets use **ControlNet OpenPose** for consistent character poses.

---

## Pose References

Place OpenPose skeleton PNGs in `pose_references/<CharID>_<animID>.png`.
See `pose_references/README.md` for tools and naming conventions.

---

## Regenerating Individual Assets

```bash
# One background level
python generate_backgrounds.py --host http://<ip>:8188 --level S1L1_greenhouse

# One character
python generate_sprites.py --host http://<ip>:8188 --char Seymour

# One animation only
python generate_sprites.py --host http://<ip>:8188 --char Seymour --anim run

# One misc asset
python generate_misc.py --host http://<ip>:8188 --id portrait_seymour

# One category
python generate_misc.py --host http://<ip>:8188 --category memory
```

---

## Style Consistency

Every prompt is prefixed with the shared `STYLE_BASE` token defined at the top
of each generator. To reskin the entire game, change that one string.

Stage palette modifiers in `generate_backgrounds.py`:
- **Stage 1**: Vibrant 1960s Technicolor, warm amber + green
- **Stage 2**: Desaturated flesh tones, sickly pink + bile yellow
- **Stage 3**: Near-monochrome, void black + bioluminescent green

Character corruption variants (Seymour only) are generated at all 4 stages
by passing `corruption_variants: True` in `CHARACTERS`.

---

## Estimated Generation Time (RTX 4090)

| Category | Count | Time each | Total |
|----------|-------|-----------|-------|
| Backgrounds | 14 sets × 3 layers = 42 | ~45s | ~32 min |
| Sprite sheets | 11 chars × avg 7 anims = 77 + 4 corruption vars = ~120 | ~60s | ~2 hrs |
| Misc assets | ~40 | ~30s | ~20 min |
| **Total** | | | **~3 hours** |
