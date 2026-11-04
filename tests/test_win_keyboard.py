"""
Unit tests for win_keyboard Win32 structs and constants.
"""

import unittest
import ctypes
from autotyper.win_keyboard import (
    INPUT,
    KEYBDINPUT,
    MOUSEINPUT,
    HARDWAREINPUT,
    INPUT_KEYBOARD,
    KEYEVENTF_UNICODE,
    KEYEVENTF_KEYUP,
    VK_RETURN,
    VK_TAB
)


class TestWinKeyboard(unittest.TestCase):
    def test_input_size(self):
        # On 64-bit Windows, sizeof(INPUT) must strictly be 40 bytes
        self.assertEqual(ctypes.sizeof(INPUT), 40)

    def test_structure_instantiation(self):
        inp = INPUT(type=INPUT_KEYBOARD)
        inp.u.ki = KEYBDINPUT(
            wVk=VK_RETURN,
            wScan=0,
            dwFlags=0,
            time=0,
            dwExtraInfo=0
        )
        self.assertEqual(inp.type, 1)
        self.assertEqual(inp.u.ki.wVk, 0x0D)

    def test_unicode_flags(self):
        self.assertEqual(KEYEVENTF_UNICODE, 0x0004)
        self.assertEqual(KEYEVENTF_KEYUP, 0x0002)


if __name__ == "__main__":
    unittest.main()
