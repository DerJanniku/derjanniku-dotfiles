#!/usr/bin/env python3
import os
import sys
import subprocess
import gi
import re

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Pango

# Configuration
WALLPAPER_DIR = os.path.expanduser("~/Pictures/wallpapers")
CACHE_DIR = os.path.expanduser("~/.cache/wallpaper_thumbs")
os.makedirs(CACHE_DIR, exist_ok=True)

# STRIKTE WHITELIST der Ordner
ALLOWED_FOLDERS = ["cold", "aerial", "anime", "animated", "00_favourite", "00_master"]

def normalize(text):
    return re.sub(r'[-_\s]', '', text).lower()

def get_wallpapers_grouped():
    groups = {}
    for folder in ALLOWED_FOLDERS:
        full_path = os.path.join(WALLPAPER_DIR, folder)
        if os.path.isdir(full_path):
            valid_files = [f for f in os.listdir(full_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.mp4'))]
            if valid_files:
                valid_files.sort(key=lambda x: (not x.startswith("00"), x.lower()))
                groups[folder] = [os.path.join(full_path, f) for f in valid_files]
    return sorted(groups.keys(), key=lambda x: (not x.startswith("00"), x.lower())), groups

class HyprDashboard(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, type=Gtk.WindowType.TOPLEVEL)
        self.set_name("WallpaperDashboard")
        self.set_decorated(False)
        self.set_default_size(1100, 700)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_keep_above(True)

        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        provider.load_from_data(b"""
            #WallpaperDashboard { background-color: #11111b; border: 2px solid #89b4fa; border-radius: 15px; }
            .sidebar { background-color: #181825; border-radius: 12px 0 0 12px; padding: 15px; }
            .preview-box { padding: 20px; }
            listbox row { padding: 10px; color: #cdd6f4; border-radius: 8px; }
            listbox row:selected { background-color: #89b4fa; color: #11111b; }
            label.category { font-weight: bold; color: #fab387; margin: 10px; }
            entry { background-color: #313244; color: #cdd6f4; border-radius: 10px; padding: 8px; margin-bottom: 10px; }
        """)
        Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(hbox)

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        sidebar.get_style_context().add_class("sidebar")
        sidebar.set_size_request(350, -1)
        hbox.pack_start(sidebar, False, False, 0)

        self.entry = Gtk.Entry()
        self.entry.connect("changed", self.on_search_changed)
        sidebar.pack_start(self.entry, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        sidebar.pack_start(scrolled, True, True, 0)
        self.listbox = Gtk.ListBox()
        self.listbox.connect("row-selected", self.on_row_selected)
        self.listbox.connect("row-activated", self.on_row_activated)
        scrolled.add(self.listbox)

        self.preview_image = Gtk.Image()
        hbox.pack_start(self.preview_image, True, True, 0)

        self.categories, self.groups = get_wallpapers_grouped()
        self.populate_list()

    def populate_list(self, filter_text=""):
        for child in self.listbox.get_children(): self.listbox.remove(child)
        q = normalize(filter_text)
        first = None
        for cat in self.categories:
            files = [f for f in self.groups[cat] if q in normalize(os.path.basename(f))]
            if files:
                l = Gtk.Label(label=f"󰉋 {cat}", xalign=0)
                l.get_style_context().add_class("category")
                r = Gtk.ListBoxRow(selectable=False); r.add(l); self.listbox.add(r)
                for f in files:
                    row = Gtk.ListBoxRow(); row.add(Gtk.Label(label=f"  󰋩 {os.path.basename(f)}", xalign=0)); row.wp_path = f
                    self.listbox.add(row)
                    if not first: first = row
        self.show_all()
        if first: self.listbox.select_row(first)

    def on_search_changed(self, e): self.populate_list(e.get_text())

    def on_row_selected(self, lb, row):
        if row and hasattr(row, 'wp_path'):
            pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(row.wp_path, 720, 500, True)
            self.preview_image.set_from_pixbuf(pix)

    def on_row_activated(self, lb, row):
        if not row or not hasattr(row, 'wp_path'): return
        wp = row.wp_path
        
        # Prüfe ob der Daemon läuft
        daemon_running = subprocess.run(["pgrep", "swww-daemon"], capture_output=True).returncode == 0
        
        if wp.lower().endswith('.mp4'):
            subprocess.run(["killall", "swww-daemon", "hyprpaper", "mpvpaper"], capture_output=True)
            if subprocess.run(["which", "mpvpaper"], capture_output=True).returncode == 0:
                subprocess.Popen(["mpvpaper", "-o", "no-audio --loop-playlist", "*", wp])
            else:
                subprocess.Popen(["swww-daemon", "--format", "argb"])
                import time; time.sleep(0.3)
                subprocess.Popen(["swww", "img", wp, "--transition-type", "grow"])
        else:
            # Falls Video lief, beenden
            subprocess.run(["killall", "hyprpaper", "mpvpaper"], capture_output=True)
            
            # Nur neu starten wenn nötig
            if not daemon_running:
                subprocess.Popen(["swww-daemon", "--format", "argb"])
                import time; time.sleep(0.3)
            
            subprocess.Popen(["swww", "img", wp, "--transition-type", "grow", "--transition-fps", "144"])
        
        # Update system memory/theme
        subprocess.run(f"ln -sf '{wp}' $HOME/.config/hypr/wallpaper.jpg", shell=True)
        
        # Memory Update
        try:
            with open(os.path.expanduser("~/.config/themes/current_theme.txt"), "r") as f:
                current_theme = f.read().strip()
            theme_path = os.path.expanduser(f"~/.config/themes/{current_theme}")
            if os.path.isdir(theme_path):
                with open(os.path.join(theme_path, "last_wallpaper.txt"), "w") as f:
                    f.write(wp)
        except: pass
        
        Gtk.main_quit()

    def on_key_press(self, w, e):
        if e.keyval == Gdk.KEY_Escape: Gtk.main_quit()
        elif e.keyval == Gdk.KEY_Return:
            sel = self.listbox.get_selected_row()
            if sel: self.on_row_activated(None, sel)

if __name__ == "__main__":
    win = HyprDashboard()
    win.connect("destroy", Gtk.main_quit)
    win.connect("key-press-event", win.on_key_press)
    win.connect("focus-out-event", lambda w, e: Gtk.main_quit())
    win.show_all()
    Gtk.main()
