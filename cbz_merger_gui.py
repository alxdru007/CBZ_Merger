#!/usr/bin/env python3
"""
CBZ Merger GUI — A modern, premium dark-themed graphical interface for merging .cbz files.

Usage:
    python cbz_merger_gui.py

Requires: tkinter (included with Python on Windows)
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# Import the core merger logic
from cbz_merger import merge_cbz_files, discover_cbz_files, _format_size, _natural_sort_key


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
                # Top rounded
                self.create_rectangle(r, y1, w - r, y2, fill=color, outline="")
                self.create_arc(0, y1, r * 2, y1 + r * 2, start=90, extent=90, fill=color, outline="")
                self.create_arc(w - r * 2, y1, w, y1 + r * 2, start=0, extent=90, fill=color, outline="")
                self.create_rectangle(0, y1 + r, r, y2, fill=color, outline="")
                self.create_rectangle(w - r, y1 + r, w, y2, fill=color, outline="")
            elif i == bands - 1:
                # Bottom rounded
                self.create_rectangle(r, y1, w - r, y2, fill=color, outline="")
                self.create_arc(0, y2 - r * 2, r * 2, y2, start=180, extent=90, fill=color, outline="")
                self.create_arc(w - r * 2, y2 - r * 2, w, y2, start=270, extent=90, fill=color, outline="")
                self.create_rectangle(0, y1, r, y2 - r, fill=color, outline="")
                self.create_rectangle(w - r, y1, w, y2 - r, fill=color, outline="")
            else:
                self.create_rectangle(0, y1, w, y2, fill=color, outline="")

        # Subtle top highlight
        self.create_line(r, 1, w - r, 1, fill=colors[2], width=1)

        # Text with shadow
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
            if self._style == "primary":
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
        r = h // 2

        # Background track
        self.create_rectangle(0, 0, w, h, fill=Colors.BG_INPUT, outline="")

        # Filled portion
        if self._progress > 0:
            fill_w = max(h, int(w * self._progress))

            # Main fill
            self.create_rectangle(0, 0, fill_w, h, fill=Colors.ACCENT_GLOW, outline="")

            # Brighter leading edge (glow effect)
            glow_w = min(20, fill_w)
            if fill_w > 4:
                self.create_rectangle(fill_w - glow_w, 0, fill_w, h,
                                      fill=Colors.ACCENT, outline="")
                self.create_rectangle(fill_w - max(1, glow_w // 3), 0, fill_w, h,
                                      fill=Colors.ACCENT_LIGHT, outline="")

            # Top highlight line
            self.create_line(0, 0, fill_w, 0, fill=Colors.ACCENT_LIGHT, width=1)

    def set_progress(self, value: float):
        """Set progress from 0.0 to 1.0"""
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

        # Focus glow
        self.entry.bind("<FocusIn>", lambda e: self.configure(bg=Colors.ACCENT))
        self.entry.bind("<FocusOut>", lambda e: self.configure(bg=Colors.BORDER))


# ─── Main Application ───────────────────────────────────────────────────────

class CBZMergerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CBZ Merger")
        self.root.configure(bg=Colors.BG_BASE)
        self.root.minsize(640, 580)
        self.root.geometry("700x660")

        # Set dark title bar on Windows
        self._set_dark_titlebar()

        # State
        self.input_folder: Path | None = None
        self.cbz_files: list[Path] = []
        self.is_running = False

        # Build UI
        self._build_ui()

    def _set_dark_titlebar(self):
        """Try to set dark title bar on Windows 10/11."""
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
        # ══════════════════════════════════════════════════════════════════
        # HEADER
        # ══════════════════════════════════════════════════════════════════
        header_bg = tk.Frame(self.root, bg=Colors.BG_SURFACE)
        header_bg.pack(fill="x")

        header = tk.Frame(header_bg, bg=Colors.BG_SURFACE)
        header.pack(fill="x", padx=28, pady=(18, 14))

        # Icon circle
        icon_canvas = tk.Canvas(header, width=42, height=42,
                                bg=Colors.BG_SURFACE, highlightthickness=0)
        icon_canvas.pack(side="left")
        # Draw accent circle background
        icon_canvas.create_oval(0, 0, 42, 42, fill=Colors.ACCENT_DARK, outline="")
        icon_canvas.create_oval(2, 2, 40, 40, fill=Colors.ACCENT_DIM, outline="")
        icon_canvas.create_text(21, 21, text="📚", font=("Segoe UI Emoji", 16))

        title_frame = tk.Frame(header, bg=Colors.BG_SURFACE)
        title_frame.pack(side="left", padx=(14, 0))

        tk.Label(title_frame, text="CBZ Merger",
                 font=("Segoe UI", 17, "bold"),
                 bg=Colors.BG_SURFACE, fg=Colors.TEXT).pack(anchor="w")
        tk.Label(title_frame, text="Combine multiple CBZ files into one",
                 font=("Segoe UI", 9),
                 bg=Colors.BG_SURFACE, fg=Colors.TEXT_DIM).pack(anchor="w")

        # Accent gradient bar under header
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

        # ══════════════════════════════════════════════════════════════════
        # BOTTOM FIXED AREA — packed first to reserve space
        # ══════════════════════════════════════════════════════════════════
        bottom = tk.Frame(self.root, bg=Colors.BG_BASE)
        bottom.pack(side="bottom", fill="x", padx=28, pady=(0, 16))

        # Status row
        status_row = tk.Frame(bottom, bg=Colors.BG_BASE)
        status_row.pack(fill="x", pady=(0, 8))

        self.status_dot = tk.Canvas(status_row, width=8, height=8,
                                    bg=Colors.BG_BASE, highlightthickness=0)
        self.status_dot.pack(side="left", padx=(0, 8), pady=2)
        self.status_dot.create_oval(0, 0, 8, 8, fill=Colors.TEXT_DIM, outline="")
        self._status_dot_color = Colors.TEXT_DIM

        self.status_label = tk.Label(
            status_row, text="Ready — select a folder to begin",
            font=("Segoe UI", 9),
            bg=Colors.BG_BASE, fg=Colors.TEXT_DIM, anchor="w"
        )
        self.status_label.pack(side="left", fill="x")

        # Progress bar
        self.progress_bar = GlowProgressBar(bottom, height=4)
        self.progress_bar.pack(fill="x", pady=(0, 12))

        # Merge button
        self.merge_btn = GradientButton(
            bottom, text="🔗  Start Merge", command=self._start_merge,
            width=644, height=44, font_size=12, style="primary"
        )
        self.merge_btn.pack(fill="x", pady=(0, 6))

        # Open folder button (hidden initially)
        self._open_folder_frame = tk.Frame(bottom, bg=Colors.BG_BASE)
        # Not packed yet — shown after merge

        self.open_folder_btn = GradientButton(
            self._open_folder_frame, text="📂  Open Output Folder",
            command=self._open_output_folder,
            width=644, height=36, font_size=10, style="secondary"
        )
        self.open_folder_btn.pack(fill="x")

        self._last_output_path = None

        # ══════════════════════════════════════════════════════════════════
        # MAIN CONTENT — fills remaining space
        # ══════════════════════════════════════════════════════════════════
        content = tk.Frame(self.root, bg=Colors.BG_BASE)
        content.pack(fill="both", expand=True, padx=28, pady=(16, 8))

        # ── Section 1: Source ─────────────────────────────────────────────
        self._make_section_label(content, "📂", "Source")

        source_card = tk.Frame(content, bg=Colors.BG_CARD)
        source_card.pack(fill="x", pady=(0, 14))

        source_inner = tk.Frame(source_card, bg=Colors.BG_CARD)
        source_inner.pack(fill="x", padx=14, pady=10)

        # Path display row
        path_row = tk.Frame(source_inner, bg=Colors.BG_CARD)
        path_row.pack(fill="x", pady=(0, 8))

        self.folder_var = tk.StringVar(value="No files or folder selected")
        path_frame = tk.Frame(path_row, bg=Colors.BG_INPUT)
        path_frame.pack(fill="x")

        self.folder_label = tk.Label(
            path_frame, textvariable=self.folder_var,
            font=("Segoe UI", 9), bg=Colors.BG_INPUT, fg=Colors.TEXT_DIM,
            anchor="w", padx=10, pady=6
        )
        self.folder_label.pack(fill="x")

        # Buttons row
        btn_row = tk.Frame(source_inner, bg=Colors.BG_CARD)
        btn_row.pack(fill="x")

        self.browse_btn = GradientButton(
            btn_row, text="📁 Select Folder", command=self._browse_folder,
            width=140, height=32, font_size=10, style="primary"
        )
        self.browse_btn.pack(side="left")

        # ── Section 2: Files to Merge ────────────────────────────────────
        files_header = tk.Frame(content, bg=Colors.BG_BASE)
        files_header.pack(fill="x", pady=(0, 4))

        self._make_section_label(files_header, "📋", "Files to Merge", pack_side="left")

        self.file_count_label = tk.Label(
            files_header, text="0 files",
            font=("Segoe UI", 9),
            bg=Colors.BG_BASE, fg=Colors.TEXT_DIM
        )
        self.file_count_label.pack(side="right")

        list_card = tk.Frame(content, bg=Colors.BORDER, padx=1, pady=1)
        # Packed later to prevent it from pushing bottom widgets off-screen!

        list_inner = tk.Frame(list_card, bg=Colors.BG_CARD)
        list_inner.pack(fill="both", expand=True)

        # Listbox with styled scrollbar
        list_frame = tk.Frame(list_inner, bg=Colors.BG_CARD)
        list_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.file_listbox = tk.Listbox(
            list_frame,
            bg=Colors.BG_CARD, fg=Colors.TEXT_SEC,
            font=("Cascadia Code", 9),
            selectbackground=Colors.ACCENT_DIM,
            selectforeground=Colors.TEXT,
            highlightthickness=0,
            borderwidth=0,
            activestyle="none",
            relief="flat"
        )

        # Custom scrollbar via ttk styling
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Vertical.TScrollbar",
                         background=Colors.BG_CARD_ALT,
                         troughcolor=Colors.BG_CARD,
                         bordercolor=Colors.BG_CARD,
                         arrowcolor=Colors.TEXT_DIM,
                         lightcolor=Colors.BG_CARD,
                         darkcolor=Colors.BG_CARD)
        style.map("Dark.Vertical.TScrollbar",
                  background=[("active", Colors.ACCENT_DIM),
                              ("pressed", Colors.ACCENT)])

        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical",
            command=self.file_listbox.yview,
            style="Dark.Vertical.TScrollbar"
        )
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.file_listbox.pack(side="left", fill="both", expand=True)

        # Empty state message
        self._empty_label = tk.Label(
            list_frame,
            text="Select a folder to discover .cbz files",
            font=("Segoe UI", 9),
            bg=Colors.BG_CARD, fg=Colors.TEXT_MUTED
        )
        self._empty_label.place(relx=0.5, rely=0.5, anchor="center")

        # ── Section 3: Output Settings ───────────────────────────────────
        out_wrapper = tk.Frame(content, bg=Colors.BG_BASE)
        out_wrapper.pack(side="bottom", fill="x", pady=(0, 0))

        self._make_section_label(out_wrapper, "💾", "Output")

        out_card = tk.Frame(out_wrapper, bg=Colors.BG_CARD)
        out_card.pack(fill="x", pady=(0, 0))

        out_inner = tk.Frame(out_card, bg=Colors.BG_CARD)
        out_inner.pack(fill="x", padx=14, pady=10)

        # Filename row
        out_row = tk.Frame(out_inner, bg=Colors.BG_CARD)
        out_row.pack(fill="x")

        tk.Label(out_row, text="Filename",
                 font=("Segoe UI", 9), bg=Colors.BG_CARD,
                 fg=Colors.TEXT_DIM).pack(side="left", padx=(0, 10))

        self.output_var = tk.StringVar(value="merged_manga.cbz")
        self.output_entry = StyledEntry(out_row, textvariable=self.output_var)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        save_as_btn = GradientButton(
            out_row, text="Save As", command=self._browse_save_location,
            width=80, height=30, font_size=9, style="secondary"
        )
        save_as_btn.pack(side="right")

        # Save location display
        self.save_location_var = tk.StringVar(value="")
        self.save_location_label = tk.Label(
            out_inner, textvariable=self.save_location_var,
            font=("Segoe UI", 8), bg=Colors.BG_CARD, fg=Colors.TEXT_DIM,
            anchor="w"
        )
        self.save_location_label.pack(fill="x", pady=(6, 0))
        self._custom_output_path = None  # When user picks a specific save location

        # Compression checkbox
        self.compress_var = tk.BooleanVar(value=False)

        compress_row = tk.Frame(out_inner, bg=Colors.BG_CARD)
        compress_row.pack(fill="x", pady=(6, 0))

        self.compress_cb = tk.Checkbutton(
            compress_row,
            text="  DEFLATE compression (smaller file, slower)",
            variable=self.compress_var,
            font=("Segoe UI", 9),
            bg=Colors.BG_CARD, fg=Colors.TEXT_DIM,
            selectcolor=Colors.BG_INPUT,
            activebackground=Colors.BG_CARD,
            activeforeground=Colors.TEXT,
            highlightthickness=0, borderwidth=0,
            cursor="hand2"
        )
        self.compress_cb.pack(side="left")

        # E-Reader Optimization checkbox
        self.ereader_var = tk.BooleanVar(value=False)

        ereader_row = tk.Frame(out_inner, bg=Colors.BG_CARD)
        ereader_row.pack(fill="x", pady=(6, 0))

        self.ereader_cb = tk.Checkbutton(
            ereader_row,
            text="  E-Reader Optimization (B&W, scale to 1600px, shrink size)",
            variable=self.ereader_var,
            font=("Segoe UI", 9),
            bg=Colors.BG_CARD, fg=Colors.TEXT_DIM,
            selectcolor=Colors.BG_INPUT,
            activebackground=Colors.BG_CARD,
            activeforeground=Colors.TEXT,
            highlightthickness=0, borderwidth=0,
            cursor="hand2"
        )
        self.ereader_cb.pack(side="left")

        # Now pack the expanding list card so it doesn't push the output section away
        list_card.pack(side="top", fill="both", expand=True, pady=(0, 14))

    def _make_section_label(self, parent, icon, text, pack_side=None):
        """Create a styled section header label."""
        frame = tk.Frame(parent, bg=Colors.BG_BASE if parent.cget("bg") == Colors.BG_BASE else parent.cget("bg"))
        if pack_side:
            frame.pack(side=pack_side, pady=(0, 4))
        else:
            frame.pack(anchor="w", pady=(0, 4))

        tk.Label(frame, text=f"{icon}",
                 font=("Segoe UI Emoji", 9),
                 bg=frame.cget("bg"), fg=Colors.ACCENT_LIGHT).pack(side="left", padx=(0, 6))
        tk.Label(frame, text=text.upper(),
                 font=("Segoe UI", 8, "bold"),
                 bg=frame.cget("bg"), fg=Colors.TEXT_DIM).pack(side="left")

    # ── Actions ──────────────────────────────────────────────────────────

    def _browse_save_location(self):
        """Let user choose where to save the merged file."""
        path = filedialog.asksaveasfilename(
            title="Save merged CBZ as",
            defaultextension=".cbz",
            filetypes=[("CBZ Files", "*.cbz"), ("All Files", "*.*")],
            initialfile=self.output_var.get()
        )
        if not path:
            return
        self._custom_output_path = Path(path)
        self.output_var.set(self._custom_output_path.name)
        self.save_location_var.set(f"📁 Save to: {self._custom_output_path.parent}")

    def _open_output_folder(self):
        """Open the folder containing the merged file in Explorer."""
        if self._last_output_path and self._last_output_path.exists():
            # Select the file in Explorer
            os.startfile(self._last_output_path.parent)

    def _set_status_dot(self, color):
        self._status_dot_color = color
        self.status_dot.delete("all")
        self.status_dot.create_oval(0, 0, 8, 8, fill=color, outline="")



    def _browse_folder(self):
        """Let the user select a folder; auto-discover .cbz files inside."""
        folder = filedialog.askdirectory(title="Select folder containing .cbz files")
        if not folder:
            return

        self.input_folder = Path(folder)
        self.folder_var.set(str(self.input_folder))
        self.folder_label.configure(fg=Colors.TEXT)

        # Discover files
        try:
            self.cbz_files = discover_cbz_files(self.input_folder)
        except FileNotFoundError:
            self.cbz_files = []

        # Show default save location
        if not self._custom_output_path:
            self.save_location_var.set(f"📁 Will save to: {self.input_folder}")

        self._populate_file_list()

    def _populate_file_list(self):
        """Fill the listbox with the currently selected cbz files."""
        self.file_listbox.delete(0, tk.END)

        if self.cbz_files:
            self._empty_label.place_forget()
        else:
            self._empty_label.place(relx=0.5, rely=0.5, anchor="center")
            self._empty_label.configure(text="No .cbz files found")

        for i, f in enumerate(self.cbz_files, 1):
            size = _format_size(f.stat().st_size)
            self.file_listbox.insert(tk.END, f"  {i:3d}.  {f.name}   ({size})")

            # Alternate row colors
            if i % 2 == 0:
                self.file_listbox.itemconfig(i - 1, bg=Colors.BG_CARD_ALT)

        count = len(self.cbz_files)
        self.file_count_label.configure(
            text=f"{count} file{'s' if count != 1 else ''}",
            fg=Colors.SUCCESS if count > 0 else Colors.WARNING
        )

        if count > 0:
            self._set_status_dot(Colors.SUCCESS)
            self.status_label.configure(
                text=f"Found {count} CBZ file(s) — ready to merge",
                fg=Colors.TEXT_SEC
            )
        else:
            self._set_status_dot(Colors.WARNING)
            self.status_label.configure(
                text="No .cbz files found in this folder",
                fg=Colors.WARNING
            )

        self.progress_bar.set_progress(0)

    def _start_merge(self):
        if self.is_running:
            return

        if not self.cbz_files:
            messagebox.showwarning("No Files", "Please select a folder with .cbz files first.")
            return

        output_name = self.output_var.get().strip()
        if not output_name:
            messagebox.showwarning("No Output", "Please enter an output filename.")
            return

        if not output_name.lower().endswith(".cbz"):
            output_name += ".cbz"
            self.output_var.set(output_name)

        # Run merge in background thread
        self.is_running = True
        self.merge_btn.set_enabled(False)
        self.browse_btn.set_enabled(False)
        self.progress_bar.set_progress(0)
        self._set_status_dot(Colors.ACCENT_LIGHT)
        self.status_label.configure(text="Starting merge...", fg=Colors.ACCENT_LIGHT)

        thread = threading.Thread(
            target=self._run_merge,
            args=(self.input_folder, output_name, self.compress_var.get(), self.ereader_var.get()),
            daemon=True
        )
        thread.start()

    def _run_merge(self, input_folder: Path, output_name: str, compress: bool, optimize_for_ereader: bool):
        """Run the merge process in a background thread with GUI progress updates."""
        import zipfile
        import tempfile
        import shutil
        import time
        from cbz_merger import extract_cbz

        compression = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
        # Determine output path
        if self._custom_output_path:
            output_path = self._custom_output_path
        else:
            output_path = input_folder / output_name

        self._last_output_path = output_path
        start_time = time.time()
        temp_dir = None

        try:
            # Step 1: Extract (Multi-threaded)
            temp_dir = Path(tempfile.mkdtemp(prefix="cbz_merger_"))
            all_images = []
            total = len(self.cbz_files)

            self._update_status("Extracting chapters...", Colors.ACCENT_LIGHT)

            def extract_task(idx, cbz_file):
                return extract_cbz(cbz_file, temp_dir, chapter_index=idx, optimize_for_ereader=optimize_for_ereader)

            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_file = {
                    executor.submit(extract_task, i, f): f 
                    for i, f in enumerate(self.cbz_files)
                }
                
                completed = 0
                for future in concurrent.futures.as_completed(future_to_file):
                    completed += 1
                    cbz_file = future_to_file[future]
                    
                    self._update_status(
                        f"Extracting ({completed}/{total}): {cbz_file.name}",
                        Colors.ACCENT_LIGHT
                    )
                    self._update_progress((completed) / (total * 2))
                    
                    try:
                        images = future.result()
                        all_images.extend(images)
                    except Exception as e:
                        print(f"Error extracting {cbz_file.name}: {e}")

            if not all_images:
                self._update_status("No images found in any file!", Colors.ERROR)
                self._update_dot(Colors.ERROR)
                return

            # Step 2: Prepare metadata and sort images
            all_images.sort(key=lambda p: p.name)
            total_images = len(all_images)

            import xml.etree.ElementTree as ET
            comic_info_path = temp_dir / "ComicInfo.xml"
            try:
                root = ET.Element("ComicInfo", {
                    "xmlns:xsd": "http://www.w3.org/2001/XMLSchema", 
                    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"
                })
                ET.SubElement(root, "Title").text = output_name.replace(".cbz", "")
                ET.SubElement(root, "Summary").text = f"Merged {total} files using CBZ Merger."
                ET.SubElement(root, "PageCount").text = str(total_images)
                
                tree = ET.ElementTree(root)
                tree.write(comic_info_path, encoding="utf-8", xml_declaration=True)
            except Exception:
                pass

            self._update_status(f"Packing {total_images} images...", Colors.ACCENT_LIGHT)

            # Step 3: Create merged archive
            with zipfile.ZipFile(output_path, "w", compression=compression) as zf_out:
                if comic_info_path.exists():
                    zf_out.write(comic_info_path, arcname="ComicInfo.xml")

                for i, img_path in enumerate(all_images):
                    zf_out.write(img_path, arcname=img_path.name)

                    if (i + 1) % 50 == 0 or (i + 1) == total_images:
                        progress = 0.5 + (0.5 * (i + 1) / total_images)
                        self._update_progress(progress)
                        self._update_status(
                            f"Packing images... ({i + 1}/{total_images})",
                            Colors.ACCENT_LIGHT
                        )

            # Done!
            elapsed = time.time() - start_time
            size = _format_size(output_path.stat().st_size)

            self._update_progress(1.0)
            self._update_status(
                f"✅ Done! {total_images} images → {output_name} ({size}) in {elapsed:.1f}s",
                Colors.SUCCESS
            )
            self._update_dot(Colors.SUCCESS)

            # Show the output path and open folder button
            self.root.after(0, lambda: self.save_location_var.set(
                f"✅ Saved to: {output_path}"
            ))
            self.root.after(0, lambda: self.save_location_label.configure(fg=Colors.SUCCESS))
            self.root.after(0, lambda: self._open_folder_frame.pack(fill="x", pady=(6, 0)))

        except PermissionError:
            self._update_status(f"Permission denied writing to {output_path}", Colors.ERROR)
            self._update_dot(Colors.ERROR)
        except Exception as e:
            self._update_status(f"Error: {e}", Colors.ERROR)
            self._update_dot(Colors.ERROR)

        finally:
            # Cleanup
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass

            self.is_running = False
            self.root.after(0, lambda: self.merge_btn.set_enabled(True))
            self.root.after(0, lambda: self.browse_btn.set_enabled(True))

    # ── Thread-safe UI updates ───────────────────────────────────────────

    def _update_status(self, text: str, color: str = Colors.TEXT_DIM):
        self.root.after(0, lambda: self.status_label.configure(text=text, fg=color))

    def _update_progress(self, value: float):
        self.root.after(0, lambda: self.progress_bar.set_progress(value))

    def _update_dot(self, color: str):
        self.root.after(0, lambda: self._set_status_dot(color))


# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()

    # Set window icon (optional, won't crash if missing)
    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    app = CBZMergerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
