"""
Theme Manager Module
Manages application themes (light/dark)
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
from typing import Dict


class ThemeManager:
    """Manages application themes"""
    
    LIGHT_THEME = {
        'background': '#ffffff',
        'foreground': '#000000',
        'window': '#f0f0f0',
        'button': '#e0e0e0',
        'text': '#000000'
    }
    
    DARK_THEME = {
        'background': '#2b2b2b',
        'foreground': '#ffffff',
        'window': '#3c3c3c',
        'button': '#555555',
        'text': '#ffffff'
    }
    
    def __init__(self):
        self.settings = QSettings('JarTool', 'Theme')
        self.current_theme = self.load_theme()
    
    def load_theme(self) -> str:
        """Load saved theme preference"""
        return self.settings.value('theme', 'light', str)
    
    def save_theme(self, theme: str):
        """Save theme preference"""
        self.settings.setValue('theme', theme)
        self.current_theme = theme
    
    def get_theme(self) -> Dict[str, str]:
        """Get current theme colors"""
        if self.current_theme == 'dark':
            return self.DARK_THEME
        else:
            return self.LIGHT_THEME
    
    def toggle_theme(self) -> str:
        """Toggle between light and dark theme"""
        new_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.save_theme(new_theme)
        return new_theme
    
    def apply_theme(self, app: QApplication):
        """Apply theme to application"""
        theme_colors = self.get_theme()
        
        # Set application stylesheet
        stylesheet = f"""
        QMainWindow {{
            background-color: {theme_colors['background']};
            color: {theme_colors['text']};
        }}
        
        QWidget {{
            background-color: {theme_colors['background']};
            color: {theme_colors['text']};
        }}
        
        QGroupBox {{
            background-color: {theme_colors['window']};
            border: 2px solid {theme_colors['button']};
            border-radius: 5px;
            margin-top: 1ex;
            font-weight: bold;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }}
        
        QPushButton {{
            background-color: {theme_colors['button']};
            border: 1px solid {theme_colors['foreground']};
            border-radius: 3px;
            padding: 5px;
            min-width: 80px;
        }}
        
        QPushButton:hover {{
            background-color: {theme_colors['foreground']};
            color: {theme_colors['background']};
        }}
        
        QPushButton:pressed {{
            background-color: {theme_colors['window']};
        }}
        
        QLineEdit {{
            background-color: {theme_colors['window']};
            border: 1px solid {theme_colors['button']};
            border-radius: 3px;
            padding: 5px;
        }}
        
        QTextEdit {{
            background-color: {theme_colors['window']};
            border: 1px solid {theme_colors['button']};
            border-radius: 3px;
        }}
        
        QRadioButton {{
            spacing: 5px;
        }}
        
        QRadioButton::indicator {{
            width: 13px;
            height: 13px;
        }}
        
        QRadioButton::indicator:unchecked {{
            border: 1px solid {theme_colors['foreground']};
            border-radius: 6px;
            background-color: {theme_colors['window']};
        }}
        
        QRadioButton::indicator:checked {{
            border: 1px solid {theme_colors['foreground']};
            border-radius: 6px;
            background-color: {theme_colors['button']};
        }}
        """
        
        app.setStyleSheet(stylesheet)
