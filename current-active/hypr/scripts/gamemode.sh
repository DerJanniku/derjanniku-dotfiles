#!/usr/bin/env bash
# ==============================================================================
# Ultra-FPS Gaming Mode Toggle for Hyprland
# ==============================================================================

STATE_FILE="/tmp/hypr_gamemode_active"

enable_gamemode() {
    touch "$STATE_FILE"
    hyprctl --batch "\
        keyword animations:enabled 0;\
        keyword decoration:shadow:enabled 0;\
        keyword decoration:blur:enabled 0;\
        keyword decoration:rounding 0;\
        keyword decoration:active_opacity 1.0;\
        keyword decoration:inactive_opacity 1.0;\
        keyword general:gaps_in 0;\
        keyword general:gaps_out 0;\
        keyword general:border_size 1;\
        keyword misc:vrr 1" > /dev/null 2>&1

    notify-send -a "GameMode" "🎮 Ultra-FPS Game Mode" "Aktiviert: Blur & Animationen aus für maximale 200 FPS." -t 2000 -i "applications-games"
    pkill -SIGRTMIN+8 waybar 2>/dev/null || true
}

disable_gamemode() {
    rm -f "$STATE_FILE"
    hyprctl --batch "\
        keyword animations:enabled 1;\
        keyword decoration:shadow:enabled 1;\
        keyword decoration:blur:enabled 0;\
        keyword decoration:rounding 15;\
        keyword decoration:active_opacity 0.90;\
        keyword decoration:inactive_opacity 0.80;\
        keyword general:gaps_in 6;\
        keyword general:gaps_out 12;\
        keyword general:border_size 3;\
        keyword misc:vrr 1" > /dev/null 2>&1
    hyprctl reload > /dev/null 2>&1

    notify-send -a "GameMode" "✨ Desktop Ästhetik-Modus" "Wiederhergestellt: Klare Transparenz & Animationen aktiv." -t 2000 -i "preferences-desktop-theme"
    pkill -SIGRTMIN+8 waybar 2>/dev/null || true
}

toggle_gamemode() {
    if [ ! -f "$STATE_FILE" ]; then
        enable_gamemode
    else
        disable_gamemode
    fi
}

case "$1" in
    on)
        [ ! -f "$STATE_FILE" ] && enable_gamemode
        ;;
    off)
        [ -f "$STATE_FILE" ] && disable_gamemode
        ;;
    status)
        if [ -f "$STATE_FILE" ]; then
            echo '{"text": "🎮 GAME MODE", "class": "active", "tooltip": "Game Mode AKTIV (Klick zum Deaktivieren)"}'
        else
            # Leere Ausgabe wenn aus, damit Waybar das Modul vollständig ausblendet
            echo '{"text": "", "class": "inactive", "tooltip": ""}'
        fi
        ;;
    *)
        toggle_gamemode
        ;;
esac
