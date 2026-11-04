"""
AutoTyper Engine: Coordinates typing execution, delays, jitter,
intelligent Python/Monaco indentation tracking, and emergency stops.
"""

import time
import random
import threading
import winsound
from dataclasses import dataclass
from typing import List, Callable, Optional
from autotyper.win_keyboard import (
    type_single_char,
    send_vk_tap,
    VK_RETURN,
    VK_TAB,
    VK_BACK,
    VK_ESCAPE,
)


@dataclass
class AutoTypeConfig:
    char_delay_ms: float = 16.0          # Delay between keystrokes in milliseconds
    jitter_percent: float = 15.0         # Random variation in delay (+/- %)
    countdown_seconds: float = 3.0       # Delay before typing begins
    play_sound: bool = True              # Audible feedback
    indent_mode: str = "smart_python"    # "smart_python" (Monaco-aware) or "raw"
    line_pause_ms: float = 25.0          # Pause after newline
    element_mode: str = "single"         # "single", "queue_step", or "auto_tab"
    element_delimiter: str = "\n\n"      # Delimiter for multi-element splitting
    auto_tab_delay_ms: float = 300.0     # Pause between auto-tabbed elements


class AutoTypeEngine:
    def __init__(self, config: Optional[AutoTypeConfig] = None):
        self.config = config or AutoTypeConfig()
        self.queue: List[str] = []
        self.queue_index: int = 0
        self.state: str = "IDLE"
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Callbacks
        self.on_status_change: Optional[Callable[[str, str], None]] = None
        self.on_progress: Optional[Callable[[int, int, int, int], None]] = None
        self.on_complete: Optional[Callable[[], None]] = None
        self.on_queue_updated: Optional[Callable[[List[str], int], None]] = None

    def _notify_status(self, state: str, details: str = ""):
        self.state = state
        if self.on_status_change:
            self.on_status_change(state, details)

    def _play_beep(self, sound_type: str):
        if not self.config.play_sound:
            return
        try:
            if sound_type == "start":
                winsound.Beep(900, 120)
            elif sound_type == "countdown":
                winsound.Beep(700, 80)
            elif sound_type == "complete":
                winsound.Beep(1200, 150)
            elif sound_type == "stop":
                winsound.Beep(450, 180)
        except Exception:
            pass

    def load_content(self, text: str, delimiter: Optional[str] = None):
        with self._lock:
            delim = delimiter if delimiter is not None else self.config.element_delimiter
            clean_text = text.replace("\r\n", "\n").replace("\r", "\n")
            if self.config.element_mode in ("queue_step", "auto_tab") and delim:
                delim_norm = delim.replace("\r\n", "\n").replace("\r", "\n")
                raw_parts = clean_text.split(delim_norm)
                self.queue = [p for p in raw_parts if p.strip()] or [clean_text]
            else:
                self.queue = [clean_text] if clean_text else []
            self.queue_index = 0

        if self.on_queue_updated:
            self.on_queue_updated(self.queue, self.queue_index)

    def set_queue_index(self, index: int):
        with self._lock:
            if 0 <= index < len(self.queue):
                self.queue_index = index
        if self.on_queue_updated:
            self.on_queue_updated(self.queue, self.queue_index)

    def trigger_start(self, override_countdown: Optional[float] = None, single_next: bool = False):
        with self._lock:
            if self.state in ("COUNTDOWN", "TYPING"):
                return

            if not self.queue:
                self._notify_status("IDLE", "Nothing to type (clipboard empty)")
                return

            self._stop_event.clear()
            cd = override_countdown if override_countdown is not None else self.config.countdown_seconds
            self._worker_thread = threading.Thread(
                target=self._run_typing_flow,
                args=(cd, single_next),
                daemon=True
            )
            self._worker_thread.start()

    def stop(self):
        self._stop_event.set()
        self._notify_status("STOPPED", "Emergency stop triggered")
        self._play_beep("stop")

    def _run_typing_flow(self, countdown_sec: float, single_next: bool):
        if countdown_sec > 0:
            self._notify_status("COUNTDOWN", f"Starting in {countdown_sec:.1f}s... Switch to portal!")
            remaining = countdown_sec
            step = 0.1
            last_beep = int(remaining)
            while remaining > 0:
                if self._stop_event.is_set():
                    self._notify_status("STOPPED", "Cancelled during countdown")
                    return
                time.sleep(min(step, remaining))
                remaining -= step

                curr_int = int(remaining)
                if curr_int != last_beep and curr_int > 0:
                    self._play_beep("countdown")
                    last_beep = curr_int
                    self._notify_status("COUNTDOWN", f"Starting in {curr_int}s...")

        if self._stop_event.is_set():
            return

        self._play_beep("start")
        self._notify_status("TYPING", "Autotyping in progress...")

        try:
            if single_next or self.config.element_mode == "queue_step":
                if self.queue_index < len(self.queue):
                    element = self.queue[self.queue_index]
                    self._type_element_content(element, self.queue_index + 1, len(self.queue))
                    with self._lock:
                        self.queue_index += 1
                    if self.on_queue_updated:
                        self.on_queue_updated(self.queue, self.queue_index)
            elif self.config.element_mode == "auto_tab":
                total_elems = len(self.queue)
                for idx in range(self.queue_index, total_elems):
                    if self._stop_event.is_set():
                        break
                    element = self.queue[idx]
                    self._type_element_content(element, idx + 1, total_elems)
                    with self._lock:
                        self.queue_index = idx + 1
                    if self.on_queue_updated:
                        self.on_queue_updated(self.queue, self.queue_index)

                    if idx < total_elems - 1 and not self._stop_event.is_set():
                        time.sleep(self.config.auto_tab_delay_ms / 1000.0)
                        send_vk_tap(VK_TAB)
                        time.sleep(0.1)
            else:
                element = self.queue[0] if self.queue else ""
                self._type_element_content(element, 1, 1)

            if not self._stop_event.is_set():
                self._notify_status("IDLE", "Typing completed successfully!")
                self._play_beep("complete")
                if self.on_complete:
                    self.on_complete()
            else:
                self._notify_status("STOPPED", "Typing halted by user")
        except Exception as e:
            self._notify_status("ERROR", f"Typing error: {e}")

    def _type_element_content(self, text: str, elem_num: int, total_elems: int):
        total_chars = len(text)
        base_delay = self.config.char_delay_ms / 1000.0
        jitter = self.config.jitter_percent / 100.0
        char_count = 0

        if self.config.indent_mode == "smart_python":
            # Smart Monaco / Python Indentation Engine
            lines = text.split("\n")
            predicted_editor_indent = 0

            for line_idx, line in enumerate(lines):
                if self._stop_event.is_set():
                    break

                raw_line = line.replace("\t", "    ")
                content = raw_line.lstrip(" ")
                target_indent = len(raw_line) - len(content)

                if line_idx > 0:
                    # Send Escape to close any lingering autocomplete dropdown
                    send_vk_tap(VK_ESCAPE)
                    time.sleep(0.005)
                    # Create new line
                    send_vk_tap(VK_RETURN)
                    char_count += 1
                    time.sleep(max(0.015, self.config.line_pause_ms / 1000.0))

                # Handle Blank Line
                if not content:
                    if self.on_progress:
                        self.on_progress(char_count, total_chars, elem_num, total_elems)
                    continue

                # Calculate indentation difference
                if line_idx == 0:
                    # First line: type whatever leading spaces were requested
                    if target_indent > 0:
                        for _ in range(target_indent):
                            type_single_char(" ")
                            char_count += 1
                    predicted_editor_indent = target_indent
                else:
                    diff = target_indent - predicted_editor_indent
                    if diff > 0:
                        # Editor is indented less than target; type the remaining spaces
                        for _ in range(diff):
                            type_single_char(" ")
                            char_count += 1
                            time.sleep(0.005)
                    elif diff < 0:
                        # Editor is indented more than target; unindent using Backspace
                        # In Monaco / VS Code, 1 Backspace removes 1 indentation level (up to 4 spaces)
                        backspaces = max(1, (abs(diff) + 3) // 4)
                        for _ in range(backspaces):
                            send_vk_tap(VK_BACK)
                            time.sleep(0.005)

                # Dismiss any autocomplete popup that might have triggered
                send_vk_tap(VK_ESCAPE)

                # Type line characters
                for ch in content:
                    if self._stop_event.is_set():
                        break

                    type_single_char(ch)
                    char_count += 1

                    if self.on_progress and (char_count % 5 == 0 or char_count == total_chars):
                        self.on_progress(char_count, total_chars, elem_num, total_elems)

                    if base_delay > 0:
                        if jitter > 0:
                            variation = random.uniform(-jitter, jitter)
                            delay = max(0.001, base_delay * (1.0 + variation))
                        else:
                            delay = base_delay
                        time.sleep(delay)

                # Update predicted editor indent for next line
                # In Python mode, Monaco adds 4 spaces if the line ends with a colon ':'
                ends_with_colon = content.rstrip().endswith(":")
                predicted_editor_indent = target_indent + (4 if ends_with_colon else 0)

        else:
            # Raw mode
            for i, ch in enumerate(text):
                if self._stop_event.is_set():
                    break

                type_single_char(ch)

                if self.on_progress and (i % 5 == 0 or i == total_chars - 1):
                    self.on_progress(i + 1, total_chars, elem_num, total_elems)

                if base_delay > 0:
                    if jitter > 0:
                        variation = random.uniform(-jitter, jitter)
                        delay = max(0.001, base_delay * (1.0 + variation))
                    else:
                        delay = base_delay

                    if ch == "\n":
                        delay += max(0.015, self.config.line_pause_ms / 1000.0)

                    time.sleep(delay)
