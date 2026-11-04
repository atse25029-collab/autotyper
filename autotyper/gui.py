"""
Modern, responsive GUI for AutoTyper built with Tkinter.
Includes clipboard preview, multi-element queue management, speed/jitter controls,
smart auto-indent toggles, global hotkey display, and a safe built-in test scratchpad.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import pyperclip

from autotyper.engine import AutoTypeEngine, AutoTypeConfig
from autotyper.hotkeys import HotkeyManager


class AutoTyperGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AutoTyper Pro - Keystroke Portal Bypass")
        self.root.geometry("740x800")
        self.root.minsize(680, 720)

        # Apply dark aesthetic theme
        self.colors = {
            "bg": "#181825",
            "card": "#1e1e2e",
            "card_sub": "#252538",
            "border": "#313244",
            "text": "#cdd6f4",
            "text_dim": "#a6adc8",
            "accent": "#89b4fa",
            "accent_hover": "#b4befe",
            "start": "#a6e3a1",
            "start_hover": "#94e2d5",
            "stop": "#f38ba8",
            "stop_hover": "#eba0ac",
            "badge_idle": "#45475a",
            "badge_countdown": "#f9e2af",
            "badge_typing": "#a6e3a1",
            "badge_stop": "#f38ba8",
        }
        self.root.configure(bg=self.colors["bg"])

        # Engine & Config
        self.config = AutoTypeConfig()
        self.engine = AutoTypeEngine(self.config)
        self.hotkey_mgr = HotkeyManager(
            on_trigger=self._on_hotkey_trigger,
            on_stop=self._on_hotkey_stop,
            trigger_hotkey="<f8>",
            stop_hotkey="<f9>",
            alt_trigger_hotkey="<ctrl>+<alt>+v"
        )

        # State Variables
        self.var_status_badge = tk.StringVar(value="READY")
        self.var_status_detail = tk.StringVar(value="Press F8 or click Start to begin typing")
        self.var_char_delay = tk.DoubleVar(value=20.0)
        self.var_jitter = tk.DoubleVar(value=25.0)
        self.var_countdown = tk.DoubleVar(value=3.0)
        self.var_sound = tk.BooleanVar(value=True)
        self.var_ontop = tk.BooleanVar(value=False)
        self.var_autosync = tk.BooleanVar(value=True)
        self.var_strip_indent = tk.BooleanVar(value=False)
        self.var_element_mode = tk.StringVar(value="single")  # single, queue_step, auto_tab
        self.var_delimiter = tk.StringVar(value="\\n\\n")

        self.last_clipboard_content = ""
        self.is_monitoring_clipboard = True

        # Wire engine callbacks
        self.engine.on_status_change = self._engine_status_changed
        self.engine.on_progress = self._engine_progress
        self.engine.on_queue_updated = self._engine_queue_updated
        self.engine.on_complete = self._engine_completed

        self._build_ui()
        self._apply_styles()

        # Start background clipboard listener & hotkeys
        self.hotkey_mgr.start()
        self._start_clipboard_watcher()

        # Handle window close cleanly
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Global styling overrides
        style.configure(".", background=self.colors["card"], foreground=self.colors["text"])
        style.configure("TLabel", background=self.colors["card"], foreground=self.colors["text"], font=("Segoe UI", 9))
        style.configure("Sub.TLabel", foreground=self.colors["text_dim"], font=("Segoe UI", 8))
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground=self.colors["accent"])
        style.configure("Card.TFrame", background=self.colors["card"])
        style.configure("Inner.TFrame", background=self.colors["card_sub"])

        style.configure(
            "Start.TButton",
            font=("Segoe UI", 10, "bold"),
            background="#2e7d32",
            foreground="#ffffff",
            borderwidth=0,
            padding=8
        )
        style.map("Start.TButton", background=[("active", "#388e3c")])

        style.configure(
            "Stop.TButton",
            font=("Segoe UI", 10, "bold"),
            background="#c62828",
            foreground="#ffffff",
            borderwidth=0,
            padding=8
        )
        style.map("Stop.TButton", background=[("active", "#d32f2f")])

        style.configure(
            "TCheckbutton",
            background=self.colors["card"],
            foreground=self.colors["text"],
            font=("Segoe UI", 9)
        )
        style.configure(
            "TRadiobutton",
            background=self.colors["card"],
            foreground=self.colors["text"],
            font=("Segoe UI", 9)
        )
        style.configure("TProgressbar", thickness=10, troughcolor=self.colors["card_sub"], background=self.colors["accent"])

    def _build_ui(self):
        main_container = tk.Frame(self.root, bg=self.colors["bg"], padx=14, pady=10)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 1. TOP HEADER & HOTKEY BADGE
        header_frame = tk.Frame(main_container, bg=self.colors["card"], padx=12, pady=10, relief=tk.FLAT)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = tk.Label(
            header_frame,
            text="⚡ AutoTyper Pro",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["card"]
        )
        title_label.pack(side=tk.LEFT)

        sub_title = tk.Label(
            header_frame,
            text="Bypass disabled paste by simulating direct keyboard typing",
            font=("Segoe UI", 8),
            fg=self.colors["text_dim"],
            bg=self.colors["card"]
        )
        sub_title.pack(side=tk.LEFT, padx=(8, 0), pady=(4, 0))

        # Hotkeys pill
        hotkey_pill = tk.Label(
            header_frame,
            text="[ F8: Start ]  [ F9: Stop ]",
            font=("Consolas", 9, "bold"),
            fg="#181825",
            bg=self.colors["accent"],
            padx=8,
            pady=3
        )
        hotkey_pill.pack(side=tk.RIGHT)

        # 2. STATUS & PROGRESS CARD
        status_card = tk.Frame(main_container, bg=self.colors["card"], padx=12, pady=10)
        status_card.pack(fill=tk.X, pady=(0, 10))

        status_header = tk.Frame(status_card, bg=self.colors["card"])
        status_header.pack(fill=tk.X)

        self.lbl_badge = tk.Label(
            status_header,
            textvariable=self.var_status_badge,
            font=("Segoe UI", 9, "bold"),
            fg="#181825",
            bg=self.colors["badge_idle"],
            padx=8,
            pady=2
        )
        self.lbl_badge.pack(side=tk.LEFT)

        self.lbl_detail = tk.Label(
            status_header,
            textvariable=self.var_status_detail,
            font=("Segoe UI", 9),
            fg=self.colors["text"],
            bg=self.colors["card"]
        )
        self.lbl_detail.pack(side=tk.LEFT, padx=(10, 0))

        self.lbl_queue_indicator = tk.Label(
            status_header,
            text="",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["card"]
        )
        self.lbl_queue_indicator.pack(side=tk.RIGHT)

        # Progress bar
        self.progress_bar = ttk.Progressbar(status_card, style="TProgressbar", orient=tk.HORIZONTAL, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(8, 0))

        # 3. CONTENT & CLIPBOARD MONITOR CARD
        content_card = tk.Frame(main_container, bg=self.colors["card"], padx=12, pady=10)
        content_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        content_hdr = tk.Frame(content_card, bg=self.colors["card"])
        content_hdr.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            content_hdr,
            text="Text to Type (Active Clipboard)",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["text"],
            bg=self.colors["card"]
        ).pack(side=tk.LEFT)

        self.lbl_char_count = tk.Label(
            content_hdr,
            text="0 characters | 0 lines",
            font=("Segoe UI", 8),
            fg=self.colors["text_dim"],
            bg=self.colors["card"]
        )
        self.lbl_char_count.pack(side=tk.LEFT, padx=(10, 0))

        chk_autosync = tk.Checkbutton(
            content_hdr,
            text="Auto-sync Clipboard",
            variable=self.var_autosync,
            font=("Segoe UI", 8),
            bg=self.colors["card"],
            fg=self.colors["text"],
            activebackground=self.colors["card"],
            activeforeground=self.colors["accent"],
            selectcolor=self.colors["card_sub"]
        )
        chk_autosync.pack(side=tk.RIGHT)

        btn_sync = tk.Button(
            content_hdr,
            text="📋 Paste from Clipboard",
            command=self._manual_clipboard_sync,
            font=("Segoe UI", 8),
            bg=self.colors["card_sub"],
            fg=self.colors["accent"],
            activebackground=self.colors["border"],
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=6,
            pady=1
        )
        btn_sync.pack(side=tk.RIGHT, padx=(0, 8))

        # Text Editor / Display
        text_container = tk.Frame(content_card, bg=self.colors["card_sub"])
        text_container.pack(fill=tk.BOTH, expand=True)

        self.txt_content = tk.Text(
            text_container,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=self.colors["card_sub"],
            fg=self.colors["text"],
            insertbackground=self.colors["accent"],
            relief=tk.FLAT,
            padx=8,
            pady=8,
            height=6
        )
        scrollbar = tk.Scrollbar(text_container, command=self.txt_content.yview)
        self.txt_content.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.txt_content.bind("<KeyRelease>", self._on_text_modified)

        # 4. ELEMENT MODE & FORM AUTOMATION ("FOR EACH ELEMENT")
        elem_card = tk.Frame(main_container, bg=self.colors["card"], padx=12, pady=10)
        elem_card.pack(fill=tk.X, pady=(0, 10))

        elem_hdr = tk.Frame(elem_card, bg=self.colors["card"])
        elem_hdr.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            elem_hdr,
            text="Element Automation Mode (For multiple inputs / question forms)",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["text"],
            bg=self.colors["card"]
        ).pack(side=tk.LEFT)

        # Radio options for Element Mode
        modes_frame = tk.Frame(elem_card, bg=self.colors["card"])
        modes_frame.pack(fill=tk.X)

        tk.Radiobutton(
            modes_frame,
            text="Single (Type all into focused field)",
            variable=self.var_element_mode,
            value="single",
            command=self._update_element_mode,
            bg=self.colors["card"],
            fg=self.colors["text"],
            selectcolor=self.colors["card_sub"],
            activebackground=self.colors["card"],
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT, padx=(0, 15))

        tk.Radiobutton(
            modes_frame,
            text="Step-by-Step (Press F8 for each element)",
            variable=self.var_element_mode,
            value="queue_step",
            command=self._update_element_mode,
            bg=self.colors["card"],
            fg=self.colors["text"],
            selectcolor=self.colors["card_sub"],
            activebackground=self.colors["card"],
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT, padx=(0, 15))

        tk.Radiobutton(
            modes_frame,
            text="Auto-Tab (Type element -> Press Tab -> Type next)",
            variable=self.var_element_mode,
            value="auto_tab",
            command=self._update_element_mode,
            bg=self.colors["card"],
            fg=self.colors["text"],
            selectcolor=self.colors["card_sub"],
            activebackground=self.colors["card"],
            font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)

        # Delimiter selector for multi-element
        delim_frame = tk.Frame(elem_card, bg=self.colors["card"])
        delim_frame.pack(fill=tk.X, pady=(6, 0))

        tk.Label(
            delim_frame,
            text="Element Separator:",
            font=("Segoe UI", 8),
            fg=self.colors["text_dim"],
            bg=self.colors["card"]
        ).pack(side=tk.LEFT)

        self.cb_delimiter = ttk.Combobox(
            delim_frame,
            textvariable=self.var_delimiter,
            values=["\\n\\n (Blank Line)", "\\n (Each Line)", "---", "\\t (Tab)"],
            width=18,
            state="readonly"
        )
        self.cb_delimiter.pack(side=tk.LEFT, padx=(6, 12))
        self.cb_delimiter.bind("<<ComboboxSelected>>", lambda e: self._reload_engine_content())

        btn_reset_queue = tk.Button(
            delim_frame,
            text="↺ Reset to Element 1",
            command=self._reset_queue_index,
            font=("Segoe UI", 8),
            bg=self.colors["card_sub"],
            fg=self.colors["text"],
            relief=tk.FLAT,
            padx=6,
            pady=1
        )
        btn_reset_queue.pack(side=tk.LEFT)

        # 5. CONFIGURATION CONTROLS (SPEED, JITTER, COUNTDOWN, OPTIONS)
        config_card = tk.Frame(main_container, bg=self.colors["card"], padx=12, pady=10)
        config_card.pack(fill=tk.X, pady=(0, 10))

        cfg_grid = tk.Frame(config_card, bg=self.colors["card"])
        cfg_grid.pack(fill=tk.X)

        # Row 1: Typing Speed Slider
        tk.Label(cfg_grid, text="Typing Delay (ms/char):", bg=self.colors["card"]).grid(row=0, column=0, sticky="w", pady=3)
        scale_speed = tk.Scale(
            cfg_grid,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.var_char_delay,
            bg=self.colors["card"],
            fg=self.colors["text"],
            troughcolor=self.colors["card_sub"],
            highlightthickness=0,
            command=lambda v: self._update_config_values()
        )
        scale_speed.grid(row=0, column=1, sticky="ew", padx=8, pady=3)
        self.lbl_speed_val = tk.Label(cfg_grid, text="20 ms (~60 WPM)", bg=self.colors["card"], width=16, anchor="w")
        self.lbl_speed_val.grid(row=0, column=2, sticky="w", pady=3)

        # Row 2: Human Jitter
        tk.Label(cfg_grid, text="Human Variation Jitter:", bg=self.colors["card"]).grid(row=1, column=0, sticky="w", pady=3)
        scale_jitter = tk.Scale(
            cfg_grid,
            from_=0,
            to=50,
            orient=tk.HORIZONTAL,
            variable=self.var_jitter,
            bg=self.colors["card"],
            fg=self.colors["text"],
            troughcolor=self.colors["card_sub"],
            highlightthickness=0,
            command=lambda v: self._update_config_values()
        )
        scale_jitter.grid(row=1, column=1, sticky="ew", padx=8, pady=3)
        self.lbl_jitter_val = tk.Label(cfg_grid, text="±25%", bg=self.colors["card"], width=16, anchor="w")
        self.lbl_jitter_val.grid(row=1, column=2, sticky="w", pady=3)

        # Row 3: Countdown
        tk.Label(cfg_grid, text="Countdown Grace Delay:", bg=self.colors["card"]).grid(row=2, column=0, sticky="w", pady=3)
        scale_countdown = tk.Scale(
            cfg_grid,
            from_=0.5,
            to=8.0,
            resolution=0.5,
            orient=tk.HORIZONTAL,
            variable=self.var_countdown,
            bg=self.colors["card"],
            fg=self.colors["text"],
            troughcolor=self.colors["card_sub"],
            highlightthickness=0,
            command=lambda v: self._update_config_values()
        )
        scale_countdown.grid(row=2, column=1, sticky="ew", padx=8, pady=3)
        self.lbl_countdown_val = tk.Label(cfg_grid, text="3.0 sec", bg=self.colors["card"], width=16, anchor="w")
        self.lbl_countdown_val.grid(row=2, column=2, sticky="w", pady=3)

        cfg_grid.columnconfigure(1, weight=1)

        # Checkbox toggles row
        toggles_frame = tk.Frame(config_card, bg=self.colors["card"])
        toggles_frame.pack(fill=tk.X, pady=(8, 0))

        tk.Checkbutton(
            toggles_frame,
            text="Smart Code Indent (trim leading spaces for auto-indenting editors)",
            variable=self.var_strip_indent,
            command=self._update_config_values,
            bg=self.colors["card"],
            fg=self.colors["text"],
            activebackground=self.colors["card"],
            selectcolor=self.colors["card_sub"]
        ).pack(side=tk.LEFT, padx=(0, 15))

        tk.Checkbutton(
            toggles_frame,
            text="Audio Beeps",
            variable=self.var_sound,
            command=self._update_config_values,
            bg=self.colors["card"],
            fg=self.colors["text"],
            activebackground=self.colors["card"],
            selectcolor=self.colors["card_sub"]
        ).pack(side=tk.LEFT, padx=(0, 15))

        tk.Checkbutton(
            toggles_frame,
            text="Always On Top",
            variable=self.var_ontop,
            command=self._toggle_always_on_top,
            bg=self.colors["card"],
            fg=self.colors["text"],
            activebackground=self.colors["card"],
            selectcolor=self.colors["card_sub"]
        ).pack(side=tk.LEFT)

        # 6. BUILT-IN TEST SCRATCHPAD
        test_card = tk.Frame(main_container, bg=self.colors["card"], padx=12, pady=8)
        test_card.pack(fill=tk.X, pady=(0, 10))

        test_hdr = tk.Frame(test_card, bg=self.colors["card"])
        test_hdr.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            test_hdr,
            text="🧪 Built-in Test Scratchpad (Click inside & press F8 to test safely)",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["card"]
        ).pack(side=tk.LEFT)

        self.txt_test_scratchpad = tk.Entry(
            test_card,
            font=("Consolas", 10),
            bg=self.colors["card_sub"],
            fg=self.colors["text"],
            insertbackground=self.colors["accent"],
            relief=tk.FLAT
        )
        self.txt_test_scratchpad.pack(fill=tk.X, ipady=4)

        # 7. ACTION BUTTONS (START / STOP)
        btn_bar = tk.Frame(main_container, bg=self.colors["bg"])
        btn_bar.pack(fill=tk.X)

        self.btn_start = tk.Button(
            btn_bar,
            text="▶ Start Autotype (F8)",
            command=self._start_typing_clicked,
            font=("Segoe UI", 11, "bold"),
            bg="#2e7d32",
            fg="#ffffff",
            activebackground="#388e3c",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            pady=8
        )
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.btn_stop = tk.Button(
            btn_bar,
            text="⏹ Emergency Stop (F9)",
            command=self._stop_typing_clicked,
            font=("Segoe UI", 11, "bold"),
            bg="#c62828",
            fg="#ffffff",
            activebackground="#d32f2f",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            pady=8
        )
        self.btn_stop.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(8, 0))

        # Initial content sync
        self._manual_clipboard_sync()

    # ------------------ EVENT HANDLERS & HELPERS ------------------

    def _update_config_values(self):
        delay = self.var_char_delay.get()
        jitter = self.var_jitter.get()
        countdown = self.var_countdown.get()

        wpm = int(60000 / (delay * 5)) if delay > 0 else 999
        self.lbl_speed_val.config(text=f"{int(delay)} ms (~{wpm} WPM)")
        self.lbl_jitter_val.config(text=f"±{int(jitter)}%")
        self.lbl_countdown_val.config(text=f"{countdown:.1f} sec")

        self.config.char_delay_ms = delay
        self.config.jitter_percent = jitter
        self.config.countdown_seconds = countdown
        self.config.play_sound = self.var_sound.get()
        self.config.auto_indent_mode = "strip_indent" if self.var_strip_indent.get() else "raw"

    def _update_element_mode(self):
        self.config.element_mode = self.var_element_mode.get()
        self._reload_engine_content()

    def _toggle_always_on_top(self):
        self.root.attributes("-topmost", self.var_ontop.get())

    def _get_active_delimiter(self) -> str:
        selected = self.var_delimiter.get()
        if "\\n\\n" in selected:
            return "\n\n"
        elif "\\n" in selected:
            return "\n"
        elif "\\t" in selected:
            return "\t"
        elif "---" in selected:
            return "---"
        return "\n\n"

    def _reload_engine_content(self):
        content = self.txt_content.get("1.0", tk.END).rstrip("\r\n")
        delim = self._get_active_delimiter()
        self.engine.load_content(content, delimiter=delim)
        self._update_char_count_display(content)

    def _reset_queue_index(self):
        self.engine.set_queue_index(0)

    def _on_text_modified(self, event=None):
        self._reload_engine_content()

    def _manual_clipboard_sync(self):
        try:
            content = pyperclip.paste()
            if content:
                self.txt_content.delete("1.0", tk.END)
                self.txt_content.insert("1.0", content)
                self.last_clipboard_content = content
                self._reload_engine_content()
        except Exception:
            pass

    def _update_char_count_display(self, text: str):
        chars = len(text)
        lines = len(text.splitlines()) if text else 0
        self.lbl_char_count.config(text=f"{chars} characters | {lines} lines")

    def _start_clipboard_watcher(self):
        def watcher():
            while self.is_monitoring_clipboard:
                time.sleep(0.5)
                if not self.var_autosync.get():
                    continue
                if self.engine.state in ("COUNTDOWN", "TYPING"):
                    continue

                try:
                    curr = pyperclip.paste()
                    if curr and curr != self.last_clipboard_content:
                        self.last_clipboard_content = curr
                        self.root.after(0, self._apply_new_clipboard_text, curr)
                except Exception:
                    pass

        threading.Thread(target=watcher, daemon=True).start()

    def _apply_new_clipboard_text(self, text: str):
        self.txt_content.delete("1.0", tk.END)
        self.txt_content.insert("1.0", text)
        self._reload_engine_content()
        self.var_status_detail.set("New clipboard content synchronized!")

    def _start_typing_clicked(self):
        self._update_config_values()
        self._reload_engine_content()
        self.engine.trigger_start()

    def _stop_typing_clicked(self):
        self.engine.stop()

    def _on_hotkey_trigger(self):
        # Triggered via F8 or Ctrl+Alt+V
        self.root.after(0, self._handle_hotkey_action)

    def _handle_hotkey_action(self):
        if self.engine.state in ("COUNTDOWN", "TYPING"):
            return
        self._update_config_values()
        self._reload_engine_content()
        # For hotkey, if user is already focused on their target window,
        # a smaller grace countdown (e.g. 0.5s) allows modifiers to release cleanly
        countdown = 0.5 if self.var_countdown.get() < 0.5 else self.var_countdown.get()
        self.engine.trigger_start(override_countdown=countdown)

    def _on_hotkey_stop(self):
        # Triggered via F9
        self.root.after(0, self.engine.stop)

    # ------------------ ENGINE CALLBACKS ------------------

    def _engine_status_changed(self, state: str, details: str):
        self.root.after(0, self._ui_apply_status, state, details)

    def _ui_apply_status(self, state: str, details: str):
        self.var_status_badge.set(state)
        self.var_status_detail.set(details)

        if state == "READY" or state == "IDLE":
            self.lbl_badge.config(bg=self.colors["badge_idle"], fg="#ffffff")
        elif state == "COUNTDOWN":
            self.lbl_badge.config(bg=self.colors["badge_countdown"], fg="#181825")
        elif state == "TYPING":
            self.lbl_badge.config(bg=self.colors["badge_typing"], fg="#181825")
        elif state == "STOPPED":
            self.lbl_badge.config(bg=self.colors["badge_stop"], fg="#181825")
        elif state == "ERROR":
            self.lbl_badge.config(bg="#e78284", fg="#181825")

    def _engine_progress(self, current_char: int, total_chars: int, current_elem: int, total_elems: int):
        self.root.after(0, self._ui_apply_progress, current_char, total_chars, current_elem, total_elems)

    def _ui_apply_progress(self, current_char: int, total_chars: int, current_elem: int, total_elems: int):
        pct = (current_char / max(1, total_chars)) * 100
        self.progress_bar["value"] = pct
        if total_elems > 1:
            self.lbl_queue_indicator.config(
                text=f"Element {current_elem}/{total_elems} ({current_char}/{total_chars} chars)"
            )
        else:
            self.lbl_queue_indicator.config(text=f"{current_char}/{total_chars} chars ({int(pct)}%)")

    def _engine_queue_updated(self, queue: list, queue_index: int):
        self.root.after(0, self._ui_apply_queue_update, queue, queue_index)

    def _ui_apply_queue_update(self, queue: list, queue_index: int):
        total = len(queue)
        if total > 1:
            display_idx = min(queue_index + 1, total)
            self.lbl_queue_indicator.config(text=f"Next: Element {display_idx} of {total}")
        else:
            self.lbl_queue_indicator.config(text=f"1 Element Loaded")

    def _engine_completed(self):
        self.root.after(0, lambda: self.progress_bar.configure(value=100))

    def _on_close(self):
        self.is_monitoring_clipboard = False
        self.hotkey_mgr.stop()
        self.engine.stop()
        self.root.destroy()
