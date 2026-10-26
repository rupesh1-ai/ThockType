
        try:
            if key in MODIFIER_KEYS:
                return
        except TypeError:
            pass

        sound = self.current_sound
        char = getattr(key, "char", None)

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
