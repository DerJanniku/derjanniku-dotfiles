#!/bin/bash
# --- Dynamic Nexus Launcher v3 ---

# Defaults
ACCENT="#d32f2f"; BG="#ffffff"; FG="#1a1a1a"; BWIDTH="2px"; BRADIUS="12px"

CURRENT_COLORS="$HOME/.config/themes/current_colors.sh"
[ -f "$CURRENT_COLORS" ] && source "$CURRENT_COLORS"

ACCENT=${ACCENT:-"#d32f2f"}; BG=${BG:-"#ffffff"}; FG=${FG:-"#1a1a1a"}; BWIDTH=${BWIDTH:-"2px"}; BRADIUS=${BRADIUS:-"12px"}

# Hier werden ALLE Elemente explizit gefaerbt
ROFI_THEME="window { width: 450px; border: $BWIDTH; border-radius: $BRADIUS; border-color: $ACCENT; background-color: $BG; } 
           mainbox { border-radius: $BRADIUS; }
           inputbar { border-color: $ACCENT; text-color: $FG; }
           prompt { text-color: $ACCENT; }
           entry { text-color: $FG; }
           listview { text-color: $FG; }
           element { text-color: $FG; }
           element selected.normal { background-color: $ACCENT; text-color: #ffffff; }"

selected=$(rofi -show drun -theme-str "$ROFI_THEME" -drun-display-format "{name}" -i)
[ -n "$selected" ] && (hyprctl dispatch exec "$selected" || $selected &)
