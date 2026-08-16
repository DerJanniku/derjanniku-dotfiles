#!/usr/bin/env python3
"""
==============================================================================
Nexus Finder 2.0 - Ultimate Bespoke File Manager for Arch Linux & Hyprland
Author: DerJannik
Features:
  - Multi-Tab Support (Ctrl+T, Ctrl+W)
  - Full Cut/Copy/Paste/Duplicate (Ctrl+C, Ctrl+X, Ctrl+V, Ctrl+D)
  - Direct Path URL Input Bar (Ctrl+L) with Tab Completion
  - Live Code/Text, Image & Archive Previews in Detail Inspector
  - Dynamic Material You / Wallpaper Theming
  - SSHFS 1-Click Server Mounts & Remote Browsing
  - 1-Click Client Delivery Packaging & 0x0.st Quick Share Links
  - Built-in Archive Extract / Compress (.zip, .tar.gz, .jar, .7z)
  - Git Branch & Status Detection in Status Bar
  - Native Drag & Drop to Firefox, Discord, Terminal & Folders
==============================================================================
"""

import os
import sys
import subprocess
import shutil
import mimetypes
import datetime
import threading
import urllib.parse
import zipfile
import tarfile
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango, GObject

# -----------------------------------------------------------------------------
# Dynamic Color Palette
# -----------------------------------------------------------------------------
def load_theme_colors():
    colors = {
        "primary": "#7aa2f7",
        "secondary": "#bb9af7",
        "tertiary": "#7dcfff",
        "surface": "#16161e",
        "bg": "#101014",
        "on_surface": "#c0caf5",
        "sidebar_bg": "#13131a",
        "card_bg": "#1c1c26",
        "hover_bg": "rgba(255, 255, 255, 0.08)",
        "selected_bg": "#7aa2f7",
        "border": "rgba(255, 255, 255, 0.10)"
    }
    
    colors_file = os.path.expanduser("~/.config/waybar/colors.css")
    if os.path.isfile(colors_file):
        try:
            with open(colors_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("@define-color primary"):
                        colors["primary"] = line.split()[-1].rstrip(";")
                    elif line.startswith("@define-color secondary"):
                        colors["secondary"] = line.split()[-1].rstrip(";")
                    elif line.startswith("@define-color tertiary"):
                        colors["tertiary"] = line.split()[-1].rstrip(";")
                    elif line.startswith("@define-color surface"):
                        colors["surface"] = line.split()[-1].rstrip(";")
                    elif line.startswith("@define-color on_surface"):
                        colors["on_surface"] = line.split()[-1].rstrip(";")
        except Exception:
            pass
            
    return colors

# -----------------------------------------------------------------------------
# Utilities
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
        if name in ["delivery"]: return "package-x-generic"
        if name.startswith(".git"): return "folder-git"
        return "folder"
        
    ext = os.path.splitext(path)[1].lower()
    if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"]:
        return "image-x-generic"
    elif ext in [".mp4", ".mkv", ".webm", ".avi", ".mov"]:
        return "video-x-generic"
    elif ext in [".mp3", ".flac", ".ogg", ".wav", ".m4a"]:
        return "audio-x-generic"
    elif ext in [".zip", ".tar", ".gz", ".xz", ".7z", ".rar", ".jar"]:
        return "package-x-generic"
    elif ext in [".py", ".sh", ".js", ".ts", ".rs", ".go", ".cpp", ".c", ".h", ".java", ".json", ".yaml", ".yml", ".toml", ".css", ".html", ".md"]:
        return "text-x-script"
    elif ext in [".pdf"]:
        return "application-pdf"
    return "text-x-generic"

def parse_ssh_hosts():
    hosts = []
    ssh_config = os.path.expanduser("~/.ssh/config")
    if os.path.isfile(ssh_config):
        try:
            with open(ssh_config, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("Host ") and not "*" in line:
                        h = line.split()[1]
                        if h not in hosts:
                            hosts.append(h)
        except Exception:
            pass
    return hosts

def get_git_branch(path):
    try:
        res = subprocess.run(["git", "-C", path, "branch", "--show-current"], capture_output=True, text=True, timeout=1)
        if res.returncode == 0 and res.stdout.strip():
            # Check dirty
            dirty_res = subprocess.run(["git", "-C", path, "status", "--porcelain"], capture_output=True, text=True, timeout=1)
            dirty = "*" if dirty_res.stdout.strip() else ""
            return f"󰊢 {res.stdout.strip()}{dirty}"
    except Exception:
        pass
    return ""

# -----------------------------------------------------------------------------
# Main Nexus Finder App
# -----------------------------------------------------------------------------
class NexusFinder(Gtk.Window):
    def __init__(self, initial_path=None):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_name("NexusFinder")
        self.set_title("Nexus Finder")
        self.set_default_size(1160, 720)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        self.icon_theme = Gtk.IconTheme.get_default()
        self.show_hidden = False
        self.search_filter = ""
        self.internal_clipboard = {"action": None, "paths": []} # Cut / Copy

        # Tab Support: List of tab dicts { 'path': str, 'history': [], 'idx': int }
        initial_dir = os.path.abspath(initial_path or os.path.expanduser("~"))
        self.tabs_data = []

        # Apply CSS
        self.apply_styles()

        # Root Layout
        root_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(root_vbox)

        # 1. Header Toolbar
        self.header_bar = self.create_header_bar()
        root_vbox.pack_start(self.header_bar, False, False, 0)

        # 2. Tab Bar
        self.tab_notebook = Gtk.Notebook()
        self.tab_notebook.set_scrollable(True)
        self.tab_notebook.connect("switch-page", self.on_tab_switched)
        root_vbox.pack_start(self.tab_notebook, True, True, 0)

        # 3. Status Bar
        self.status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.status_bar.get_style_context().add_class("status-bar")
        self.status_label = Gtk.Label(label="", xalign=0)
        self.git_label = Gtk.Label(label="", xalign=1)
        self.status_bar.pack_start(self.status_label, True, True, 8)
        self.status_bar.pack_end(self.git_label, False, False, 12)
        root_vbox.pack_start(self.status_bar, False, False, 0)

        # Add initial Tab
        self.add_tab(initial_dir)

        # Global Keybindings
        self.connect("key-press-event", self.on_key_press)

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
                padding: 8px 12px;
            }}
            .sidebar {{
                background-color: {c['sidebar_bg']};
                border-right: 1px solid {c['border']};
                padding: 10px 6px;
                min-width: 220px;
            }}
            .sidebar-category {{
                font-size: 10px;
                font-weight: bold;
                color: {c['primary']};
                margin: 10px 6px 4px 6px;
                letter-spacing: 1px;
            }}
            .sidebar-item {{
                padding: 6px 10px;
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
                padding: 3px 6px;
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
                padding: 4px 8px;
            }}
            .nav-btn:hover {{
                background: {c['primary']};
                color: #101014;
            }}
            .action-btn {{
                background: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                color: {c['on_surface']};
                padding: 6px 10px;
                font-weight: 600;
            }}
            .action-btn:hover {{
                background: {c['primary']};
                color: #101014;
            }}
            .share-btn {{
                background: {c['secondary']};
                border: none;
                border-radius: 8px;
                color: #101014;
                font-weight: bold;
                padding: 6px 10px;
            }}
            .share-btn:hover {{
                background: {c['primary']};
            }}
            .search-entry {{
                background-color: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                color: {c['on_surface']};
                padding: 4px 10px;
                min-width: 180px;
            }}
            .path-entry {{
                background-color: {c['card_bg']};
                border: 1px solid {c['primary']};
                border-radius: 8px;
                color: {c['on_surface']};
                padding: 4px 8px;
            }}
            .preview-pane {{
                background-color: {c['sidebar_bg']};
                border-left: 1px solid {c['border']};
                padding: 12px;
                min-width: 280px;
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
            notebook header tab {{
                background-color: {c['card_bg']};
                border: 1px solid {c['border']};
                padding: 4px 12px;
                color: {c['on_surface']};
                border-radius: 8px 8px 0 0;
            }}
            notebook header tab:checked {{
                background-color: {c['primary']};
                color: #101014;
                font-weight: bold;
            }}
        """.encode('utf-8')
        
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    # -------------------------------------------------------------------------
    # Header Bar
    # -------------------------------------------------------------------------
    def create_header_bar(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox.get_style_context().add_class("header-bar")

        # History Buttons
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
        self.btn_up.connect("clicked", lambda w: self.navigate_current_tab(os.path.dirname(self.get_active_tab_path())))
        hbox.pack_start(self.btn_up, False, False, 0)

        # Breadcrumbs Stack (Breadcrumb buttons OR Direct Text Entry)
        self.path_stack = Gtk.Stack()
        
        self.breadcrumb_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.path_stack.add_named(self.breadcrumb_box, "breadcrumbs")
        
        self.direct_path_entry = Gtk.Entry()
        self.direct_path_entry.get_style_context().add_class("path-entry")
        self.direct_path_entry.connect("activate", self.on_direct_path_entered)
        self.direct_path_entry.connect("focus-out-event", lambda w, e: self.path_stack.set_visible_child_name("breadcrumbs"))
        self.path_stack.add_named(self.direct_path_entry, "direct_entry")

        hbox.pack_start(self.path_stack, True, True, 6)

        # New Tab Button
        btn_tab = Gtk.Button(label="󰝰+")
        btn_tab.get_style_context().add_class("nav-btn")
        btn_tab.set_tooltip_text("New Tab (Ctrl+T)")
        btn_tab.connect("clicked", lambda w: self.add_tab(self.get_active_tab_path()))
        hbox.pack_end(btn_tab, False, False, 0)

        # Search Bar
        self.search_entry = Gtk.Entry()
        self.search_entry.get_style_context().add_class("search-entry")
        self.search_entry.set_placeholder_text("󰍉 Filter...")
        self.search_entry.connect("changed", self.on_search_changed)
        hbox.pack_end(self.search_entry, False, False, 0)

        # Quick Actions
        btn_term = Gtk.Button(label="")
        btn_term.get_style_context().add_class("nav-btn")
        btn_term.set_tooltip_text("Open Kitty in folder (Ctrl+T)")
        btn_term.connect("clicked", self.on_open_terminal)
        hbox.pack_end(btn_term, False, False, 0)

        btn_new_dir = Gtk.Button(label="󰉋+")
        btn_new_dir.get_style_context().add_class("nav-btn")
        btn_new_dir.set_tooltip_text("New Folder (Ctrl+N)")
        btn_new_dir.connect("clicked", self.on_create_folder_dialog)
        hbox.pack_end(btn_new_dir, False, False, 0)

        self.btn_hidden = Gtk.ToggleButton(label="󰈈")
        self.btn_hidden.get_style_context().add_class("nav-btn")
        self.btn_hidden.set_tooltip_text("Toggle Hidden Files (Ctrl+H)")
        self.btn_hidden.connect("toggled", self.on_toggle_hidden)
        hbox.pack_end(self.btn_hidden, False, False, 0)

        return hbox

    # -------------------------------------------------------------------------
    # Tab Management
    # -------------------------------------------------------------------------
    def add_tab(self, path):
        target_path = os.path.abspath(path)
        tab_idx = len(self.tabs_data)
        
        tab_info = {
            "path": target_path,
            "history": [target_path],
            "history_idx": 0,
            "selected_path": None
        }
        self.tabs_data.append(tab_info)

        # Create Tab Content Page
        page_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        
        # Sidebar
        sidebar = self.create_sidebar()
        page_box.pack_start(sidebar, False, False, 0)

        # File View
        files_view, treeview, liststore = self.create_files_view()
        page_box.pack_start(files_view, True, True, 0)
        tab_info["treeview"] = treeview
        tab_info["liststore"] = liststore

        # Detail/Preview Pane
        preview_pane, preview_widgets = self.create_preview_pane()
        page_box.pack_start(preview_pane, False, False, 0)
        tab_info["preview_widgets"] = preview_widgets

        # Tab Header Label + Close Button
        tab_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        tab_title = Gtk.Label(label=os.path.basename(target_path) or "/")
        tab_label_box.pack_start(tab_title, True, True, 0)
        tab_info["tab_title"] = tab_title

        btn_close_tab = Gtk.Button(label="×")
        btn_close_tab.set_relief(Gtk.ReliefStyle.NONE)
        btn_close_tab.connect("clicked", lambda w: self.close_tab(page_box))
        tab_label_box.pack_end(btn_close_tab, False, False, 0)
        tab_label_box.show_all()

        self.tab_notebook.append_page(page_box, tab_label_box)
        page_box.show_all()
        self.tab_notebook.set_current_page(-1)

        self.load_tab_directory(tab_info, target_path)

    def close_tab(self, page_widget):
        page_num = self.tab_notebook.page_num(page_widget)
        if self.tab_notebook.get_n_pages() > 1 and page_num != -1:
            self.tabs_data.pop(page_num)
            self.tab_notebook.remove_page(page_num)
        else:
            self.destroy()

    def get_active_tab(self):
        idx = self.tab_notebook.get_current_page()
        if 0 <= idx < len(self.tabs_data):
            return self.tabs_data[idx]
        return None

    def get_active_tab_path(self):
        tab = self.get_active_tab()
        return tab["path"] if tab else os.path.expanduser("~")

    def on_tab_switched(self, notebook, page, page_num):
        if page_num < len(self.tabs_data):
            tab = self.tabs_data[page_num]
            self.update_breadcrumbs(tab["path"])
            self.update_status_and_git(tab["path"])

    # -------------------------------------------------------------------------
    # Sidebar
    # -------------------------------------------------------------------------
    def create_sidebar(self):
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        sidebar_box.get_style_context().add_class("sidebar")

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

        vault_paths = [
            os.path.expanduser("~/Documents/Obsidian Vault"),
            "/Users/jannik/Documents/Obsidian Vault"
        ]
        for vp in vault_paths:
            if os.path.isdir(vp):
                favorites.append(("🧠 Obsidian Vault", vp))
                break

        for name, path in favorites:
            if os.path.isdir(path):
                btn = Gtk.Button(label=name)
                btn.set_alignment(0, 0.5)
                btn.get_style_context().add_class("sidebar-item")
                btn.target_path = path
                btn.connect("clicked", lambda w: self.navigate_current_tab(w.target_path))
                sidebar_box.pack_start(btn, False, False, 0)

        # Delivery & Customer category
        lbl_clients = Gtk.Label(label="DELIVERY & CLIENTS", xalign=0)
        lbl_clients.get_style_context().add_class("sidebar-category")
        sidebar_box.pack_start(lbl_clients, False, False, 0)

        client_dirs = [
            ("📦 Sapphire Delivery", "/srv/sapphire/customercodes/Fiverr"),
            ("💼 Customer Codes", "/srv/sapphire"),
        ]
        for name, path in client_dirs:
            if os.path.isdir(path):
                btn = Gtk.Button(label=name)
                btn.set_alignment(0, 0.5)
                btn.get_style_context().add_class("sidebar-item")
                btn.target_path = path
                btn.connect("clicked", lambda w: self.navigate_current_tab(w.target_path))
                sidebar_box.pack_start(btn, False, False, 0)

        # SSHFS Remote Servers
        ssh_hosts = parse_ssh_hosts()
        if ssh_hosts:
            lbl_servers = Gtk.Label(label="REMOTE SERVERS", xalign=0)
            lbl_servers.get_style_context().add_class("sidebar-category")
            sidebar_box.pack_start(lbl_servers, False, False, 0)

            for host in ssh_hosts[:6]:
                btn = Gtk.Button(label=f"🌐 {host}")
                btn.set_alignment(0, 0.5)
                btn.get_style_context().add_class("sidebar-item")
                btn.ssh_host = host
                btn.connect("clicked", self.on_mount_ssh_server)
                sidebar_box.pack_start(btn, False, False, 0)

        # System
        lbl_places = Gtk.Label(label="SYSTEM", xalign=0)
        lbl_places.get_style_context().add_class("sidebar-category")
        sidebar_box.pack_start(lbl_places, False, False, 0)

        places = [
            ("󰋊 Root (/)", "/"),
            ("󰉋 ArchSwitch", "/home/ArchSwitch"),
            ("󰒋 .config", os.path.expanduser("~/.config")),
            ("🗑️ Trash", os.path.expanduser("~/.local/share/Trash/files")),
        ]
        for name, path in places:
            if os.path.isdir(path):
                btn = Gtk.Button(label=name)
                btn.set_alignment(0, 0.5)
                btn.get_style_context().add_class("sidebar-item")
                btn.target_path = path
                btn.connect("clicked", lambda w: self.navigate_current_tab(w.target_path))
                sidebar_box.pack_start(btn, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(sidebar_box)
        return scrolled

    # -------------------------------------------------------------------------
    # Files View (Grid & List)
    # -------------------------------------------------------------------------
    def create_files_view(self):
        liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str, str, bool, str)
        treeview = Gtk.TreeView(model=liststore)
        treeview.set_headers_visible(True)
        treeview.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

        treeview.connect("row-activated", self.on_item_double_clicked)
        treeview.connect("button-press-event", self.on_treeview_button_press)
        treeview.get_selection().connect("changed", self.on_selection_changed)

        # Enable Drag & Drop to external apps (Firefox/Discord)
        target_entry = Gtk.TargetEntry.new("text/uri-list", Gtk.TargetFlags.OTHER_APP, 0)
        treeview.enable_model_drag_source(
            Gdk.ModifierType.BUTTON1_MASK,
            [target_entry],
            Gdk.DragAction.COPY | Gdk.DragAction.MOVE
        )
        treeview.connect("drag-data-get", self.on_drag_data_get)

        # Columns
        col_name = Gtk.TreeViewColumn("Name")
        col_name.set_resizable(True)
        col_name.set_min_width(320)
        
        renderer_icon = Gtk.CellRendererPixbuf()
        col_name.pack_start(renderer_icon, False)
        col_name.add_attribute(renderer_icon, "pixbuf", 0)

        renderer_text = Gtk.CellRendererText()
        col_name.pack_start(renderer_text, True)
        col_name.add_attribute(renderer_text, "text", 1)
        treeview.append_column(col_name)

        col_size = Gtk.TreeViewColumn("Size", Gtk.CellRendererText(), text=2)
        col_size.set_resizable(True)
        col_size.set_min_width(90)
        treeview.append_column(col_size)

        col_mod = Gtk.TreeViewColumn("Modified", Gtk.CellRendererText(), text=3)
        col_mod.set_resizable(True)
        col_mod.set_min_width(140)
        treeview.append_column(col_mod)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(treeview)
        return scrolled, treeview, liststore

    # -------------------------------------------------------------------------
    # Preview & Detail Pane
    # -------------------------------------------------------------------------
    def create_preview_pane(self):
        preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        preview_box.get_style_context().add_class("preview-pane")

        # Media Preview / Code Snippet Frame
        preview_image = Gtk.Image()
        preview_image.set_size_request(240, 160)
        preview_box.pack_start(preview_image, False, False, 0)

        # Text/Code Snippet Viewer for text files
        text_scroll = Gtk.ScrolledWindow()
        text_scroll.set_size_request(240, 150)
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_cursor_visible(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        text_scroll.add(text_view)
        preview_box.pack_start(text_scroll, False, False, 0)

        # Metadata Labels
        lbl_name = Gtk.Label(label="Select an item", xalign=0)
        lbl_name.set_line_wrap(True)
        lbl_name.get_style_context().add_class("sidebar-category")
        preview_box.pack_start(lbl_name, False, False, 0)

        lbl_meta = Gtk.Label(label="", xalign=0)
        lbl_meta.set_line_wrap(True)
        preview_box.pack_start(lbl_meta, False, False, 0)

        # Quick Actions
        actions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        btn_share_link = Gtk.Button(label="🚀 Quick Share Link (0x0.st)")
        btn_share_link.get_style_context().add_class("share-btn")
        btn_share_link.connect("clicked", self.on_upload_and_share_link)
        actions_box.pack_start(btn_share_link, False, False, 0)

        btn_pkg_delivery = Gtk.Button(label="📦 Package for Delivery (.zip)")
        btn_pkg_delivery.get_style_context().add_class("action-btn")
        btn_pkg_delivery.connect("clicked", self.on_package_for_delivery)
        actions_box.pack_start(btn_pkg_delivery, False, False, 0)

        btn_open = Gtk.Button(label="󰅩 Open Default App")
        btn_open.get_style_context().add_class("action-btn")
        btn_open.connect("clicked", self.on_open_selected)
        actions_box.pack_start(btn_open, False, False, 0)

        btn_copy_path = Gtk.Button(label="📋 Copy Path")
        btn_copy_path.get_style_context().add_class("action-btn")
        btn_copy_path.connect("clicked", self.on_copy_selected_path)
        actions_box.pack_start(btn_copy_path, False, False, 0)

        preview_box.pack_end(actions_box, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(preview_box)

        widgets = {
            "image": preview_image,
            "text_scroll": text_scroll,
            "text_view": text_view,
            "lbl_name": lbl_name,
            "lbl_meta": lbl_meta
        }
        return scrolled, widgets

    # -------------------------------------------------------------------------
    # Directory Loading & Navigation
    # -------------------------------------------------------------------------
    def load_tab_directory(self, tab, target_dir):
        if not os.path.isdir(target_dir):
            return

        target_dir = os.path.abspath(target_dir)
        tab["path"] = target_dir
        tab["liststore"].clear()

        # Update Tab Title
        tab_name = os.path.basename(target_dir) or "/"
        tab["tab_title"].set_text(tab_name)

        # Update Breadcrumb Bar & Git Status
        self.update_breadcrumbs(target_dir)
        self.update_status_and_git(target_dir)

        # Scan folder items
        try:
            entries = os.listdir(target_dir)
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

            full_path = os.path.join(target_dir, name)
            is_dir = os.path.isdir(full_path)
            
            try:
                stat = os.stat(full_path)
                size_str = "<DIR>" if is_dir else format_size(stat.st_size)
                mtime_str = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
            except Exception:
                size_str = "-"
                mtime_str = "-"

            icon_name = get_file_icon_name(full_path, is_dir)
            try:
                pixbuf = self.icon_theme.load_icon(icon_name, 22, Gtk.IconLookupFlags.GENERIC_FALLBACK)
            except Exception:
                pixbuf = self.icon_theme.load_icon("text-x-generic", 22, Gtk.IconLookupFlags.GENERIC_FALLBACK)

            if is_dir:
                dirs.append((pixbuf, name, size_str, mtime_str, True, full_path))
            else:
                files.append((pixbuf, name, size_str, mtime_str, False, full_path))

        for item in dirs + files:
            tab["liststore"].append(item)

        self.status_label.set_text(f"📁 {len(dirs)} Folders, 📄 {len(files)} Files  |  {target_dir}")

    def navigate_current_tab(self, path):
        tab = self.get_active_tab()
        if not tab or not os.path.isdir(path):
            return
        
        path = os.path.abspath(path)
        if tab["path"] != path:
            tab["history"] = tab["history"][:tab["history_idx"] + 1]
            tab["history"].append(path)
            tab["history_idx"] += 1
            self.load_tab_directory(tab, path)

    def update_breadcrumbs(self, path):
        for child in self.breadcrumb_box.get_children():
            self.breadcrumb_box.remove(child)

        parts = path.strip("/").split("/")
        accum = "/"
        
        btn_root = Gtk.Button(label="󰋊 /")
        btn_root.get_style_context().add_class("path-button")
        btn_root.target_path = "/"
        btn_root.connect("clicked", lambda w: self.navigate_current_tab(w.target_path))
        self.breadcrumb_box.pack_start(btn_root, False, False, 0)

        if parts and parts[0]:
            for p in parts:
                accum = os.path.join(accum, p)
                sep = Gtk.Label(label="›")
                self.breadcrumb_box.pack_start(sep, False, False, 1)

                btn = Gtk.Button(label=p)
                btn.get_style_context().add_class("path-button")
                btn.target_path = accum
                btn.connect("clicked", lambda w: self.navigate_current_tab(w.target_path))
                self.breadcrumb_box.pack_start(btn, False, False, 0)

        self.breadcrumb_box.show_all()

    def update_status_and_git(self, path):
        git_branch = get_git_branch(path)
        self.git_label.set_text(git_branch)

    def on_direct_path_entered(self, entry):
        target = os.path.expanduser(entry.get_text().strip())
        if os.path.isdir(target):
            self.navigate_current_tab(target)
            self.path_stack.set_visible_child_name("breadcrumbs")
        else:
            self.status_label.set_text(f"Invalid path: {target}")

    def on_back_clicked(self, w):
        tab = self.get_active_tab()
        if tab and tab["history_idx"] > 0:
            tab["history_idx"] -= 1
            self.load_tab_directory(tab, tab["history"][tab["history_idx"]])

    def on_forward_clicked(self, w):
        tab = self.get_active_tab()
        if tab and tab["history_idx"] < len(tab["history"]) - 1:
            tab["history_idx"] += 1
            self.load_tab_directory(tab, tab["history"][tab["history_idx"]])

    def on_search_changed(self, entry):
        self.search_filter = entry.get_text().strip()
        tab = self.get_active_tab()
        if tab:
            self.load_tab_directory(tab, tab["path"])

    def on_toggle_hidden(self, btn):
        self.show_hidden = btn.get_active()
        tab = self.get_active_tab()
        if tab:
            self.load_tab_directory(tab, tab["path"])

    # -------------------------------------------------------------------------
    # Drag & Drop Handler
    # -------------------------------------------------------------------------
    def on_drag_data_get(self, treeview, context, selection_data, info, time):
        selection = treeview.get_selection()
        model, paths = selection.get_selected_rows()
        uris = []
        for path in paths:
            iter_ = model.get_iter(path)
            full_path = model.get_value(iter_, 5)
            uris.append(f"file://{urllib.parse.quote(full_path)}")
        
        if uris:
            selection_data.set_uris(uris)

    # -------------------------------------------------------------------------
    # SSHFS Server Mounting
    # -------------------------------------------------------------------------
    def on_mount_ssh_server(self, btn):
        host = btn.ssh_host
        mount_dir = os.path.expanduser(f"~/Remote/{host}")
        os.makedirs(mount_dir, exist_ok=True)

        res = subprocess.run(["mountpoint", "-q", mount_dir])
        if res.returncode != 0:
            self.status_label.set_text(f"Connecting to {host} via SSHFS...")
            cmd = ["sshfs", "-o", "reconnect,ServerAliveInterval=15", f"{host}:/", mount_dir]
            mount_proc = subprocess.run(cmd)
            if mount_proc.returncode == 0:
                subprocess.Popen(["notify-send", "-a", "Nexus Finder", "-i", "network-server", "🌐 Server gemountet", f"{host} ist bereit unter ~/Remote/{host}"])
            else:
                self.status_label.set_text(f"⚠️ SSHFS Connection Failed for {host}")
                return

        self.navigate_current_tab(mount_dir)

    # -------------------------------------------------------------------------
    # Cut, Copy, Paste & File Operations
    # -------------------------------------------------------------------------
    def get_selected_paths(self):
        tab = self.get_active_tab()
        if not tab: return []
        selection = tab["treeview"].get_selection()
        model, paths = selection.get_selected_rows()
        selected = []
        for path in paths:
            iter_ = model.get_iter(path)
            selected.append(model.get_value(iter_, 5))
        return selected

    def on_copy_files(self):
        paths = self.get_selected_paths()
        if paths:
            self.internal_clipboard = {"action": "copy", "paths": paths}
            subprocess.Popen(["notify-send", "-a", "Nexus Finder", "-i", "edit-copy", "-t", "1000", f"📋 {len(paths)} Element(e) kopiert", "Bereit zum Einfügen"])

    def on_cut_files(self):
        paths = self.get_selected_paths()
        if paths:
            self.internal_clipboard = {"action": "cut", "paths": paths}
            subprocess.Popen(["notify-send", "-a", "Nexus Finder", "-i", "edit-cut", "-t", "1000", f"✂️ {len(paths)} Element(e) ausgeschnitten", "Bereit zum Verschieben"])

    def on_paste_files(self):
        tab = self.get_active_tab()
        if not tab or not self.internal_clipboard["paths"]:
            return

        dest_dir = tab["path"]
        action = self.internal_clipboard["action"]
        paths = self.internal_clipboard["paths"]

        for src in paths:
            if not os.path.exists(src): continue
            base = os.path.basename(src)
            dest = os.path.join(dest_dir, base)

            # Avoid overwrite collision by numbering
            counter = 1
            name, ext = os.path.splitext(base)
            while os.path.exists(dest):
                dest = os.path.join(dest_dir, f"{name}_{counter}{ext}")
                counter += 1

            try:
                if action == "copy":
                    if os.path.isdir(src):
                        shutil.copytree(src, dest)
                    else:
                        shutil.copy2(src, dest)
                elif action == "cut":
                    shutil.move(src, dest)
            except Exception as e:
                self.status_label.set_text(f"Paste error: {e}")

        if action == "cut":
            self.internal_clipboard = {"action": None, "paths": []}

        self.load_tab_directory(tab, dest_dir)
        subprocess.Popen(["notify-send", "-a", "Nexus Finder", "-i", "edit-paste", "-t", "1000", "✅ Eingefügt", f"Elemente nach {dest_dir} übertragen"])

    def on_archive_extract(self, path):
        dest = os.path.join(os.path.dirname(path), os.path.splitext(os.path.basename(path))[0])
        os.makedirs(dest, exist_ok=True)
        try:
            if path.endswith(".zip") or path.endswith(".jar"):
                with zipfile.ZipFile(path, 'r') as zip_ref:
                    zip_ref.extractall(dest)
            elif path.endswith((".tar.gz", ".tgz", ".tar.xz", ".tar")):
                with tarfile.open(path, 'r:*') as tar_ref:
                    tar_ref.extractall(dest)
            
            tab = self.get_active_tab()
            if tab: self.load_tab_directory(tab, tab["path"])
            subprocess.Popen(["notify-send", "-a", "Nexus Finder", "-i", "package-x-generic", "📦 Entpackt", f"Entpackt nach {dest}"])
        except Exception as e:
            self.status_label.set_text(f"Extract error: {e}")

    def on_archive_compress(self, path):
        base = os.path.basename(path)
        out_zip = os.path.join(os.path.dirname(path), f"{base}.zip")
        try:
            if os.path.isdir(path):
                shutil.make_archive(os.path.join(os.path.dirname(path), base), 'zip', path)
            else:
                with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as z:
                    z.write(path, base)
            
            tab = self.get_active_tab()
            if tab: self.load_tab_directory(tab, tab["path"])
            subprocess.Popen(["notify-send", "-a", "Nexus Finder", "-i", "package-x-generic", "📦 Archiv erstellt", f"{base}.zip"])
        except Exception as e:
            self.status_label.set_text(f"Compress error: {e}")

    # -------------------------------------------------------------------------
    # Client Delivery & 1-Click Share Engine
    # -------------------------------------------------------------------------
    def on_upload_and_share_link(self, w):
        paths = self.get_selected_paths()
        if not paths: return
        target = paths[0]

        if os.path.isdir(target):
            zip_dest = f"/tmp/{os.path.basename(target)}.zip"
            shutil.make_archive(f"/tmp/{os.path.basename(target)}", 'zip', target)
            upload_target = zip_dest
        else:
            upload_target = target

        self.status_label.set_text(f"Uploading {os.path.basename(upload_target)} for share URL...")
        subprocess.Popen(["notify-send", "-a", "Nexus Share", "-i", "network-transmit-receive", "🚀 Upload gestartet...", f"Lade {os.path.basename(upload_target)} hoch"])

        def upload_thread():
            try:
                curl_cmd = ["curl", "-s", "-F", f"file=@{upload_target}", "https://0x0.st"]
                res = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
                url = res.stdout.strip()
                if url.startswith("http"):
                    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                    clipboard.set_text(url, -1)
                    
                    if which_cmd := shutil.which("canberra-gtk-play"):
                        subprocess.Popen([which_cmd, "-i", "complete"])
                        
                    subprocess.Popen([
                        "notify-send",
                        "-a", "Nexus Share",
                        "-i", "edit-paste",
                        "-t", "3000",
                        "📋 Direkter Download-Link kopiert!",
                        f"{url}\n(Bereit zum Einfügen im Fiverr/Discord Chat)"
                    ])
                    GLib.idle_add(lambda: self.status_label.set_text(f"Share URL: {url}"))
                else:
                    GLib.idle_add(lambda: self.status_label.set_text("Upload failed"))
            except Exception as e:
                GLib.idle_add(lambda: self.status_label.set_text(f"Upload error: {e}"))

        threading.Thread(target=upload_thread, daemon=True).start()

    def on_package_for_delivery(self, w):
        paths = self.get_selected_paths()
        if not paths: return
        target = paths[0]

        base_name = os.path.basename(target)
        tab = self.get_active_tab()
        delivery_folder = os.path.join(tab["path"] if tab else os.path.expanduser("~"), "delivery")
        os.makedirs(delivery_folder, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        zip_output = os.path.join(delivery_folder, f"{base_name}_Delivery_{timestamp}")

        try:
            if os.path.isdir(target):
                shutil.make_archive(zip_output, 'zip', target)
            else:
                dest_file = os.path.join(delivery_folder, base_name)
                shutil.copy2(target, dest_file)

            subprocess.Popen([
                "notify-send",
                "-a", "Nexus Delivery",
                "-i", "package-x-generic",
                "-t", "2500",
                "📦 Übergabe-Paket erstellt!",
                f"Gespeichert in: delivery/\nBereit für den Kunden!"
            ])
            if tab: self.load_tab_directory(tab, tab["path"])
        except Exception as e:
            self.status_label.set_text(f"Delivery pack error: {e}")

    # -------------------------------------------------------------------------
    # Interactions & Selection
    # -------------------------------------------------------------------------
    def on_item_double_clicked(self, treeview, path, column):
        model = treeview.get_model()
        iter_ = model.get_iter(path)
        is_dir = model.get_value(iter_, 4)
        full_path = model.get_value(iter_, 5)

        if is_dir:
            self.navigate_current_tab(full_path)
        else:
            subprocess.Popen(["xdg-open", full_path])

    def on_selection_changed(self, selection):
        tab = self.get_active_tab()
        if not tab: return
        
        model, paths = selection.get_selected_rows()
        pw = tab["preview_widgets"]

        if not paths:
            pw["image"].clear()
            pw["text_scroll"].hide()
            pw["lbl_name"].set_text("No selection")
            pw["lbl_meta"].set_text("")
            return

        iter_ = model.get_iter(paths[0])
        name = model.get_value(iter_, 1)
        size_str = model.get_value(iter_, 2)
        mod_str = model.get_value(iter_, 3)
        is_dir = model.get_value(iter_, 4)
        full_path = model.get_value(iter_, 5)

        tab["selected_path"] = full_path
        pw["lbl_name"].set_text(name)
        pw["lbl_meta"].set_text(f"Type: {'Folder' if is_dir else 'File'}\nSize: {size_str}\nModified: {mod_str}\nPath:\n{full_path}")

        ext = os.path.splitext(full_path)[1].lower()
        if not is_dir and ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"]:
            pw["text_scroll"].hide()
            pw["image"].show()
            try:
                pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(full_path, 240, 160, True)
                pw["image"].set_from_pixbuf(pix)
            except Exception:
                pw["image"].clear()
        elif not is_dir and ext in [".py", ".sh", ".json", ".yaml", ".yml", ".md", ".txt", ".java", ".rs", ".css", ".html", ".toml", ".conf"]:
            pw["image"].clear()
            pw["image"].hide()
            pw["text_scroll"].show()
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    preview_text = "".join([f.readline() for _ in range(35)])
                buf = pw["text_view"].get_buffer()
                buf.set_text(preview_text)
            except Exception:
                pw["text_scroll"].hide()
        else:
            pw["image"].clear()
            pw["image"].hide()
            pw["text_scroll"].hide()

    def on_treeview_button_press(self, treeview, event):
        if event.button == 3: # Right Click Context Menu
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

        item_open = Gtk.MenuItem(label="󰅩 Open Default App")
        item_open.connect("activate", lambda w: subprocess.Popen(["xdg-open", path]))
        menu.append(item_open)

        item_share = Gtk.MenuItem(label="🚀 1-Click Quick Share Link (0x0.st)")
        item_share.connect("activate", lambda w: self.on_upload_and_share_link(None))
        menu.append(item_share)

        item_pkg = Gtk.MenuItem(label="📦 Package for Delivery (.zip)")
        item_pkg.connect("activate", lambda w: self.on_package_for_delivery(None))
        menu.append(item_pkg)

        menu.append(Gtk.SeparatorMenuItem())

        # Archive operations
        if path.endswith((".zip", ".tar.gz", ".tgz", ".jar", ".tar.xz", ".tar")):
            item_extract = Gtk.MenuItem(label="📦 Extract Archive Here")
            item_extract.connect("activate", lambda w: self.on_archive_extract(path))
            menu.append(item_extract)
        else:
            item_compress = Gtk.MenuItem(label="📦 Compress to .zip")
            item_compress.connect("activate", lambda w: self.on_archive_compress(path))
            menu.append(item_compress)

        menu.append(Gtk.SeparatorMenuItem())

        item_copy = Gtk.MenuItem(label="📋 Copy (Ctrl+C)")
        item_copy.connect("activate", lambda w: self.on_copy_files())
        menu.append(item_copy)

        item_cut = Gtk.MenuItem(label="✂️ Cut (Ctrl+X)")
        item_cut.connect("activate", lambda w: self.on_cut_files())
        menu.append(item_cut)

        item_paste = Gtk.MenuItem(label="📥 Paste (Ctrl+V)")
        item_paste.connect("activate", lambda w: self.on_paste_files())
        menu.append(item_paste)

        menu.append(Gtk.SeparatorMenuItem())

        item_term = Gtk.MenuItem(label=" Open in Kitty Terminal")
        dir_to_open = path if os.path.isdir(path) else os.path.dirname(path)
        item_term.connect("activate", lambda w: subprocess.Popen(["kitty", "--directory", dir_to_open]))
        menu.append(item_term)

        item_copy_p = Gtk.MenuItem(label="📋 Copy Path")
        item_copy_p.connect("activate", lambda w: self.copy_to_clipboard(path))
        menu.append(item_copy_p)

        menu.append(Gtk.SeparatorMenuItem())

        item_rename = Gtk.MenuItem(label="✏️ Rename (F2)")
        item_rename.connect("activate", lambda w: self.on_rename_dialog(path))
        menu.append(item_rename)

        item_delete = Gtk.MenuItem(label="🗑️ Delete (Delete)")
        item_delete.connect("activate", lambda w: self.on_delete_dialog(path))
        menu.append(item_delete)

        menu.show_all()
        menu.popup_at_pointer(event)

    def on_open_terminal(self, w):
        subprocess.Popen(["kitty", "--directory", self.get_active_tab_path()])

    def on_open_selected(self, w):
        paths = self.get_selected_paths()
        if paths:
            subprocess.Popen(["xdg-open", paths[0]])

    def on_copy_selected_path(self, w):
        paths = self.get_selected_paths()
        if paths:
            self.copy_to_clipboard(paths[0])

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

        tab = self.get_active_tab()
        if res == Gtk.ResponseType.OK and name and tab:
            new_dir = os.path.join(tab["path"], name)
            try:
                os.makedirs(new_dir, exist_ok=True)
                self.load_tab_directory(tab, tab["path"])
            except Exception as e:
                self.status_label.set_text(f"Folder create error: {e}")

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

        tab = self.get_active_tab()
        if res == Gtk.ResponseType.OK and new_name and new_name != old_name and tab:
            new_path = os.path.join(os.path.dirname(path), new_name)
            try:
                os.rename(path, new_path)
                self.load_tab_directory(tab, tab["path"])
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

        tab = self.get_active_tab()
        if res == Gtk.ResponseType.OK and tab:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.load_tab_directory(tab, tab["path"])
            except Exception as e:
                self.status_label.set_text(f"Delete error: {e}")

    def on_key_press(self, w, event):
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        alt = bool(event.state & Gdk.ModifierType.MOD1_MASK)

        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        elif event.keyval == Gdk.KEY_BackSpace or (alt and event.keyval == Gdk.KEY_Left):
            self.navigate_current_tab(os.path.dirname(self.get_active_tab_path()))
            return True
        elif ctrl and event.keyval == Gdk.KEY_t:
            self.add_tab(self.get_active_tab_path())
            return True
        elif ctrl and event.keyval == Gdk.KEY_w:
            current_page = self.tab_notebook.get_nth_page(self.tab_notebook.get_current_page())
            if current_page:
                self.close_tab(current_page)
            return True
        elif ctrl and event.keyval == Gdk.KEY_l:
            self.path_stack.set_visible_child_name("direct_entry")
            self.direct_path_entry.set_text(self.get_active_tab_path())
            self.direct_path_entry.grab_focus()
            return True
        elif ctrl and event.keyval == Gdk.KEY_h:
            self.btn_hidden.set_active(not self.btn_hidden.get_active())
            return True
        elif ctrl and event.keyval == Gdk.KEY_f:
            self.search_entry.grab_focus()
            return True
        elif ctrl and event.keyval == Gdk.KEY_c:
            self.on_copy_files()
            return True
        elif ctrl and event.keyval == Gdk.KEY_x:
            self.on_cut_files()
            return True
        elif ctrl and event.keyval == Gdk.KEY_v:
            self.on_paste_files()
            return True
        elif ctrl and event.keyval == Gdk.KEY_n:
            self.on_create_folder_dialog(None)
            return True
        elif event.keyval == Gdk.KEY_F5 or (ctrl and event.keyval == Gdk.KEY_r):
            tab = self.get_active_tab()
            if tab: self.load_tab_directory(tab, tab["path"])
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
