"""
Test Language Manager Module
Tests for language management functionality
"""

import unittest
import os
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.language_manager import LanguageManager


class TestLanguageManager(unittest.TestCase):
    """Test cases for LanguageManager class"""
    
    def setUp(self):
        """Setup test environment"""
        # Mock QSettings to avoid affecting actual settings
        with patch('core.language_manager.QSettings') as mock_settings:
            mock_settings.return_value.value.return_value = 'es'
            self.language_manager = LanguageManager()
    
    def test_init(self):
        """Test LanguageManager initialization"""
        self.assertIsNotNone(self.language_manager.TRANSLATIONS)
        self.assertIn('es', self.language_manager.TRANSLATIONS)
        self.assertIn('en', self.language_manager.TRANSLATIONS)
        self.assertIn(self.language_manager.current_language, ['es', 'en'])
    
    def test_get_current_language(self):
        """Test getting current language"""
        current = self.language_manager.get_current_language()
        self.assertIn(current, ['es', 'en'])
        self.assertEqual(current, self.language_manager.current_language)
    
    def test_translate_spanish(self):
        """Test Spanish translation"""
        self.language_manager.current_language = 'es'
        
        translation = self.language_manager.translate('window_title')
        
        self.assertEqual(translation, 'JarTool - Extrae y comprime archivos JAR')
    
    def test_translate_english(self):
        """Test English translation"""
        self.language_manager.current_language = 'en'
        
        translation = self.language_manager.translate('window_title')
        
        self.assertEqual(translation, 'JarTool - Extract and compress JAR files')
    
    def test_translate_missing_key(self):
        """Test translation with missing key"""
        translation = self.language_manager.translate('non_existent_key')
        
        self.assertEqual(translation, 'non_existent_key')
    
    def test_toggle_language(self):
        """Test toggling between languages"""
        original_lang = self.language_manager.current_language
        
        new_lang = self.language_manager.toggle_language()
        
        self.assertNotEqual(new_lang, original_lang)
        self.assertEqual(new_lang, self.language_manager.current_language)
        
        # Toggle back
        new_lang = self.language_manager.toggle_language()
        
        self.assertEqual(new_lang, original_lang)
    
    def test_translations_completeness(self):
        """Test that both languages have all required keys"""
        spanish_keys = set(self.language_manager.TRANSLATIONS['es'].keys())
        english_keys = set(self.language_manager.TRANSLATIONS['en'].keys())
        
        self.assertEqual(spanish_keys, english_keys)
        
        # Check for essential keys
        essential_keys = [
            'window_title', 'files_group', 'actions_group',
            'extract_radio', 'compress_radio', 'browse', 'execute',
            'exit', 'themes', 'language'
        ]
        
        for key in essential_keys:
            self.assertIn(key, spanish_keys)
            self.assertIn(key, english_keys)
    
    def test_translation_values_not_empty(self):
        """Test that all translation values are non-empty"""
        for lang in ['es', 'en']:
            translations = self.language_manager.TRANSLATIONS[lang]
            
            for key, value in translations.items():
                self.assertIsInstance(value, str)
                self.assertTrue(len(value.strip()) > 0)
    
    @patch('core.language_manager.QApplication')
    def test_apply_language(self, mock_app):
        """Test applying language to application"""
        # Test with English (default)
        self.language_manager.current_language = 'en'
        
        self.language_manager.apply_language(mock_app)
        
        # Test with Spanish
        self.language_manager.current_language = 'es'
        
        self.language_manager.apply_language(mock_app)
        
        # Should not raise any exceptions
        mock_app.removeTranslator.assert_called()
    
    def test_spanish_translations(self):
        """Test specific Spanish translations"""
        self.language_manager.current_language = 'es'
        
        expected_translations = {
            'window_title': 'JarTool - Extrae y comprime archivos JAR',
            'extract_radio': 'Extraer archivo JAR',
            'compress_radio': 'Crear archivo JAR desde carpeta',
            'browse': 'Explorar',
            'execute': 'Ejecutar',
            'exit': 'Salir'
        }
        
        for key, expected_value in expected_translations.items():
            actual_value = self.language_manager.translate(key)
            self.assertEqual(actual_value, expected_value)
    
    def test_english_translations(self):
        """Test specific English translations"""
        self.language_manager.current_language = 'en'
        
        expected_translations = {
            'window_title': 'JarTool - Extract and compress JAR files',
            'extract_radio': 'Extract JAR file',
            'compress_radio': 'Create JAR file from folder',
            'browse': 'Browse',
            'execute': 'Execute',
            'exit': 'Exit'
        }
        
        for key, expected_value in expected_translations.items():
            actual_value = self.language_manager.translate(key)
            self.assertEqual(actual_value, expected_value)


if __name__ == '__main__':
    unittest.main()
