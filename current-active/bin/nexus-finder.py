#!/usr/bin/env python3
"""
==============================================================================
Nexus Finder - Bespoke Next-Gen File Manager for Arch Linux & Hyprland
Author: DerJannik
==============================================================================
"""

import os
import sys
import subprocess
import shutil
import mimetypes
import datetime
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango

# -----------------------------------------------------------------------------
# Color Palette & Dynamic Theming
# -----------------------------------------------------------------------------
def load_theme_colors():
    colors = {
        "primary": "#7aa2f7",
        "secondary": "#bb9af7",
        "tertiary": "#7dcfff",
        "surface": "#16161e",
        "bg": "#101014",
        "on_surface": "#c0caf5",
        "sidebar_bg": "#121218",
        "card_bg": "#1c1c24",
        "hover_bg": "rgba(255, 255, 255, 0.08)",
        "selected_bg": "#7aa2f7",
        "selected_fg": "#101014",
        "border": "rgba(255, 255, 255, 0.10)"
    }
    
    colors_file = os.path.expanduser("~/.config/waybar/colors.css")
    if os.path.isfile(colors_file):
        try:
            with open(colors_file, "r") as f:
                for line in f:
                    if "@define-color primary" in line:
                        colors["primary"] = line.split()[-1].rstrip(";")
                    elif "@define-color secondary" in line:
                        colors["secondary"] = line.split()[-1].rstrip(";")
                    elif "@define-color tertiary" in line:
                        colors["tertiary"] = line.split()[-1].rstrip(";")
                    elif "@define-color surface" in line:
                        colors["surface"] = line.split()[-1].rstrip(";")
                    elif "@define-color on_surface" in line:
                        colors["on_surface"] = line.split()[-1].rstrip(";")
        except Exception:
            pass
            
    return colors

# -----------------------------------------------------------------------------
# Helper Utilities
# -----------------------------------------------------------------------------
def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def get_file_icon_name(path, is_dir):
    if is_dir:
        name = os.path.basename(path).lower()
        if name in ["desktop"]: return "folder-desktop"
        if name in ["documents", "document"]: return "folder-documents"
        if name in ["downloads", "download"]: return "folder-download"
        if name in ["music"]: return "folder-music"
        if name in ["pictures", "wallpapers"]: return "folder-pictures"
        if name in ["videos"]: return "folder-videos"
        return "folder"
        
    ext = os.path.splitext(path)[1].lower()
    if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"]:
        return "image-x-generic"
    elif ext in [".mp4", ".mkv", ".webm", ".avi", ".mov"]:
        return "video-x-generic"
    elif ext in [".mp3", ".flac", ".ogg", ".wav", ".m4a"]:
        return "audio-x-generic"
    elif ext in [".zip", ".tar", ".gz", ".xz", ".7z", ".rar"]:
        return "package-x-generic"
    elif ext in [".py", ".sh", ".js", ".ts", ".rs", ".go", ".cpp", ".c", ".h", ".java", ".json", ".yaml", ".yml", ".toml", ".css", ".html"]:
        return "text-x-script"
    elif ext in [".pdf"]:
        return "application-pdf"
    return "text-x-generic"

