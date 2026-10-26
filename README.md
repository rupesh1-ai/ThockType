# ThockType

A lightweight Windows desktop app that plays synthesized mechanical-keyboard sounds when you press keys. It includes Creamy, Deep Thock, Clicky, and Soft Linear profiles, a volume slider, preview button, start/stop controls, and an optional Windows sign-in startup setting.

## Features

- Global keypress sound simulation while enabled
- Four synthesized sound profiles (no external sound downloads required)
- Adjustable volume and one-click sound preview
- Optional launch-on-sign-in setting for the current Windows user
- Dark desktop interface built with PySide6
- No typing content is stored, logged, or transmitted

## Requirements

- Windows 10/11 (Windows 11 recommended)
- Python 3.10 or newer, 64-bit
- Speakers or headphones

## Run from source

1. Install Python from https://www.python.org/downloads/windows/. During installation, enable **Add python.exe to PATH**.
2. Download or clone this repository.
3. Open PowerShell in the project folder.
4. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt instead:

   ```bat
   .venv\Scripts\activate.bat
   ```

5. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. Start the app:

   ```powershell
   python main.py
   ```

7. Choose a sound profile, adjust volume, and click **Start typing sounds**. Test in Notepad.

## Build a standalone Windows executable

From an activated virtual environment:

```powershell
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name ThockType --add-data "sounds;sounds" main.py
```

The executable will be created at `dist\ThockType\ThockType.exe` (PyInstaller's default output is a folder because this command does not use `--onefile`). Share the full `dist\ThockType` folder, or create a zip of that folder.

## Push to a new GitHub repository

First create an **empty** repository named `ThockType` at https://github.com/new. Do not initialize it with a README, license, or `.gitignore`, because this project already contains those files.

Then run these commands in PowerShell from the project folder, replacing `YOUR_GITHUB_USERNAME` with your GitHub username:

```powershell
git init
git add .
git commit -m "Initial commit: ThockType desktop app"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/ThockType.git
git push -u origin main
```

If Git asks you to sign in, complete the browser authentication flow. Never put a password or personal access token directly into source code.

## Privacy and limitations

ThockType uses a global keyboard listener only to trigger sound playback. It does not capture text into a file, clipboard, or network request. Because it reacts to keypresses globally, sound can also play while typing into password fields; disable the app when you do not want sound feedback.

This app simulates audio only. It cannot change the physical feel of a membrane keyboard. Some managed, remote-desktop, or elevated applications may handle global keyboard hooks differently. Use only on devices where you are allowed to run keyboard-listener software.

## Troubleshooting

- **No sound:** Use the Preview button, check Windows output device/volume, and confirm the app's volume slider is above 0.
- **No typing sounds:** Click Start typing sounds. Try typing in Notepad. Check whether security software is blocking global keyboard hooks.
- **Dependency errors:** Activate `.venv` and rerun `python -m pip install -r requirements.txt`.
- **Startup checkbox:** It changes the current Windows user's Run registry key. Uncheck it to remove the startup entry.
