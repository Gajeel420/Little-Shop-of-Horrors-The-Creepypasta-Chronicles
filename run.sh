#!/usr/bin/env bash
# Little Shop of Horrors: The Creepypasta Chronicles
# Launcher – handles venv creation automatically.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

# Create venv if it doesn't exist
if [ ! -f "$VENV/bin/python" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install -q pygame
    echo "Done."
fi

# Run the game from the repo root so relative paths work
cd "$SCRIPT_DIR"
exec "$VENV/bin/python" src/main.py
