"""
Language Selector UI Component
Professional language selection dialog with search and preview
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton,
    QLineEdit, QDialogButtonBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap


class LanguageSelector(QDialog):
    """Professional language selection dialog"""
    
    language_selected = pyqtSignal(str)
    
    def __init__(self, language_manager, parent=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.setup_ui()
        self.load_languages()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the UI components"""
        self.setWindowTitle("Select Language / Seleccionar Idioma")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Select Language / Seleccionar Idioma")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Search box
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search languages... / Buscar idiomas...")
        self.search_edit.setMinimumHeight(35)
        search_layout.addWidget(self.search_edit)
        main_layout.addLayout(search_layout)
        
        # Language list with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        
        self.language_list = QListWidget()
        self.language_list.setIconSize(Qt.QSize(32, 24))
        self.language_list.setMinimumHeight(300)
        
        scroll_area.setWidget(self.language_list)
        main_layout.addWidget(scroll_area)
        
        # Current language indicator
        self.current_label = QLabel()
        self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_label.setStyleSheet("""
            QLabel {
                background-color: #e8f4f8;
                border: 1px solid #b3d9ff;
                border-radius: 6px;
                padding: 8px;
                margin: 10px 0;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(self.current_label)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def load_languages(self):
        """Load languages into the list"""
        languages_data = self.language_manager.get_language_menu_data()
        
        for lang_data in languages_data:
            item = QListWidgetItem()
            
            # Create display text
            display_text = f"{lang_data['flag']} {lang_data['native_name']}"
            if lang_data['coverage'] < 100:
                display_text += f" ({lang_data['coverage']}%)"
            
            item.setText(display_text)
            item.setData(Qt.ItemDataRole.UserRole, lang_data['code'])
            
            # Highlight current language
            if lang_data['is_current']:
                item.setFont(QFont("", -1, QFont.Weight.Bold))
                item.setForeground(Qt.GlobalColor.blue)
            
            self.language_list.addItem(item)
        
        # Update current language label
        self.update_current_language_label()
    
    def update_current_language_label(self):
        """Update the current language indicator"""
        current_lang = self.language_manager.get_current_language()
        lang_info = self.language_manager.get_language_info(current_lang)
        
        if lang_info:
            text = f"Current: {lang_info['flag']} {lang_info['native_name']}"
            self.current_label.setText(text)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.search_edit.textChanged.connect(self.filter_languages)
        self.language_list.itemDoubleClicked.connect(self.on_language_selected)
        self.language_list.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Setup search timer for debouncing
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
    
    def filter_languages(self, text):
        """Filter languages based on search text"""
        self.search_timer.start(300)  # 300ms debounce
    
    def perform_search(self):
        """Perform the actual search filtering"""
        search_text = self.search_edit.text().lower()
        
        for i in range(self.language_list.count()):
            item = self.language_list.item(i)
            item.setHidden(False)
            
            if search_text:
                item_text = item.text().lower()
                if search_text not in item_text:
                    item.setHidden(True)
    
    def on_language_selected(self, item):
        """Handle language selection"""
        lang_code = item.data(Qt.ItemDataRole.UserRole)
        self.language_selected.emit(lang_code)
        self.accept()
    
    def on_selection_changed(self):
        """Handle selection change"""
        selected_items = self.language_list.selectedItems()
        if selected_items:
            # Enable OK button only if something is selected
            self.findChild(QDialogButtonBox).button(
                QDialogButtonBox.StandardButton.Ok
            ).setEnabled(True)
        else:
            self.findChild(QDialogButtonBox).button(
                QDialogButtonBox.StandardButton.Ok
            ).setEnabled(False)
    
    def get_selected_language(self):
        """Get the selected language code"""
        selected_items = self.language_list.selectedItems()
        if selected_items:
            return selected_items[0].data(Qt.ItemDataRole.UserRole)
        return None


class QuickLanguageSwitcher:
    """Quick language switcher for toolbar"""
    
    def __init__(self, language_manager, parent=None):
        self.language_manager = language_manager
        self.parent = parent
    
    def create_language_menu(self):
        """Create language menu for quick switching"""
        from PyQt6.QtWidgets import QMenu, QAction
        
        menu = QMenu("Language / Idioma", self.parent)
        
        languages_data = self.language_manager.get_language_menu_data()
        
        for lang_data in languages_data:
            action = QAction(
                f"{lang_data['flag']} {lang_data['native_name']}", 
                self.parent
            )
            action.setData(lang_data['code'])
            action.triggered.connect(
                lambda checked, code=lang_data['code']: self.switch_language(code)
            )
            
            if lang_data['is_current']:
                action.setCheckable(True)
                action.setChecked(True)
                action.setEnabled(False)
            
            menu.addAction(action)
        
        return menu
    
    def switch_language(self, language_code):
        """Switch to a different language"""
        if language_code != self.language_manager.get_current_language():
            self.language_manager.save_language(language_code)
            # Emit signal or call callback to update UI
            if hasattr(self.parent, 'on_language_changed'):
                self.parent.on_language_changed(language_code)
