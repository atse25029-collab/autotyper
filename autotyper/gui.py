"""
Clean, minimal desktop UI for AutoTyper.
Designed with focused ergonomics, high readability, and zero clutter.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import pyperclip

from autotyper.engine import AutoTypeEngine, AutoTypeConfig
from autotyper.hotkeys import HotkeyManager


class AutoTyperGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AutoTyper")
        self.root.geometry("640x660")
        self.root.minsize(580, 560)

        # Clean, modern Zinc / Slate dark palette
        self.colors = {
            "bg": "#121214",
            "surface": "#1a1a1e",
            "surface_alt": "#222227",
            "border": "#2e2e36",
            "text": "#e4e4e7",
            "text_muted": "#71717a",
            "accent": "#3b82f6",
            "start": "#15803d",
            "start_hover": "#16a34a",
            "stop": "#b91c1c",
            "stop_hover": "#dc2626",
            "status_idle": "#27272a",
            "status_active": "#1e3a8a",
            "status_typing": "#14532d",
            "status_stopped": "#7f1d1d",
        }
        self.root.configure(bg=self.colors["bg"])

        # Engine & Config
        self.config = AutoTypeConfig(
            char_delay_ms=16.0,
            jitter_percent=15.0,
            countdown_seconds=3.0,
            play_sound=True,
            indent_mode="smart_python",
            line_pause_ms=25.0
        )
        self.engine = AutoTypeEngine(self.config)
        self.hotkey_mgr = HotkeyManager(
            on_trigger=self._on_hotkey_trigger,
            on_stop=self._on_hotkey_stop,
            trigger_hotkey="<f8>",
            stop_hotkey="<f9>",
            alt_trigger_hotkey="<ctrl>+<alt>+v"
        )

        # State Variables
        self.var_status = tk.StringVar(value="Ready")
        self.var_char_delay = tk.DoubleVar(value=16.0)
        self.var_countdown = tk.DoubleVar(value=3.0)
        self.var_code_mode = tk.BooleanVar(value=True)
        self.var_always_on_top = tk.BooleanVar(value=False)
        self.var_sound = tk.BooleanVar(value=True)

        self.last_clipboard_content = ""
        self.is_monitoring = True

        # Bind engine events
        self.engine.on_status_change = self._on_engine_status
        self.engine.on_progress = self._on_engine_progress
        self.engine.on_complete = self._on_engine_complete

        self._build_interface()
        self._apply_styles()

        self.hotkey_mgr.start()
        self._start_clipboard_monitor()

        self.root.protocol("WM_DELETE_WINDOW", self._on_exit)

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=self.colors["surface"], foreground=self.colors["text"])
        style.configure("TProgressbar", thickness=4, troughcolor=self.colors["surface_alt"], background=self.colors["accent"])

    def _build_interface(self):
        root_pad = tk.Frame(self.root, bg=self.colors["bg"], padx=18, pady=16)
        root_pad.pack(fill=tk.BOTH, expand=True)

        # --- Top Navigation Bar ---
        top_bar = tk.Frame(root_pad, bg=self.colors["bg"])
        top_bar.pack(fill=tk.X, pady=(0, 14))

        app_title = tk.Label(
            top_bar,
            text="AutoTyper",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["text"],
            bg=self.colors["bg"]
        )
        app_title.pack(side=tk.LEFT)

        hotkey_tag = tk.Label(
            top_bar,
            text="F8: Start  |  F9: Stop",
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["surface"],
            padx=10,
            pady=3
        )
        hotkey_tag.pack(side=tk.RIGHT)

        # --- Status Indicator ---
        status_panel = tk.Frame(root_pad, bg=self.colors["surface"], padx=12, pady=10, highlightbackground=self.colors["border"], highlightthickness=1)
        status_panel.pack(fill=tk.X, pady=(0, 12))

        self.lbl_status = tk.Label(
            status_panel,
            textvariable=self.var_status,
            font=("Segoe UI", 10),
            fg=self.colors["text"],
            bg=self.colors["surface"]
        )
        self.lbl_status.pack(side=tk.LEFT)

        self.lbl_counter = tk.Label(
            status_panel,
            text="0 characters",
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["surface"]
        )
        self.lbl_counter.pack(side=tk.RIGHT)

        self.progress = ttk.Progressbar(root_pad, style="TProgressbar", orient=tk.HORIZONTAL, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(0, 12))

        # --- Content / Clipboard Area ---
        content_frame = tk.Frame(root_pad, bg=self.colors["surface"], padx=12, pady=10, highlightbackground=self.colors["border"], highlightthickness=1)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        content_hdr = tk.Frame(content_frame, bg=self.colors["surface"])
        content_hdr.pack(fill=tk.X, pady=(0, 8))

        lbl_content = tk.Label(
            content_hdr,
            text="Input Content",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["text"],
            bg=self.colors["surface"]
        )
        lbl_content.pack(side=tk.LEFT)

        btn_paste = tk.Button(
            content_hdr,
            text="Sync Clipboard",
            command=self._sync_clipboard_now,
            font=("Segoe UI", 8),
            bg=self.colors["surface_alt"],
            fg=self.colors["text"],
            activebackground=self.colors["border"],
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=8,
            pady=2
        )
        btn_paste.pack(side=tk.RIGHT)

        text_wrap = tk.Frame(content_frame, bg=self.colors["surface_alt"])
        text_wrap.pack(fill=tk.BOTH, expand=True)

        self.txt_content = tk.Text(
            text_wrap,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=self.colors["surface_alt"],
            fg=self.colors["text"],
            insertbackground=self.colors["accent"],
            relief=tk.FLAT,
            padx=10,
            pady=10,
            height=10
        )
        scrollbar = tk.Scrollbar(text_wrap, command=self.txt_content.yview)
        self.txt_content.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.txt_content.bind("<KeyRelease>", self._on_text_edited)

        # --- Settings Panel ---
        settings_frame = tk.Frame(root_pad, bg=self.colors["surface"], padx=12, pady=10, highlightbackground=self.colors["border"], highlightthickness=1)
        settings_frame.pack(fill=tk.X, pady=(0, 14))

        # Slider: Speed
        slider_row = tk.Frame(settings_frame, bg=self.colors["surface"])
        slider_row.pack(fill=tk.X, pady=(0, 8))

        tk.Label(slider_row, text="Typing Delay:", font=("Segoe UI", 9), fg=self.colors["text"], bg=self.colors["surface"]).pack(side=tk.LEFT)
        scale_speed = tk.Scale(
            slider_row,
            from_=0,
            to=60,
            orient=tk.HORIZONTAL,
            variable=self.var_char_delay,
            bg=self.colors["surface"],
            fg=self.colors["text"],
            troughcolor=self.colors["surface_alt"],
            highlightthickness=0,
            command=lambda v: self._apply_settings()
        )
        scale_speed.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=12)
        self.lbl_speed_readout = tk.Label(slider_row, text="16 ms", font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["surface"], width=6, anchor="e")
        self.lbl_speed_readout.pack(side=tk.RIGHT)

        # Options Row
        options_row = tk.Frame(settings_frame, bg=self.colors["surface"])
        options_row.pack(fill=tk.X)

        tk.Checkbutton(
            options_row,
            text="Code Editor Indentation (Monaco / NxtWave)",
            variable=self.var_code_mode,
            command=self._apply_settings,
            font=("Segoe UI", 9),
            fg=self.colors["text"],
            bg=self.colors["surface"],
            activebackground=self.colors["surface"],
            selectcolor=self.colors["surface_alt"]
        ).pack(side=tk.LEFT, padx=(0, 18))

        tk.Checkbutton(
            options_row,
            text="Sound Cues",
            variable=self.var_sound,
            command=self._apply_settings,
            font=("Segoe UI", 9),
            fg=self.colors["text"],
            bg=self.colors["surface"],
            activebackground=self.colors["surface"],
            selectcolor=self.colors["surface_alt"]
        ).pack(side=tk.LEFT, padx=(0, 18))

        tk.Checkbutton(
            options_row,
            text="Always on Top",
            variable=self.var_always_on_top,
            command=self._toggle_topmost,
            font=("Segoe UI", 9),
            fg=self.colors["text"],
            bg=self.colors["surface"],
            activebackground=self.colors["surface"],
            selectcolor=self.colors["surface_alt"]
        ).pack(side=tk.LEFT)

        # --- Action Buttons ---
        btn_row = tk.Frame(root_pad, bg=self.colors["bg"])
        btn_row.pack(fill=tk.X)

        self.btn_start = tk.Button(
            btn_row,
            text="Start Typing (F8)",
            command=self._trigger_start,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["start"],
            fg="#ffffff",
            activebackground=self.colors["start_hover"],
            activeforeground="#ffffff",
            relief=tk.FLAT,
            pady=8
        )
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self.btn_stop = tk.Button(
            btn_row,
            text="Stop (F9)",
            command=self._trigger_stop,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["stop"],
            fg="#ffffff",
            activebackground=self.colors["stop_hover"],
            activeforeground="#ffffff",
            relief=tk.FLAT,
            pady=8
        )
        self.btn_stop.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0))

        # Initial content sync
        self._sync_clipboard_now()

    def _apply_settings(self):
        delay = self.var_char_delay.get()
        self.lbl_speed_readout.config(text=f"{int(delay)} ms")
        self.config.char_delay_ms = delay
        self.config.indent_mode = "smart_python" if self.var_code_mode.get() else "raw"
        self.config.play_sound = self.var_sound.get()

    def _toggle_topmost(self):
        self.root.attributes("-topmost", self.var_always_on_top.get())

    def _sync_clipboard_now(self):
        try:
            txt = pyperclip.paste()
            if txt:
                self.txt_content.delete("1.0", tk.END)
                self.txt_content.insert("1.0", txt)
                self.last_clipboard_content = txt
                self._update_engine_content()
        except Exception:
            pass

    def _update_engine_content(self):
        content = self.txt_content.get("1.0", tk.END).rstrip("\r\n")
        self.engine.load_content(content)
        chars = len(content)
        lines = len(content.splitlines()) if content else 0
        self.lbl_counter.config(text=f"{chars} chars | {lines} lines")

    def _on_text_edited(self, event=None):
        self._update_engine_content()

    def _start_clipboard_monitor(self):
        def monitor():
            while self.is_monitoring:
                time.sleep(0.5)
                if self.engine.state in ("COUNTDOWN", "TYPING"):
                    continue
                try:
                    curr = pyperclip.paste()
                    if curr and curr != self.last_clipboard_content:
                        self.last_clipboard_content = curr
                        self.root.after(0, self._set_clipboard_content, curr)
                except Exception:
                    pass

        threading.Thread(target=monitor, daemon=True).start()

    def _set_clipboard_content(self, text: str):
        self.txt_content.delete("1.0", tk.END)
        self.txt_content.insert("1.0", text)
        self._update_engine_content()
        self.var_status.set("Clipboard updated")

    def _trigger_start(self):
        self._apply_settings()
        self._update_engine_content()
        self.engine.trigger_start()

    def _trigger_stop(self):
        self.engine.stop()

    def _on_hotkey_trigger(self):
        self.root.after(0, self._handle_hotkey_action)

    def _handle_hotkey_action(self):
        if self.engine.state in ("COUNTDOWN", "TYPING"):
            return
        self._apply_settings()
        self._update_engine_content()
        self.engine.trigger_start(override_countdown=0.5)

    def _on_hotkey_stop(self):
        self.root.after(0, self.engine.stop)

    def _on_engine_status(self, state: str, details: str):
        self.root.after(0, self._update_status_ui, state, details)

    def _update_status_ui(self, state: str, details: str):
        self.var_status.set(details if details else state)

    def _on_engine_progress(self, current: int, total: int, elem: int, total_elems: int):
        self.root.after(0, self._update_progress_ui, current, total)

    def _update_progress_ui(self, current: int, total: int):
        pct = (current / max(1, total)) * 100
        self.progress["value"] = pct
        self.lbl_counter.config(text=f"{current} / {total} chars ({int(pct)}%)")

    def _on_engine_complete(self):
        self.root.after(0, lambda: self.progress.configure(value=100))

    def _on_exit(self):
        self.is_monitoring = False
        self.hotkey_mgr.stop()
        self.engine.stop()
        self.root.destroy()
