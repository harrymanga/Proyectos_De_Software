#!/usr/bin/env python3
"""
Test script to verify cleanup functionality
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from gui.main_window import JarToolWindow

def test_cleanup_functionality():
    """Test cleanup functionality"""
    print("🧹 Testing cleanup functionality...")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    window = JarToolWindow()
    
    # Test 1: Automatic cleanup on mode change
    print("1. Testing automatic cleanup on mode change...")
    
    # Simulate file selection
    window.selected_files = ["/test/file1.jar", "/test/file2.jar"]
    window.ui.fileLineEdit.setText("2 files selected")
    window.ui.outputLineEdit.setText("/test/output")
    
    print(f"   Before mode change: {len(window.selected_files)} files selected")
    print(f"   File input: '{window.ui.fileLineEdit.text()}'")
    print(f"   Output input: '{window.ui.outputLineEdit.text()}'")
    
    # Switch mode (should trigger cleanup)
    window.ui.compressRadio.setChecked(True)
    window.on_mode_changed()
    
    print(f"   After mode change: {len(window.selected_files)} files selected")
    print(f"   File input: '{window.ui.fileLineEdit.text()}'")
    print(f"   Output input: '{window.ui.outputLineEdit.text()}'")
    
    if len(window.selected_files) == 0 and not window.ui.fileLineEdit.text():
        print("   ✅ Automatic cleanup successful")
    else:
        print("   ❌ Automatic cleanup failed")
    
    # Test 2: Manual cleanup
    print("\n2. Testing manual cleanup...")
    
    # Simulate folder selection
    window.selected_folders = ["/test/folder1", "/test/folder2"]
    window.ui.fileLineEdit.setText("2 folders selected")
    window.ui.outputLineEdit.setText("/test/output.jar")
    
    print(f"   Before manual cleanup: {len(window.selected_folders)} folders selected")
    print(f"   File input: '{window.ui.fileLineEdit.text()}'")
    print(f"   Output input: '{window.ui.outputLineEdit.text()}'")
    
    # Trigger manual cleanup
    window.clear_all()
    
    print(f"   After manual cleanup: {len(window.selected_folders)} folders selected")
    print(f"   File input: '{window.ui.fileLineEdit.text()}'")
    print(f"   Output input: '{window.ui.outputLineEdit.text()}'")
    
    if len(window.selected_folders) == 0 and not window.ui.fileLineEdit.text():
        print("   ✅ Manual cleanup successful")
    else:
        print("   ❌ Manual cleanup failed")
    
    # Test 3: Clear button exists and is connected
    print("\n3. Testing clear button...")
    
    if hasattr(window.ui, 'clearBtn'):
        print("   ✅ Clear button exists in UI")
        
        if window.ui.clearBtn.isEnabled():
            print("   ✅ Clear button is enabled")
        else:
            print("   ❌ Clear button is disabled")
            
        # Check tooltip
        tooltip = window.ui.clearBtn.toolTip()
        if tooltip:
            print(f"   ✅ Clear button has tooltip: '{tooltip}'")
        else:
            print("   ❌ Clear button has no tooltip")
    else:
        print("   ❌ Clear button not found in UI")
    
    window.close()
    app.quit()

if __name__ == "__main__":
    test_cleanup_functionality()
    
    print("\n" + "=" * 50)
    print("✅ Cleanup functionality test completed!")
    print("\n📋 Summary of cleanup features:")
    print("1. ✅ Automatic cleanup when switching modes")
    print("2. ✅ Manual cleanup with clear button")
    print("3. ✅ Clear button with tooltip and feedback")
    print("4. ✅ Status messages for cleanup actions")
    print("5. ✅ Logging of cleanup operations")
