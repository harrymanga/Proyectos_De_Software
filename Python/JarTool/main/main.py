"""
Main Entry Point
Application entry point and initialization
"""

import sys
import os
from pathlib import Path

# Permite `python main/main.py` desde la raíz sin hacks duplicados
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QIcon

from gui import JarToolWindow
from core import ThemeManager, LanguageManager


def main():
    """Main application entry point"""
    # Create application
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("JarTool")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("JarTool")
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons', 'jartool.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Initialize managers
    theme_manager = ThemeManager()
    language_manager = LanguageManager()
    
    # Apply initial theme and language
    theme_manager.apply_theme(app)
    language_manager.apply_language(app)
    
    # Create and show main window
    window = JarToolWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
