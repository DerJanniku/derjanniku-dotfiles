#!/usr/bin/env bash
# ==============================================================================
# Nexus Hyprland Maccy-Style Clipboard Watcher & Audio Notifier
# Author: DerJannik
# ==============================================================================

# Kill previous instances of this watcher
for pid in $(pgrep -f "clipboard-watcher.sh"); do
    if [ "$pid" != "$$" ]; then
        kill "$pid" 2>/dev/null
    fi
done

# Kill old wl-paste watches to avoid stacking
pkill -f "wl-paste --watch" 2>/dev/null || true
pkill -f "wl-paste --type image --watch" 2>/dev/null || true

# Watch Text Clips
wl-paste --watch bash -c '
    CLIP=$(wl-paste --no-newline 2>/dev/null)
    
    if [ -n "$CLIP" ]; then
        # 1. Store in cliphist
        echo -n "$CLIP" | cliphist store
        
        # 2. Extract Preview
        PREVIEW=$(echo "$CLIP" | head -n 3 | cut -c 1-90)
        LINE_COUNT=$(echo "$CLIP" | wc -l)
        CHAR_COUNT=${#CLIP}
        
        if [ "$LINE_COUNT" -gt 3 ] || [ "$CHAR_COUNT" -gt 90 ]; then
            PREVIEW="${PREVIEW}..."
        fi
        
        # 3. Play Subtle Audio Feedback (Maccy pop/click sound)
        if which canberra-gtk-play >/dev/null 2>&1; then
            canberra-gtk-play -i audio-volume-change >/dev/null 2>&1 &
        elif [ -f "/usr/share/sounds/freedesktop/stereo/audio-volume-change.oga" ] && which paplay >/dev/null 2>&1; then
            paplay /usr/share/sounds/freedesktop/stereo/audio-volume-change.oga >/dev/null 2>&1 &
        fi
        
        # 4. Fire Maccy-Style Notification with Preview
        notify-send \
            -a "Maccy Clipboard" \
            -i edit-copy \
            -t 1600 \
            -h string:x-canonical-private-synchronous:clipboard \
            "📋 Kopiert (${CHAR_COUNT} Zeichen)" \
            "$PREVIEW"
    fi
' &

# Watch Image Clips
wl-paste --type image --watch bash -c '
    cliphist store
    if which canberra-gtk-play >/dev/null 2>&1; then
        canberra-gtk-play -i camera-shutter >/dev/null 2>&1 &
    elif [ -f "/usr/share/sounds/freedesktop/stereo/camera-shutter.oga" ] && which paplay >/dev/null 2>&1; then
        paplay /usr/share/sounds/freedesktop/stereo/camera-shutter.oga >/dev/null 2>&1 &
    fi
    notify-send \
        -a "Maccy Clipboard" \
        -i image-x-generic \
        -t 1600 \
        -h string:x-canonical-private-synchronous:clipboard \
        "🖼️ Bild kopiert" \
        "Grafik in Zwischenablage gespeichert"
' &

wait
