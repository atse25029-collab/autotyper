"""
Low-level Windows keyboard simulation using SendInput with KEYEVENTF_UNICODE and hardware scan codes.
Provides reliable keystroke delivery for all characters (letters, numbers,
symbols, tabs, enters, and non-BMP unicode) without depending on keyboard layout
or modifier key states.
"""

import ctypes
from ctypes import wintypes
import time

# Win32 Constants
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001

VK_RETURN = 0x0D
VK_TAB = 0x09
VK_BACK = 0x08
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_SHIFT = 0x10
VK_HOME = 0x24
VK_END = 0x23
VK_DELETE = 0x2E

# Win32 Structures
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", _INPUT_UNION),
    ]

# Setup Windows API call
_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
_user32.SendInput.restype = wintypes.UINT
_user32.MapVirtualKeyW.argtypes = (wintypes.UINT, wintypes.UINT)
_user32.MapVirtualKeyW.restype = wintypes.UINT


def _send_input(inputs):
    """Send an array of INPUT structures to the operating system."""
    n = len(inputs)
    arr = (INPUT * n)(*inputs)
    sent = _user32.SendInput(n, arr, ctypes.sizeof(INPUT))
    return sent == n


def send_vk(vk_code: int, keyup: bool = False, is_extended: bool = False):
    """Send a virtual key press or release with accurate hardware scan code."""
    flags = KEYEVENTF_KEYUP if keyup else 0
    if is_extended:
        flags |= KEYEVENTF_EXTENDEDKEY

    # Populate hardware scan code so browser event listeners don't ignore the key
    scan = _user32.MapVirtualKeyW(vk_code, 0)

    inp = INPUT(type=INPUT_KEYBOARD)
    inp.u.ki = KEYBDINPUT(
        wVk=vk_code,
        wScan=scan,
        dwFlags=flags,
        time=0,
        dwExtraInfo=0
    )
    _send_input([inp])


def send_vk_tap(vk_code: int, hold_delay: float = 0.005, is_extended: bool = False):
    """Simulate pressing and releasing a virtual key."""
    send_vk(vk_code, keyup=False, is_extended=is_extended)
    if hold_delay > 0:
        time.sleep(hold_delay)
    send_vk(vk_code, keyup=True, is_extended=is_extended)


def clear_editor_line_indent(hold_delay: float = 0.005):
    """
    Cleans any auto-indentation inserted by Monaco/VS Code/Ace on a new line.
    Selects from current cursor back to column 0 (Shift + Home) and deletes it (Backspace).
    """
    # Shift Down
    send_vk(VK_SHIFT, keyup=False)
    time.sleep(hold_delay)

    # Home key twice to ensure reaching column 0
    send_vk_tap(VK_HOME, hold_delay=hold_delay, is_extended=True)
    time.sleep(hold_delay)
    send_vk_tap(VK_HOME, hold_delay=hold_delay, is_extended=True)
    time.sleep(hold_delay)

    # Shift Up
    send_vk(VK_SHIFT, keyup=True)
    time.sleep(hold_delay)

    # Delete the selected whitespace
    send_vk_tap(VK_BACK, hold_delay=hold_delay)
    time.sleep(hold_delay)


def send_unicode_char(ch: str, hold_delay: float = 0.002):
    """
    Send a character using KEYEVENTF_UNICODE.
    Handles BMP characters and surrogate pairs for supplementary unicode (e.g. emojis).
    """
    code = ord(ch)
    if code > 0xFFFF:
        # Surrogate pairs for non-BMP unicode
        encoded = ch.encode("utf-16le")
        surrogates = [encoded[i] | (encoded[i + 1] << 8) for i in range(0, len(encoded), 2)]
        inputs = []
        for s in surrogates:
            inp_down = INPUT(type=INPUT_KEYBOARD)
            inp_down.u.ki = KEYBDINPUT(0, s, KEYEVENTF_UNICODE, 0, 0)
            inp_up = INPUT(type=INPUT_KEYBOARD)
            inp_up.u.ki = KEYBDINPUT(0, s, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)
            inputs.extend([inp_down, inp_up])
        _send_input(inputs)
    else:
        inp_down = INPUT(type=INPUT_KEYBOARD)
        inp_down.u.ki = KEYBDINPUT(0, code, KEYEVENTF_UNICODE, 0, 0)
        inp_up = INPUT(type=INPUT_KEYBOARD)
        inp_up.u.ki = KEYBDINPUT(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)
        _send_input([inp_down])
        if hold_delay > 0:
            time.sleep(hold_delay)
        _send_input([inp_up])


def type_single_char(ch: str, hold_delay: float = 0.002):
    """
    Types a single character naturally:
    - '\r': ignored (carriage return)
    - '\n': sends VK_RETURN with hardware scan code
    - '\t': sends VK_TAB with hardware scan code
    - others: sends unicode character
    """
    if ch == "\r":
        return
    elif ch == "\n":
        send_vk_tap(VK_RETURN, hold_delay=hold_delay)
    elif ch == "\t":
        send_vk_tap(VK_TAB, hold_delay=hold_delay)
    else:
        send_unicode_char(ch, hold_delay=hold_delay)
