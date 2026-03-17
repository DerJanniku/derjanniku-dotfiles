#!/bin/bash

# Spotlight-Modus für Rofi
# Wird von Rofi mit dem aktuellen Input aufgerufen

QUERY=$1

if [ -z "$QUERY" ]; then
    # Leere Ansicht am Anfang
    exit 0
fi

# 1. Dateien suchen (Limit 10)
if [ ${#QUERY} -ge 2 ]; then
    fd --hidden --exclude .git --max-results 10 "$QUERY" "$HOME" | while read -r line; do
        # Format: Pfad\0icon\x1fIcon-Name
        echo -e "${line/#$HOME/~}\0icon\x1ftext-x-generic"
    done
fi

# 2. Web Search Option
echo -e "󰈹  In Firefox suchen: '$QUERY'\0icon\x1ffirefox"

# 3. Terminal Run Option
echo -e "  In Terminal ausführen: '$QUERY'\0icon\x1futilities-terminal"
