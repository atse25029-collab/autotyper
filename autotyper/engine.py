"""
AutoTyper Engine: Coordinates typing execution, delays, jitter,
multi-element queues, auto-indent handling, and emergency stops.
"""

import time
import random
import threading
import winsound
from dataclasses import dataclass, field
from typing import List, Callable, Optional
from autotyper.win_keyboard import type_single_char, send_vk_tap, VK_TAB


@dataclass
class AutoTypeConfig:
    char_delay_ms: float = 20.0          # Delay between keystrokes in milliseconds
    jitter_percent: float = 25.0         # Random variation in delay (+/- %)
    countdown_seconds: float = 3.0       # Delay before typing begins
    play_sound: bool = True              # Audible feedback
    auto_indent_mode: str = "raw"        # "raw" or "strip_indent"
    element_mode: str = "single"         # "single", "queue_step", or "auto_tab"
    element_delimiter: str = "\n\n"      # Delimiter for multi-element splitting
    auto_tab_delay_ms: float = 300.0     # Pause between auto-tabbed elements


class AutoTypeEngine:
    def __init__(self, config: Optional[AutoTypeConfig] = None):
        self.config = config or AutoTypeConfig()
        self.queue: List[str] = []
        self.queue_index: int = 0
        self.state: str = "IDLE"  # "IDLE", "COUNTDOWN", "TYPING", "STOPPED"
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Callbacks for UI updates
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
        """Parse text into elements according to delimiter and update the queue."""
        with self._lock:
            delim = delimiter if delimiter is not None else self.config.element_delimiter
            if self.config.element_mode in ("queue_step", "auto_tab") and delim:
                # Split content into distinct elements
                raw_parts = text.split(delim)
                # Keep elements clean but don't discard empty unless all are empty
                self.queue = [p for p in raw_parts if p.strip()] or [text]
            else:
                self.queue = [text] if text else []
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
        """Start the typing process in a separate background thread."""
        with self._lock:
            if self.state in ("COUNTDOWN", "TYPING"):
                return  # Already running

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
        """Immediately aborts any ongoing countdown or typing."""
        self._stop_event.set()
        self._notify_status("STOPPED", "Emergency stop triggered")
        self._play_beep("stop")

    def _run_typing_flow(self, countdown_sec: float, single_next: bool):
        # 1. Countdown Phase
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

        # 2. Typing Phase
        try:
            if single_next or self.config.element_mode == "queue_step":
                # Type only the current element from the queue
                if self.queue_index < len(self.queue):
                    element = self.queue[self.queue_index]
                    self._type_element_text(element, self.queue_index + 1, len(self.queue))
                    with self._lock:
                        self.queue_index += 1
                    if self.on_queue_updated:
                        self.on_queue_updated(self.queue, self.queue_index)
            elif self.config.element_mode == "auto_tab":
                # Type all elements sequentially with Tab in between
                total_elems = len(self.queue)
                for idx in range(self.queue_index, total_elems):
                    if self._stop_event.is_set():
                        break
                    element = self.queue[idx]
                    self._type_element_text(element, idx + 1, total_elems)
                    with self._lock:
                        self.queue_index = idx + 1
                    if self.on_queue_updated:
                        self.on_queue_updated(self.queue, self.queue_index)

                    # If not the last element, press TAB to navigate to next input field
                    if idx < total_elems - 1 and not self._stop_event.is_set():
                        time.sleep(self.config.auto_tab_delay_ms / 1000.0)
                        send_vk_tap(VK_TAB)
                        time.sleep(0.1)
            else:
                # "single" mode: Type entire first element
                element = self.queue[0] if self.queue else ""
                self._type_element_text(element, 1, 1)

            if not self._stop_event.is_set():
                self._notify_status("IDLE", "Typing completed successfully!")
                self._play_beep("complete")
                if self.on_complete:
                    self.on_complete()
            else:
                self._notify_status("STOPPED", "Typing halted by user")
        except Exception as e:
            self._notify_status("ERROR", f"Typing error: {e}")

    def _type_element_text(self, text: str, elem_num: int, total_elems: int):
        # Format text if auto-indent handling is activated
        if self.config.auto_indent_mode == "strip_indent":
            # For code editors that automatically indent subsequent lines:
            # Strip leading whitespace on lines after the first
            lines = text.splitlines(keepends=True)
            formatted_lines = []
            for i, line in enumerate(lines):
                if i == 0:
                    formatted_lines.append(line)
                else:
                    # Strip leading spaces/tabs on subsequent lines
                    formatted_lines.append(line.lstrip(" \t"))
            text = "".join(formatted_lines)

        total_chars = len(text)
        base_delay = self.config.char_delay_ms / 1000.0
        jitter = self.config.jitter_percent / 100.0

        for i, ch in enumerate(text):
            if self._stop_event.is_set():
                break

            # Send the keystroke
            type_single_char(ch)

            # Report progress
            if self.on_progress and (i % 5 == 0 or i == total_chars - 1):
                self.on_progress(i + 1, total_chars, elem_num, total_elems)

            # Apply delay with natural jitter
            if base_delay > 0:
                if jitter > 0:
                    variation = random.uniform(-jitter, jitter)
                    delay = max(0.001, base_delay * (1.0 + variation))
                else:
                    delay = base_delay

                # Extra realistic pause after punctuation or newlines
                if ch in ("\n", ". ", ";\n", "}\n"):
                    delay += base_delay * 1.5

                time.sleep(delay)
