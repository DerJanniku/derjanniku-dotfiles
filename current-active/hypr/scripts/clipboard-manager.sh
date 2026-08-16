#!/usr/bin/env bash
# ==============================================================================
# Maccy-Style Clipboard History Popup (Rofi Wayland)
# Author: DerJannik
# ==============================================================================

# Prompt via Rofi with styled Maccy window
ROFI_THEME='window { width: 680px; border: 2px solid @accent; border-radius: 14px; background-color: rgba(20, 20, 30, 0.92); }
            mainbox { padding: 12px; }
            inputbar { margin-bottom: 8px; }
            listview { lines: 12; scrollbar: false; }
            element { padding: 8px 12px; border-radius: 8px; }
            element selected { background-color: @accent; color: #11111b; }'

SELECTION=$(cliphist list | rofi -dmenu -i -p "📋 Maccy Clipboard" -theme-str "$ROFI_THEME")

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
