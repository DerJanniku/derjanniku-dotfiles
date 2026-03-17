#!/bin/bash

# ==============================================================================
# PROFESSIONAL Wallpaper Dashboard Launcher
# ==============================================================================

PYTHON_SCRIPT="$HOME/bin/wallpaper-dashboard.py"

# Falls das Python-Skript existiert, starte es direkt (beste UI)
if [ -f "$PYTHON_SCRIPT" ]; then
    python3 "$PYTHON_SCRIPT"
else
    # Fallback auf einfaches Rofi, falls Python fehlt (was es nicht sollte)
    notify-send "Wallpaper Dashboard" "Starting fallback selector..."
    ~/.config/rofi/wallpaper-launcher.sh.bak
fi
