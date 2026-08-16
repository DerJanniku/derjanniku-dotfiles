#!/usr/bin/env bash
# ==============================================================================
# Maccy-Style Clipboard History Popup (Rofi Wayland)
# Author: DerJannik
# ==============================================================================

THEME_FILE="$HOME/.config/rofi/clipboard.rasi"

if [ -f "$THEME_FILE" ]; then
    SELECTION=$(cliphist list | rofi -dmenu -i -p "📋 Maccy" -theme "$THEME_FILE")
else
    SELECTION=$(cliphist list | rofi -dmenu -i -p "📋 Maccy")
fi

if [ -n "$SELECTION" ]; then
    if [[ "$SELECTION" == *":clear"* ]] || [[ "$SELECTION" == *"Wipe History"* ]]; then
        cliphist wipe
        notify-send -a "Maccy Clipboard" -i edit-clear -t 1200 "🧹 Verlauf gelöscht" "Zwischenablage wurde geleert"
    else
        echo "$SELECTION" | cliphist decode | wl-copy
        
        # Audio feedback on selection
        if which canberra-gtk-play >/dev/null 2>&1; then
            canberra-gtk-play -i complete >/dev/null 2>&1 &
        fi
        
        notify-send -a "Maccy Clipboard" -i edit-paste -t 1200 -h string:x-canonical-private-synchronous:clipboard "📋 Ausgewählt" "In Zwischenablage geladen"
    fi
fi
