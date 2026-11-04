# AutoTyper Pro ⚡
> **Hardware-Level Keystroke Simulator for Restricted Online Portals**

AutoTyper Pro is a Windows desktop application engineered to bypass web portals, exam engines, and coding platforms (such as Mercer Mettl, HackerEarth, HackerRank, Cocubes, Examly, Canvas, etc.) that disable pasting (`Ctrl+V`, right-click context menu, or clipboard API interception).

Instead of pasting into the DOM, **AutoTyper Pro generates genuine Windows hardware keyboard events (`SendInput`)** with full Unicode support. To the browser and operating system, the text appears as if you are physically typing it on your keyboard.

---

## 🌟 Key Features

- **🛡️ Hardware-Level Simulation**:
  - Uses Windows Win32 `SendInput` with `KEYEVENTF_UNICODE`.
  - Supports all special characters (`{}`, `()`, `[]`, quotes, colons, semicolons, emojis, tabs, enters) without layout dependency or Shift/Caps-lock glitches.

- **📑 Multi-Element & Form Automation ("For Each Element")**:
  - **Single Mode**: Types the current clipboard content directly into the active field.
  - **Step-by-Step Queue Mode**: Splits multi-part answers or answers for multiple questions by a delimiter (e.g. blank lines `\n\n`, lines `\n`, or `---`). Each press of `F8` types the **next** element!
  - **Auto-Tab Form Mode**: Automatically types an element, sends a `Tab` keystroke to advance to the next field, and types the next element.

- **🎯 College Code Editor Protection**:
  - **Smart Indentation Compensation**: Coding portals automatically indent new lines. When enabled, AutoTyper trims duplicated leading whitespace on subsequent lines so code is not double-indented.

- **⚡ Adjustable Speed & Human Jitter**:
  - **Delay Slider**: 0 ms (instant turbo) up to 100 ms per character (default ~20 ms / 60 WPM).
  - **Human Typing Jitter**: Adds natural, organic variance (±25%) so keystroke timing is indistinguishable from human typing.

- **⌨️ Global Hotkeys**:
  - `F8` or `Ctrl + Alt + V`: Trigger autotype (works even when the portal or browser is focused).
  - `F9`: Emergency Stop / Killswitch (aborts typing immediately).

- **🔔 User Experience & Audio Feedback**:
  - **Countdown Timer**: 3-second countdown giving you ample time to focus the portal input box.
  - **Audio Beeps**: Gentle pitch cues for countdown ticks, typing start, completion, and abort.
  - **Live Clipboard Monitor**: Automatically syncs your copied text (`Ctrl+C`) in real-time.
  - **Always on Top**: Pin the tool in a screen corner to monitor progress while interacting with your browser.
  - **Built-in Test Scratchpad**: Test typing speed and hotkeys directly within the app before opening your exam.

---

## 🚀 Quick Start

### 1. One-Click Launch (Recommended)
Simply double-click:
```bat
run.bat
```
`run.bat` automatically verifies Python, creates a virtual environment, installs dependencies, and launches the app.

### 2. Manual Setup
```powershell
# Create & activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run AutoTyper
python main.py
```

---

## 📖 How to Use for College Portals

1. **Launch AutoTyper Pro** (keep it open or minimized).
2. **Copy your code/text** as you normally do (`Ctrl + C`).
   - AutoTyper immediately updates with the copied text and shows character/line counts.
3. **Switch to your college portal** and click inside the target input box or code editor.
4. **Press `F8`** (or `Ctrl + Alt + V`):
   - You will hear a short countdown (default 3 seconds).
   - AutoTyper will simulate physical keystrokes directly into your portal!
5. **Press `F9` at any time** if you need to abort typing immediately.

---

## 🛠️ Multi-Element Example

If an online form has 3 separate input fields:
1. Copy all 3 answers separated by a blank line or `---`:
   ```text
   Answer for Field 1

   Answer for Field 2

   Answer for Field 3
   ```
2. In AutoTyper Pro, select **Step-by-Step** or **Auto-Tab** mode.
3. With **Step-by-Step**, focus Field 1 and press `F8` -> it types Answer 1. Click Field 2 and press `F8` -> it types Answer 2!

---

## 🧪 Testing

Run the test suite at any time:
```powershell
.\venv\Scripts\python.exe -m unittest discover tests
```
