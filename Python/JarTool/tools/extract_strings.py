#!/usr/bin/env python3
"""
String Extraction Tool
Extracts all translatable strings from source code
"""

import sys
import os
import re
from typing import List, Set
from pathlib import Path


def extract_strings_from_file(file_path: str) -> List[str]:
    """Extract translatable strings from a source file"""
    strings = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match lang.translate('key') calls
        pattern = r"lang\.translate\(\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(pattern, content)
        strings.update(matches)
        
        # Pattern to match _translate() calls
        pattern2 = r"_translate\(\s*['\"]([^'\"]+)['\"]"
        matches2 = re.findall(pattern2, content)
        strings.update(matches2)
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
    
    return sorted(list(strings))


def extract_strings_from_directory(directory: str) -> Set[str]:
    """Extract strings from all Python files in directory"""
    all_strings = set()
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                strings = extract_strings_from_file(file_path)
                all_strings.update(strings)
    
    return all_strings


def generate_translation_template(strings: List[str], output_dir: str):
    """Generate translation template files"""
    print(f"\n📝 Generating translation templates in {output_dir}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate template for each language
    languages = {
        'es': 'Español',
        'en': 'English',
        'fr': 'Français',
        'de': 'Deutsch',
        'pt': 'Português',
        'it': 'Italiano',
        'ja': '日本語',
        'zh': '中文',
        'ar': 'العربية'
    }
    
    for lang_code, lang_name in languages.items():
        template = {
            '_metadata': {
                'language': lang_name,
                'code': lang_code,
                'generated': str(datetime.datetime.now()),
                'total_keys': len(strings)
            }
        }
        
        # Add all keys with empty values (except English)
        for key in strings:
            if lang_code == 'en':
                # For English, try to extract from existing translations
                template[key] = extract_english_value(key)
            else:
                template[key] = ""
        
        # Save template file
        template_file = os.path.join(output_dir, f"{lang_code}_template.json")
        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            print(f"   ✅ Generated: {lang_code}_template.json")
        except Exception as e:
            print(f"   ❌ Error generating {lang_code}_template.json: {e}")


def extract_english_value(key: str) -> str:
    """Try to extract existing English translation"""
    # Try to load existing English translations
    en_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        '..', 'translations', 'en.json'
    )
    
    try:
        with open(en_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            return translations.get(key, key)
    except:
        return key


def analyze_strings_usage(strings: List[str]):
    """Analyze usage patterns of translatable strings"""
    print(f"\n📊 String Usage Analysis")
    print("=" * 40)
    
    # Group strings by category
    categories = {
        'ui_elements': [],
        'messages': [],
        'titles': [],
        'placeholders': [],
        'other': []
    }
    
    for string in strings:
        if any(keyword in string.lower() for keyword in ['title', 'window']):
            categories['titles'].append(string)
        elif any(keyword in string.lower() for keyword in ['placeholder', 'select', 'browse']):
            categories['placeholders'].append(string)
        elif any(keyword in string.lower() for keyword in ['error', 'warning', 'success', 'message']):
            categories['messages'].append(string)
        elif any(keyword in string.lower() for keyword in ['button', 'radio', 'group']):
            categories['ui_elements'].append(string)
        else:
            categories['other'].append(string)
    
    # Print analysis
    for category, items in categories.items():
        if items:
            print(f"\n📁 {category.replace('_', ' ').title()}: {len(items)}")
            for item in items[:5]:  # Show first 5
                print(f"   - {item}")
            if len(items) > 5:
                print(f"   ... and {len(items) - 5} more")


def main():
    """Main extraction function"""
    print("🔍 JarTool String Extraction Tool")
    print("Extracting translatable strings from source code\n")
    
    # Get project root
    project_root = os.path.dirname(os.path.dirname(__file__))
    
    # Extract strings from core and gui directories
    core_strings = extract_strings_from_directory(os.path.join(project_root, 'core'))
    gui_strings = extract_strings_from_directory(os.path.join(project_root, 'gui'))
    
    # Combine all strings
    all_strings = sorted(list(set(core_strings) | set(gui_strings)))
    
    print(f"📋 Extraction Results:")
    print(f"   Core strings: {len(core_strings)}")
    print(f"   GUI strings: {len(gui_strings)}")
    print(f"   Total unique strings: {len(all_strings)}")
    
    # Analyze usage
    analyze_strings_usage(all_strings)
    
    # Generate templates
    output_dir = os.path.join(project_root, 'translation_templates')
    generate_translation_template(all_strings, output_dir)
    
    # Generate strings list
    strings_file = os.path.join(output_dir, 'all_strings.txt')
    try:
        with open(strings_file, 'w', encoding='utf-8') as f:
            for string in all_strings:
                f.write(f"{string}\n")
        print(f"\n📄 Strings list saved to: {strings_file}")
    except Exception as e:
        print(f"\n❌ Error saving strings list: {e}")
    
    print(f"\n✅ Extraction completed!")
    print(f"📁 Templates generated in: {output_dir}")
    print(f"\n📝 Next steps:")
    print(f"   1. Translate the template files")
    print(f"   2. Save as lang_code.json in translations/ directory")
    print(f"   3. Run validation: python tools/validate_translations.py")


if __name__ == "__main__":
    import datetime
    import json
    
    main()
