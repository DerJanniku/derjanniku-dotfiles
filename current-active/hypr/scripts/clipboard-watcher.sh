#!/usr/bin/env bash
# ==============================================================================
# Nexus Hyprland Clipboard Watcher & Maccy-like Notifier
# Author: DerJannik
# ==============================================================================

LAST_CLIP=""

# Main watcher loop
wl-paste --watch bash -c '
    CLIP=$(wl-paste --no-newline 2>/dev/null)
    
    # Ignore empty or duplicate clips
    if [ -n "$CLIP" ]; then
        # Store in cliphist
        echo -n "$CLIP" | cliphist store
        
        # Format preview (truncate if too long)
        PREVIEW=$(echo "$CLIP" | head -n 3 | cut -c 1-80)
        LINE_COUNT=$(echo "$CLIP" | wc -l)
        if [ "$LINE_COUNT" -gt 3 ]; then
            PREVIEW="${PREVIEW}..."
        fi
        
        # Fire subtle notification (1.2 seconds, replacing previous clipboard notifications)
        notify-send \
            -a "Clipboard" \
            -i edit-copy \
            -t 1200 \
            -h string:x-canonical-private-synchronous:clipboard \
            "📋 In Zwischenablage kopiert" \
            "$PREVIEW"
    fi
' &

# Also watch image clips
wl-paste --type image --watch bash -c '
    cliphist store
    notify-send \
        -a "Clipboard" \
        -i image-x-generic \
        -t 1200 \
        -h string:x-canonical-private-synchronous:clipboard \
        "🖼️ Bild kopiert" \
        "Grafik in Zwischenablage gespeichert"
' &

echo "Clipboard watcher started successfully"
