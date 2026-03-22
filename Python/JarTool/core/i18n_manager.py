"""
Internationalization Manager
Efficient multi-language support with best practices
"""

import os
import json
from typing import Dict, Optional
from PyQt6.QtCore import QSettings, QTranslator, QCoreApplication, QLocale
from PyQt6.QtWidgets import QApplication


class I18nManager:
    """Internationalization Manager with support for multiple languages"""
    
    # Language definitions with metadata
    LANGUAGES = {
        'es': {
            'name': 'Español',
            'native_name': 'Español',
            'code': 'es',
            'locale': 'es_ES',
            'flag': '🇪🇸',
            'rtl': False
        },
        'en': {
            'name': 'English',
            'native_name': 'English',
            'code': 'en',
            'locale': 'en_US',
            'flag': '🇺🇸',
            'rtl': False
        },
        'fr': {
            'name': 'Français',
            'native_name': 'Français',
            'code': 'fr',
            'locale': 'fr_FR',
            'flag': '🇫🇷',
            'rtl': False
        },
        'de': {
            'name': 'Deutsch',
            'native_name': 'Deutsch',
            'code': 'de',
            'locale': 'de_DE',
            'flag': '🇩🇪',
            'rtl': False
        },
        'pt': {
            'name': 'Português',
            'native_name': 'Português',
            'code': 'pt',
            'locale': 'pt_BR',
            'flag': '🇧🇷',
            'rtl': False
        },
        'it': {
            'name': 'Italiano',
            'native_name': 'Italiano',
            'code': 'it',
            'locale': 'it_IT',
            'flag': '🇮🇹',
            'rtl': False
        },
        'ja': {
            'name': '日本語',
            'native_name': '日本語',
            'code': 'ja',
            'locale': 'ja_JP',
            'flag': '🇯🇵',
            'rtl': False
        },
        'zh': {
            'name': '中文',
            'native_name': '中文',
            'code': 'zh',
            'locale': 'zh_CN',
            'flag': '🇨🇳',
            'rtl': False
        },
        'ar': {
            'name': 'العربية',
            'native_name': 'العربية',
            'code': 'ar',
            'locale': 'ar_SA',
            'flag': '🇸🇦',
            'rtl': True
        }
    }
    
    def __init__(self):
        self.settings = QSettings('JarTool', 'Language')
        self.current_language = self.load_language()
        self.translator = QTranslator()
        self.fallback_translations = self._load_fallback_translations()
    
    def _load_fallback_translations(self) -> Dict[str, Dict[str, str]]:
        """Load fallback translations from embedded JSON"""
        translations = {}
        
        # Try to load from external file first
        translations_file = os.path.join(os.path.dirname(__file__), '..', 'translations.json')
        if os.path.exists(translations_file):
            try:
                with open(translations_file, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # If no external file, use embedded translations
        if not translations:
            translations = self._get_embedded_translations()
        
        return translations
    
    def _get_embedded_translations(self) -> Dict[str, Dict[str, str]]:
        """Get embedded translations as fallback"""
        return {
            'es': {
                'window_title': 'JarTool - Extrae y comprime archivos JAR',
                'files_group': 'Archivos JAR / Carpetas',
                'actions_group': 'Acciones',
                'extract_radio': 'Extraer archivo JAR',
                'compress_radio': 'Crear archivo JAR desde carpeta',
                'browse': 'Explorar',
                'execute': 'Ejecutar',
                'exit': 'Salir',
                'clear': 'Limpiar',
                'themes': 'Temas',
                'language': 'Idioma',
                'select_jar': 'Seleccionar archivo JAR...',
                'select_folder': 'Seleccionar carpeta a comprimir...',
                'output_dir': 'Directorio de salida...',
                'output_jar': 'Archivo JAR de salida...',
                'log_placeholder': 'Log de operaciones...',
                'warning_title': 'Advertencia',
                'warning_message': 'Por favor seleccione un archivo o carpeta',
                'error_title': 'Error',
                'success_title': 'Éxito',
                'jar_not_exist': 'El archivo JAR no existe',
                'folder_not_exist': 'La carpeta no existe',
                'extract_success': 'Archivo extraído en:',
                'compress_success': 'Archivo JAR creado:',
                'extract_complete': 'Extracción completada',
                'compress_complete': 'Compresión completada',
                'extracting': 'Extrayendo:',
                'compressing': 'Comprimiendo:',
                'destination': 'Destino:',
                'extract_error': 'Error al extraer:',
                'compress_error': 'Error al comprimir:',
                'select_jar_files': 'Seleccionar archivos JAR',
                'select_folders': 'Seleccionar carpetas',
                'select_output_dir': 'Seleccionar directorio de salida',
                'save_jar': 'Guardar archivo JAR',
                'jar_files': 'Archivos JAR (*.jar)',
                'all_files': 'Todos los archivos (*)',
                'custom_folder_dialog': 'Seleccionar carpetas',
                'custom_folder_instruction': 'Seleccione carpetas para comprimir (Haga clic en "Agregar carpeta" para agregar cada carpeta):',
                'add_folder': 'Agregar carpeta',
                'select_folder': 'Seleccionar carpeta',
                'browse_files': 'Examinar archivos',
                'browse_folders': 'Examinar carpetas'
            },
            'en': {
                'window_title': 'JarTool - Extract and compress JAR files',
                'files_group': 'JAR Files / Folders',
                'actions_group': 'Actions',
                'extract_radio': 'Extract JAR file',
                'compress_radio': 'Create JAR file from folder',
                'browse': 'Browse',
                'execute': 'Execute',
                'exit': 'Exit',
                'clear': 'Clear',
                'themes': 'Themes',
                'language': 'Language',
                'select_jar': 'Select JAR file...',
                'select_folder': 'Select folder to compress...',
                'output_dir': 'Output directory...',
                'output_jar': 'Output JAR file...',
                'log_placeholder': 'Operations log...',
                'warning_title': 'Warning',
                'warning_message': 'Please select a file or folder',
                'error_title': 'Error',
                'success_title': 'Success',
                'jar_not_exist': 'The JAR file does not exist',
                'folder_not_exist': 'The folder does not exist',
                'extract_success': 'File extracted in:',
                'compress_success': 'JAR file created:',
                'extract_complete': 'Extraction completed',
                'compress_complete': 'Compression completed',
                'extracting': 'Extracting:',
                'compressing': 'Compressing:',
                'destination': 'Destination:',
                'extract_error': 'Error extracting:',
                'compress_error': 'Error compressing:',
                'select_jar_files': 'Select JAR files',
                'select_folders': 'Select folders',
                'select_output_dir': 'Select output directory',
                'save_jar': 'Save JAR file',
                'jar_files': 'JAR Files (*.jar)',
                'all_files': 'All Files (*)',
                'custom_folder_dialog': 'Select folders',
                'custom_folder_instruction': 'Select folders to compress (click "Add Folder" to add each folder):',
                'add_folder': 'Add Folder',
                'select_folder': 'Select Folder',
                'browse_files': 'Browse files',
                'browse_folders': 'Browse folders'
            }
        }
    
    def get_available_languages(self) -> Dict[str, Dict]:
        """Get all available languages with metadata"""
        return self.LANGUAGES
    
    def get_current_language(self) -> str:
        """Get current language code"""
        return self.current_language
    
    def load_language(self) -> str:
        """Load saved language preference"""
        saved_lang = self.settings.value('language', 'auto', str)
        
        if saved_lang == 'auto':
            # Auto-detect system language
            system_locale = QLocale.system().name()
            return self._map_locale_to_language(system_locale)
        
        # Validate saved language
        if saved_lang in self.LANGUAGES:
            return saved_lang
        
        # Fallback to Spanish
        return 'es'
    
    def save_language(self, language_code: str):
        """Save language preference"""
        if language_code in self.LANGUAGES:
            self.settings.setValue('language', language_code)
            self.current_language = language_code
    
    def translate(self, key: str, context: Optional[str] = None) -> str:
        """Get translation for a key"""
        translations = self.fallback_translations.get(self.current_language, {})
        
        # Try to get translation
        translation = translations.get(key, key)
        
        # If key not found, try English as fallback
        if translation == key and self.current_language != 'en':
            en_translations = self.fallback_translations.get('en', {})
            translation = en_translations.get(key, key)
        
        return translation
    
    def _map_locale_to_language(self, locale_name: str) -> str:
        """Map system locale to supported language code"""
        locale_mapping = {
            'es': 'es', 'es_ES': 'es', 'es_MX': 'es',
            'en': 'en', 'en_US': 'en', 'en_GB': 'en',
            'fr': 'fr', 'fr_FR': 'fr',
            'de': 'de', 'de_DE': 'de', 'de_AT': 'de',
            'pt': 'pt', 'pt_BR': 'pt', 'pt_PT': 'pt',
            'it': 'it', 'it_IT': 'it',
            'ja': 'ja', 'ja_JP': 'ja',
            'zh': 'zh', 'zh_CN': 'zh', 'zh_TW': 'zh',
            'ar': 'ar', 'ar_SA': 'ar', 'ar_EG': 'ar'
        }
        
        return locale_mapping.get(locale_name, 'es')
    
    def apply_language(self, app: QApplication):
        """Apply language to application"""
        # Remove previous translator
        if app.removeTranslator(self.translator):
            pass
        
        # Load and apply new translator
        language_code = self.current_language
        
        # Try to load external translation file
        translations_file = os.path.join(os.path.dirname(__file__), '..', 'translations', f'{language_code}.qm')
        if os.path.exists(translations_file):
            if self.translator.load(app, translations_file):
                app.installTranslator(self.translator)
                return
        
        # Fallback to internal translations
        # (In a real implementation, you would generate .qm files from .ts files)
        pass
    
    def get_language_info(self, language_code: str) -> Optional[Dict]:
        """Get detailed information about a language"""
        return self.LANGUAGES.get(language_code)
    
    def is_rtl_language(self, language_code: str) -> bool:
        """Check if language is right-to-left"""
        lang_info = self.LANGUAGES.get(language_code)
        return lang_info.get('rtl', False) if lang_info else False
