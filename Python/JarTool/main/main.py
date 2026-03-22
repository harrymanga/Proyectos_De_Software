"""
Main Entry Point
Application entry point and initialization
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
