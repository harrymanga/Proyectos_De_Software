#!/usr/bin/env python3
"""
Verify all translations are present
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.language_manager import LanguageManager

def verify_translations():
    """Verify all translations exist"""
    print("🔍 Verifying translations...")
    print("=" * 60)
    
    lang_manager = LanguageManager()
    
    # All translation keys used in the code
    used_keys = [
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
        'custom_folder_dialog', 'custom_folder_instruction', 'add_folder'
    ]
    
    print("Checking translations for both languages...")
    
    missing_translations = []
    
    for key in used_keys:
        try:
            es_translation = lang_manager.TRANSLATIONS['es'][key]
            en_translation = lang_manager.TRANSLATIONS['en'][key]
            
            if not es_translation or not en_translation:
                missing_translations.append(f"❌ {key}: Empty translation")
            else:
                print(f"✅ {key}: ES='{es_translation[:30]}...' EN='{en_translation[:30]}...'")
                
        except KeyError:
            missing_translations.append(f"❌ {key}: Missing key")
    
    print("\n" + "=" * 60)
    
    if missing_translations:
        print("❌ MISSING TRANSLATIONS:")
        for missing in missing_translations:
            print(f"   {missing}")
    else:
        print("✅ ALL TRANSLATIONS FOUND!")
    
    print(f"\n📊 Summary:")
    print(f"   Total keys checked: {len(used_keys)}")
    print(f"   Missing translations: {len(missing_translations)}")
    print(f"   Coverage: {((len(used_keys) - len(missing_translations)) / len(used_keys)) * 100:.1f}%")
    
    # Check specific dialog texts
    print("\n" + "=" * 60)
    print("📋 Checking specific dialog texts...")
    
    dialog_checks = [
        ("select_jar_files", "Select JAR files", "Seleccionar archivos JAR"),
        ("select_folders", "Select folders", "Seleccionar carpetas"),
        ("select_output_dir", "Select output directory", "Seleccionar directorio de salida"),
        ("save_jar", "Save JAR file", "Guardar archivo JAR"),
        ("jar_files", "JAR Files (*.jar)", "JAR Files (*.jar)"),
        ("all_files", "All Files (*)", "All Files (*)"),
        ("custom_folder_dialog", "Select folders", "Seleccionar carpetas"),
        ("custom_folder_instruction", "Select folders to compress", "Seleccione carpetas para comprimir"),
        ("add_folder", "Add Folder", "Add Folder")
    ]
    
    for key, en_expected, es_expected in dialog_checks:
        es_actual = lang_manager.TRANSLATIONS['es'].get(key, "MISSING")
        en_actual = lang_manager.TRANSLATIONS['en'].get(key, "MISSING")
        
        print(f"\n🔍 {key}:")
        print(f"   EN: {en_actual}")
        print(f"   ES: {es_actual}")
        
        if en_actual != en_expected:
            print(f"   ⚠️  Expected EN: {en_expected}")
        if es_actual != es_expected:
            print(f"   ⚠️  Expected ES: {es_expected}")

if __name__ == "__main__":
    verify_translations()
