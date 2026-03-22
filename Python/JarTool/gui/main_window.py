"""
Main Window GUI Module
Contains the main application window
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QMessageBox, QApplication,
    QProgressDialog, QProgressBar, QLabel, QHBoxLayout, QWidget
)
from PyQt6.QtCore import QSettings, QTimer, QThread, pyqtSignal, Qt

from core import JarHandler, ThemeManager, LanguageManager
from gui.ui_main_window import Ui_JarToolWindow
from gui.worker_thread import JarWorkerThread


class JarToolWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.ui = Ui_JarToolWindow()
        self.ui.setupUi(self)
        
        # Initialize core components
        self.jar_handler = JarHandler()
        self.theme_manager = ThemeManager()
        self.language_manager = LanguageManager()
        
        # Current selections
        self.selected_files = []
        self.selected_folders = []
        
        # Progress tracking
        self.progress_dialog = None
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress_animation)
        self.worker_thread = None
        
        # Setup connections
        self.setup_connections()
        
        # Apply initial theme and language
        self.update_ui_text()
        self.theme_manager.apply_theme(QApplication.instance())
        
        # Initialize UI state
        self.on_mode_changed()
    
    def setup_connections(self):
        """Setup signal connections"""
        # File/folder selection
        self.ui.browseBtn.clicked.connect(self.browse_files)
        self.ui.outputBrowseBtn.clicked.connect(self.browse_output)
        
        # Actions
        self.ui.actionBtn.clicked.connect(self.execute_action)
        self.ui.clearBtn.clicked.connect(self.clear_all)
        self.ui.exitBtn.clicked.connect(self.close)
        
        # Mode selection
        self.ui.extractRadio.toggled.connect(self.on_mode_changed)
        self.ui.compressRadio.toggled.connect(self.on_mode_changed)
        
        # Theme and language
        self.ui.themeBtn.clicked.connect(self.toggle_theme)
        self.ui.languageBtn.clicked.connect(self.toggle_language)
        
        # Add visual feedback for buttons
        self.setup_button_feedback()
    
    def setup_button_feedback(self):
        """Setup visual feedback for buttons"""
        # Enable hover effects
        buttons = [
            self.ui.browseBtn, self.ui.outputBrowseBtn, self.ui.actionBtn,
            self.ui.clearBtn, self.ui.exitBtn, self.ui.themeBtn, self.ui.languageBtn
        ]
        
        for button in buttons:
            # Set cursor to hand pointer
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Add tooltip with action description
            if button == self.ui.browseBtn:
                button.setToolTip("Select files or folders to process")
            elif button == self.ui.outputBrowseBtn:
                button.setToolTip("Choose output location")
            elif button == self.ui.actionBtn:
                button.setToolTip("Start the selected operation")
            elif button == self.ui.clearBtn:
                button.setToolTip("Clear all selections and inputs")
            elif button == self.ui.exitBtn:
                button.setToolTip("Close the application")
            elif button == self.ui.themeBtn:
                button.setToolTip("Toggle between light and dark themes")
            elif button == self.ui.languageBtn:
                button.setToolTip("Switch between Spanish and English")
    
    def update_ui_text(self):
        """Update UI text based on current language"""
        lang = self.language_manager
        
        self.setWindowTitle(lang.translate('window_title'))
        self.ui.groupBox.setTitle(lang.translate('files_group'))
        self.ui.groupBox_2.setTitle(lang.translate('actions_group'))
        self.ui.extractRadio.setText(lang.translate('extract_radio'))
        self.ui.compressRadio.setText(lang.translate('compress_radio'))
        self.ui.browseBtn.setText(lang.translate('browse'))
        self.ui.outputBrowseBtn.setText(lang.translate('browse'))
        self.ui.actionBtn.setText(lang.translate('execute'))
        self.ui.clearBtn.setText(lang.translate('clear'))
        self.ui.exitBtn.setText(lang.translate('exit'))
        self.ui.themeBtn.setText(lang.translate('themes'))
        self.ui.languageBtn.setText(lang.translate('language'))
        self.ui.logTextEdit.setPlaceholderText(lang.translate('log_placeholder'))
        
        # Update placeholders based on mode
        self.on_mode_changed()
    
    def on_mode_changed(self):
        """Handle mode change between extract and compress"""
        lang = self.language_manager
        
        # Clear previous selections and inputs
        self.clear_selections()
        
        if self.ui.extractRadio.isChecked():
            self.ui.fileLineEdit.setPlaceholderText(lang.translate('select_jar'))
            self.ui.outputLineEdit.setPlaceholderText(lang.translate('output_dir'))
            self.ui.browseBtn.setText(lang.translate('browse'))
        else:
            self.ui.fileLineEdit.setPlaceholderText(lang.translate('select_folder'))
            self.ui.outputLineEdit.setPlaceholderText(lang.translate('output_jar'))
            self.ui.browseBtn.setText(lang.translate('browse'))
    
    def clear_all(self):
        """Manually clear all selections and inputs"""
        lang = self.language_manager
        
        # Clear selections
        self.selected_files = []
        self.selected_folders = []
        
        # Clear input fields
        self.ui.fileLineEdit.clear()
        self.ui.outputLineEdit.clear()
        
        # Log the manual cleanup
        self.log("Manual cleanup: All selections and inputs cleared")
        
        # Show status message
        self.statusBar().showMessage(lang.translate('clear'), 2000)
    
    def clear_selections(self):
        """Clear all selections and input fields"""
        # Clear selections
        self.selected_files = []
        self.selected_folders = []
        
        # Clear input fields
        self.ui.fileLineEdit.clear()
        self.ui.outputLineEdit.clear()
        
        # Clear log (optional - keep recent history)
        # self.ui.logTextEdit.clear()
        
        # Log the cleanup
        mode = "Extraction" if self.ui.extractRadio.isChecked() else "Compression"
        self.log(f"Switched to {mode} mode - selections cleared")
    
    def browse_files(self):
        """Browse for files or folders based on mode"""
        lang = self.language_manager
        
        if self.ui.extractRadio.isChecked():
            # Select multiple JAR files
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, 
                lang.translate('select_jar_files'),
                "",
                f"{lang.translate('jar_files')};;{lang.translate('all_files')}"
            )
            
            if file_paths:
                self.selected_files = file_paths
                
                # Show detailed information
                total_size = sum(os.path.getsize(f) for f in file_paths if os.path.exists(f))
                size_mb = total_size / (1024 * 1024)
                
                display_text = f"{len(file_paths)} files ({size_mb:.1f} MB)"
                self.ui.fileLineEdit.setText(display_text)
                
                # Log detailed information
                self.log(f"Selected {len(file_paths)} JAR files ({size_mb:.1f} MB total)")
                for file_path in file_paths[:3]:  # Show first 3 files
                    file_size = os.path.getsize(file_path) / 1024  # KB
                    self.log(f"  - {os.path.basename(file_path)} ({file_size:.1f} KB)")
                
                if len(file_paths) > 3:
                    self.log(f"  ... and {len(file_paths) - 3} more files")
        
        else:
            # Select multiple folders using a custom dialog
            from PyQt6.QtWidgets import QInputDialog, QListWidget, QVBoxLayout, QDialog
            
            # Create a custom dialog for folder selection
            dialog = QDialog(self)
            dialog.setWindowTitle(lang.translate('custom_folder_dialog'))
            dialog.setMinimumWidth(500)
            dialog.setMinimumHeight(400)
            
            layout = QVBoxLayout(dialog)
            
            # Instructions
            from PyQt6.QtWidgets import QLabel
            instructions = QLabel(lang.translate('custom_folder_instruction'))
            layout.addWidget(instructions)
            
            # List widget for selected folders
            folder_list = QListWidget()
            layout.addWidget(folder_list)
            
            # Add folder button
            from PyQt6.QtWidgets import QPushButton
            add_btn = QPushButton(lang.translate('add_folder'))
            layout.addWidget(add_btn)
            
            # Dialog buttons
            from PyQt6.QtWidgets import QDialogButtonBox
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            # Add folder functionality
            def add_folder():
                folder_path = QFileDialog.getExistingDirectory(
                    dialog,
                    lang.translate('select_folder_dialog'),
                    "",
                    QFileDialog.Option.ShowDirsOnly
                )
                if folder_path:
                    # Check if already added
                    for i in range(folder_list.count()):
                        if folder_list.item(i).text() == folder_path:
                            return
                    
                    folder_list.addItem(folder_path)
            
            add_btn.clicked.connect(add_folder)
            
            # Show dialog
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.selected_folders = []
                for i in range(folder_list.count()):
                    self.selected_folders.append(folder_list.item(i).text())
                
                if self.selected_folders:
                    # Calculate total size
                    total_size = 0
                    for folder_path in self.selected_folders:
                        total_size += self.get_folder_size(folder_path)
                    
                    size_mb = total_size / (1024 * 1024)
                    
                    display_text = f"{len(self.selected_folders)} folders ({size_mb:.1f} MB)"
                    self.ui.fileLineEdit.setText(display_text)
                    
                    self.log(f"Selected {len(self.selected_folders)} folders ({size_mb:.1f} MB total)")
                    for folder_path in self.selected_folders[:3]:  # Show first 3 folders
                        folder_size = self.get_folder_size(folder_path) / (1024 * 1024)  # MB
                        self.log(f"  - {os.path.basename(folder_path)} ({folder_size:.1f} MB)")
                    
                    if len(self.selected_folders) > 3:
                        self.log(f"  ... and {len(self.selected_folders) - 3} more folders")
    
    def get_folder_size(self, folder_path):
        """Calculate total size of a folder"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except (OSError, PermissionError):
            pass
        return total_size
    
    def browse_output(self):
        """Browse for output location"""
        lang = self.language_manager
        
        if self.ui.extractRadio.isChecked():
            # Select output directory
            dir_path = QFileDialog.getExistingDirectory(
                self, 
                lang.translate('select_output_dir'),
                ""
            )
            
            if dir_path:
                self.ui.outputLineEdit.setText(dir_path)
                self.log(f"Output directory: {dir_path}")
        
        else:
            # Select output directory for JAR files
            dir_path = QFileDialog.getExistingDirectory(
                self, 
                lang.translate('select_output_dir'),
                ""
            )
            
            if dir_path:
                # Auto-generate JAR filename from selected folder name
                if self.selected_folders:
                    folder_name = os.path.basename(self.selected_folders[0])
                    jar_filename = f"{folder_name}.jar"
                    full_jar_path = os.path.join(dir_path, jar_filename)
                    self.ui.outputLineEdit.setText(full_jar_path)
                    self.log(f"Output JAR: {full_jar_path}")
                else:
                    self.ui.outputLineEdit.setText(dir_path)
                    self.log(f"Output directory: {dir_path}")
    
    def execute_action(self):
        """Execute the selected action"""
        lang = self.language_manager
        
        if self.ui.extractRadio.isChecked():
            self.extract_jars()
        else:
            self.compress_folders()
    
    def create_progress_dialog(self, title, maximum):
        """Create and setup progress dialog"""
        self.progress_dialog = QProgressDialog(title, "Cancel", 0, maximum, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        
        # Add custom progress bar with better styling
        progress_bar = QProgressBar()
        progress_bar.setTextVisible(True)
        progress_bar.setFormat("%v / %m (%p%)")
        self.progress_dialog.setBar(progress_bar)
        
        # Add status label
        self.progress_dialog.setLabelText("Starting...")
        
        return self.progress_dialog
    
    def update_progress_animation(self):
        """Update progress animation"""
        if self.progress_dialog and self.progress_dialog.isVisible():
            # Add visual feedback
            current_value = self.progress_dialog.value()
            if current_value < self.progress_dialog.maximum():
                self.progress_dialog.setValue(current_value)
    
    def extract_jars(self):
        """Extract selected JAR files with progress dialog"""
        lang = self.language_manager
        
        if not self.selected_files:
            QMessageBox.warning(
                self, 
                lang.translate('warning_title'),
                lang.translate('warning_message')
            )
            return
        
        output_dir = self.ui.outputLineEdit.text().strip()
        
        # Create progress dialog
        total_files = len(self.selected_files)
        progress_dialog = self.create_progress_dialog(
            lang.translate('extracting'), 
            total_files
        )
        
        # Create and setup worker thread
        self.worker_thread = JarWorkerThread(
            'extract', 
            self.selected_files, 
            output_dir if output_dir else None
        )
        
        # Connect signals
        self.worker_thread.progress_updated.connect(
            lambda current, total, filename: self.update_progress(current, total, filename)
        )
        self.worker_thread.operation_completed.connect(
            lambda results: self.on_extraction_completed(results, output_dir)
        )
        self.worker_thread.operation_failed.connect(
            lambda error: self.on_operation_failed(error)
        )
        self.worker_thread.log_message.connect(self.log)
        
        # Connect cancel button
        progress_dialog.canceled.connect(self.worker_thread.stop)
        
        # Start operation
        self.worker_thread.start()
        progress_dialog.exec()
    
    def update_progress(self, current, total, filename):
        """Update progress dialog"""
        if self.progress_dialog:
            self.progress_dialog.setValue(current)
            self.progress_dialog.setLabelText(f"Processing: {filename}")
            self.statusBar().showMessage(f"Processing {current}/{total}: {filename}", 1000)
    
    def on_extraction_completed(self, results, output_dir):
        """Handle extraction completion"""
        lang = self.language_manager
        
        if self.progress_dialog:
            self.progress_dialog.close()
        
        processed = results.get('processed', 0)
        total = len(self.selected_files)
        
        if processed == total:
            QMessageBox.information(
                self,
                lang.translate('success_title'),
                f"{lang.translate('extract_success')}\n{output_dir or 'Current directory'}\n\nProcessed {processed} files"
            )
            self.statusBar().showMessage(f"{lang.translate('extract_complete')} ({processed}/{total})", 3000)
        else:
            QMessageBox.warning(
                self,
                lang.translate('warning_title'),
                f"Extracted {processed} of {total} files"
            )
        
        self.log(f"Extraction complete: {processed}/{total} files")
    
    def on_operation_failed(self, error_message):
        """Handle operation failure"""
        lang = self.language_manager
        
        if self.progress_dialog:
            self.progress_dialog.close()
        
        self.log(f"Operation failed: {error_message}")
        QMessageBox.critical(
            self,
            lang.translate('error_title'),
            f"Operation failed: {error_message}"
        )
    
    def compress_folders(self):
        """Compress selected folders with progress dialog"""
        lang = self.language_manager
        
        if not self.selected_folders:
            QMessageBox.warning(
                self,
                lang.translate('warning_title'),
                lang.translate('warning_message')
            )
            return
        
        output_dir = self.ui.outputLineEdit.text().strip()
        
        # Handle output directory - if it's a full path to a JAR, extract directory
        if output_dir and output_dir.endswith('.jar'):
            output_dir = os.path.dirname(output_dir)
        
        # Create progress dialog
        total_folders = len(self.selected_folders)
        progress_dialog = self.create_progress_dialog(
            lang.translate('compressing'), 
            total_folders
        )
        
        # Create and setup worker thread
        self.worker_thread = JarWorkerThread(
            'compress', 
            self.selected_folders, 
            output_dir if output_dir else None
        )
        
        # Connect signals
        self.worker_thread.progress_updated.connect(
            lambda current, total, filename: self.update_progress(current, total, filename)
        )
        self.worker_thread.operation_completed.connect(
            lambda results: self.on_compression_completed(results, output_dir)
        )
        self.worker_thread.operation_failed.connect(
            lambda error: self.on_operation_failed(error)
        )
        self.worker_thread.log_message.connect(self.log)
        
        # Connect cancel button
        progress_dialog.canceled.connect(self.worker_thread.stop)
        
        # Start operation
        self.worker_thread.start()
        progress_dialog.exec()
    
    def on_compression_completed(self, results, output_dir):
        """Handle compression completion"""
        lang = self.language_manager
        
        if self.progress_dialog:
            self.progress_dialog.close()
        
        processed = results.get('processed', 0)
        total = len(self.selected_folders)
        
        # Generate detailed success message
        if processed == total:
            success_details = []
            for folder_path in self.selected_folders:
                folder_name = os.path.basename(folder_path)
                if output_dir:
                    jar_path = os.path.join(output_dir, f"{folder_name}.jar")
                else:
                    jar_path = f"{folder_name}.jar"
                success_details.append(f"• {folder_name} → {jar_path}")
            
            details_text = "\n".join(success_details)
            
            QMessageBox.information(
                self,
                lang.translate('success_title'),
                f"{lang.translate('compress_success')}\n\n{details_text}\n\nOutput directory: {output_dir or 'Current directory'}\n\nProcessed {processed} folders"
            )
            self.statusBar().showMessage(f"{lang.translate('compress_complete')} ({processed}/{total})", 3000)
        else:
            QMessageBox.warning(
                self,
                lang.translate('warning_title'),
                f"Compressed {processed} of {total} folders"
            )
        
        self.log(f"Compression complete: {processed}/{total} folders")
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        new_theme = self.theme_manager.toggle_theme()
        self.theme_manager.apply_theme(QApplication.instance())
        self.log(f"Theme changed to: {new_theme}")
        self.statusBar().showMessage(f"Theme: {new_theme}", 2000)
    
    def toggle_language(self):
        """Show language selector dialog"""
        self.show_language_selector()
    
    def show_language_selector(self):
        """Show professional language selector dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QLabel, QHBoxLayout, QDialogButtonBox
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Language / Seleccionar Idioma")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title = QLabel("🌍 Select Language")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Language list
        lang_list = QListWidget()
        lang_data = self.language_manager.get_language_menu_data()
        
        for lang in lang_data:
            item = QListWidgetItem(f"{lang['flag']} {lang['native_name']}")
            item.setData(Qt.ItemDataRole.UserRole, lang['code'])
            if lang['is_current']:
                item.setFont(QFont("", -1, QFont.Weight.Bold))
                item.setForeground(Qt.GlobalColor.blue)
            lang_list.addItem(item)
        
        layout.addWidget(lang_list)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_item = lang_list.currentItem()
            if selected_item:
                lang_code = selected_item.data(Qt.ItemDataRole.UserRole)
                self.change_language(lang_code)
    
    def change_language(self, lang_code):
        """Change application language"""
        if self.language_manager.set_language(lang_code):
            self.language_manager.apply_language(QApplication.instance())
            self.update_ui_text()
            
            lang_info = self.language_manager.get_language_info(lang_code)
            lang_name = lang_info['native_name'] if lang_info else lang_code
            
            self.log(f"Language changed to: {lang_name}")
            self.statusBar().showMessage(f"Language: {lang_name}", 3000)
    
    def create_language_menu(self):
        """Create language selection menu for toolbar"""
        from PyQt6.QtWidgets import QMenu, QAction
        
        menu = QMenu("Language", self)
        
        lang_data = self.language_manager.get_language_menu_data()
        for lang in lang_data:
            action = QAction(f"{lang['flag']} {lang['native_name']}", self)
            action.setData(lang['code'])
            if lang['is_current']:
                action.setCheckable(True)
                action.setChecked(True)
            action.triggered.connect(lambda checked, code=lang['code']: self.change_language(code))
            menu.addAction(action)
        
        return menu
    
    def log(self, message):
        """Add timestamped message to log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.ui.logTextEdit.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.ui.logTextEdit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
