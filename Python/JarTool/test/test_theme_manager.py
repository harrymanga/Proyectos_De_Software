"""
Test Theme Manager Module
Tests for theme management functionality
"""

import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.theme_manager import ThemeManager


class TestThemeManager(unittest.TestCase):
    """Test cases for ThemeManager class"""
    
    def setUp(self):
        """Setup test environment"""
        # Mock QSettings to avoid affecting actual settings
        with patch('core.theme_manager.QSettings') as mock_settings:
            mock_settings.return_value.value.return_value = 'light'
            self.theme_manager = ThemeManager()
    
    def test_init(self):
        """Test ThemeManager initialization"""
        self.assertIsNotNone(self.theme_manager.LIGHT_THEME)
        self.assertIsNotNone(self.theme_manager.DARK_THEME)
        self.assertIn(self.theme_manager.current_theme, ['light', 'dark'])
    
    def test_get_theme_light(self):
        """Test getting light theme"""
        self.theme_manager.current_theme = 'light'
        theme = self.theme_manager.get_theme()
        
        self.assertEqual(theme, self.theme_manager.LIGHT_THEME)
        self.assertEqual(theme['background'], '#ffffff')
    
    def test_get_theme_dark(self):
        """Test getting dark theme"""
        self.theme_manager.current_theme = 'dark'
        theme = self.theme_manager.get_theme()
        
        self.assertEqual(theme, self.theme_manager.DARK_THEME)
        self.assertEqual(theme['background'], '#2b2b2b')
    
    def test_toggle_theme(self):
        """Test toggling between themes"""
        original_theme = self.theme_manager.current_theme
        
        new_theme = self.theme_manager.toggle_theme()
        
        self.assertNotEqual(new_theme, original_theme)
        self.assertEqual(new_theme, self.theme_manager.current_theme)
        
        # Toggle back
        new_theme = self.theme_manager.toggle_theme()
        
        self.assertEqual(new_theme, original_theme)
    
    @patch('core.theme_manager.QApplication')
    def test_apply_theme(self, mock_app):
        """Test applying theme to application"""
        self.theme_manager.current_theme = 'dark'
        
        self.theme_manager.apply_theme(mock_app)
        
        # Check that setStyleSheet was called
        mock_app.setStyleSheet.assert_called_once()
        
        # Get the stylesheet that was applied
        call_args = mock_app.setStyleSheet.call_args[0][0]
        self.assertIn('background-color: #2b2b2b', call_args)
        self.assertIn('color: #ffffff', call_args)
    
    def test_theme_colors(self):
        """Test theme color definitions"""
        light_theme = self.theme_manager.LIGHT_THEME
        dark_theme = self.theme_manager.DARK_THEME
        
        # Check that both themes have required keys
        required_keys = ['background', 'foreground', 'window', 'button', 'text']
        
        for key in required_keys:
            self.assertIn(key, light_theme)
            self.assertIn(key, dark_theme)
        
        # Check that themes are different
        self.assertNotEqual(light_theme['background'], dark_theme['background'])
        self.assertNotEqual(light_theme['text'], dark_theme['text'])


if __name__ == '__main__':
    unittest.main()
