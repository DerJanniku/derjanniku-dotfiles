# DerJanniku-Dotfiles

![Setup Preview 1](assets/preview.png)
![Setup Preview 2](assets/preview-2.png)

My personal, high-performance desktop environment for Arch Linux. Built on Hyprland with a focus on aesthetics, productivity, and seamless theme-switching.

## Features

- **Integrated Voice Dictation (VibeFlow)**: My custom-built voice-to-text engine, seamlessly integrated into the workflow.
- **Dynamic Theme Engine**: Switch between multiple professional styles (Dark, Light, Glassmorphism) on the fly.
- **Floating Capsule UI**: A modern, clean interface with a minimalist Waybar and Rofi integration.
- **Workflow Focused**: Optimized for development and daily driving with custom window management and hotkeys.
- **Easy Setup**: Modular installation script to get you up and running quickly.

## Custom Tools & Dashboards

### Professional Wallpaper Dashboard (`Meta + W`)
A custom-built Python/GTK3 dashboard to manage the wallpaper gallery with a sidebar list and high-quality real-time preview. Includes smart search and native support for JPG, PNG, GIFs, and MP4 videos.
![Wallpaper Dashboard](screenshots/wallpaper-dashboard.png)

### App Launcher (`Meta + D`)
A clean, focused launcher for all installed applications.
![App Launcher](screenshots/app-launcher.png)

### Nexus Search (`Meta + Escape`)
Central command hub for system controls, styling options, and communication.
![Nexus Search](screenshots/nexus-search.png)

## Quick Start

To install these dotfiles on a fresh Arch Linux system, run:

```bash
git clone https://github.com/DerJanniku/derjanniku-dotfiles.git ~/derjanniku-dotfiles
cd ~/derjanniku-dotfiles
chmod +x install.sh
./install.sh
```

### Prerequisites
- A working Arch Linux installation.
- An AUR helper like `yay` or `paru` (recommended).

## Theme Switching

Trigger the dynamic theme switcher at any time:
- **Hotkey:** `Meta + T`
- **Effect:** Instantly applies colors, transparency, and wallpapers to Hyprland, Waybar, Rofi, and Kitty.

## Structure

- **`current-active/`**: Core configuration files (Hyprland, Waybar, Rofi, Kitty).
- **`themes/`**: Visual styles and color schemes.
- **`docs/`**: Setup guides and technical notes.

## License
MIT License. Created by DerJanniku.