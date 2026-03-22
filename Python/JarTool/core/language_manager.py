"""
Language Manager Module - Enhanced Multi-Language Support
Manages application language with support for ES, EN, FR, DE, PT, AR
"""

import os
import json
from PyQt6.QtCore import QCoreApplication, QSettings, QTranslator, Qt, QLocale
from PyQt6.QtWidgets import QApplication
from typing import Dict, List, Optional


class LanguageManager:
    """Manages application languages with multi-language support"""
    
    # Supported languages with metadata
    SUPPORTED_LANGUAGES = {
        'es': {'name': 'Español', 'native_name': 'Español', 'flag': '🇪🇸', 'rtl': False},
        'en': {'name': 'English', 'native_name': 'English', 'flag': '🇺🇸', 'rtl': False},
        'fr': {'name': 'Français', 'native_name': 'Français', 'flag': '🇫🇷', 'rtl': False},
        'de': {'name': 'Deutsch', 'native_name': 'Deutsch', 'flag': '🇩🇪', 'rtl': False},
        'pt': {'name': 'Português', 'native_name': 'Português', 'flag': '🇧🇷', 'rtl': False},
        'ar': {'name': 'العربية', 'native_name': 'العربية', 'flag': '🇸🇦', 'rtl': True}
    }
    
    TRANSLATIONS = {
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
            'add_folder': 'Agregar Carpeta',
            'select_folder_dialog': 'Seleccionar Carpeta',
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
            'select_folder_dialog': 'Select Folder',
            'browse_files': 'Browse files',
            'browse_folders': 'Browse folders'
        }
    }
    
    def __init__(self):
        self.settings = QSettings('JarTool', 'Language')
        self.current_language = self.load_language()
        self.translator = QTranslator()
        self._translations_cache = {}
        self._load_all_translations()
    
    def _load_all_translations(self):
        """Load translations from JSON files for all supported languages"""
        translations_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'translations'
        )
        
        for lang_code in self.SUPPORTED_LANGUAGES.keys():
            translation_file = os.path.join(translations_dir, f'{lang_code}.json')
            
            try:
                with open(translation_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Remove metadata key if present
                    data.pop('_metadata', None)
                    self._translations_cache[lang_code] = data
            except (FileNotFoundError, json.JSONDecodeError):
                # Fallback to empty dict
                self._translations_cache[lang_code] = {}
    
    def _detect_language_from_locale(self, locale_name: str) -> str:
        """Detect language from system locale"""
        locale_map = {
            'es': 'es', 'es_ES': 'es', 'es_MX': 'es', 'es_AR': 'es',
            'en': 'en', 'en_US': 'en', 'en_GB': 'en', 'en_CA': 'en',
            'fr': 'fr', 'fr_FR': 'fr', 'fr_CA': 'fr', 'fr_BE': 'fr',
            'de': 'de', 'de_DE': 'de', 'de_AT': 'de', 'de_CH': 'de',
            'pt': 'pt', 'pt_BR': 'pt', 'pt_PT': 'pt',
            'ar': 'ar', 'ar_SA': 'ar', 'ar_EG': 'ar'
        }
        return locale_map.get(locale_name, 'es')
    
    def load_language(self) -> str:
        """Load saved language preference with auto-detection"""
        saved_lang = self.settings.value('language', 'auto', str)
        
        if saved_lang == 'auto':
            # Auto-detect system language
            system_locale = QLocale.system().name()
            detected = self._detect_language_from_locale(system_locale)
            if detected in self.SUPPORTED_LANGUAGES:
                return detected
        
        # Validate saved language
        if saved_lang in self.SUPPORTED_LANGUAGES:
            return saved_lang
        
        # Default to Spanish
        return 'es'
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return list(self.SUPPORTED_LANGUAGES.keys())
    
    def get_language_info(self, lang_code: str) -> Optional[Dict]:
        """Get language metadata"""
        return self.SUPPORTED_LANGUAGES.get(lang_code)
    
    def set_language(self, language: str) -> bool:
        """Set specific language"""
        if language in self.SUPPORTED_LANGUAGES:
            self.save_language(language)
            return True
        return False
    
    def save_language(self, language: str):
        """Save language preference"""
        self.settings.setValue('language', language)
        self.current_language = language
    
    def get_current_language(self) -> str:
        """Get current language"""
        return self.current_language
    
    def toggle_language(self) -> str:
        """Toggle to next available language"""
        languages = self.get_supported_languages()
        current_index = languages.index(self.current_language)
        next_index = (current_index + 1) % len(languages)
        new_language = languages[next_index]
        self.save_language(new_language)
        return new_language
    
    def translate(self, key: str) -> str:
        """Get translation for a key with fallback"""
        # Try current language
        translation = self._translations_cache.get(self.current_language, {}).get(key)
        if translation:
            return translation
        
        # Fallback to English
        if self.current_language != 'en':
            translation = self._translations_cache.get('en', {}).get(key)
            if translation:
                return translation
        
        # Fallback to Spanish
        if self.current_language != 'es':
            translation = self._translations_cache.get('es', {}).get(key)
            if translation:
                return translation
        
        # Return key if no translation found
        return key
    
    def is_rtl_language(self, lang_code: str = None) -> bool:
        """Check if language is right-to-left"""
        if lang_code is None:
            lang_code = self.current_language
        lang_info = self.SUPPORTED_LANGUAGES.get(lang_code)
        return lang_info.get('rtl', False) if lang_info else False
    
    def get_language_menu_data(self) -> List[Dict]:
        """Get language data for menu display"""
        menu_data = []
        for code, info in self.SUPPORTED_LANGUAGES.items():
            menu_data.append({
                'code': code,
                'name': info['name'],
                'native_name': info['native_name'],
                'flag': info['flag'],
                'is_current': code == self.current_language,
                'is_rtl': info['rtl']
            })
        
        # Sort: current first, then alphabetically
        current = [d for d in menu_data if d['is_current']]
        others = sorted([d for d in menu_data if not d['is_current']], key=lambda x: x['name'])
        return current + others
    
    def apply_language(self, app: QApplication):
        """Apply language to application with RTL support"""
        # Remove previous translator
        app.removeTranslator(self.translator)
        
        # Check if RTL layout is needed
        if self.is_rtl_language():
            app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        
        # Reload translations
        self._load_all_translations()
