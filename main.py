"""
main.py - Entry point for the HomeCTRL system tray application.

Initializes the Qt application event loop and launches the system tray icon.
"""

import sys
from PySide6.QtWidgets import QApplication
from ui import TrayApp


def main():
    # Initialize the PySide6 application
    app = QApplication(sys.argv)
    app.setApplicationName("HomeCTRL")
    app.setApplicationDisplayName("HomeCTRL")

    # Keep app running in tray when popup closes
    app.setQuitOnLastWindowClosed(False)

    # Create and display the system tray icon
    tray = TrayApp()
    tray.show()

    print("[HomeCTRL] App started in Windows system tray.")
    print(" - Left-click the lamp icon: Open/close control panel")
    print(" - Right-click the lamp icon: Show menu (Show, Start with Windows, Quit)")

    # Start the Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
