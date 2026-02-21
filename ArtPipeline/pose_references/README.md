# Pose References

Place OpenPose skeleton images here to guide character sprite generation.

## Naming convention

`<CharacterID>_<animationID>.png`

Examples:
- `Seymour_run.png`
- `Seymour_attack_shears.png`
- `OrinScrivello_drill_lunge.png`

## How to create pose images

1. Draw a stick-figure skeleton on a black background using the OpenPose color scheme:
   - Nose: red dot
   - Neck, shoulders, hips: colored circles
   - Limb connections: colored lines
2. Export at 256×256 pixels (matches GEN_FRAME_W/H in generate_sprites.py)
3. Drop here — generate_sprites.py auto-detects and applies ControlNet

## Free tools for making pose references

- **ControlNet OpenPose Editor** (browser): https://huchenlei.github.io/sd-webui-openpose-editor/
- **PoseMy.Art** (3D poser): https://posemy.art/
- **Magicpose** (ComfyUI node): included in comfyui_controlnet_aux

## Without pose references

If no `.png` exists for a given character+animation, the ControlNet node is
bypassed and SDXL generates poses freely. This is fine for idle/death/hit
animations but may produce inconsistent poses for action frames.
