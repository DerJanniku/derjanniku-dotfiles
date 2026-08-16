#!/usr/bin/env bash
# ==============================================================================
# Smart Window Mover for Hyprland (Tiled & Floating)
# Author: DerJannik
# ==============================================================================

DIR="$1"
[ -z "$DIR" ] && exit 0

WIN_INFO=$(hyprctl activewindow -j 2>/dev/null)
IS_FLOATING=$(echo "$WIN_INFO" | jq -r '.floating // false' 2>/dev/null)
ADDR_BEFORE=$(echo "$WIN_INFO" | jq -r '.address // ""' 2>/dev/null)
POS_BEFORE=$(echo "$WIN_INFO" | jq -r '.at | join(",")' 2>/dev/null)

if [ "$IS_FLOATING" = "true" ]; then
    case "$DIR" in
        u) hyprctl dispatch moveactive 0 -60 ;;
        d) hyprctl dispatch moveactive 0 60 ;;
        l) hyprctl dispatch moveactive -60 0 ;;
        r) hyprctl dispatch moveactive 60 0 ;;
    esac
    exit 0
fi

# 1. Try standard movewindow
hyprctl dispatch movewindow "$DIR" >/dev/null 2>&1

WIN_AFTER=$(hyprctl activewindow -j 2>/dev/null)
POS_AFTER=$(echo "$WIN_AFTER" | jq -r '.at | join(",")' 2>/dev/null)

# 2. If position did not change
if [ "$POS_BEFORE" = "$POS_AFTER" ]; then
    if [ "$DIR" = "u" ]; then
        # Try swapping with upper window
        hyprctl dispatch swapwindow u >/dev/null 2>&1
        
        WIN_AFTER2=$(hyprctl activewindow -j 2>/dev/null)
        POS_AFTER2=$(echo "$WIN_AFTER2" | jq -r '.at | join(",")' 2>/dev/null)
        
        # If still unchanged, toggle split to make it horizontal (top/bottom) and put active on top
        if [ "$POS_BEFORE" = "$POS_AFTER2" ]; then
            hyprctl dispatch layoutmsg togglesplit >/dev/null 2>&1
            hyprctl dispatch swapwindow u >/dev/null 2>&1
        fi
    elif [ "$DIR" = "d" ]; then
        hyprctl dispatch swapwindow d >/dev/null 2>&1
    elif [ "$DIR" = "l" ]; then
        hyprctl dispatch swapwindow l >/dev/null 2>&1
    elif [ "$DIR" = "r" ]; then
        hyprctl dispatch swapwindow r >/dev/null 2>&1
    fi
fi
