"""
Language Manager V2 - Enhanced with Multi-language Support
Improved version following best practices
"""

import os
from typing import Dict, List, Optional
from PyQt6.QtCore import QSettings, QTranslator, QCoreApplication
from .i18n_manager import I18nManager


class LanguageManagerV2:
    """Enhanced Language Manager with multi-language support"""
    
    def __init__(self):
        self.settings = QSettings('JarTool', 'Language')
        self.i18n = I18nManager()
        self.current_language = self.load_language()
        self.translator = QTranslator()
    
    def load_language(self) -> str:
        """Load saved language preference with auto-detection"""
        saved_lang = self.settings.value('language', 'auto', str)
        
        if saved_lang == 'auto':
            # Auto-detect system language
            return self.i18n._map_locale_to_language(
                QCoreApplication.instance().locale().name()
            )
        
        # Validate saved language
        available_languages = self.get_available_languages()
        if saved_lang in available_languages:
            return saved_lang
        
        # Fallback to system detection or Spanish
        system_lang = self.i18n._map_locale_to_language(
            QCoreApplication.instance().locale().name()
        )
        return system_lang if system_lang in available_languages else 'es'
    
    def save_language(self, language_code: str):
        """Save language preference"""
        available_languages = self.get_available_languages()
        if language_code in available_languages:
            self.settings.setValue('language', language_code)
            self.current_language = language_code
    
    def translate(self, key: str, context: Optional[str] = None) -> str:
        """Get translation for a key with fallback support"""
        return self.i18n.translate(key)
    
    def get_available_languages(self) -> List[str]:
        """Get list of available language codes"""
        return list(self.i18n.get_available_languages().keys())
    
    def get_current_language(self) -> str:
        """Get current language code"""
        return self.current_language
    
    def get_language_display_name(self, language_code: str) -> str:
        """Get display name for language"""
        lang_info = self.i18n.get_language_info(language_code)
        if lang_info:
            return lang_info.get('native_name', language_code)
        return language_code
    
    def apply_language(self, app):
        """Apply language to application"""
        self.i18n.apply_language(app)
    
    def get_language_menu_data(self) -> List[Dict]:
        """Get language data for menu/selection UI"""
        languages = []
        for code, info in self.i18n.get_available_languages().items():
            languages.append({
                'code': code,
                'name': info.get('name', code),
                'native_name': info.get('native_name', code),
                'flag': info.get('flag', '🌐'),
                'is_current': code == self.current_language,
                'is_rtl': info.get('rtl', False)
            })
        
        # Sort by name, but keep current language first
        current_langs = [lang for lang in languages if lang['is_current']]
        other_langs = sorted([lang for lang in languages if not lang['is_current']], 
                           key=lambda x: x['name'])
        
        return current_langs + other_langs
    
    def get_translation_coverage(self) -> Dict[str, float]:
        """Get translation coverage statistics"""
        translations = self.i18n.fallback_translations
        coverage = {}
        
        for lang_code, lang_translations in translations.items():
            total_keys = len(self._get_all_translation_keys())
            translated_keys = len([k for k in self._get_all_translation_keys() 
                                   if k in lang_translations and lang_translations[k]])
            coverage[lang_code] = (translated_keys / total_keys) * 100 if total_keys > 0 else 0
        
        return coverage
    
    def _get_all_translation_keys(self) -> List[str]:
        """Get all possible translation keys"""
        return [
            'window_title', 'files_group', 'actions_group',
            'extract_radio', 'compress_radio', 'browse', 'execute',
            'exit', 'clear', 'themes', 'language',
            'select_jar', 'select_folder', 'output_dir', 'output_jar',
            'log_placeholder', 'warning_title', 'warning_message',
            'error_title', 'success_title', 'jar_not_exist',
            'folder_not_exist', 'extract_success', 'compress_success',
            'extract_complete', 'compress_complete', 'extracting',
            'compressing', 'destination', 'extract_error',
            'compress_error', 'select_jar_files', 'select_folders',
            'select_output_dir', 'save_jar', 'jar_files', 'all_files',
            'custom_folder_dialog', 'custom_folder_instruction', 'add_folder',
            'select_folder', 'browse_files', 'browse_folders'
        ]
