#!/usr/bin/env bash
# ==============================================================================
# Maccy-like Clipboard History Popup (Rofi Wayland)
# ==============================================================================

# Fetch cliphist list and prompt via Rofi
SELECTION=$(cliphist list | rofi -dmenu -p "📋 Maccy Clipboard" -theme-str 'window {width: 600px; border-radius: 12px;} listview {lines: 12;}' -display-columns 2)

if [ -n "$SELECTION" ]; then
    echo "$SELECTION" | cliphist decode | wl-copy
    notify-send -a "Clipboard" -i edit-paste -t 1000 -h string:x-canonical-private-synchronous:clipboard "📋 Ausgewählt" "In Zwischenablage geladen"
fi
