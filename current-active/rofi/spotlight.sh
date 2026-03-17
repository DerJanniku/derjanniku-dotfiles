#!/bin/bash

# Apple Spotlight-like search for Rofi (Hyprland)
# Handles: Apps, Files, Web Search, Terminal Run

# Configuration
CONFIG="$HOME/.config/rofi/config.rasi"

# Run Rofi and get user input
# We use -drun to show apps first, but let's use a custom script for a combined view
# To make it really like Spotlight, we want a single entry field that searches everything.

query=$(rofi -dmenu -config "$CONFIG" -p "Spotlight " -i -theme-str 'entry { placeholder: "Search Apps, Files, or Web..."; }')

if [ -z "$query" ]; then
    exit 0
fi

# 1. Check if it's an application (in $PATH)
if command -v "$query" >/dev/null 2>&1; then
    # It's a command, offer to run it in terminal or background
    choice=$(echo -e "  Run '$query'
  Run '$query' in Terminal" | rofi -dmenu -config "$CONFIG" -p "Action " -i)
    if [[ "$choice" == *"Terminal"* ]]; then
        kitty -e "$query" &
    elif [[ "$choice" == *"Run"* ]]; then
        $query &
    fi
    exit 0
fi

# 2. Check for files (using fd for speed)
# We search in common directories (Home, Documents, etc.)
files=$(fd --hidden --exclude .git --max-results 10 "$query" "$HOME" | sed "s|^$HOME|~|")

# 3. Web Search Options
web_search="󰈹  Search Google for '$query'"

# Combine results for a second stage if not a direct match
# Or we can just present them as a list
options=$(echo -e "$files
$web_search
  Run in Terminal: $query")

selected=$(echo -e "$options" | rofi -dmenu -config "$CONFIG" -p "Results " -i)

if [ -z "$selected" ]; then
    exit 0
fi

if [[ "$selected" == "󰈹"* ]]; then
    firefox "https://www.google.com/search?q=$query" &
elif [[ "$selected" == ""* ]]; then
    kitty -e bash -c "$query; read -p 'Press enter to close...'" &
elif [[ "$selected" == "~"* ]]; then
    # Expand ~ and open file
    file_path="${selected/#\~/$HOME}"
    xdg-open "$file_path" &
else
    # Try to open as file
    xdg-open "$selected" &
fi
