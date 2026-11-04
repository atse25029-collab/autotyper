"""
Global Hotkey Manager using pynput.
Allows triggering autotype or emergency stops even when the application
is in the background and the college portal has active focus.
"""

import threading
from typing import Callable, Optional
from pynput import keyboard


class HotkeyManager:
    def __init__(
        self,
        on_trigger: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        trigger_hotkey: str = "<f8>",
        stop_hotkey: str = "<f9>",
        alt_trigger_hotkey: str = "<ctrl>+<alt>+v",
    ):
        self.on_trigger = on_trigger
        self.on_stop = on_stop
        self.trigger_hotkey = trigger_hotkey
        self.stop_hotkey = stop_hotkey
        self.alt_trigger_hotkey = alt_trigger_hotkey

        self._listener: Optional[keyboard.GlobalHotKeys] = None
        self._running = False
        self._lock = threading.Lock()

    def _handle_trigger(self):
        if self.on_trigger:
            # Dispatch in separate thread so we never block pynput's hook
            threading.Thread(target=self.on_trigger, daemon=True).start()

    def _handle_stop(self):
        if self.on_stop:
            threading.Thread(target=self.on_stop, daemon=True).start()

    def start(self):
        with self._lock:
            if self._running:
                return

            bindings = {}
            if self.trigger_hotkey:
                bindings[self.trigger_hotkey] = self._handle_trigger
            if self.alt_trigger_hotkey:
                bindings[self.alt_trigger_hotkey] = self._handle_trigger
            if self.stop_hotkey:
                bindings[self.stop_hotkey] = self._handle_stop

            try:
                self._listener = keyboard.GlobalHotKeys(bindings)
                self._listener.start()
                self._running = True
            except Exception as e:
                print(f"Error starting global hotkey listener: {e}")

    def stop(self):
        with self._lock:
            if not self._running:
                return
            if self._listener:
                self._listener.stop()
                self._listener = None
            self._running = False

    def update_hotkeys(self, trigger: str, stop: str, alt_trigger: str = ""):
        self.stop()
        self.trigger_hotkey = trigger
        self.stop_hotkey = stop
        self.alt_trigger_hotkey = alt_trigger
        self.start()
