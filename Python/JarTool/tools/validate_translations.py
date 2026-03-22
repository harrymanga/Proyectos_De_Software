#!/usr/bin/env python3
"""
Translation Validation Tool
Validates all translation files for completeness and consistency
"""

import sys
import os
import json
from typing import Dict, List, Set
import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def load_translation_file(file_path: str) -> Dict[str, str]:
    """Load translation file and return as dictionary"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading {file_path}: {e}")
        return {}


def get_all_translation_keys() -> List[str]:
    """Get all expected translation keys from code"""
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


def validate_translations():
    """Validate all translation files"""
    print("🔍 Validating Translation Files")
    print("=" * 50)
    
    translations_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'translations'
    )
    
    if not os.path.exists(translations_dir):
        print(f"❌ Translations directory not found: {translations_dir}")
        return
    
    # Get all translation files
    translation_files = {}
    for file_name in os.listdir(translations_dir):
        if file_name.endswith('.json'):
            lang_code = file_name[:-5]  # Remove .json
            file_path = os.path.join(translations_dir, file_name)
            translation_files[lang_code] = load_translation_file(file_path)
    
    if not translation_files:
        print("❌ No translation files found")
        return
    
    # Get all expected keys
    expected_keys = set(get_all_translation_keys())
    
    # Validate each language
    all_valid = True
    for lang_code, translations in translation_files.items():
        print(f"\n🌍 Validating {lang_code}:")
        
        if not translations:
            print(f"   ❌ Empty translation file")
            all_valid = False
            continue
        
        # Check for missing keys
        translation_keys = set(translations.keys())
        missing_keys = expected_keys - translation_keys
        extra_keys = translation_keys - expected_keys
        
        # Check for empty values
        empty_values = [k for k, v in translations.items() if not v or v.strip() == '']
        
        # Report results
        if missing_keys:
            print(f"   ❌ Missing keys ({len(missing_keys)}): {sorted(missing_keys)}")
            all_valid = False
        
        if extra_keys:
            print(f"   ⚠️  Extra keys ({len(extra_keys)}): {sorted(extra_keys)}")
        
        if empty_values:
            print(f"   ⚠️  Empty values ({len(empty_values)}): {sorted(empty_values)}")
        
        if not missing_keys and not extra_keys and not empty_values:
            print(f"   ✅ All {len(expected_keys)} keys present and valid")
        
        # Calculate coverage
        coverage = len(translation_keys) / len(expected_keys) * 100
        print(f"   📊 Coverage: {coverage:.1f}%")
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print(f"   Languages validated: {len(translation_files)}")
    print(f"   Total keys expected: {len(expected_keys)}")
    
    if all_valid:
        print("   ✅ All translations are valid!")
    else:
        print("   ❌ Some translations have issues")
    
    # Generate report
    generate_validation_report(translation_files, expected_keys)


def generate_validation_report(translation_files: Dict[str, Dict[str, str]], expected_keys: Set[str]):
    """Generate detailed validation report"""
    report = {
        'timestamp': str(datetime.datetime.now()),
        'languages': {},
        'summary': {
            'total_languages': len(translation_files),
            'total_keys': len(expected_keys),
            'all_valid': True
        }
    }
    
    for lang_code, translations in translation_files.items():
        translation_keys = set(translations.keys())
        missing_keys = sorted(list(expected_keys - translation_keys))
        coverage = len(translation_keys) / len(expected_keys) * 100
        
        report['languages'][lang_code] = {
            'total_keys': len(translations),
            'missing_keys': missing_keys,
            'coverage_percent': coverage,
            'is_valid': len(missing_keys) == 0
        }
        
        if len(missing_keys) > 0:
            report['summary']['all_valid'] = False
    
    # Save report
    report_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'translations_validation_report.json'
    )
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Report saved to: {report_file}")
    except Exception as e:
        print(f"\n❌ Error saving report: {e}")


def check_consistency():
    """Check consistency between translation files"""
    print("\n🔍 Checking Translation Consistency")
    print("=" * 50)
    
    translations_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'translations'
    )
    
    # Load all translation files
    all_translations = {}
    for file_name in os.listdir(translations_dir):
        if file_name.endswith('.json'):
            lang_code = file_name[:-5]
            file_path = os.path.join(translations_dir, file_name)
            all_translations[lang_code] = load_translation_file(file_path)
    
    # Check for key consistency
    if len(all_translations) < 2:
        print("❌ Need at least 2 translation files to check consistency")
        return
    
    # Get reference keys (from first file)
    reference_lang = list(all_translations.keys())[0]
    reference_keys = set(all_translations[reference_lang].keys())
    
    # Check each language against reference
    inconsistencies = {}
    for lang_code, translations in all_translations.items():
        if lang_code == reference_lang:
            continue
        
        lang_keys = set(translations.keys())
        
        # Find keys in reference but not in this language
        missing_in_lang = reference_keys - lang_keys
        extra_in_lang = lang_keys - reference_keys
        
        if missing_in_lang or extra_in_lang:
            inconsistencies[lang_code] = {
                'missing': sorted(list(missing_in_lang)),
                'extra': sorted(list(extra_in_lang))
            }
    
    if inconsistencies:
        print("❌ Inconsistencies found:")
        for lang_code, issues in inconsistencies.items():
            print(f"\n   {lang_code}:")
            if issues['missing']:
                print(f"     Missing: {issues['missing']}")
            if issues['extra']:
                print(f"     Extra: {issues['extra']}")
    else:
        print("✅ All translation files are consistent")


if __name__ == "__main__":
    import datetime
    
    print("🌍 JarTool Translation Validator")
    print("Validating translation files for completeness and consistency\n")
    
    validate_translations()
    check_consistency()
    
    print("\n" + "=" * 50)
    print("✅ Validation completed!")
