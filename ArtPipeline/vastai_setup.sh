#!/usr/bin/env bash
# =============================================================================
# vast.ai ComfyUI Setup — Feed Me: Descent into Madness Art Pipeline
# =============================================================================
# Run this script ONCE on a fresh vast.ai GPU instance after SSH login.
#
# Recommended vast.ai template:
#   Image : pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime  (or any CUDA 12.x)
#   GPU   : RTX 3090 / 4090 / A100  (24 GB+ VRAM recommended)
#   Disk  : 80 GB+  (models are large)
#   Ports : 8188/tcp  (ComfyUI web UI + API)
#
# Usage after SSH:
#   chmod +x vastai_setup.sh
#   ./vastai_setup.sh
# =============================================================================

set -euo pipefail

COMFY_DIR="$HOME/ComfyUI"
MODELS_DIR="$COMFY_DIR/models"
PIPELINE_DIR="$HOME/feedme_pipeline"

echo "============================================================"
echo " Feed Me: Descent into Madness — Art Pipeline Setup"
echo "============================================================"

# ── System deps ────────────────────────────────────────────────────────────────
echo "[1/7] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq git wget curl ffmpeg libgl1 libglib2.0-0 unzip aria2 tmux

# ── ComfyUI ────────────────────────────────────────────────────────────────────
echo "[2/7] Cloning ComfyUI..."
if [ ! -d "$COMFY_DIR" ]; then
    git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFY_DIR"
fi
cd "$COMFY_DIR"
pip install -q -r requirements.txt

# ── ComfyUI Manager (for easy model/node installs) ─────────────────────────────
echo "[3/7] Installing ComfyUI-Manager..."
cd "$COMFY_DIR/custom_nodes"
if [ ! -d "ComfyUI-Manager" ]; then
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git
fi

# ── Custom nodes needed for our workflows ─────────────────────────────────────
echo "[4/7] Installing custom nodes..."
cd "$COMFY_DIR/custom_nodes"

# Efficient nodes (batching + latent upscale)
[ ! -d "comfyui-efficient-nodes" ] && \
    git clone https://github.com/jags111/efficiency-nodes-comfyui.git comfyui-efficient-nodes

# ControlNet preprocessing
[ ! -d "comfyui_controlnet_aux" ] && \
    git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git

# Image resize / crop for sprite sheets
[ ! -d "was-node-suite-comfyui" ] && \
    git clone https://github.com/WASasquatch/was-node-suite-comfyui.git

# Install node requirements
for node_dir in comfyui-efficient-nodes comfyui_controlnet_aux was-node-suite-comfyui; do
    [ -f "$COMFY_DIR/custom_nodes/$node_dir/requirements.txt" ] && \
        pip install -q -r "$COMFY_DIR/custom_nodes/$node_dir/requirements.txt" || true
done

# ── Model Downloads ────────────────────────────────────────────────────────────
echo "[5/7] Downloading models (this takes a while)..."
mkdir -p "$MODELS_DIR"/{checkpoints,vae,loras,controlnet,upscale_models}

# Stable Diffusion XL base (our primary model)
# Using aria2c for parallel chunk downloading
download_if_missing() {
    local url="$1" dest="$2"
    if [ ! -f "$dest" ]; then
        echo "  Downloading $(basename "$dest")..."
        aria2c --console-log-level=warn -x8 -s8 -k1M -o "$(basename "$dest")" \
            -d "$(dirname "$dest")" "$url"
    else
        echo "  Skipping $(basename "$dest") (already exists)"
    fi
}

# SDXL Base 1.0
download_if_missing \
    "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" \
    "$MODELS_DIR/checkpoints/sd_xl_base_1.0.safetensors"

# SDXL Refiner (used for sprite cleanup pass)
download_if_missing \
    "https://huggingface.co/stabilityai/stable-diffusion-xl-refiner-1.0/resolve/main/sd_xl_refiner_1.0.safetensors" \
    "$MODELS_DIR/checkpoints/sd_xl_refiner_1.0.safetensors"

# SDXL VAE fix (prevents grey/washed images)
download_if_missing \
    "https://huggingface.co/madebyollin/sdxl-vae-fp16-fix/resolve/main/sdxl_vae.safetensors" \
    "$MODELS_DIR/vae/sdxl_vae.safetensors"

# ControlNet XL (OpenPose for consistent character poses)
download_if_missing \
    "https://huggingface.co/thibaud/controlnet-openpose-sdxl-1.0/resolve/main/control-lora-openposeXL2-rank256.safetensors" \
    "$MODELS_DIR/controlnet/control-lora-openposeXL2-rank256.safetensors"

# 4x Upscaler (ESRGAN) for final sprite sheet upscale
download_if_missing \
    "https://huggingface.co/lokCX/4x-Ultrasharp/resolve/main/4x-UltraSharp.pth" \
    "$MODELS_DIR/upscale_models/4x-UltraSharp.pth"

# ── Pipeline scripts ────────────────────────────────────────────────────────────
echo "[6/7] Setting up pipeline scripts..."
mkdir -p "$PIPELINE_DIR"
if [ -d /workspace/feedme_pipeline ]; then
    cp -r /workspace/feedme_pipeline/. "$PIPELINE_DIR/"
fi

# ── Launch ComfyUI in background via tmux ─────────────────────────────────────
echo "[7/7] Starting ComfyUI server..."
tmux new-session -d -s comfyui \
    "cd $COMFY_DIR && python main.py --listen 0.0.0.0 --port 8188 --enable-cors-header"

echo ""
echo "============================================================"
echo " Setup complete!"
echo ""
echo " ComfyUI API: http://<vast-ip>:8188"
echo " tmux session: tmux attach -t comfyui"
echo ""
echo " Next steps:"
echo "   cd $PIPELINE_DIR"
echo "   pip install -r requirements.txt"
echo "   python generate_all.py --stage 1"
echo "============================================================"