# -----------------------------------------------------------------------------
# Nexus Finder Window
# -----------------------------------------------------------------------------
class NexusFinder(Gtk.Window):
    def __init__(self, initial_path=None):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_name("NexusFinder")
        self.set_title("Nexus Finder")
        self.set_default_size(1080, 680)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        self.current_path = os.path.abspath(initial_path or os.path.expanduser("~"))
        self.history = [self.current_path]
        self.history_idx = 0
        self.show_hidden = False
        self.search_filter = ""
        self.icon_theme = Gtk.IconTheme.get_default()

        # Apply Dynamic CSS Styling
        self.apply_styles()

        # Main Layout
        root_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(root_vbox)

        # 1. Header Navigation Bar
        self.header_bar = self.create_header_bar()
        root_vbox.pack_start(self.header_bar, False, False, 0)

        # 2. Main Content Split: Sidebar + File Area + Detail Pane
        content_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root_vbox.pack_start(content_hbox, True, True, 0)

        # Left Sidebar (Places & Favorites)
        sidebar = self.create_sidebar()
        content_hbox.pack_start(sidebar, False, False, 0)

        # Center File List / Grid View
        self.files_box = self.create_files_view()
        content_hbox.pack_start(self.files_box, True, True, 0)

        # Right Inspector / Preview Pane
        self.preview_pane = self.create_preview_pane()
        content_hbox.pack_start(self.preview_pane, False, False, 0)

        # Status Bar
        self.status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.status_bar.get_style_context().add_class("status-bar")
        self.status_label = Gtk.Label(label="", xalign=0)
        self.status_bar.pack_start(self.status_label, True, True, 8)
        root_vbox.pack_start(self.status_bar, False, False, 0)

        # Keybindings
        self.connect("key-press-event", self.on_key_press)

        # Initial Load
        self.load_directory(self.current_path)

    def apply_styles(self):
        c = load_theme_colors()
        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        
        css = f"""
            #NexusFinder {{
                background-color: {c['bg']};
                color: {c['on_surface']};
                font-family: 'JetBrainsMono Nerd Font', 'Noto Sans', sans-serif;
            }}
            .header-bar {{
                background-color: {c['sidebar_bg']};
                border-bottom: 1px solid {c['border']};
                padding: 10px 14px;
            }}
            .sidebar {{
                background-color: {c['sidebar_bg']};
                border-right: 1px solid {c['border']};
                padding: 12px 8px;
                min-width: 210px;
            }}
            .sidebar-category {{
                font-size: 10px;
                font-weight: bold;
                color: {c['primary']};
                margin: 10px 6px 4px 6px;
                letter-spacing: 1px;
            }}
            .sidebar-item {{
                padding: 7px 10px;
                border-radius: 8px;
                color: {c['on_surface']};
                margin-bottom: 2px;
            }}
            .sidebar-item:hover {{
                background-color: {c['hover_bg']};
            }}
            .sidebar-item.active {{
                background-color: {c['primary']};
                color: #101014;
                font-weight: bold;
            }}
            .path-button {{
                background: transparent;
                border: none;
                color: {c['on_surface']};
                padding: 4px 8px;
                border-radius: 6px;
                font-weight: 600;
            }}
            .path-button:hover {{
                background-color: {c['hover_bg']};
                color: {c['primary']};
            }}
            .nav-btn {{
                background: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                color: {c['on_surface']};
                padding: 4px 10px;
            }}
            .nav-btn:hover {{
                background: {c['primary']};
                color: #101014;
            }}
            .search-entry {{
                background-color: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                color: {c['on_surface']};
                padding: 6px 12px;
                min-width: 220px;
            }}
            .search-entry:focus {{
                border-color: {c['primary']};
            }}
            .preview-pane {{
                background-color: {c['sidebar_bg']};
                border-left: 1px solid {c['border']};
                padding: 14px;
                min-width: 260px;
            }}
            .file-row {{
                padding: 6px 10px;
                border-radius: 6px;
                margin: 1px 4px;
                color: {c['on_surface']};
            }}
            .file-row:hover {{
                background-color: {c['hover_bg']};
            }}
            .file-row:selected {{
                background-color: {c['primary']};
                color: #101014;
                font-weight: bold;
            }}
            .status-bar {{
                background-color: {c['sidebar_bg']};
                border-top: 1px solid {c['border']};
                padding: 4px 12px;
                font-size: 11px;
                color: rgba(255, 255, 255, 0.6);
            }}
            treeview {{
                background-color: {c['bg']};
                color: {c['on_surface']};
            }}
            treeview:selected {{
                background-color: {c['primary']};
                color: #101014;
            }}
        """.encode('utf-8')
        
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def create_header_bar(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hbox.get_style_context().add_class("header-bar")

        # Back & Forward History Buttons
        self.btn_back = Gtk.Button(label="󰁍")
        self.btn_back.get_style_context().add_class("nav-btn")
        self.btn_back.connect("clicked", self.on_back_clicked)
        hbox.pack_start(self.btn_back, False, False, 0)

        self.btn_fwd = Gtk.Button(label="󰁔")
        self.btn_fwd.get_style_context().add_class("nav-btn")
        self.btn_fwd.connect("clicked", self.on_forward_clicked)
        hbox.pack_start(self.btn_fwd, False, False, 0)

        self.btn_up = Gtk.Button(label="󰁞")
        self.btn_up.get_style_context().add_class("nav-btn")
        self.btn_up.connect("clicked", lambda w: self.navigate_to(os.path.dirname(self.current_path)))
        hbox.pack_start(self.btn_up, False, False, 0)

        # Breadcrumb Path Bar Box
        self.breadcrumb_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        hbox.pack_start(self.breadcrumb_box, True, True, 8)

        # Quick Search Entry
        self.search_entry = Gtk.Entry()
        self.search_entry.get_style_context().add_class("search-entry")
        self.search_entry.set_placeholder_text("󰍉 Search folder...")
        self.search_entry.connect("changed", self.on_search_changed)
        hbox.pack_end(self.search_entry, False, False, 0)

        # Terminal Quick Launch Button
        btn_term = Gtk.Button(label="")
        btn_term.get_style_context().add_class("nav-btn")
        btn_term.set_tooltip_text("Open Kitty in current folder")
        btn_term.connect("clicked", self.on_open_terminal)
        hbox.pack_end(btn_term, False, False, 0)

        # New Folder Button
        btn_new_dir = Gtk.Button(label="󰉋+")
        btn_new_dir.get_style_context().add_class("nav-btn")
        btn_new_dir.set_tooltip_text("New Folder")
        btn_new_dir.connect("clicked", self.on_create_folder_dialog)
        hbox.pack_end(btn_new_dir, False, False, 0)

        # Toggle Hidden Files Button
        self.btn_hidden = Gtk.ToggleButton(label="󰈈")
        self.btn_hidden.get_style_context().add_class("nav-btn")
        self.btn_hidden.set_tooltip_text("Toggle Hidden Files (Ctrl+H)")
        self.btn_hidden.connect("toggled", self.on_toggle_hidden)
        hbox.pack_end(self.btn_hidden, False, False, 0)

        return hbox

    def create_sidebar(self):
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        sidebar_box.get_style_context().add_class("sidebar")

        # Category: Favorites
        lbl_fav = Gtk.Label(label="FAVORITES", xalign=0)
        lbl_fav.get_style_context().add_class("sidebar-category")
        sidebar_box.pack_start(lbl_fav, False, False, 0)

        favorites = [
            ("󰋜 Home", os.path.expanduser("~")),
            ("󰇄 Desktop", os.path.expanduser("~/Desktop")),
            ("󰉋 Hyprland Rice", os.path.expanduser("~/Desktop/Hyprland_Setup_ArchLinux")),
            ("󰈔 Documents", os.path.expanduser("~/Documents")),
            ("󰉍 Downloads", os.path.expanduser("~/Downloads")),
            ("󰋩 Wallpapers", os.path.expanduser("~/Pictures/wallpapers")),
            ("󰹑 Screenshots", os.path.expanduser("~/Pictures/Screenshots")),
        ]

        # Check Obsidian Vault paths
        vault_paths = [
            os.path.expanduser("~/Documents/Obsidian Vault"),
            "/Users/jannik/Documents/Obsidian Vault"
        ]
        for vp in vault_paths:
            if os.path.isdir(vp):
                favorites.append(("🧠 Obsidian Vault", vp))
                break

        self.sidebar_buttons = []
        for name, path in favorites:
            if os.path.isdir(path):
                btn = Gtk.Button(label=name)
                btn.set_alignment(0, 0.5)
                btn.get_style_context().add_class("sidebar-item")
                btn.target_path = path
                btn.connect("clicked", lambda w: self.navigate_to(w.target_path))
                sidebar_box.pack_start(btn, False, False, 0)
                self.sidebar_buttons.append(btn)

        # Category: Places / System
        lbl_places = Gtk.Label(label="SYSTEM", xalign=0)
        lbl_places.get_style_context().add_class("sidebar-category")
        sidebar_box.pack_start(lbl_places, False, False, 0)

        places = [
            ("󰋊 Root (/)", "/"),
            ("󰉋 ArchSwitch", "/home/ArchSwitch"),
            ("󰒋 .config", os.path.expanduser("~/.config")),
        ]
        for name, path in places:
            if os.path.isdir(path):
                btn = Gtk.Button(label=name)
                btn.set_alignment(0, 0.5)
                btn.get_style_context().add_class("sidebar-item")
                btn.target_path = path
                btn.connect("clicked", lambda w: self.navigate_to(w.target_path))
                sidebar_box.pack_start(btn, False, False, 0)
                self.sidebar_buttons.append(btn)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(sidebar_box)
        return scrolled

    def create_files_view(self):
        # ListStore: [Icon(Pixbuf), Name(str), Size(str), Modified(str), IsDir(bool), FullPath(str)]
        self.liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str, str, bool, str)

        self.treeview = Gtk.TreeView(model=self.liststore)
        self.treeview.set_headers_visible(True)
        self.treeview.connect("row-activated", self.on_item_double_clicked)
        self.treeview.connect("button-press-event", self.on_treeview_button_press)
        self.treeview.get_selection().connect("changed", self.on_selection_changed)

        # Column 1: Name with Icon
        col_name = Gtk.TreeViewColumn("Name")
        col_name.set_resizable(True)
        col_name.set_min_width(320)
        
        renderer_icon = Gtk.CellRendererPixbuf()
        col_name.pack_start(renderer_icon, False)
        col_name.add_attribute(renderer_icon, "pixbuf", 0)

        renderer_text = Gtk.CellRendererText()
        col_name.pack_start(renderer_text, True)
        col_name.add_attribute(renderer_text, "text", 1)
        self.treeview.append_column(col_name)

        # Column 2: Size
        col_size = Gtk.TreeViewColumn("Size", Gtk.CellRendererText(), text=2)
        col_size.set_resizable(True)
        col_size.set_min_width(90)
        self.treeview.append_column(col_size)

        # Column 3: Modified Date
        col_mod = Gtk.TreeViewColumn("Modified", Gtk.CellRendererText(), text=3)
        col_mod.set_resizable(True)
        col_mod.set_min_width(140)
        self.treeview.append_column(col_mod)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.treeview)
        return scrolled

    def create_preview_pane(self):
        self.preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.preview_box.get_style_context().add_class("preview-pane")

        # Preview Thumbnail Frame
        self.preview_image = Gtk.Image()
        self.preview_image.set_size_request(240, 180)
        self.preview_box.pack_start(self.preview_image, False, False, 0)

        # Details Labels
        self.lbl_item_name = Gtk.Label(label="Select an item", xalign=0)
        self.lbl_item_name.set_line_wrap(True)
        self.lbl_item_name.get_style_context().add_class("sidebar-category")
        self.preview_box.pack_start(self.lbl_item_name, False, False, 0)

        self.lbl_item_meta = Gtk.Label(label="", xalign=0)
        self.lbl_item_meta.set_line_wrap(True)
        self.preview_box.pack_start(self.lbl_item_meta, False, False, 0)

        # Action Buttons
        actions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        btn_open = Gtk.Button(label="󰅩 Open Default App")
        btn_open.get_style_context().add_class("nav-btn")
        btn_open.connect("clicked", self.on_open_selected)
        actions_box.pack_start(btn_open, False, False, 0)

        btn_copy_path = Gtk.Button(label="📋 Copy Absolute Path")
        btn_copy_path.get_style_context().add_class("nav-btn")
        btn_copy_path.connect("clicked", self.on_copy_selected_path)
        actions_box.pack_start(btn_copy_path, False, False, 0)

        self.preview_box.pack_end(actions_box, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.preview_box)
        return scrolled

    # -------------------------------------------------------------------------
    # Directory Loading & Navigation
    # -------------------------------------------------------------------------
    def load_directory(self, target_dir):
        if not os.path.isdir(target_dir):
            return

        self.current_path = os.path.abspath(target_dir)
        self.liststore.clear()

        # Update Breadcrumb bar
        self.update_breadcrumbs()

        # Highlight active sidebar item
        for btn in self.sidebar_buttons:
            if hasattr(btn, 'target_path') and os.path.abspath(btn.target_path) == self.current_path:
                btn.get_style_context().add_class("active")
            else:
                btn.get_style_context().remove_class("active")

        # Scan folder items
        try:
            entries = os.listdir(self.current_path)
        except PermissionError:
            self.status_label.set_text("⚠️ Permission Denied")
            return

        entries.sort(key=lambda x: x.lower())
        dirs = []
        files = []

        for name in entries:
            if not self.show_hidden and name.startswith("."):
                continue
            if self.search_filter and self.search_filter.lower() not in name.lower():
                continue

            full_path = os.path.join(self.current_path, name)
            is_dir = os.path.isdir(full_path)
            
            try:
                stat = os.stat(full_path)
                size_str = "<DIR>" if is_dir else format_size(stat.st_size)
                mtime_str = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
            except Exception:
                size_str = "-"
                mtime_str = "-"

            # Load Icon
            icon_name = get_file_icon_name(full_path, is_dir)
            try:
                pixbuf = self.icon_theme.load_icon(icon_name, 22, Gtk.IconLookupFlags.GENERIC_FALLBACK)
            except Exception:
                pixbuf = self.icon_theme.load_icon("text-x-generic", 22, Gtk.IconLookupFlags.GENERIC_FALLBACK)

            if is_dir:
                dirs.append((pixbuf, name, size_str, mtime_str, True, full_path))
            else:
                files.append((pixbuf, name, size_str, mtime_str, False, full_path))

        # Add directories first, then files
        for item in dirs + files:
            self.liststore.append(item)

        total_count = len(dirs) + len(files)
        self.status_label.set_text(f"📁 {len(dirs)} Folders, 📄 {len(files)} Files  |  {self.current_path}")

    def update_breadcrumbs(self):
        for child in self.breadcrumb_box.get_children():
            self.breadcrumb_box.remove(child)

        parts = self.current_path.strip("/").split("/")
        accum = "/"
        
        btn_root = Gtk.Button(label="󰋊 /")
        btn_root.get_style_context().add_class("path-button")
        btn_root.target_path = "/"
        btn_root.connect("clicked", lambda w: self.navigate_to(w.target_path))
        self.breadcrumb_box.pack_start(btn_root, False, False, 0)

        if parts and parts[0]:
            for p in parts:
                accum = os.path.join(accum, p)
                sep = Gtk.Label(label="›")
                sep.get_style_context().add_class("path-sep")
                self.breadcrumb_box.pack_start(sep, False, False, 2)

                btn = Gtk.Button(label=p)
                btn.get_style_context().add_class("path-button")
                btn.target_path = accum
                btn.connect("clicked", lambda w: self.navigate_to(w.target_path))
                self.breadcrumb_box.pack_start(btn, False, False, 0)

        self.breadcrumb_box.show_all()

    def navigate_to(self, path):
        if not os.path.isdir(path):
            return
        if self.current_path != path:
            # Append to history
            self.history = self.history[:self.history_idx + 1]
            self.history.append(path)
            self.history_idx += 1
            self.load_directory(path)

    def on_back_clicked(self, w):
        if self.history_idx > 0:
            self.history_idx -= 1
            self.load_directory(self.history[self.history_idx])

    def on_forward_clicked(self, w):
        if self.history_idx < len(self.history) - 1:
            self.history_idx += 1
            self.load_directory(self.history[self.history_idx])

    def on_search_changed(self, entry):
        self.search_filter = entry.get_text().strip()
        self.load_directory(self.current_path)

    def on_toggle_hidden(self, btn):
        self.show_hidden = btn.get_active()
        self.load_directory(self.current_path)

    # -------------------------------------------------------------------------
    # Interactions & Context Menu
    # -------------------------------------------------------------------------
    def on_item_double_clicked(self, treeview, path, column):
        model = treeview.get_model()
        iter_ = model.get_iter(path)
        is_dir = model.get_value(iter_, 4)
        full_path = model.get_value(iter_, 5)

        if is_dir:
            self.navigate_to(full_path)
        else:
            subprocess.Popen(["xdg-open", full_path])

    def on_selection_changed(self, selection):
        model, iter_ = selection.get_selected()
        if not iter_:
            self.preview_image.clear()
            self.lbl_item_name.set_text("No selection")
            self.lbl_item_meta.set_text("")
            return

        name = model.get_value(iter_, 1)
        size_str = model.get_value(iter_, 2)
        mod_str = model.get_value(iter_, 3)
        is_dir = model.get_value(iter_, 4)
        full_path = model.get_value(iter_, 5)

        self.selected_path = full_path
        self.lbl_item_name.set_text(name)

        # Metadata format
        meta_text = f"Type: {'Folder' if is_dir else 'File'}\nSize: {size_str}\nModified: {mod_str}\nPath:\n{full_path}"
        self.lbl_item_meta.set_text(meta_text)

        # Image preview
        ext = os.path.splitext(full_path)[1].lower()
        if not is_dir and ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"]:
            try:
                pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(full_path, 240, 180, True)
                self.preview_image.set_from_pixbuf(pix)
            except Exception:
                self.preview_image.clear()
        else:
            self.preview_image.clear()

    def on_treeview_button_press(self, treeview, event):
        if event.button == 3: # Right Click
            pos = treeview.get_path_at_pos(int(event.x), int(event.y))
            if pos:
                treeview.get_selection().select_path(pos[0])
                model, iter_ = treeview.get_selection().get_selected()
                if iter_:
                    full_path = model.get_value(iter_, 5)
                    self.show_context_menu(event, full_path)
            return True
        return False

    def show_context_menu(self, event, path):
        menu = Gtk.Menu()

        item_open = Gtk.MenuItem(label="󰅩 Open")
        item_open.connect("activate", lambda w: subprocess.Popen(["xdg-open", path]))
        menu.append(item_open)

        item_term = Gtk.MenuItem(label=" Open in Kitty Terminal")
        dir_to_open = path if os.path.isdir(path) else os.path.dirname(path)
        item_term.connect("activate", lambda w: subprocess.Popen(["kitty", "--directory", dir_to_open]))
        menu.append(item_term)

        item_copy = Gtk.MenuItem(label="📋 Copy Path")
        item_copy.connect("activate", lambda w: self.copy_to_clipboard(path))
        menu.append(item_copy)

        item_sep = Gtk.SeparatorMenuItem()
        menu.append(item_sep)

        item_rename = Gtk.MenuItem(label="✏️ Rename")
        item_rename.connect("activate", lambda w: self.on_rename_dialog(path))
        menu.append(item_rename)

        item_delete = Gtk.MenuItem(label="🗑️ Delete")
        item_delete.connect("activate", lambda w: self.on_delete_dialog(path))
        menu.append(item_delete)

        menu.show_all()
        menu.popup_at_pointer(event)

    def on_open_terminal(self, w):
        subprocess.Popen(["kitty", "--directory", self.current_path])

    def on_open_selected(self, w):
        if hasattr(self, 'selected_path') and self.selected_path:
            subprocess.Popen(["xdg-open", self.selected_path])

    def on_copy_selected_path(self, w):
        if hasattr(self, 'selected_path') and self.selected_path:
            self.copy_to_clipboard(self.selected_path)

    def copy_to_clipboard(self, text):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)
        subprocess.Popen(["notify-send", "-a", "Nexus Finder", "-i", "edit-copy", "-t", "1000", "📋 Pfad kopiert", text])

    def on_create_folder_dialog(self, w):
        dialog = Gtk.Dialog(title="New Folder", parent=self, flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_placeholder_text("Folder name")
        box.pack_start(entry, True, True, 10)
        dialog.show_all()
        
        res = dialog.run()
        name = entry.get_text().strip()
        dialog.destroy()

        if res == Gtk.ResponseType.OK and name:
            new_dir = os.path.join(self.current_path, name)
            try:
                os.makedirs(new_dir, exist_ok=True)
                self.load_directory(self.current_path)
            except Exception as e:
                self.status_label.set_text(f"Error creating folder: {e}")

    def on_rename_dialog(self, path):
        old_name = os.path.basename(path)
        dialog = Gtk.Dialog(title="Rename", parent=self, flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_text(old_name)
        box.pack_start(entry, True, True, 10)
        dialog.show_all()
        
        res = dialog.run()
        new_name = entry.get_text().strip()
        dialog.destroy()

        if res == Gtk.ResponseType.OK and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(path), new_name)
            try:
                os.rename(path, new_path)
                self.load_directory(self.current_path)
            except Exception as e:
                self.status_label.set_text(f"Rename error: {e}")

    def on_delete_dialog(self, path):
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f"Möchtest du '{os.path.basename(path)}' wirklich löschen?"
        )
        res = dialog.run()
        dialog.destroy()

        if res == Gtk.ResponseType.OK:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.load_directory(self.current_path)
            except Exception as e:
                self.status_label.set_text(f"Delete error: {e}")

    def on_key_press(self, w, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        elif event.keyval == Gdk.KEY_BackSpace or (event.state & Gdk.ModifierType.MOD1_MASK and event.keyval == Gdk.KEY_Left):
            self.navigate_to(os.path.dirname(self.current_path))
            return True
        elif (event.state & Gdk.ModifierType.CONTROL_MASK) and event.keyval == Gdk.KEY_h:
            self.btn_hidden.set_active(not self.btn_hidden.get_active())
            return True
        elif (event.state & Gdk.ModifierType.CONTROL_MASK) and event.keyval == Gdk.KEY_f:
            self.search_entry.grab_focus()
            return True
        elif (event.state & Gdk.ModifierType.CONTROL_MASK) and event.keyval == Gdk.KEY_t:
            self.on_open_terminal(None)
            return True
        return False

# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    initial_dir = sys.argv[1] if len(sys.argv) > 1 else None
    win = NexusFinder(initial_dir)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
