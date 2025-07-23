#!/usr/bin/env python3
"""
PyTorrent - A Python Qt5 Torrent Client
Main application entry point
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from torrent_client import TorrentClient

def main():
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("PyTorrent")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PyTorrent")
    
    # Set application icon
    try:
        import os
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.svg')
        if os.path.exists(icon_path):
            # For SVG support, we'd need to convert to pixmap
            # For now, use system default
            pass
        # Set a default icon from system
        app.setWindowIcon(app.style().standardIcon(app.style().SP_ComputerIcon))
    except Exception:
        pass  # Fallback to no icon
    
    # Create and show the main window
    client = TorrentClient()
    client.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 