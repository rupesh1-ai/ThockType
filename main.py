import sys
import os
import wave
import math
import struct
import tempfile
from pathlib import Path

import pygame
from pynput import keyboard
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QSlider, QVBoxLayout, QWidget
)

APP_NAME = "ThockType"
SOUND_NAMES = {
    "Creamy": "creamy.wav",
    "Deep Thock": "thock.wav",
    "Clicky": "clicky.wav",
    "Soft Linear": "linear.wav",
}
MODIFIER_KEYS = {
    keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r,
    keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
    keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
    keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r,
    keyboard.Key.caps_lock, keyboard.Key.num_lock, keyboard.Key.scroll_lock,
}

def resource_path(relative):
    """Resolve bundled resources both in source runs and PyInstaller builds."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / relative

def ensure_sound_assets():
    """Create short synthesized samples if sound files are missing."""
    sound_dir = resource_path("sounds")
    sound_dir.mkdir(parents=True, exist_ok=True)
    specs = {
        "creamy.wav": (0.105, 125, 0.16, 0.32),
        "thock.wav": (0.145, 82, 0.22, 0.48),
        "clicky.wav": (0.070, 185, 0.25, 0.18),
        "linear.wav": (0.085, 145, 0.10, 0.24),
    }
    rate = 44100
    for filename, (duration, freq, noise_mix, decay) in specs.items():
        path = sound_dir / filename
        # Always regenerate these profile samples so stale/identical WAV files
        # from an earlier build cannot make every profile sound the same.
        count = int(rate * duration)
        frames = bytearray()
        # Deterministic noise: no external audio files or network needed.
        seed = 7123
        for i in range(count):
            t = i / rate
            envelope = math.exp(-t / (duration * (0.28 + decay)))
            seed = (1103515245 * seed + 12345) & 0x7fffffff
            noise = ((seed / 0x7fffffff) * 2.0) - 1.0
            tone = math.sin(2 * math.pi * freq * t) * (1.0 - noise_mix)
            # A brief bright transient gives each profile a distinct attack.
            transient = math.sin(2 * math.pi * (freq * 3.3) * t) * math.exp(-t / 0.006) * 0.22
            sample = max(-1.0, min(1.0, (tone + noise * noise_mix * 0.35 + transient) * envelope))
            frames.extend(struct.pack("<h", int(sample * 26000)))
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            wav.writeframes(frames)

class ThockTypeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ThockType")
        self.setMinimumSize(570, 520)
        self.setMaximumWidth(760)
        self.listener = None
        self.enabled = False
        self.sounds = {}
        self.sound_dir = resource_path("sounds")
        ensure_sound_assets()

        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=256)
            for label, filename in SOUND_NAMES.items():
                self.sounds[label] = pygame.mixer.Sound(str(self.sound_dir / filename))
        except Exception as exc:
            QMessageBox.critical(
                self, "Audio initialization failed",
                "ThockType couldn't initialize audio playback.\n\n"
                f"Details: {exc}\n\nCheck that your Windows audio output is available."
            )

        self._build_ui()
        self.set_profile(self.profile_combo.currentText())
        self.set_volume(self.volume_slider.value())
        self.update_status(False)

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(30, 26, 30, 26)
        root.setSpacing(16)

        logo = QLabel("THOCKTYPE")
        logo.setObjectName("logo")
        logo.setFont(QFont("Segoe UI", 24, QFont.Bold))
        root.addWidget(logo)

        subtitle = QLabel("Mechanical keyboard sounds for your everyday keyboard")
        subtitle.setObjectName("subtitle")
        root.addWidget(subtitle)

        hero = QFrame()
        hero.setObjectName("hero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(20, 18, 20, 18)
        hero_layout.setSpacing(10)
        self.status_title = QLabel("Typing sounds are off")
        self.status_title.setObjectName("statusTitle")
        self.status_detail = QLabel("Turn sounds on, then type in any app.")
        self.status_detail.setObjectName("subtitle")
        hero_layout.addWidget(self.status_title)
        hero_layout.addWidget(self.status_detail)
        root.addWidget(hero)

        profile_label = QLabel("SOUND PROFILE")
        profile_label.setObjectName("fieldLabel")
        root.addWidget(profile_label)
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(list(SOUND_NAMES.keys()))
        self.profile_combo.setMinimumHeight(42)
        self.profile_combo.currentTextChanged.connect(self.set_profile)
        root.addWidget(self.profile_combo)

        volume_row = QHBoxLayout()
        volume_label = QLabel("Volume")
        volume_label.setObjectName("fieldLabel")
        self.volume_value = QLabel("35%")
        self.volume_value.setObjectName("volumeValue")
        volume_row.addWidget(volume_label)
        volume_row.addStretch()
        volume_row.addWidget(self.volume_value)
        root.addLayout(volume_row)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(35)
        self.volume_slider.valueChanged.connect(self.set_volume)
        root.addWidget(self.volume_slider)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        self.toggle_button = QPushButton("▶  Start typing sounds")
        self.toggle_button.setObjectName("primary")
        self.toggle_button.setMinimumHeight(48)
        self.toggle_button.clicked.connect(self.toggle_listening)
        button_row.addWidget(self.toggle_button, 2)

        preview_button = QPushButton("▶  Preview")
        preview_button.setMinimumHeight(48)
        preview_button.clicked.connect(self.preview_sound)
        button_row.addWidget(preview_button, 1)
        root.addLayout(button_row)

        self.startup_checkbox = QCheckBox("Launch ThockType when I sign in to Windows")
        self.startup_checkbox.stateChanged.connect(self.set_startup)
        root.addWidget(self.startup_checkbox)

        note = QLabel(
            "Privacy: key presses are detected only to trigger sound. "
            "ThockType does not save, log, or transmit what you type."
        )
        note.setObjectName("note")
        note.setWordWrap(True)
        root.addWidget(note)

        footer = QLabel("ThockType • Local audio • No account required")
        footer.setObjectName("footer")
        root.addStretch()
        root.addWidget(footer)

        self.setStyleSheet("""
            QWidget#central { background: #111318; color: #f4f5f7; }
            QLabel#logo { color: #f5f6f8; letter-spacing: 2px; }
            QLabel#subtitle { color: #a5aab5; font-size: 12px; }
            QFrame#hero { background: #1c2028; border: 1px solid #2b303b; border-radius: 14px; }
            QLabel#statusTitle { font-size: 18px; font-weight: 600; }
            QLabel#fieldLabel { color: #c7cbd4; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
            QLabel#volumeValue { color: #c6a8ff; font-weight: 600; }
            QComboBox { background: #1c2028; border: 1px solid #353b48; border-radius: 9px; padding: 9px 12px; }
            QComboBox QAbstractItemView { background: #1c2028; selection-background-color: #6f4cc3; }
            QSlider::groove:horizontal { height: 6px; background: #343946; border-radius: 3px; }
            QSlider::sub-page:horizontal { background: #9b7bff; border-radius: 3px; }
            QSlider::handle:horizontal { background: #f4f0ff; width: 16px; margin: -5px 0; border-radius: 8px; }
            QPushButton { background: #272c36; border: 1px solid #3b414e; border-radius: 10px; padding: 10px; font-weight: 600; }
            QPushButton:hover { background: #343a47; }
            QPushButton#primary { background: #8661e9; border: none; color: white; }
            QPushButton#primary:hover { background: #9878f0; }
            QCheckBox { color: #d6d9e0; spacing: 8px; }
            QCheckBox::indicator { width: 16px; height: 16px; }
            QLabel#note { background: #191d24; color: #9ca3b2; border-radius: 9px; padding: 12px; font-size: 11px; }
            QLabel#footer { color: #737b8a; font-size: 10px; }
        """)

    def set_profile(self, profile):
        self.current_profile = profile
        self.current_sound = self.sounds.get(profile)
        if self.current_sound:
            self.current_sound.set_volume(self.volume_slider.value() / 100.0 if hasattr(self, "volume_slider") else 0.35)

    def set_volume(self, value):
        self.volume_value.setText(f"{value}%")
        for sound in self.sounds.values():
            sound.set_volume(value / 100.0)

    def play_key_sound(self, key=None):
        """Play key-specific sounds: letters are clicky, digits are creamy."""
        if not self.enabled:
            return

        try:
            if key in MODIFIER_KEYS:
                return
        except TypeError:
            pass

        sound = self.current_sound
        char = getattr(key, "char", None)
        if char is not None:
            char = str(char)

        if char and char.isalpha():
            sound = self.sounds.get("Clicky", sound)
        elif char and char.isdigit():
            sound = self.sounds.get("Creamy", sound)

        if sound:
            try:
                sound.play()
            except Exception:
                pass

    def toggle_listening(self):
        if self.enabled:
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self):
        try:
            self.listener = keyboard.Listener(on_press=self.play_key_sound)
            self.listener.start()
            self.enabled = True
            self.update_status(True)
        except Exception as exc:
            QMessageBox.warning(self, "Keyboard listener error", str(exc))

    def stop_listening(self):
        self.enabled = False
        if self.listener:
            self.listener.stop()
            self.listener = None
        self.update_status(False)

    def update_status(self, active):
        if active:
            self.status_title.setText("Typing sounds are on")
            self.status_detail.setText("Type anywhere to hear your selected profile.")
            self.toggle_button.setText("■  Stop typing sounds")
        else:
            self.status_title.setText("Typing sounds are off")
            self.status_detail.setText("Turn sounds on, then type in any app.")
            self.toggle_button.setText("▶  Start typing sounds")

    def preview_sound(self):
        if self.current_sound:
            self.current_sound.play()

    def set_startup(self, state):
        # Windows startup shortcut is managed through the per-user Run registry key.
        if os.name != "nt":
            self.startup_checkbox.blockSignals(True)
            self.startup_checkbox.setChecked(False)
            self.startup_checkbox.blockSignals(False)
            QMessageBox.information(self, "Windows only", "Startup integration is available on Windows.")
            return
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                if state == Qt.Checked:
                    executable = sys.executable
                    script = str(Path(__file__).resolve())
                    if getattr(sys, "frozen", False):
                        command = f'"{executable}"'
                    else:
                        command = f'"{executable}" "{script}"'
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                    except FileNotFoundError:
                        pass
        except Exception as exc:
            QMessageBox.warning(self, "Startup setting failed", f"Couldn't update the startup setting:\n{exc}")
            self.startup_checkbox.blockSignals(True)
            self.startup_checkbox.setChecked(False)
            self.startup_checkbox.blockSignals(False)

    def closeEvent(self, event):
        self.stop_listening()
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    window = ThockTypeWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
