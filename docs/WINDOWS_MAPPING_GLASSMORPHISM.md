# Setup-Geheimnisse: Windows AltGr-Mapping & Glassmorphismus

In diesem Dokument halte ich fest, wie ich mein Hyprland so aufgesetzt habe, dass es den Windows-Komfort auf Linux bringt – insbesondere für das Programmieren wichtig.

## ⌨️ Windows-ähnliches "AltGr" Verhalten in Hyprland

Unter Linux (Wayland) ist es oft schwierig, das typische Windows-Verhalten der "AltGr"-Taste (bzw. `Ctrl` + `Alt`) für Sonderzeichen wie `{`, `[`, `\`, `@` exakt nachzubilden. 

Die Lösung liegt in **`wtype`**, einem X11 `xdotool` Equivalent für Wayland. Durch explizites Binden in der `hyprland.conf` simuliert Hyprland bei den Shortcuts den direkten Input des jeweiligen Zeichens:

```ini
# Map CTRL + ALT combinations to AltGr characters (Windows-like behavior)
bind = CTRL ALT, Q, exec, wtype "@"
bind = CTRL ALT, E, exec, wtype "€"
bind = CTRL ALT, 2, exec, wtype "²"
bind = CTRL ALT, 3, exec, wtype "³"
bind = CTRL ALT, M, exec, wtype "µ"
bind = CTRL ALT, 7, exec, wtype "{"
bind = CTRL ALT, 8, exec, wtype "["
bind = CTRL ALT, 9, exec, wtype "]"
bind = CTRL ALT, 0, exec, wtype "}"
bind = CTRL ALT, backslash, exec, wtype "\\"
```

### Voraussetzung:
- Das Paket `wtype` muss installiert sein (`sudo pacman -S wtype` oder via AUR).

---

## 💎 Premium Glassmorphismus (Hyprland Styling)

Um den perfekten "Milchglas"-Effekt (Glassmorphismus) zu erzielen, ohne die Framerates zu ruinieren, habe ich folgende Einstellungen in der `hyprland.conf` kombiniert:

```ini
decoration {
    rounding = 10                  # Moderne, abgerundete Ecken
    active_opacity = 0.95          # Fast deckend, wenn aktiv
    inactive_opacity = 0.85        # Deutlich transparent, wenn inaktiv
    
    # Tiefe durch Drop-Shadows
    shadow {
        enabled = true
        range = 30
        render_power = 3
        color = rgba(1a1b26ee)     # Dunkler, bläulicher Schatten (Mac/Windows11 Style)
    }

    # Fortgeschrittener Blur-Effekt
    blur {
        enabled = true
        size = 6                   # Stärke der Unschärfe
        passes = 3                 # Qualität der Unschärfe (Höher = besser, aber teurer)
        new_optimizations = true   # Wichtig für Performance
        ignore_opacity = true      # Der Blur ignoriert die Opacity des Fensters
        xray = false               # Fenster verschmelzen nicht miteinander
        brightness = 0.8
        contrast = 1.2
        vibrancy = 0.5             # Verstärkt die Farben hinter dem Glas
    }
}
```

Die Magie liegt hier im **Zusammenspiel von `ignore_opacity = true` und einem hohen `passes`-Wert (3)**. Das sorgt dafür, dass Terminal-Emulatoren (wie Kitty) oder der Hintergrund hinter transparenten Fenstern weich verschwommen gezeichnet werden (wie bei iOS oder Windows 11 Acrylic).

Zusätzlich in Kitty (`kitty.conf`):
```ini
background_opacity 0.85
linux_display_server wayland
```