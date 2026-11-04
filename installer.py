"""
Standalone Windows Installer for AutoTyper.
Extracts AutoTyper.exe, creates Desktop and Start Menu shortcuts,
and sets up an uninstaller.
"""

import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).resolve().parent / relative_path


def create_shortcut(target_exe: str, shortcut_path: str, description: str = "AutoTyper"):
    """Create a Windows .lnk shortcut using PowerShell."""
    try:
        ps_cmd = f'$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut("{shortcut_path}"); $s.TargetPath = "{target_exe}"; $s.Description = "{description}"; $s.Save()'
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True, creationflags=0x08000000)
    except Exception as e:
        print(f"Error creating shortcut {shortcut_path}: {e}")


class InstallerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AutoTyper Setup")
        self.root.geometry("540x440")
        self.root.resizable(False, False)

        # Minimal Dark Theme
        self.colors = {
            "bg": "#121214",
            "surface": "#1a1a1e",
            "surface_alt": "#222227",
            "border": "#2e2e36",
            "text": "#e4e4e7",
            "text_muted": "#71717a",
            "accent": "#3b82f6",
            "btn_install": "#15803d",
            "btn_install_hover": "#16a34a",
        }
        self.root.configure(bg=self.colors["bg"])

        # Default Install Path: %LOCALAPPDATA%\Programs\AutoTyper
        local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        default_dir = os.path.join(local_app_data, "Programs", "AutoTyper")

        self.var_install_dir = tk.StringVar(value=default_dir)
        self.var_create_desktop = tk.BooleanVar(value=True)
        self.var_create_startmenu = tk.BooleanVar(value=True)
        self.var_launch_now = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        pad = tk.Frame(self.root, bg=self.colors["bg"], padx=24, pady=20)
        pad.pack(fill=tk.BOTH, expand=True)

        # Header
        lbl_title = tk.Label(
            pad,
            text="Install AutoTyper",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["text"],
            bg=self.colors["bg"]
        )
        lbl_title.pack(anchor="w", pady=(0, 4))

        lbl_desc = tk.Label(
            pad,
            text="Choose an installation location and options below.",
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["bg"]
        )
        lbl_desc.pack(anchor="w", pady=(0, 16))

        # Destination Card
        dest_card = tk.Frame(pad, bg=self.colors["surface"], padx=14, pady=12, highlightbackground=self.colors["border"], highlightthickness=1)
        dest_card.pack(fill=tk.X, pady=(0, 14))

        tk.Label(
            dest_card,
            text="Installation Folder",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["text"],
            bg=self.colors["surface"]
        ).pack(anchor="w", pady=(0, 6))

        browse_row = tk.Frame(dest_card, bg=self.colors["surface"])
        browse_row.pack(fill=tk.X)

        self.entry_dir = tk.Entry(
            browse_row,
            textvariable=self.var_install_dir,
            font=("Consolas", 9),
            bg=self.colors["surface_alt"],
            fg=self.colors["text"],
            insertbackground=self.colors["accent"],
            relief=tk.FLAT
        )
        self.entry_dir.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 8))

        btn_browse = tk.Button(
            browse_row,
            text="Browse...",
            command=self._browse_directory,
            font=("Segoe UI", 8),
            bg=self.colors["surface_alt"],
            fg=self.colors["text"],
            activebackground=self.colors["border"],
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=3
        )
        btn_browse.pack(side=tk.RIGHT)

        # Options Card
        opt_card = tk.Frame(pad, bg=self.colors["surface"], padx=14, pady=12, highlightbackground=self.colors["border"], highlightthickness=1)
        opt_card.pack(fill=tk.X, pady=(0, 14))

        tk.Label(
            opt_card,
            text="Shortcuts & Launch",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["text"],
            bg=self.colors["surface"]
        ).pack(anchor="w", pady=(0, 6))

        tk.Checkbutton(
            opt_card,
            text="Create Desktop Shortcut",
            variable=self.var_create_desktop,
            font=("Segoe UI", 9),
            fg=self.colors["text"],
            bg=self.colors["surface"],
            activebackground=self.colors["surface"],
            selectcolor=self.colors["surface_alt"]
        ).pack(anchor="w", pady=2)

        tk.Checkbutton(
            opt_card,
            text="Create Start Menu Shortcut",
            variable=self.var_create_startmenu,
            font=("Segoe UI", 9),
            fg=self.colors["text"],
            bg=self.colors["surface"],
            activebackground=self.colors["surface"],
            selectcolor=self.colors["surface_alt"]
        ).pack(anchor="w", pady=2)

        tk.Checkbutton(
            opt_card,
            text="Launch AutoTyper immediately after installation",
            variable=self.var_launch_now,
            font=("Segoe UI", 9),
            fg=self.colors["text"],
            bg=self.colors["surface"],
            activebackground=self.colors["surface"],
            selectcolor=self.colors["surface_alt"]
        ).pack(anchor="w", pady=2)

        # Progress / Status
        self.lbl_status = tk.Label(
            pad,
            text="",
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["bg"]
        )
        self.lbl_status.pack(anchor="w", pady=(0, 6))

        self.progress = ttk.Progressbar(pad, orient=tk.HORIZONTAL, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(0, 16))

        # Bottom Buttons
        btn_row = tk.Frame(pad, bg=self.colors["bg"])
        btn_row.pack(fill=tk.X)

        btn_cancel = tk.Button(
            btn_row,
            text="Cancel",
            command=self.root.destroy,
            font=("Segoe UI", 9),
            bg=self.colors["surface"],
            fg=self.colors["text"],
            activebackground=self.colors["surface_alt"],
            relief=tk.FLAT,
            padx=14,
            pady=6
        )
        btn_cancel.pack(side=tk.RIGHT)

        self.btn_install = tk.Button(
            btn_row,
            text="Install Now",
            command=self._perform_installation,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["btn_install"],
            fg="#ffffff",
            activebackground=self.colors["btn_install_hover"],
            relief=tk.FLAT,
            padx=18,
            pady=6
        )
        self.btn_install.pack(side=tk.RIGHT, padx=(0, 8))

    def _browse_directory(self):
        chosen = filedialog.askdirectory(initialdir=self.var_install_dir.get(), title="Select Install Directory")
        if chosen:
            # Append AutoTyper folder if not already specified
            if not chosen.lower().endswith("autotyper"):
                chosen = os.path.join(chosen, "AutoTyper")
            self.var_install_dir.set(chosen)

    def _perform_installation(self):
        target_dir = Path(self.var_install_dir.get().strip())
        if not target_dir:
            messagebox.showerror("Error", "Please provide a valid destination folder.")
            return

        self.btn_install.config(state=tk.DISABLED)
        self.lbl_status.config(text="Installing...")
        self.progress["value"] = 20

        try:
            # 1. Locate source AutoTyper.exe
            bundled_exe = get_resource_path("AutoTyper.exe")
            if not bundled_exe.exists():
                # Dev fallback: check in dist/
                bundled_exe = Path(__file__).resolve().parent / "dist" / "AutoTyper.exe"

            if not bundled_exe.exists():
                messagebox.showerror("Error", f"AutoTyper.exe payload not found at {bundled_exe}")
                self.btn_install.config(state=tk.NORMAL)
                return

            # 2. Create Target Directory
            target_dir.mkdir(parents=True, exist_ok=True)
            installed_exe = target_dir / "AutoTyper.exe"
            self.progress["value"] = 50

            # 3. Copy executable
            shutil.copy2(bundled_exe, installed_exe)
            self.progress["value"] = 70

            # 4. Generate Uninstaller
            uninstaller_bat = target_dir / "uninstall.bat"
            desktop = Path.home() / "Desktop"
            start_menu = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            desktop_lnk = desktop / "AutoTyper.lnk"
            startmenu_lnk = start_menu / "AutoTyper.lnk"

            uninstall_script = f"""@echo off
echo Uninstalling AutoTyper...
if exist "{desktop_lnk}" del /f /q "{desktop_lnk}"
if exist "{startmenu_lnk}" del /f /q "{startmenu_lnk}"
timeout /t 1 /nobreak >nul
del /f /q "{installed_exe}"
del /f /q "%~f0"
echo AutoTyper has been uninstalled.
pause
"""
            uninstaller_bat.write_text(uninstall_script, encoding="utf-8")

            # 5. Create Shortcuts
            if self.var_create_desktop.get():
                create_shortcut(str(installed_exe), str(desktop_lnk), "AutoTyper Keystroke Simulator")

            if self.var_create_startmenu.get():
                create_shortcut(str(installed_exe), str(startmenu_lnk), "AutoTyper Keystroke Simulator")

            self.progress["value"] = 100
            self.lbl_status.config(text="Installation Complete!")

            # 6. Launch if requested
            if self.var_launch_now.get():
                subprocess.Popen([str(installed_exe)], cwd=str(target_dir))

            messagebox.showinfo("Success", f"AutoTyper successfully installed to:\n{target_dir}")
            self.root.destroy()

        except Exception as e:
            messagebox.showerror("Installation Error", f"Failed to complete installation: {e}")
            self.btn_install.config(state=tk.NORMAL)


def main():
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
