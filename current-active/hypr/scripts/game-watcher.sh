#!/usr/bin/env bash
# ==============================================================================
# Automatic Game Watcher Daemon
# Detects running games and automatically turns Game Mode ON / OFF
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GAMEMODE_SCRIPT="$SCRIPT_DIR/gamemode.sh"
AUTO_FLAG="/tmp/hypr_gamemode_auto"

# Game Process Patterns (Regex) - matches real game binaries, gamescope, wine games, rocketleague
GAME_PATTERNS="rocketleague\.exe|RocketLeague|steam_app_[0-9]+|gamescope|wine64-preloader|cs2|dota2|overwatch\.exe|valorant"

# Kill existing watcher instances to prevent duplicates
for pid in $(pgrep -f "game-watcher.sh"); do
    if [ "$pid" != "$$" ]; then
        kill "$pid" 2>/dev/null
    fi
done

while true; do
    # Check running processes and active window class for games
    ACTIVE_CLASS=$(hyprctl activewindow -j 2>/dev/null | jq -r '.class // empty')
    
    IS_GAME_RUNNING=0
    if pgrep -f -i "$GAME_PATTERNS" > /dev/null 2>&1; then
        IS_GAME_RUNNING=1
    elif [[ "$ACTIVE_CLASS" =~ (steam_app_|rocketleague|gamescope) ]]; then
        IS_GAME_RUNNING=1
    fi

    if [ "$IS_GAME_RUNNING" -eq 1 ]; then
        if [ ! -f "/tmp/hypr_gamemode_active" ]; then
            touch "$AUTO_FLAG"
            "$GAMEMODE_SCRIPT" on
        fi
    else
        # If game closed and GameMode was turned on automatically -> restore desktop
        if [ -f "$AUTO_FLAG" ] && [ -f "/tmp/hypr_gamemode_active" ]; then
            rm -f "$AUTO_FLAG"
            "$GAMEMODE_SCRIPT" off
        fi
    fi
    sleep 3
done
