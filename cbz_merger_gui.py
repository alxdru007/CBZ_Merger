#!/usr/bin/env python3
"""
CBZ Merger GUI — A modern, premium dark-themed graphical interface for merging .cbz files.

Usage:
    python cbz_merger_gui.py

Requires: tkinter (included with Python on Windows)
Optional: tkinterdnd2 (for drag and drop support)
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import zipfile
import tempfile
import shutil
import time

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

# Import the core merger logic
from cbz_merger import merge_cbz_files, discover_cbz_files, _format_size, _natural_sort_key

# ─── Translations ────────────────────────────────────────────────────────────
TRANSLATIONS = {
    "en": {
        "title_main": "CBZ Merger",
        "title_desc": "Combine multiple CBZ files into one",
        "ready_start": "Ready — select a folder to begin",
        "start_merge": "🔗  Start Merge",
        "cancel_merge": "🛑 Cancel",
        "open_folder": "📂  Open Output Folder",
        "source": "Source",
        "files_to_merge": "Files to Merge",
        "output": "Output",
        "no_files": "No files or folder selected",
        "select_folder": "📁 Select Folder",
        "filename": "Filename",
        "save_as": "Save As",
        "deflate": "  DEFLATE compression (smaller file, slower)",
        "ereader": "  E-Reader Optimization (B&W, scale to 1600px, shrink size)",
        "empty_list": "Select a folder to discover .cbz files",
        "no_cbz": "No .cbz files found",
        "ready_merge": "Ready to merge {} files",
        "starting": "Starting merge...",
        "aborting": "Aborting merge...",
        "aborted": "❌ Merge aborted by user.",
        "extracting": "Extracting chapters...",
        "packing": "Packing {} images...",
        "done": "✅ Done! {} images → {} ({}) in {:.1f}s",
        "status_files": "{} / {} files selected",
        "warn_no_files": "Please select a folder with .cbz files first.",
        "warn_no_selection": "Please select at least one file to merge.",
        "warn_no_output": "Please enter an output filename.",
        "err_no_img": "No images found in any selected file!",
        "lang_btn": "🇩🇪 DE",
        "save_to": "📁 Will save to: {}",
        "saved_to": "✅ Saved to: {}",
        "alert_title": "Notice",
        "pack_prog": "Packing images... ({}/{})",
        "extr_prog": "Extracting ({}/{}): {}",
        "perm_err": "Permission denied writing to {}",
        "err": "Error: {}",
        "custom_drop": "{} files manually dropped",
        "split_vols": "  📦 Split into Volumes",
        "ch_per_vol": "Chapters per Volume:",
        "pack_vol_prog": "Packing Volume {}/{}...",
        "done_split": "✅ Done! {} images → {} Volumes in {:.1f}s",
        "auto_cover": "Auto (File 1)",
        "custom_cover": "Custom Cover",
        "no_cover": "No Cover",
    },
    "de": {
        "title_main": "CBZ Merger",
        "title_desc": "Kombiniere mehrere CBZ-Dateien zu einer",
        "ready_start": "Bereit — Wähle einen Ordner zum Starten",
        "start_merge": "🔗  Merge Starten",
        "cancel_merge": "🛑 Abbrechen",
        "open_folder": "📂  Ausgabe-Ordner öffnen",
        "source": "Quelle",
        "files_to_merge": "Zu Mergende Dateien",
        "output": "Ausgabe",
        "no_files": "Keine Dateien oder Ordner ausgewählt",
        "select_folder": "📁 Ordner wählen",
        "filename": "Dateiname",
        "save_as": "Speichern unter",
        "deflate": "  DEFLATE-Kompression (kleinere Datei, langsamer)",
        "ereader": "  E-Reader Optimierung (S/W, skalieren auf 1600px, komprimieren)",
        "empty_list": "Ordner wählen oder Dateien hierher ziehen",
        "no_cbz": "Keine .cbz-Dateien gefunden",
        "ready_merge": "Bereit zum Mergen von {} Dateien",
        "starting": "Merge startet...",
        "aborting": "Merge wird abgebrochen...",
        "aborted": "❌ Merge durch Benutzer abgebrochen.",
        "extracting": "Kapitel werden entpackt...",
        "packing": "Verpacke {} Bilder...",
        "done": "✅ Fertig! {} Bilder → {} ({}) in {:.1f}s",
        "status_files": "{} / {} Dateien ausgewählt",
        "warn_no_files": "Bitte wähle zuerst einen Ordner mit .cbz-Dateien.",
        "warn_no_selection": "Bitte markiere mindestens eine Datei zum Mergen.",
        "warn_no_output": "Bitte gib einen Ausgabenamen ein.",
        "err_no_img": "Keine Bilder in den ausgewählten Dateien gefunden!",
        "lang_btn": "🇬🇧 EN",
        "save_to": "📁 Ziel: {}",
        "saved_to": "✅ Gespeichert in: {}",
        "alert_title": "Hinweis",
        "pack_prog": "Bilder werden verpackt... ({}/{})",
        "extr_prog": "Entpacke ({}/{}): {}",
        "perm_err": "Zugriff verweigert auf {}",
        "err": "Fehler: {}",
        "custom_drop": "{} Dateien manuell hinzugefügt",
        "split_vols": "  📦 In Volumes aufteilen",
        "ch_per_vol": "Kapitel pro Volume:",
        "pack_vol_prog": "Verpacke Volume {}/{}...",
        "done_split": "✅ Fertig! {} Bilder → {} Volumes in {:.1f}s",
        "auto_cover": "Auto (Datei 1)",
        "custom_cover": "Eigenes Cover",
        "no_cover": "Kein Cover",
    }
}


# ─── Color Palette ───────────────────────────────────────────────────────────
class Colors:
    # Backgrounds — deep, layered
    BG_BASE       = "#0c0c14"
    BG_SURFACE    = "#13131f"
    BG_CARD       = "#1a1a2a"
    BG_CARD_ALT   = "#1e1e30"
    BG_INPUT      = "#161624"
    BG_HOVER      = "#252540"

    # Accent — refined purple gradient endpoints
    ACCENT        = "#7c5cf5"
    ACCENT_LIGHT  = "#a78bfa"
    ACCENT_GLOW   = "#6d4de8"
    ACCENT_DIM    = "#4a3a8a"
    ACCENT_DARK   = "#2d1f6e"

    # Semantic
    SUCCESS       = "#34d399"
    SUCCESS_DIM   = "#065f46"
    WARNING       = "#fbbf24"
    WARNING_DIM   = "#78350f"
    ERROR         = "#f87171"
    ERROR_DIM     = "#7f1d1d"

    # Text
    TEXT          = "#eeeef5"
    TEXT_SEC      = "#a0a0c0"
    TEXT_DIM      = "#6a6a8a"
    TEXT_MUTED    = "#404060"

    # Borders
    BORDER        = "#2a2a42"
    BORDER_LIGHT  = "#353555"
    BORDER_ACCENT = "#4a3a8a"


# ─── Custom Widgets ──────────────────────────────────────────────────────────

class GradientButton(tk.Canvas):
    """A gradient button with smooth hover animation."""

    def __init__(self, parent, text, command=None, width=200, height=44,
                 font_size=12, style="primary", **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=parent.cget("bg") if hasattr(parent, "cget") else Colors.BG_BASE,
                         highlightthickness=0, **kwargs)
        self._command = command
        self._text = text
        self._width = width
        self._height = height
        self._font_size = font_size
        self._enabled = True
        self._hovering = False
        self._style = style

        if style == "primary":
            self._colors = (Colors.ACCENT_GLOW, Colors.ACCENT, Colors.ACCENT_LIGHT)
            self._hover_colors = (Colors.ACCENT, Colors.ACCENT_LIGHT, "#b89cff")
            self._fg = "#ffffff"
        elif style == "secondary":
            self._colors = (Colors.BG_CARD, Colors.BG_CARD, Colors.BG_CARD_ALT)
            self._hover_colors = (Colors.BG_HOVER, Colors.BG_HOVER, Colors.BG_HOVER)
            self._fg = Colors.TEXT_SEC
        elif style == "danger":
            self._colors = (Colors.ERROR_DIM, Colors.ERROR, Colors.ERROR_DIM)
            self._hover_colors = (Colors.ERROR, Colors.ERROR, Colors.ERROR)
            self._fg = "#ffffff"

        self._draw(self._colors)

        self.bind("<Enter>", lambda e: self._on_hover(True))
        self.bind("<Leave>", lambda e: self._on_hover(False))
        self.bind("<Button-1>", lambda e: self._on_click())
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        if event.width != self._width or event.height != self._height:
            self._width = event.width
            self._height = event.height
            self._draw(self._hover_colors if self._hovering else self._colors)

    def _draw(self, colors):
        self.delete("all")
        w, h = self._width, self._height
        r = 10  # corner radius

        # Draw gradient with horizontal bands
        bands = 3
        band_h = h // bands
        for i, color in enumerate(colors):
            y1 = i * band_h
            y2 = (i + 1) * band_h if i < bands - 1 else h
            if i == 0:
                self.create_rectangle(r, y1, w - r, y2, fill=color, outline="")
                self.create_arc(0, y1, r * 2, y1 + r * 2, start=90, extent=90, fill=color, outline="")
                self.create_arc(w - r * 2, y1, w, y1 + r * 2, start=0, extent=90, fill=color, outline="")
                self.create_rectangle(0, y1 + r, r, y2, fill=color, outline="")
                self.create_rectangle(w - r, y1 + r, w, y2, fill=color, outline="")
            elif i == bands - 1:
                self.create_rectangle(r, y1, w - r, y2, fill=color, outline="")
                self.create_arc(0, y2 - r * 2, r * 2, y2, start=180, extent=90, fill=color, outline="")
                self.create_arc(w - r * 2, y2 - r * 2, w, y2, start=270, extent=90, fill=color, outline="")
                self.create_rectangle(0, y1, r, y2 - r, fill=color, outline="")
                self.create_rectangle(w - r, y1, w, y2 - r, fill=color, outline="")
            else:
                self.create_rectangle(0, y1, w, y2, fill=color, outline="")

        self.create_line(r, 1, w - r, 1, fill=colors[2], width=1)
        self.create_text(w // 2 + 1, h // 2 + 1, text=self._text,
                         fill="#1a1a2a", font=("Segoe UI", self._font_size, "bold"))
        self.create_text(w // 2, h // 2, text=self._text,
                         fill=self._fg, font=("Segoe UI", self._font_size, "bold"))

    def _on_hover(self, entering):
        self._hovering = entering
        if self._enabled:
            self._draw(self._hover_colors if entering else self._colors)
            self.configure(cursor="hand2" if entering else "")

    def _on_click(self):
        if self._enabled and self._command:
            self._command()

    def set_enabled(self, enabled):
        self._enabled = enabled
        if not enabled:
            disabled_colors = (Colors.BG_CARD, Colors.BG_CARD, Colors.BG_CARD)
            self._fg = Colors.TEXT_DIM
            self._draw(disabled_colors)
        else:
            if self._style in ["primary", "danger"]:
                self._fg = "#ffffff"
            else:
                self._fg = Colors.TEXT_SEC
            self._draw(self._colors)

    def set_text(self, text):
        self._text = text
        self._draw(self._hover_colors if self._hovering else self._colors)


class GlowProgressBar(tk.Canvas):
    """A smooth progress bar with a glowing leading edge."""

    def __init__(self, parent, width=400, height=6, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=parent.cget("bg") if hasattr(parent, "cget") else Colors.BG_BASE,
                         highlightthickness=0, **kwargs)
        self._width = width
        self._height = height
        self._progress = 0
        self._draw()
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        if event.width != self._width or event.height != self._height:
            self._width = event.width
            self._height = event.height
            self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self._width, self._height
        # Background track
        self.create_rectangle(0, 0, w, h, fill=Colors.BG_INPUT, outline="")
        # Filled portion
        if self._progress > 0:
            fill_w = max(h, int(w * self._progress))
            self.create_rectangle(0, 0, fill_w, h, fill=Colors.ACCENT_GLOW, outline="")
            glow_w = min(20, fill_w)
            if fill_w > 4:
                self.create_rectangle(fill_w - glow_w, 0, fill_w, h, fill=Colors.ACCENT, outline="")
                self.create_rectangle(fill_w - max(1, glow_w // 3), 0, fill_w, h, fill=Colors.ACCENT_LIGHT, outline="")
            self.create_line(0, 0, fill_w, 0, fill=Colors.ACCENT_LIGHT, width=1)

    def set_progress(self, value: float):
        self._progress = max(0, min(1, value))
        self._draw()


class StyledEntry(tk.Frame):
    """An entry field with a styled border that glows on focus."""

    def __init__(self, parent, textvariable=None, placeholder="", **kwargs):
        super().__init__(parent, bg=Colors.BORDER, padx=1, pady=1)
        self.inner = tk.Frame(self, bg=Colors.BG_INPUT)
        self.inner.pack(fill="both", expand=True)
        self.entry = tk.Entry(
            self.inner, textvariable=textvariable,
            font=("Segoe UI", 10), bg=Colors.BG_INPUT, fg=Colors.TEXT,
            insertbackground=Colors.ACCENT_LIGHT,
            highlightthickness=0, borderwidth=0, relief="flat"
        )
        self.entry.pack(fill="x", padx=10, pady=7)
        self.entry.bind("<FocusIn>", lambda e: self.configure(bg=Colors.ACCENT))
        self.entry.bind("<FocusOut>", lambda e: self.configure(bg=Colors.BORDER))


class ScrollableFrame(tk.Frame):
    """A vertical scrollable frame container."""
    def __init__(self, parent, bg, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, bg=bg)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Vertical.TScrollbar",
                         background=Colors.BG_CARD_ALT, troughcolor=Colors.BG_CARD,
                         bordercolor=Colors.BG_CARD, arrowcolor=Colors.TEXT_DIM,
                         lightcolor=Colors.BG_CARD, darkcolor=Colors.BG_CARD)
        style.map("Dark.Vertical.TScrollbar",
                  background=[("active", Colors.ACCENT_DIM), ("pressed", Colors.ACCENT)])

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, style="Dark.Vertical.TScrollbar")
        self.scrollable_inner = tk.Frame(self.canvas, bg=bg)
        
        self.scrollable_inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_inner, anchor="nw")
        
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.bind("<Enter>", self._bind_mousewheel)
        self.bind("<Leave>", self._unbind_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        bbox = self.canvas.bbox("all")
        if bbox and bbox[3] > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")


# ─── Main Application ───────────────────────────────────────────────────────

class CBZMergerApp:
    def __init__(self, root):
        self.root = root
        self.lang = "en"
        self.root.title(self.t("title_main"))
        self.root.configure(bg=Colors.BG_BASE)
        self.root.minsize(640, 580)
        self.root.geometry("700x660")

        self._set_dark_titlebar()

        # State
        self.input_folder: Path | None = None
        self.cbz_file_items = []
        self.is_running = False
        self.abort_event = threading.Event()
        self.custom_cover_path = None
        self.cover_photo = None

        self._build_ui()
        self._update_texts()

        if HAS_DND:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self._on_drop)

    def t(self, key, *args):
        val = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"]).get(key, key)
        if args:
            return val.format(*args)
        return val

    def _toggle_language(self):
        self.lang = "de" if self.lang == "en" else "en"
        self._update_texts()
        self._update_selection_counts()

    def _set_dark_titlebar(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
            )
        except Exception:
            pass

    def _build_ui(self):
        # HEADER
        header_bg = tk.Frame(self.root, bg=Colors.BG_SURFACE)
        header_bg.pack(fill="x")

        header = tk.Frame(header_bg, bg=Colors.BG_SURFACE)
        header.pack(fill="x", padx=28, pady=(18, 14))

        icon_canvas = tk.Canvas(header, width=42, height=42, bg=Colors.BG_SURFACE, highlightthickness=0)
        icon_canvas.pack(side="left")
        icon_canvas.create_oval(0, 0, 42, 42, fill=Colors.ACCENT_DARK, outline="")
        icon_canvas.create_oval(2, 2, 40, 40, fill=Colors.ACCENT_DIM, outline="")
        icon_canvas.create_text(21, 21, text="📚", font=("Segoe UI Emoji", 16))

        title_frame = tk.Frame(header, bg=Colors.BG_SURFACE)
        title_frame.pack(side="left", padx=(14, 0))

        self.lbl_title_main = tk.Label(title_frame, font=("Segoe UI", 17, "bold"), bg=Colors.BG_SURFACE, fg=Colors.TEXT)
        self.lbl_title_main.pack(anchor="w")
        self.lbl_title_desc = tk.Label(title_frame, font=("Segoe UI", 9), bg=Colors.BG_SURFACE, fg=Colors.TEXT_DIM)
        self.lbl_title_desc.pack(anchor="w")

        self.lang_btn = GradientButton(header, text=self.t("lang_btn"), command=self._toggle_language,
                                       width=60, height=32, font_size=10, style="secondary")
        self.lang_btn.pack(side="right")

        self.accent_bar = tk.Canvas(self.root, height=3, bg=Colors.BG_BASE, highlightthickness=0)
        self.accent_bar.pack(fill="x")

        def draw_accent_bar(event):
            self.accent_bar.delete("all")
            gradient_colors = [Colors.ACCENT_DARK, Colors.ACCENT_GLOW, Colors.ACCENT,
                               Colors.ACCENT_LIGHT, Colors.ACCENT, Colors.ACCENT_GLOW,
                               Colors.ACCENT_DARK]
            segment_w = max(1, event.width / len(gradient_colors))
            for i, color in enumerate(gradient_colors):
                x1 = i * segment_w
                x2 = (i + 1) * segment_w
                self.accent_bar.create_rectangle(x1, 0, x2 + 1, 3, fill=color, outline="")

        self.accent_bar.bind("<Configure>", draw_accent_bar)

        # BOTTOM FIXED AREA
        bottom = tk.Frame(self.root, bg=Colors.BG_BASE)
        bottom.pack(side="bottom", fill="x", padx=28, pady=(0, 16))

        status_row = tk.Frame(bottom, bg=Colors.BG_BASE)
        status_row.pack(fill="x", pady=(0, 8))

        self.status_dot = tk.Canvas(status_row, width=8, height=8, bg=Colors.BG_BASE, highlightthickness=0)
        self.status_dot.pack(side="left", padx=(0, 8), pady=2)
        self.status_dot.create_oval(0, 0, 8, 8, fill=Colors.TEXT_DIM, outline="")
        self._status_dot_color = Colors.TEXT_DIM

        self.status_label = tk.Label(status_row, font=("Segoe UI", 9), bg=Colors.BG_BASE, fg=Colors.TEXT_DIM, anchor="w")
        self.status_label.pack(side="left", fill="x")

        self.progress_bar = GlowProgressBar(bottom, height=4)
        self.progress_bar.pack(fill="x", pady=(0, 12))

        self.action_frame = tk.Frame(bottom, bg=Colors.BG_BASE)
        self.action_frame.pack(fill="x", pady=(0, 6))

        self.merge_btn = GradientButton(self.action_frame, text="", command=self._start_merge, width=510, height=44, font_size=12, style="primary")
        self.merge_btn.pack(side="left", fill="x", expand=True)

        self.cancel_btn = GradientButton(self.action_frame, text="", command=self._cancel_merge, width=130, height=44, font_size=12, style="danger")

        self._open_folder_frame = tk.Frame(bottom, bg=Colors.BG_BASE)
        self.open_folder_btn = GradientButton(self._open_folder_frame, text="", command=self._open_output_folder,
                                              width=644, height=36, font_size=10, style="secondary")
        self.open_folder_btn.pack(fill="x")

        self._last_output_path = None

        # MAIN CONTENT
        content = tk.Frame(self.root, bg=Colors.BG_BASE)
        content.pack(fill="both", expand=True, padx=28, pady=(16, 8))

        # ── Section 1: Source
        self.lbl_sec_source = self._make_section_label(content, "📂", "")

        source_card = tk.Frame(content, bg=Colors.BG_CARD)
        source_card.pack(fill="x", pady=(0, 14))

        source_inner = tk.Frame(source_card, bg=Colors.BG_CARD)
        source_inner.pack(fill="x", padx=14, pady=10)

        path_row = tk.Frame(source_inner, bg=Colors.BG_CARD)
        path_row.pack(fill="x", pady=(0, 8))

        self.folder_var = tk.StringVar(value="")
        path_frame = tk.Frame(path_row, bg=Colors.BG_INPUT)
        path_frame.pack(fill="x")

        self.folder_label = tk.Label(path_frame, textvariable=self.folder_var, font=("Segoe UI", 9),
                                     bg=Colors.BG_INPUT, fg=Colors.TEXT_DIM, anchor="w", padx=10, pady=6)
        self.folder_label.pack(fill="x")

        btn_row = tk.Frame(source_inner, bg=Colors.BG_CARD)
        btn_row.pack(fill="x")

        self.browse_btn = GradientButton(btn_row, text="", command=self._browse_folder, width=140, height=32, font_size=10, style="primary")
        self.browse_btn.pack(side="left")

        # ── Section 2: Files to Merge
        files_header = tk.Frame(content, bg=Colors.BG_BASE)
        files_header.pack(fill="x", pady=(0, 4))

        self.lbl_sec_files = self._make_section_label(files_header, "📋", "", pack_side="left")

        self.file_count_label = tk.Label(files_header, text="0", font=("Segoe UI", 9), bg=Colors.BG_BASE, fg=Colors.TEXT_DIM)
        self.file_count_label.pack(side="right")

        list_card = tk.Frame(content, bg=Colors.BORDER, padx=1, pady=1)

        list_inner = tk.Frame(list_card, bg=Colors.BG_CARD)
        list_inner.pack(fill="both", expand=True)

        list_frame = tk.Frame(list_inner, bg=Colors.BG_CARD)
        list_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.scroll_list = ScrollableFrame(list_frame, bg=Colors.BG_CARD)
        self.scroll_list.pack(fill="both", expand=True)

        self._empty_label = tk.Label(list_frame, font=("Segoe UI", 9), bg=Colors.BG_CARD, fg=Colors.TEXT_MUTED)
        self._empty_label.place(relx=0.5, rely=0.5, anchor="center")

        # ── Section 3: Output Settings
        out_wrapper = tk.Frame(content, bg=Colors.BG_BASE)
        out_wrapper.pack(side="bottom", fill="x", pady=(0, 0))

        self.lbl_sec_output = self._make_section_label(out_wrapper, "💾", "")

        out_card = tk.Frame(out_wrapper, bg=Colors.BG_CARD)
        out_card.pack(fill="x", pady=(0, 0))

        out_inner = tk.Frame(out_card, bg=Colors.BG_CARD)
        out_inner.pack(fill="both", expand=True, padx=14, pady=10)

        settings_frame = tk.Frame(out_inner, bg=Colors.BG_CARD)
        settings_frame.pack(side="left", fill="both", expand=True)

        cover_wrap = tk.Frame(out_inner, bg=Colors.BG_CARD)
        cover_wrap.pack(side="right", fill="y", padx=(15, 0))
        
        self.cover_canvas = tk.Canvas(cover_wrap, width=100, height=140, bg=Colors.BG_INPUT, highlightthickness=1, highlightbackground=Colors.BORDER)
        self.cover_canvas.pack(side="top")
        self.cover_canvas.create_text(50, 70, text="Drop\nCover", fill=Colors.TEXT_MUTED, justify="center")
        
        self.cover_label = tk.Label(cover_wrap, text="No Cover", font=("Segoe UI", 7), bg=Colors.BG_CARD, fg=Colors.TEXT_DIM)
        self.cover_label.pack(side="top", pady=(2, 0))

        out_row = tk.Frame(settings_frame, bg=Colors.BG_CARD)
        out_row.pack(fill="x")

        self.lbl_filename = tk.Label(out_row, font=("Segoe UI", 9), bg=Colors.BG_CARD, fg=Colors.TEXT_DIM)
        self.lbl_filename.pack(side="left", padx=(0, 10))

        self.output_var = tk.StringVar(value="merged_manga.cbz")
        self.output_entry = StyledEntry(out_row, textvariable=self.output_var)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.save_as_btn = GradientButton(out_row, text="", command=self._browse_save_location,
                                          width=110, height=30, font_size=9, style="secondary")
        self.save_as_btn.pack(side="right")

        self.save_location_var = tk.StringVar(value="")
        self.save_location_label = tk.Label(settings_frame, textvariable=self.save_location_var,
                                            font=("Segoe UI", 8), bg=Colors.BG_CARD, fg=Colors.TEXT_DIM, anchor="w")
        self.save_location_label.pack(fill="x", pady=(6, 0))
        self._custom_output_path = None

        self.compress_var = tk.BooleanVar(value=False)
        compress_row = tk.Frame(settings_frame, bg=Colors.BG_CARD)
        compress_row.pack(fill="x", pady=(6, 0))

        self.compress_cb = tk.Checkbutton(
            compress_row, variable=self.compress_var, font=("Segoe UI", 9),
            bg=Colors.BG_CARD, fg=Colors.TEXT_DIM, selectcolor=Colors.BG_INPUT,
            activebackground=Colors.BG_CARD, activeforeground=Colors.TEXT,
            highlightthickness=0, borderwidth=0, cursor="hand2"
        )
        self.compress_cb.pack(side="left")

        self.ereader_var = tk.BooleanVar(value=False)
        ereader_row = tk.Frame(settings_frame, bg=Colors.BG_CARD)
        ereader_row.pack(fill="x", pady=(6, 0))

        self.ereader_cb = tk.Checkbutton(
            ereader_row, variable=self.ereader_var, font=("Segoe UI", 9),
            bg=Colors.BG_CARD, fg=Colors.TEXT_DIM, selectcolor=Colors.BG_INPUT,
            activebackground=Colors.BG_CARD, activeforeground=Colors.TEXT,
            highlightthickness=0, borderwidth=0, cursor="hand2"
        )
        self.ereader_cb.pack(side="left")

        # Split into Volumes
        self.split_var = tk.BooleanVar(value=False)
        self.split_count_var = tk.StringVar(value="15")
        split_row = tk.Frame(settings_frame, bg=Colors.BG_CARD)
        split_row.pack(fill="x", pady=(6, 0))
        
        self.split_cb = tk.Checkbutton(
            split_row, variable=self.split_var, font=("Segoe UI", 9),
            bg=Colors.BG_CARD, fg=Colors.TEXT_DIM, selectcolor=Colors.BG_INPUT,
            activebackground=Colors.BG_CARD, activeforeground=Colors.TEXT,
            highlightthickness=0, borderwidth=0, cursor="hand2",
            command=self._toggle_split_entry
        )
        self.split_cb.pack(side="left")
        
        self.split_lbl = tk.Label(split_row, font=("Segoe UI", 8), bg=Colors.BG_CARD, fg=Colors.TEXT_MUTED)
        self.split_lbl.pack(side="left", padx=(15, 5))
        
        self.split_entry = tk.Entry(
            split_row, textvariable=self.split_count_var, width=5, font=("Segoe UI", 9),
            bg=Colors.BG_INPUT, fg=Colors.TEXT_DIM, insertbackground=Colors.ACCENT_LIGHT,
            highlightthickness=0, borderwidth=0, state="disabled"
        )
        self.split_entry.pack(side="left")

        list_card.pack(side="top", fill="both", expand=True, pady=(0, 14))

    def _toggle_split_entry(self):
        if self.split_var.get():
            self.split_entry.configure(state="normal", fg=Colors.TEXT)
            self.split_lbl.configure(fg=Colors.TEXT_DIM)
        else:
            self.split_entry.configure(state="disabled", fg=Colors.TEXT_DIM)
            self.split_lbl.configure(fg=Colors.TEXT_MUTED)

    def _make_section_label(self, parent, icon, text, pack_side=None):
        frame = tk.Frame(parent, bg=Colors.BG_BASE if parent.cget("bg") == Colors.BG_BASE else parent.cget("bg"))
        if pack_side:
            frame.pack(side=pack_side, pady=(0, 4))
        else:
            frame.pack(anchor="w", pady=(0, 4))

        tk.Label(frame, text=f"{icon}", font=("Segoe UI Emoji", 9),
                 bg=frame.cget("bg"), fg=Colors.ACCENT_LIGHT).pack(side="left", padx=(0, 6))
        lbl = tk.Label(frame, text=text, font=("Segoe UI", 8, "bold"), bg=frame.cget("bg"), fg=Colors.TEXT_DIM)
        lbl.pack(side="left")
        return lbl

    def _update_texts(self):
        self.lbl_title_main.configure(text=self.t("title_main"))
        self.lbl_title_desc.configure(text=self.t("title_desc"))
        self.root.title(self.t("title_main"))
        
        if not self.cbz_file_items:
            self.status_label.configure(text=self.t("ready_start"))
            self.folder_var.set(self.t("no_files"))
            self._empty_label.configure(text=self.t("empty_list"))

        self.merge_btn.set_text(self.t("start_merge"))
        self.cancel_btn.set_text(self.t("cancel_merge"))
        self.open_folder_btn.set_text(self.t("open_folder"))
        self.browse_btn.set_text(self.t("select_folder"))
        self.save_as_btn.set_text(self.t("save_as"))
        
        self.lbl_sec_source.configure(text=self.t("source").upper())
        self.lbl_sec_files.configure(text=self.t("files_to_merge").upper())
        self.lbl_sec_output.configure(text=self.t("output").upper())
        
        self.lbl_filename.configure(text=self.t("filename"))
        self.compress_cb.configure(text=self.t("deflate"))
        self.ereader_cb.configure(text=self.t("ereader"))
        self.split_cb.configure(text=self.t("split_vols"))
        self.split_lbl.configure(text=self.t("ch_per_vol"))
        self.lang_btn.set_text(self.t("lang_btn"))
        
        if not self._custom_output_path and self.input_folder:
            self.save_location_var.set(self.t("save_to", self.input_folder))

    # ── Actions ──────────────────────────────────────────────────────────

    def _extract_first_image(self, cbz_path: Path):
        import zipfile
        from PIL import Image
        from io import BytesIO
        try:
            with zipfile.ZipFile(cbz_path, 'r') as zf:
                entries = [n for n in zf.namelist() if Path(n).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} and not n.startswith("__MACOSX")]
                entries.sort(key=lambda n: _natural_sort_key(Path(n)))
                if entries:
                    data = zf.read(entries[0])
                    return Image.open(BytesIO(data))
        except Exception:
            pass
        return None

    def _update_cover_preview(self, custom_path=None):
        try:
            from PIL import Image, ImageTk
        except ImportError:
            return

        img = None
        if custom_path:
            self.custom_cover_path = Path(custom_path)
            if self.custom_cover_path.exists():
                try: img = Image.open(self.custom_cover_path)
                except Exception: pass
        elif self.custom_cover_path and self.custom_cover_path.exists():
            try: img = Image.open(self.custom_cover_path)
            except Exception: pass
            
        if img is None and not self.custom_cover_path:
            first_sel = next((i["path"] for i in self.cbz_file_items if i["var"].get()), None)
            if first_sel:
                img = self._extract_first_image(first_sel)

        self.cover_canvas.delete("all")
        if img:
            img.thumbnail((100, 140), Image.Resampling.LANCZOS)
            self.cover_photo = ImageTk.PhotoImage(img) # Keep ref
            self.cover_canvas.create_image(50, 70, image=self.cover_photo, anchor="center")
            self.cover_label.configure(text=self.t("custom_cover") if self.custom_cover_path else self.t("auto_cover"), fg=Colors.ACCENT_LIGHT if self.custom_cover_path else Colors.TEXT_DIM)
        else:
            self.cover_canvas.create_text(50, 70, text="Drop\nCover", fill=Colors.TEXT_MUTED, justify="center")
            self.cover_label.configure(text=self.t("no_cover"), fg=Colors.TEXT_DIM)

    def _on_drop(self, event):
        if self.is_running: return
        
        dropped = self.root.tk.splitlist(event.data)
        if not dropped: return
        
        first_path = Path(dropped[0])
        
        # Cover detection
        if first_path.is_file() and first_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            self._update_cover_preview(custom_path=first_path)
            return

        if len(dropped) == 1 and first_path.is_dir():
            self.input_folder = first_path
            self.folder_var.set(str(self.input_folder))
            self.folder_label.configure(fg=Colors.TEXT)
            if not self._custom_output_path:
                self.save_location_var.set(self.t("save_to", self.input_folder))
            try:
                discovered = discover_cbz_files(self.input_folder)
            except FileNotFoundError:
                discovered = []
            self._populate_file_list(discovered)
        else:
            cbz_files = [Path(p) for p in dropped if Path(p).is_file() and Path(p).name.lower().endswith(".cbz")]
            if cbz_files:
                self.input_folder = cbz_files[0].parent
                self.folder_var.set(self.t("custom_drop", len(cbz_files)))
                self.folder_label.configure(fg=Colors.TEXT)
                if not self._custom_output_path:
                    self.save_location_var.set(self.t("save_to", self.input_folder))
                self._populate_file_list(cbz_files)

    def _browse_save_location(self):
        path = filedialog.asksaveasfilename(
            title=self.t("save_as"),
            defaultextension=".cbz",
            filetypes=[("CBZ Files", "*.cbz"), ("All Files", "*.*")],
            initialfile=self.output_var.get()
        )
        if not path: return
        self._custom_output_path = Path(path)
        self.output_var.set(self._custom_output_path.name)
        self.save_location_var.set(self.t("save_to", self._custom_output_path.parent))

    def _open_output_folder(self):
        if self._last_output_path and self._last_output_path.exists():
            os.startfile(self._last_output_path.parent)

    def _set_status_dot(self, color):
        self._status_dot_color = color
        self.status_dot.delete("all")
        self.status_dot.create_oval(0, 0, 8, 8, fill=color, outline="")

    def _browse_folder(self):
        folder = filedialog.askdirectory(title=self.t("select_folder"))
        if not folder: return

        self.input_folder = Path(folder)
        self.folder_var.set(str(self.input_folder))
        self.folder_label.configure(fg=Colors.TEXT)

        try:
            discovered = discover_cbz_files(self.input_folder)
        except FileNotFoundError:
            discovered = []

        if not self._custom_output_path:
            self.save_location_var.set(self.t("save_to", self.input_folder))

        self._populate_file_list(discovered)

    def _cancel_merge(self):
        if self.is_running:
            self.abort_event.set()
            self._update_status(self.t("aborting"), Colors.WARNING)
            self.cancel_btn.set_enabled(False)

    def _populate_file_list(self, files: list[Path]):
        for widget in self.scroll_list.scrollable_inner.winfo_children():
            widget.destroy()

        self.cbz_file_items = []
        if not files:
            self._empty_label.place(relx=0.5, rely=0.5, anchor="center")
            self._empty_label.configure(text=self.t("no_cbz"))
            self._update_selection_counts()
            return
            
        self._empty_label.place_forget()

        for f in files:
            self._create_file_item(f)

        self._render_file_list()

    def _create_file_item(self, f: Path):
        var = tk.BooleanVar(value=True)
        frame = tk.Frame(self.scroll_list.scrollable_inner, bg=Colors.BG_CARD)
        
        cb = tk.Checkbutton(
            frame, variable=var, bg=Colors.BG_CARD, activebackground=Colors.BG_CARD,
            selectcolor=Colors.BG_INPUT, command=self._update_selection_counts,
            cursor="hand2", highlightthickness=0, borderwidth=0
        )
        cb.pack(side="left", padx=(5, 5))
        
        size_str = _format_size(f.stat().st_size)
        lbl = tk.Label(frame, text=f"{f.name} ({size_str})", fg=Colors.TEXT_SEC, bg=Colors.BG_CARD, font=("Cascadia Code", 9), anchor="w")
        lbl.pack(side="left", fill="x", expand=True)

        btn_down = tk.Button(
            frame, text="⬇️", bg=Colors.BG_CARD, fg=Colors.TEXT,
            activebackground=Colors.BG_HOVER, relief="flat", cursor="hand2",
            command=lambda p=f: self._move_item(p, 1), font=("Segoe UI Emoji", 8),
            borderwidth=0, highlightthickness=0, padx=4, pady=2
        )
        btn_down.pack(side="right", padx=(2, 5))

        btn_up = tk.Button(
            frame, text="⬆️", bg=Colors.BG_CARD, fg=Colors.TEXT,
            activebackground=Colors.BG_HOVER, relief="flat", cursor="hand2",
            command=lambda p=f: self._move_item(p, -1), font=("Segoe UI Emoji", 8),
            borderwidth=0, highlightthickness=0, padx=4, pady=2
        )
        btn_up.pack(side="right", padx=(0, 2))
        
        self.cbz_file_items.append({
            "path": f, "var": var, "frame": frame, "lbl": lbl, "cb": cb, "up": btn_up, "dn": btn_down
        })

    def _move_item(self, path: Path, direction: int):
        idx = next((i for i, item in enumerate(self.cbz_file_items) if item["path"] == path), -1)
        if idx == -1: return
        new_idx = idx + direction
        if 0 <= new_idx < len(self.cbz_file_items):
            self.cbz_file_items[idx], self.cbz_file_items[new_idx] = self.cbz_file_items[new_idx], self.cbz_file_items[idx]
            self._render_file_list()

    def _render_file_list(self):
        for item in self.cbz_file_items:
            item["frame"].pack_forget()
            
        for i, item in enumerate(self.cbz_file_items):
            bg = Colors.BG_CARD if i % 2 == 0 else Colors.BG_CARD_ALT
            item["frame"].configure(bg=bg)
            item["lbl"].configure(bg=bg)
            item["cb"].configure(bg=bg, activebackground=bg)
            item["up"].configure(bg=bg, state="normal" if i > 0 else "disabled")
            item["dn"].configure(bg=bg, state="normal" if i < len(self.cbz_file_items)-1 else "disabled")
            item["frame"].pack(fill="x", pady=0)
            
        self._update_selection_counts()

    def _update_selection_counts(self):
        total = len(self.cbz_file_items)
        selected = sum(1 for item in self.cbz_file_items if item["var"].get())
        
        self.file_count_label.configure(
            text=self.t("status_files", selected, total),
            fg=Colors.SUCCESS if selected > 0 else Colors.WARNING
        )
        
        if selected > 0:
            self._set_status_dot(Colors.SUCCESS)
            self.status_label.configure(text=self.t("ready_merge", selected), fg=Colors.TEXT_SEC)
        else:
            self._set_status_dot(Colors.WARNING)
            self.status_label.configure(text=self.t("warn_no_selection") if total > 0 else self.t("empty_list"), fg=Colors.WARNING)
        self.progress_bar.set_progress(0)
        self._update_cover_preview()

    def _start_merge(self):
        if self.is_running: return

        selected_files = [item["path"] for item in self.cbz_file_items if item["var"].get()]
        if not selected_files:
            messagebox.showwarning(self.t("alert_title"), self.t("warn_no_selection") if self.cbz_file_items else self.t("warn_no_files"))
            return

        output_name = self.output_var.get().strip()
        if not output_name:
            messagebox.showwarning(self.t("alert_title"), self.t("warn_no_output"))
            return

        if not output_name.lower().endswith(".cbz"):
            output_name += ".cbz"
            self.output_var.set(output_name)

        self.is_running = True
        self.abort_event.clear()
        
        self.cancel_btn.pack(side="left", padx=(10, 0))
        self.cancel_btn.set_enabled(True)
        self.merge_btn.set_enabled(False)
        self.browse_btn.set_enabled(False)
        self.progress_bar.set_progress(0)
        self._set_status_dot(Colors.ACCENT_LIGHT)
        self.status_label.configure(text=self.t("starting"), fg=Colors.ACCENT_LIGHT)

        split_enabled = self.split_var.get()
        count_str = self.split_count_var.get().strip()
        split_count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 15

        thread = threading.Thread(
            target=self._run_merge,
            args=(self.input_folder, output_name, self.compress_var.get(), self.ereader_var.get(), selected_files, split_enabled, split_count),
            daemon=True
        )
        thread.start()

    def _run_merge(self, input_folder: Path, output_name: str, compress: bool, optimize_for_ereader: bool, selected_files: list[Path], split: bool, split_count: int):
        from cbz_merger import extract_cbz

        compression = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
        start_time = time.time()
        temp_dir = None

        chunks = []
        if split and split_count > 0:
            chunks = [selected_files[i:i + split_count] for i in range(0, len(selected_files), split_count)]
        else:
            chunks = [selected_files]

        total_chapters = len(selected_files)
        chapters_processed = 0
        volumes_created = len(chunks)
        total_extracted_images = 0

        try:
            temp_dir = Path(tempfile.mkdtemp(prefix="cbz_merger_"))
            self._update_status(self.t("extracting"), Colors.ACCENT_LIGHT)

            def extract_task(idx, cbz_file):
                return extract_cbz(cbz_file, temp_dir, chapter_index=idx, optimize_for_ereader=optimize_for_ereader)

            for vol_index, chunk in enumerate(chunks):
                if self.abort_event.is_set(): break
                
                if volumes_created > 1:
                    vol_suffix = f"_Vol_{vol_index + 1}.cbz"
                    v_name = output_name[:-4] + vol_suffix if output_name.lower().endswith(".cbz") else output_name + vol_suffix
                    v_path = input_folder / v_name if not self._custom_output_path else self._custom_output_path.parent / v_name
                else:
                    v_name = output_name
                    v_path = input_folder / v_name if not self._custom_output_path else self._custom_output_path
                    
                self._last_output_path = v_path
                all_images = []

                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future_to_file = {
                        executor.submit(extract_task, i, f): f 
                        for i, f in enumerate(chunk)
                    }
                    
                    for future in concurrent.futures.as_completed(future_to_file):
                        if self.abort_event.is_set():
                            for f_pending in future_to_file: f_pending.cancel()
                            break

                        chapters_processed += 1
                        cbz_file = future_to_file[future]
                        
                        self._update_status(self.t("extr_prog", chapters_processed, total_chapters, cbz_file.name), Colors.ACCENT_LIGHT)
                        self._update_progress((chapters_processed) / (total_chapters * 2))
                        
                        try:
                            images = future.result()
                            all_images.extend(images)
                        except Exception as e:
                            print(f"Error extracting {cbz_file.name}: {e}")

                if self.abort_event.is_set(): break
                if not all_images and not self.custom_cover_path: continue

                total_extracted_images += len(all_images)
                all_images.sort(key=lambda p: p.name)
                
                # Check for custom cover
                if self.custom_cover_path and self.custom_cover_path.exists():
                    cover_target = temp_dir / f"00000_cover{self.custom_cover_path.suffix}"
                    try:
                        shutil.copy(self.custom_cover_path, cover_target)
                        all_images.insert(0, cover_target)
                    except Exception as e:
                        print(f"Error copying custom cover: {e}")

                total_images = len(all_images)

                import xml.etree.ElementTree as ET
                comic_info_path = temp_dir / "ComicInfo.xml"
                try:
                    root = ET.Element("ComicInfo", {
                        "xmlns:xsd": "http://www.w3.org/2001/XMLSchema", 
                        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"
                    })
                    title_text = output_name.replace(".cbz", "")
                    if volumes_created > 1: title_text += f" Volume {vol_index + 1}"
                    ET.SubElement(root, "Title").text = title_text
                    ET.SubElement(root, "Summary").text = f"Merged {len(chunk)} files using CBZ Merger."
                    ET.SubElement(root, "PageCount").text = str(total_images)
                    
                    tree = ET.ElementTree(root)
                    tree.write(comic_info_path, encoding="utf-8", xml_declaration=True)
                except Exception:
                    pass

                self._update_status(self.t("pack_vol_prog" if volumes_created > 1 else "packing", 
                                          vol_index+1 if volumes_created > 1 else total_images,
                                          volumes_created if volumes_created > 1 else ""), Colors.ACCENT_LIGHT)

                with zipfile.ZipFile(v_path, "w", compression=compression) as zf_out:
                    if comic_info_path.exists():
                        zf_out.write(comic_info_path, arcname="ComicInfo.xml")

                    for i, img_path in enumerate(all_images):
                        if self.abort_event.is_set(): break
                        zf_out.write(img_path, arcname=img_path.name)

                        if (i + 1) % 50 == 0 or (i + 1) == total_images:
                            base_prog = 0.5
                            vol_prog = (vol_index / volumes_created) * 0.5
                            img_prog = ((i + 1) / total_images) * (0.5 / volumes_created)
                            progress = base_prog + vol_prog + img_prog
                            self._update_progress(progress)

                # Clean up images in temp_dir before next chunk to save RAM / Disk Space
                for img in all_images:
                    if img.exists():
                        try: img.unlink()
                        except: pass
                if comic_info_path.exists():
                    try: comic_info_path.unlink()
                    except: pass
                    
                if self.abort_event.is_set():
                    if v_path.exists():
                        try: v_path.unlink()
                        except: pass
                    break

            # End chunk loop
            if self.abort_event.is_set():
                self._update_status(self.t("aborted"), Colors.WARNING)
                self._update_dot(Colors.WARNING)
                return
                
            if total_extracted_images == 0:
                self._update_status(self.t("err_no_img"), Colors.ERROR)
                self._update_dot(Colors.ERROR)
                return

            elapsed = time.time() - start_time
            self._update_progress(1.0)
            
            if volumes_created > 1:
                self._update_status(self.t("done_split", total_extracted_images, volumes_created, elapsed), Colors.SUCCESS)
                self.root.after(0, lambda: self.save_location_var.set(self.t("saved_to", v_path.parent)))
            else:
                size = _format_size(v_path.stat().st_size)
                self._update_status(self.t("done", total_extracted_images, output_name, size, elapsed), Colors.SUCCESS)
                self.root.after(0, lambda: self.save_location_var.set(self.t("saved_to", v_path)))

            self._update_dot(Colors.SUCCESS)
            self.root.after(0, lambda: self.save_location_label.configure(fg=Colors.SUCCESS))
            self.root.after(0, lambda: self._open_folder_frame.pack(fill="x", pady=(6, 0)))

        except PermissionError:
            self._update_status(self.t("perm_err", output_path), Colors.ERROR)
            self._update_dot(Colors.ERROR)
        except Exception as e:
            self._update_status(self.t("err", e), Colors.ERROR)
            self._update_dot(Colors.ERROR)

        finally:
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass

            self.is_running = False
            self.root.after(0, lambda: self.cancel_btn.pack_forget())
            self.root.after(0, lambda: self.merge_btn.set_enabled(True))
            self.root.after(0, lambda: self.browse_btn.set_enabled(True))

    def _update_status(self, text: str, color: str = Colors.TEXT_DIM):
        self.root.after(0, lambda: self.status_label.configure(text=text, fg=color))

    def _update_progress(self, value: float):
        self.root.after(0, lambda: self.progress_bar.set_progress(value))

    def _update_dot(self, color: str):
        self.root.after(0, lambda: self._set_status_dot(color))

def main():
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    try:
        root.iconbitmap(default="")
    except Exception:
        pass
    app = CBZMergerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
