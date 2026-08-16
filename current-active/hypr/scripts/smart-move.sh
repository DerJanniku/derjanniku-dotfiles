#!/usr/bin/env bash
# ==============================================================================
# Smart Window Mover for Hyprland (Tiled & Floating)
# Author: DerJannik
# ==============================================================================

DIR="$1"
[ -z "$DIR" ] && exit 0

WIN_INFO=$(hyprctl activewindow -j 2>/dev/null)
IS_FLOATING=$(echo "$WIN_INFO" | jq -r '.floating // false' 2>/dev/null)

if [ "$IS_FLOATING" = "true" ]; then
    case "$DIR" in
        u) hyprctl dispatch moveactive 0 -60 ;;
        d) hyprctl dispatch moveactive 0 60 ;;
        l) hyprctl dispatch moveactive -60 0 ;;
        r) hyprctl dispatch moveactive 60 0 ;;
    esac
else
    # Try movewindow in direction
    hyprctl dispatch movewindow "$DIR" >/dev/null 2>&1
    
    # Ensure Up moves/swaps to the upper container
    if [ "$DIR" = "u" ]; then
        hyprctl dispatch swapwindow u >/dev/null 2>&1 || true
    fi
fi
