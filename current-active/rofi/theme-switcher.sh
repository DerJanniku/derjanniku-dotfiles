#!/bin/bash
# --- Nexus Theme Engine v5 (with Wallpaper Memory) ---

THEMES_DIR="$HOME/.config/themes"
CURRENT_COLORS="$HOME/.config/themes/current_colors.sh"
CURRENT_THEME_FILE="$HOME/.config/themes/current_theme.txt"
BG_DIR="$HOME/Pictures/wallpapers"

# Load style for SELF-STYLING
[ -f "$CURRENT_COLORS" ] && source "$CURRENT_COLORS"
ACCENT=${ACCENT:-"#d32f2f"}; BG=${BG:-"#ffffff"}; FG=${FG:-"#1a1a1a"}; BWIDTH=${BWIDTH:-"2px"}; BRADIUS=${BRADIUS:-"12px"}

ROFI_THEME="window { width: 350px; border: $BWIDTH; border-radius: $BRADIUS; border-color: $ACCENT; background-color: $BG; } 
           mainbox { border-radius: $BRADIUS; }
           inputbar { border-color: $ACCENT; text-color: $FG; }
           prompt { text-color: $ACCENT; }
           entry { text-color: $FG; }
           listview { lines: 6; scrollbar: false; } 
           element { padding: 8px; text-color: $FG; } 
           element selected.normal { background-color: $ACCENT; text-color: #ffffff; border-radius: 6px; }"

THEMES=$(ls -d "$THEMES_DIR"/*/ | xargs -n 1 basename | grep -vE "current_colors.sh|colors.sh")
SELECTED=$(echo "$THEMES" | rofi -dmenu -i -p "🎨 Theme" -theme-str "$ROFI_THEME")

if [ -n "$SELECTED" ]; then
    THEME_PATH="$THEMES_DIR/$SELECTED"
    echo "$SELECTED" > "$CURRENT_THEME_FILE"

    # --- 1. Wallpaper Memory Restore ---
    LAST_WP_FILE="$THEME_PATH/last_wallpaper.txt"
    if [ -f "$LAST_WP_FILE" ]; then
        WP_PATH=$(cat "$LAST_WP_FILE")
    elif [[ "$SELECTED" == "modern-white-red" ]]; then
        WP_PATH="$BG_DIR/00_master_industrial.jpg"
    else
        WP_PATH="$BG_DIR/00_FAVORITE_wp12.jpg" # Global Default
    fi

    if [ -f "$WP_PATH" ]; then
        swww img "$WP_PATH" --transition-type grow --transition-pos center --transition-duration 2
        ln -sf "$WP_PATH" "$HOME/.config/hypr/wallpaper.jpg"
    fi

    # --- 2. Overwrite Configs ---
    cp "$THEME_PATH/waybar/config" "$HOME/.config/waybar/config" 2>/dev/null
    cp "$THEME_PATH/waybar/style.css" "$HOME/.config/waybar/style.css" 2>/dev/null
    mkdir -p "$HOME/.config/hypr/themes"
    cp "$THEME_PATH/hypr/theme.conf" "$HOME/.config/hypr/themes/current.conf" 2>/dev/null
    cp "$THEME_PATH/kitty/colors.conf" "$HOME/.config/kitty/colors.conf" 2>/dev/null
    killall -SIGUSR1 kitty 2>/dev/null
    
    # --- 3. Global Colors ---
    cp "$THEME_PATH/colors.sh" "$CURRENT_COLORS"
    source "$CURRENT_COLORS"
    CLEAN_BG=$(echo "$BG" | sed 's/rgba(//;s/)//;s/,/ /g' | awk '{if ($1 ~ /^#/) print $1; else printf "#%02x%02x%02x%02x\n", $1, $2, $3, $4*255}')
    sed -e "s|__ACCENT__|$ACCENT|g" -e "s|__BG__|${CLEAN_BG}|g" -e "s|__FG__|$FG|g" \
        "$HOME/.config/mako/config.template" > "$HOME/.config/mako/config"
    makoctl reload

    # --- 4. GTK Mode ---
    [[ "$SELECTED" == *"dark"* ]] || [[ "$SELECTED" == "pro-glassmorphism" ]] && gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' || gsettings set org.gnome.desktop.interface color-scheme 'prefer-light'
    
    # --- 5. Refresh ---
    hyprctl reload
    pkill waybar; waybar > /dev/null 2>&1 &
    notify-send "Nexus Engine" "Thema '$SELECTED' geladen." -i "view-refresh"
fi
