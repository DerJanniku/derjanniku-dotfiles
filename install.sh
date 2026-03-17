#!/bin/bash

# ==============================================================================
# derjanniku-dotfiles - Automated Installation Script
# ==============================================================================
# Installs core dependencies and sets up my Hyprland environment.

set -e

echo "🚀 Starting derjanniku-dotfiles installation..."

# --- 1. System Update & Dependencies ---
echo "📦 Checking and installing dependencies..."

DEPENDENCIES=(
    "hyprland" "waybar" "kitty" "rofi-wayland" "swww" "wtype" "starship"
    "hypridle" "hyprlock" "ttf-jetbrains-mono-nerd" "npm" "nodejs" "python"
    "python-pip" "python-virtualenv" "git" "grim" "slurp" "wl-clipboard"
    "libnotify" "dolphin" "playerctl" "brightnessctl"
)

install_pkg() {
    if ! command -v "$1" &> /dev/null && ! pacman -Qs "^$1$" &> /dev/null; then
        echo "Installing $1..."
        if command -v yay &> /dev/null; then
            yay -S --noconfirm "$1"
        else
            sudo pacman -S --noconfirm "$1"
        fi
    else
        echo "✅ $1 is already installed."
    fi
}

for pkg in "${DEPENDENCIES[@]}"; do
    install_pkg "$pkg"
done

# --- 2. Dotfiles Setup ---
echo "📂 Setting up configuration files..."

CONFIG_DIR="$HOME/.config"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTIVE_DIR="$REPO_DIR/current-active"

# Create necessary directories
mkdir -p "$CONFIG_DIR"
mkdir -p "$HOME/Pictures/wallpapers"

# Copy configurations
echo "Applying my personal configurations..."
cp -r "$ACTIVE_DIR/hypr" "$CONFIG_DIR/"
cp -r "$ACTIVE_DIR/waybar" "$CONFIG_DIR/"
cp -r "$ACTIVE_DIR/rofi" "$CONFIG_DIR/"
cp -r "$ACTIVE_DIR/kitty" "$CONFIG_DIR/"
cp -r "$ACTIVE_DIR/mako" "$CONFIG_DIR/" 2>/dev/null || true
cp -r "$ACTIVE_DIR/matugen" "$CONFIG_DIR/" 2>/dev/null || true
cp -r "$ACTIVE_DIR/themes" "$CONFIG_DIR/" 2>/dev/null || true
cp "$ACTIVE_DIR/starship.toml" "$CONFIG_DIR/" 2>/dev/null || true

# Copy Wallpapers
if [ -d "$ACTIVE_DIR/backgrounds" ]; then
    cp -r "$ACTIVE_DIR/backgrounds/"* "$HOME/Pictures/wallpapers/"
fi

# Make scripts executable
echo "Setting permissions..."
find "$CONFIG_DIR/rofi" -name "*.sh" -exec chmod +x {} + 2>/dev/null || true
find "$CONFIG_DIR/hypr" -name "*.sh" -exec chmod +x {} + 2>/dev/null || true
[ -f "$CONFIG_DIR/bin/nexus-menu" ] && chmod +x "$CONFIG_DIR/bin/nexus-menu"

# --- 3. Developer Tooling (VibeFlow) ---
echo "🎙️ Setting up VibeFlow (Voice Dictation)..."
VIBEFLOW_DIR="$HOME/Documents/VibeFlow"

if [ ! -d "$VIBEFLOW_DIR" ]; then
    echo "Cloning VibeFlow repository..."
    git clone https://github.com/DerJanniku/VibeFlow-Test-Core.git "$VIBEFLOW_DIR"
else
    echo "VibeFlow directory already exists. Pulling latest changes..."
    cd "$VIBEFLOW_DIR" && git pull
fi

echo "Configuring Python environment for VibeFlow..."
cd "$VIBEFLOW_DIR"
python -m venv venv
source venv/bin/activate
[ -f "requirements.txt" ] && pip install -r requirements.txt || echo "No requirements found."
deactivate
echo "✅ VibeFlow setup complete."

# --- 4. Finalization ---
echo "🎉 Installation Complete!"
echo ""
echo "To apply all changes immediately, use the Theme Switcher:"
echo "👉 Press 'Meta (Windows) + T' and select a theme."
echo ""
echo "Welcome to my Arch setup."
